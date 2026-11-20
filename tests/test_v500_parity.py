"""v0.50 parity (INV-GV-PARITY-01/02, INV-GV-TEL-01): older presets replay byte-identically against the v0.49 golden;
the v0.50 flags at their v0.49 values reproduce v049_roster; telemetry changes no gameplay."""

import functools
import json
import unittest

from tests.parity_v049 import capture as c49


def _run(config_name, players, seed, **ov):
    from sim.config import GameConfig
    import random

    from sim.engine import GameEngine
    from sim.entities import get_random_companies, get_random_setup, get_random_white_hats

    classes = c49._bot_classes()
    rng = random.Random(seed)
    bots = [classes[(seed * players + i) % len(classes)](i) for i in range(players)]
    rng.shuffle(bots)
    for i, b in enumerate(bots):
        b.player_id = i
    variants, version_deck = get_random_setup(rng, profile="STANDARD")
    companies = get_random_companies(players, rng)
    white_hats = get_random_white_hats(players, rng)
    cfg = getattr(GameConfig, config_name)(
        num_players=players, starting_money=6, starting_gray_dice=3, starting_purple_dice=1,
        starting_purple_reserve=1, corruption_track_profile="STANDARD", enable_corporate_asymmetry=True, **ov)
    return GameEngine(config=cfg, bots=bots, seed=seed, variant_cards=variants, version_deck=version_deck,
                      companies=companies, white_hats=white_hats).run_game()


def _digest(res):
    import hashlib

    payload = {"end": str(getattr(res.end_reason, "value", res.end_reason)), "rounds": res.total_rounds,
               "winners": sorted(res.winner_ids), "wipeout": bool(res.is_total_wipeout), "rankings": res.rankings,
               "snapshots": [t.player_snapshots for t in res.telemetry_history]}
    return hashlib.sha1(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


class TestV049Golden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(c49.GOLDEN_PATH) as fh:
            cls.golden = json.load(fh)

    def test_t_par_1_golden_complete(self):
        self.assertEqual(len(self.golden), len(c49.CONFIGS) * len(c49.PLAYERS) * len(c49.SEEDS))

    def test_t_par_1_v049_replays_golden(self):
        bad = [k for k, v in self.golden.items()
               if c49.digest(k.split("|")[0], int(k.split("|")[1]), int(k.split("|")[2])) != v]
        self.assertEqual(bad, [], f"{len(bad)} parity mismatches, first: {bad[:5]}")


class TestV050Neutral(unittest.TestCase):
    def test_t_par_3_flags_at_v049_values_equal_v049_roster(self):
        """INV-GV-PARITY-02: v050_roster with every v0.50 flag back at its v0.49 value digests like v049_roster."""
        neutral = dict(gray_face_profile="V048_SPRINT", pen_test_l2_breakthrough="NONE",
                       bot_research_mode="THINNING_AWARE", gray_vuln_telemetry=False)
        bad = []
        for players in (2, 3, 4):
            for seed in range(42, 72):
                a = _digest(_run("v050_roster", players, seed, **neutral))
                if a != self_golden(players, seed):
                    bad.append((players, seed))
        self.assertEqual(bad, [])

    def test_t_par_4_telemetry_changes_no_gameplay(self):
        """INV-GV-TEL-01."""
        for seed in range(42, 62):
            on = _run("v050_roster", 3, seed, gray_vuln_telemetry=True)
            off = _run("v050_roster", 3, seed, gray_vuln_telemetry=False)
            key = lambda r: (r.end_reason, r.total_rounds, sorted(r.winner_ids),  # noqa: E731
                             [(x["player_id"], x["secrets"]) for x in r.rankings])
            self.assertEqual(key(on), key(off), seed)
            self.assertIn("gray_le3_round", on.rankings[0])
            self.assertNotIn("gray_le3_round", off.rankings[0])


def self_golden(players, seed):
    return _golden()[f"v049_roster|{players}|{seed}"]


@functools.lru_cache(maxsize=1)
def _golden():
    with open(c49.GOLDEN_PATH) as fh:
        return json.load(fh)


if __name__ == "__main__":
    unittest.main()
