"""v0.38.0 web flow (Phase 49 Phase B): ``GameConfig.v038c()`` is the web default.

Covers the config choice, Secret faces to the Processing Box, Glitched Shield Slots, Any-only shields, the Market
Leader Bonus on Red Secret banks (Phase 5) and at game end, retired-term hygiene in the web UI text, and a fuzz run
of complete games with random human decisions (invariants checked after every action).
"""

from __future__ import annotations

import json
import os
import random
import re
import unittest

from sim.config import DieColor, GameConfig, ShieldColor
from sim.engine import secret_faces
from web.game_controller import GameController

ROOT = os.path.join(os.path.dirname(__file__), "..")


# ---------------------------------------------------------------------------
# Random human driver (every decision comes from the public controller API / capabilities)
# ---------------------------------------------------------------------------
def _zone_ids(p):
    return {
        "ready": [d.die_id for d in p.ready_for_release_dice],
        "prod": [d.die_id for d in p.in_production_dice],
        "proc": [d.die_id for d in p.glitched_dice],
        "scan": [d.die_id for d in p.scanned_dice],
        "contractor": [d.die_id for d in p.contractor_dice],
    }


def check_invariants(gc: GameController) -> None:
    st = gc.state
    cfg = st.config
    for p in st.players:
        z = _zone_ids(p)
        # a die is in at most one CI/CD zone (Contractors may sit In Production too)
        permanent = z["ready"] + z["prod"] + z["proc"] + z["scan"]
        mid_roll = gc.phase == 1 and gc.player_meta[p.player_id].get("has_rolled") and not gc.player_meta[p.player_id].get("has_committed")
        if not mid_roll:
            assert len(permanent) == len(set(permanent)), f"die in two zones for player {p.player_id}: {z}"
        # Processing Box holds only Secret-pending dice (nothing else can enter it in v0.38.0)
        for d in p.glitched_dice:
            assert d.secret_pending and d.color != DieColor.WHITE, f"non-Secret die in Processing Box: {d}"
        for d in p.ready_for_release_dice + p.scanned_dice + p.in_production_dice:
            assert not d.secret_pending, "Secret-pending die outside the Processing Box"
        seqs = [d.processing_entry_seq for d in p.glitched_dice]
        assert seqs == sorted(seqs) and len(set(seqs)) == len(seqs), "Processing Box not in entry order"
        assert 0 <= p.glitched_shield_slots <= p.defense_capacity, "Glitched Shield Slots out of range"
        if not p.is_patient_zero:
            assert 0 <= p.market_share <= p.market_share_max
        shields = [d for d in p.in_production_dice if d.production_role is not None and d.production_role.value.endswith("SHIELD")]
        assert all(d.production_role.value == "ANY_SHIELD" for d in shields), "non-Any shield deployed"
    assert cfg.secret_face_enabled and cfg.glitched_shield_slots_enabled


def _pick(rng, seq):
    seq = list(seq)
    return rng.choice(seq) if seq else None


def _phase1(gc, pid, rng):
    meta = gc.player_meta[pid]
    p = gc.state.players[pid]
    caps = gc.get_action_capabilities(pid)
    if not meta["has_rolled"]:
        if caps["can_operator"] and rng.random() < 0.3:
            gc.hire_contractors(pid, rng.randint(1, 2), use_operator_ability=True)
        elif caps["can_hire_contractors"] and rng.random() < 0.4:
            gc.hire_contractors(pid, 1)
        gc.roll_pool(pid)
        return
    if not meta["has_committed"]:
        rolled = meta["rolled_pool"]
        r = rng.random()
        if caps["can_override_face_helix"] and r < 0.3 and rolled:
            i = rng.randrange(len(rolled))
            legal = [k for k, f in enumerate(rolled[i].faces) if not f.is_star]
            gc.override_face(pid, i, rng.choice(legal), "helix")
            return
        if caps["can_override_face_prodigy"] and r < 0.5 and len(rolled) > 1:
            stars = {k for k, d in enumerate(rolled) if d.current_face and d.current_face.star_code == "PURPLE_STAR"}
            for i in rng.sample(range(len(rolled)), len(rolled)):
                if i in stars:
                    continue
                legal = [k for k, f in enumerate(rolled[i].faces) if not f.is_star and not f.secrets_pending]
                if legal:
                    gc.override_face(pid, i, rng.choice(legal), "prodigy")
                    break
            return
        if caps["can_reroll"] and rng.random() < 0.6:
            pool = [i for i, d in enumerate(rolled) if not d.is_locked or meta.get("prodigy_active")]
            if pool:
                n = rng.randint(1, len(pool))
                gc.perform_reroll(pid, rng.sample(pool, n), use_prodigy_ability=bool(caps["can_prodigy"] and rng.random() < 0.3))
                return
        # commit: random shield subset (invalid picks are never submitted), random choices, random slot cleaners
        shield_idx = [i for i, d in enumerate(rolled) if d.current_face and d.current_face.is_shield and not d.current_face.is_glitch]
        chosen = {i: "any" for i in shield_idx if rng.random() < 0.8}
        decl = {i: rng.randrange(len(d.current_face.choices)) for i, d in enumerate(rolled)
                if d.current_face and d.current_face.is_choice}
        cleaners = [i for i in shield_idx if rng.random() < 0.5]
        gc.commit_defenses(pid, chosen, decl, cleaners)
        return
    gc.compile_drop()


def _phase3(gc, pid, rng):
    p = gc.state.players[pid]
    caps = gc.get_action_capabilities(pid)
    burn = None
    diag = None
    if caps["can_spook_burn"] and rng.random() < 0.5:
        owned = [d for d in p.total_dice if d.color not in (DieColor.GRAY, DieColor.WHITE)]
        if owned:
            burn = rng.choice(owned).die_id
    if caps["can_phreaker_diagnostics"] and rng.random() < 0.7:
        zone = list(p.under_development_dice)
        if zone:
            diag = rng.choice(zone).die_id
    gc.confirm_income(pid, spook_burn_die_id=burn, phreaker_die_id=diag)


def _phase5(gc, pid, rng):
    info = gc.pending_graduation[pid]
    ids = [c["die_id"] for c in info["candidates"]]
    k = rng.randint(0, info["n"])
    grads = rng.sample(ids, min(k, len(ids)))
    splice = None
    if info["splice_available"] and info["processing_box"] and rng.random() < 0.6:
        splice = rng.choice(info["processing_box"])["die_id"]
    gc.choose_graduates(pid, grads, splice_die_id=splice)


def _phase6(gc, pid, rng):
    caps = gc.get_action_capabilities(pid)
    if caps["pending_breakthrough"] is not None:
        opts = caps["pending_breakthrough"]["options"]
        if rng.random() < 0.5 and opts.get("can_accept", opts.get("available", False)):
            gray = opts.get("gray_die_ids") or [None]
            gc.resolve_breakthrough(pid, accept=True, gray_die_id=gray[0], color=_pick(rng, opts.get("colors") or ["red"]))
        else:
            gc.resolve_breakthrough(pid, accept=False)
        return
    options = []
    for c, ok in caps["can_buy"].items():
        if ok:
            options.append(("buy", c))
    for t, ok in caps["can_upgrade_track"].items():
        if ok and t != "patent":
            options.append(("upgrade", t))
    if caps["can_regain_market_share"]:
        options.append(("regain", None))
    if caps["can_ad_campaign"]:
        options.append(("star", "R2"))
    for code in ("B2", "Y1", "P1"):
        if caps["can_star"].get(code):
            options.append(("star", code))
    options += [("end", None)] * 3
    kind, arg = rng.choice(options)
    if kind == "buy":
        gc.buy_die(pid, arg)
    elif kind == "upgrade":
        gc.upgrade_track(pid, arg)
    elif kind == "regain":
        gc.regain_market_share(pid)
    elif kind == "star":
        gc.execute_star_action(pid, arg)
    else:
        gc.end_turn(pid)


def play_random_game(seed: int, check_each: bool = True, max_steps: int = 4000) -> GameController:
    rng = random.Random(seed * 7919 + 13)
    n = 2 + seed % 3
    gc = GameController()
    humans = [{"is_human": i == 0 or (seed % 5 == 0 and i == 1)} for i in range(n)]
    gc.new_game(num_players=n, seed=seed, randomize_cards=True, players_config=humans)
    for _ in range(max_steps):
        if gc.phase == 7:
            break
        ph = gc.phase
        humans_alive = [pid for pid, m in gc.player_meta.items() if m["is_human"] and not gc.state.players[pid].is_patient_zero]
        if ph == 1:
            if not humans_alive:
                gc.compile_drop()
            else:
                todo = [pid for pid in humans_alive if not gc.player_meta[pid]["has_committed"]]
                _phase1(gc, rng.choice(todo) if todo else humans_alive[0], rng)
        elif ph == 2:
            gc.compile_drop()
        elif ph == 3:
            _phase3(gc, rng.choice([p for p in humans_alive if not gc.player_meta[p].get("income_confirmed")]), rng)
        elif ph == 4:
            pid = rng.choice([p for p in humans_alive if p not in gc.attack_resolved_pids])
            alloc = {c: rng.randint(0, 3) for c in ("red", "blue", "green")}
            caps = gc.get_action_capabilities(pid)
            aegis = rng.choice(["decline", "none"]) if caps["can_aegis_echo"] and rng.random() < 0.3 else None
            gc.confirm_attacks(pid, any_shield_allocations=alloc, aegis_color=aegis, use_slush_fund=rng.random() < 0.3)
        elif ph == 5:
            _phase5(gc, rng.choice(list(gc.pending_graduation)), rng)
        elif ph == 6:
            _phase6(gc, gc.active_player_index, rng)
        else:
            raise AssertionError(f"unexpected phase {ph}")
        if check_each:
            check_invariants(gc)
        json.dumps(gc.get_full_state(), default=str)
    assert gc.phase == 7, f"seed {seed}: game did not finish"
    return gc


class TestWebV038Config(unittest.TestCase):
    def test_default_is_v038c(self):
        for n, secrets, ms in ((2, 3, 13), (3, 4, 16), (4, 4, 17)):
            gc = GameController()
            st = gc.new_game(num_players=n, seed=5)
            self.assertEqual(gc.state.config, GameConfig.v038c(num_players=n, enable_corporate_asymmetry=True))
            self.assertEqual(st["rules_version"], "v0.38.0")
            self.assertTrue(st["is_secret_faces"] and st["is_glitched_slots"] and st["is_round_leader_bonus"])
            self.assertEqual(st["round_leader_bonus_schedule"][:2], [3, 1])
            self.assertEqual(st["version_share_payout"], {})
            p0 = st["players"][0]
            self.assertEqual((p0["secrets"], p0["market_share"], p0["market_share_max"], p0["regain_cost"]), (secrets, ms, ms, 3))
            self.assertEqual(p0["defense_capacity"], 2)
            colors = [d["color"] for d in p0["ready_for_release_dice"]]
            self.assertEqual(sorted(colors), sorted(["gray", "gray", "purple", p0["company_color"]]))

    def test_v037_still_selectable(self):
        gc = GameController()
        st = gc.new_game(num_players=3, seed=5, rules_version="v0.37.0")
        self.assertEqual(gc.state.config, GameConfig.v037(num_players=3, enable_corporate_asymmetry=True))
        self.assertEqual(st["rules_version"], "v0.37.0")
        self.assertFalse(st["is_secret_faces"])
        with self.assertRaises(ValueError):
            GameController().new_game(num_players=2, rules_version="v9")


class TestWebV038Flow(unittest.TestCase):
    def _fresh(self, n=2, seed=3):
        gc = GameController()
        gc.new_game(num_players=n, seed=seed)
        return gc

    def _to_phase5(self, gc):
        """Phase 2 with an empty tower drop (Compile Buffer Overflow: no attacks, Phase 4 resolves itself)."""
        gc.state.tower.drop = lambda cup, rng: {c: 0 for c in cup}
        gc.compile_drop()
        gc.confirm_income(0)
        if gc.phase == 4:
            gc.confirm_attacks(0, any_shield_allocations={})

    def _secret_face(self, die):
        return next(f for f in die.faces if f.secrets_pending)

    def test_secret_face_goes_to_processing_box_and_banks_in_phase5(self):
        gc = self._fresh()
        p = gc.state.players[0]
        gc.roll_pool(0)
        rolled = gc.player_meta[0]["rolled_pool"]
        target = next(d for d in rolled if d.color not in (DieColor.GRAY, DieColor.WHITE))
        for d in rolled:
            if d is not target and d.current_face.secrets_pending:
                d.current_face = next(f for f in d.faces if not f.secrets_pending and not f.is_star)
        target.current_face = self._secret_face(target)
        secrets_before = p.secrets
        gc.commit_defenses(0, {})
        self.assertEqual([d.die_id for d in p.glitched_dice], [target.die_id])
        self.assertTrue(target.secret_pending)
        self.assertNotIn(target.die_id, [d.die_id for d in p.in_production_dice])
        self.assertEqual(p.secrets, secrets_before)  # nothing banked until it leaves the Processing Box
        st = gc.get_full_state()
        self.assertEqual([d["die_id"] for d in st["players"][0]["processing_box_dice"]], [target.die_id])
        self.assertEqual(st["players"][0]["processing_box_dice"][0]["secret_yield"], secret_faces.secret_yield(gc.state.config, p, target.color))
        # roll out Phase 2-4 with no exits
        self._to_phase5(gc)
        self.assertEqual(gc.phase, 5)
        if gc.pending_graduation:
            gc.choose_graduates(0, None)
        self.assertEqual(len(p.glitched_dice), 0)
        self.assertGreater(p.secrets, secrets_before)

    def test_secret_face_cannot_be_committed_as_shield(self):
        gc = self._fresh()
        gc.roll_pool(0)
        rolled = gc.player_meta[0]["rolled_pool"]
        d = next(d for d in rolled if d.color not in (DieColor.GRAY, DieColor.WHITE))
        d.current_face = self._secret_face(d)
        with self.assertRaises(ValueError):
            gc.commit_defenses(0, {rolled.index(d): "any"})

    def test_color_shields_are_rejected(self):
        gc = self._fresh()
        gc.roll_pool(0)
        rolled = gc.player_meta[0]["rolled_pool"]
        for d in rolled:
            d.current_face = d.faces[0]
        idx = next(i for i, d in enumerate(rolled) if d.current_face.is_shield)
        with self.assertRaises(ValueError):
            gc.commit_defenses(0, {idx: "red"})

    def test_glitched_slots_limit_shields_and_can_be_cleaned_by_a_shield_die(self):
        gc = self._fresh()
        p = gc.state.players[0]
        p.glitched_shield_slots = 1  # capacity 2 -> 1 effective
        gc.roll_pool(0)
        rolled = gc.player_meta[0]["rolled_pool"]
        grays = [d for d in rolled if d.color == DieColor.GRAY]
        for d in grays:
            d.current_face = next(f for f in d.faces if f.is_shield)
        for d in rolled:
            if d.color != DieColor.GRAY:
                d.current_face = next(f for f in d.faces if not f.is_shield and not f.is_star and not f.secrets_pending
                                      and not f.is_glitch and not f.clean_slots and not any(c.clean_slots for c in f.choices))
        idx = [i for i, d in enumerate(rolled) if d.color == DieColor.GRAY]
        gc.commit_defenses(0, {i: "any" for i in idx}, None, [idx[0]])
        self.assertEqual(p.glitched_shield_slots, 0)  # cleaned by the die
        self.assertIn(grays[0].die_id, [d.die_id for d in p.scanned_dice])  # that die went to the Scanned Box
        self.assertEqual(len(gc.player_meta[0]["shield_slots"]["any"]), 1)

    def test_phase5_market_leader_bonus_after_red_secret_bank(self):
        gc = self._fresh()
        p0, p1 = gc.state.players
        gc.roll_pool(0)
        rolled = gc.player_meta[0]["rolled_pool"]
        red = next((d for d in rolled if d.color == DieColor.RED), None)
        if red is None:  # company colour decides; force a Red die into the pool
            from sim.entities import create_colored_die

            red = create_colored_die(color=DieColor.RED, die_id=99, variant_card=gc.state.variant_cards[DieColor.RED],
                                     face_profile=gc.state.config.die_face_profile)
            p0.ready_for_release_dice.append(red)
            rolled.append(red)
        red.current_face = self._secret_face(red)
        p0.market_share, p1.market_share = 10, 5
        gc.commit_defenses(0, {})
        self._to_phase5(gc)
        if gc.pending_graduation:
            gc.choose_graduates(0, None)
        self.assertTrue(gc.state.red_secret_banked_this_round)
        self.assertTrue(any(e.startswith("MARKET LEADER BONUS (Red Secret") for e in gc.event_log))
        st = gc.get_full_state()
        self.assertEqual(st["last_round_bonus"]["gains"]["0"], 3)
        self.assertEqual(st["last_round_bonus"]["gains"]["1"], 1)

    def test_end_screen_has_game_end_bonus(self):
        awarded = 0
        for seed in range(12):
            gc = play_random_game(seed, check_each=False)
            fr = gc.final_result
            json.dumps(fr, default=str)
            self.assertEqual(fr["game_end_bonus_awarded"], not fr["is_total_wipeout"])
            for r in fr["rankings"]:
                self.assertEqual(r["secrets"], r["secrets_before_bonus"] + r["end_bonus"])
            awarded += int(fr["game_end_bonus_awarded"])
        self.assertGreater(awarded, 0)

    def test_triage_is_oldest_first_without_choice(self):
        gc = self._fresh()
        p = gc.state.players[0]
        from sim.entities import create_colored_die

        dice = []
        for i, c in enumerate((DieColor.GREEN, DieColor.RED, DieColor.BLUE)):
            d = create_colored_die(color=c, die_id=200 + i, variant_card=gc.state.variant_cards[c],
                                   face_profile=gc.state.config.die_face_profile)
            secret_faces.enter_processing_box(p, d, 1)
            dice.append(d)
        p.triage_bandwidth = 2
        moved = [d.die_id for d in secret_faces.triage_order(gc.state.config, p, p.glitched_dice)][:2]
        self.assertEqual(moved, [200, 201])
        view = gc.get_full_state()["players"][0]["processing_box_dice"]
        self.assertEqual([(v["die_id"], v["will_triage"]) for v in view], [(200, True), (201, True), (202, False)])


class TestWebV038Http(unittest.TestCase):
    """The real HTTP server defaults to v0.38.0 and exposes the new Phase 1 endpoints."""

    @classmethod
    def setUpClass(cls):
        import threading

        from web.server import create_server

        cls.server = create_server(host="127.0.0.1", port=0)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, path, data):
        import urllib.error
        import urllib.request

        req = urllib.request.Request(self.base + path, data=json.dumps(data).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            return json.loads(exc.read())

    def test_new_game_defaults_and_rules_version(self):
        st = self._post("/api/game/new", {"num_players": 3, "seed": 4})["state"]
        self.assertEqual((st["rules_version"], st["is_secret_faces"]), ("v0.38.0", True))
        st = self._post("/api/game/new", {"num_players": 3, "seed": 4, "rules_version": "v0.37.0"})["state"]
        self.assertEqual((st["rules_version"], st["is_secret_faces"]), ("v0.37.0", False))
        self.assertFalse(self._post("/api/game/new", {"num_players": 3, "rules_version": "nope"})["success"])

    def test_phase1_endpoints(self):
        self._post("/api/game/new", {"num_players": 2, "seed": 9})
        st = self._post("/api/game/action/roll", {"player_id": 0})["state"]
        me = st["players"][0]
        self.assertTrue(all("faces" in d for d in me["rolled_pool"]))  # faces for the override pickers
        bad = self._post("/api/game/action/commit", {"player_id": 0, "commitments": {"0": "red"}})
        self.assertFalse(bad["success"])  # colour shields no longer exist
        st = self._post("/api/game/action/commit", {"player_id": 0, "commitments": {}, "slot_cleaner_indices": []})["state"]
        self.assertEqual(st["phase"], 2)
        self.assertEqual(self._post("/api/game/action/hotfix", {"player_id": 0, "die_index": 0})["success"], False)


class TestRetiredTermsInWebUi(unittest.TestCase):
    RETIRED = [
        "Glitched Box", "Color-Specific Shield", "Red Shield", "Blue Shield", "Green Shield", "Two-Stage",
        "Hash Match", "Defensive Shield Sacrifice", "Consultancy", "Lead Consultant", "CISO", "Unpatched Zone",
        "Zero Wear Retention", "Malware Fizzle", "Net Wipeout Score", "Emergency Hotfix", "Passive Firewall",
        "Personal Reserve Procurement", "Unpaid Ransom", "Ransomware", "Financial Wiretap", "Cryptographic Patent",
        "Patent Filing", "FinSec", "Ransom Insurance", "Threat Bounty", "Short Squeeze",
    ]

    def _web_text(self):
        """User-visible text: JS / HTML / CSS in full, Python string literals (docstrings and comments excluded)."""
        import ast

        out = {}
        for base in ("web/static", "web/controller", "web/server.py", "web/schemas.py"):
            path = os.path.join(ROOT, base)
            files = [path] if os.path.isfile(path) else [
                os.path.join(d, f) for d, _, fs in os.walk(path) for f in fs if f.endswith((".js", ".html", ".css", ".py"))]
            for f in files:
                with open(f, encoding="utf-8") as fh:
                    text = fh.read()
                if f.endswith(".py"):
                    tree = ast.parse(text)
                    doc_ids = set()
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                            body = node.body
                            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                                doc_ids.add(id(body[0].value))
                    text = "\n".join(n.value for n in ast.walk(tree)
                                     if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in doc_ids)
                out[os.path.relpath(f, ROOT)] = text
        return out

    def test_no_retired_terms_in_user_visible_text(self):
        bad = []
        for name, text in self._web_text().items():
            for term in self.RETIRED:
                for m in re.finditer(re.escape(term), text):
                    line = text[:m.start()].count("\n") + 1
                    bad.append(f"{name}:{line}: {term}")
        self.assertEqual(bad, [])


class TestRandomHumanFuzz(unittest.TestCase):
    GAMES = int(os.environ.get("WEB_FUZZ_GAMES", "320"))

    def test_random_human_games(self):
        stats = {"secret_faces": 0, "cleaned": 0, "bonus_rounds": 0, "collapse": 0, "games": 0}
        for seed in range(self.GAMES):
            try:
                gc = play_random_game(seed, check_each=(seed % 4 == 0))
            except Exception as exc:  # surface the seed
                raise AssertionError(f"fuzz seed {seed} failed: {type(exc).__name__}: {exc}") from exc
            stats["games"] += 1
            stats["secret_faces"] += sum(sum(p.secret_faces_rolled.values()) for p in gc.state.players)
            stats["cleaned"] += sum(p.slots_cleaned_by_die + p.slots_cleaned_by_face for p in gc.state.players)
            stats["bonus_rounds"] += gc.state.red_secret_payouts_fired
            for key, needle in (("bypass", "Brute-Force Bypass"), ("ace", "Arbitrary Code Execution"),
                                ("splice", " Magnetic Splice, "), ("burn", "Burn Notice"), ("jumper", "Jumper Diagnostics"),
                                ("slot_die", "Glitched Shield Slot: slot cleaned"), ("bonus_log", "MARKET LEADER BONUS")):
                stats[key] = stats.get(key, 0) + sum(needle in e and not e.count("0 Magnetic Splice") for e in gc.event_log)
            stats["collapse"] += int(gc.final_result["end_reason"] == "market_collapse")
            self.assertIn(gc.final_result["end_reason"], {"patient_zero", "singularity", "market_collapse", "total_wipeout"})
        print(f"\nfuzz: {stats}")
        self.assertGreater(stats["secret_faces"], 0)


if __name__ == "__main__":
    unittest.main()
