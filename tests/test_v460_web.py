"""v0.46.0 web flow: the web plays ``GameConfig.v046()`` only (Vulnerability Track, no shields, no Defense Grid).

Covers the config choice, Phase 1 Deploy (+1 Vulnerability per ⚠), the rules' phase order (5 Operations, then
6 CI/CD Pipeline Shift), Phase 4 (Red / Blue, table-wide Green, Patient Zero, Target Lock Signature Attacks), the
Pen Test Track, purchases into the Sprint Plan, Market Share regain for cash, retired-term hygiene in the web UI
text, and a fuzz run of complete games with random human decisions (invariants checked after every action).
"""

from __future__ import annotations

import json
import os
import random
import re
import unittest

from sim.config import CubeColor, DieColor
from sim.engine import vulnerability
from web.controller import phases
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
    }


def check_invariants(gc: GameController) -> None:
    st = gc.state
    cfg = st.config
    assert cfg.is_vulnerability and not cfg.glitched_shield_slots_enabled
    for p in st.players:
        z = _zone_ids(p)
        permanent = z["ready"] + z["prod"] + z["proc"] + z["scan"]
        mid_roll = gc.phase == 1 and gc.player_meta[p.player_id].get("has_rolled") and not gc.player_meta[p.player_id].get("has_committed")
        if not mid_roll:
            assert len(permanent) == len(set(permanent)), f"die in two zones for player {p.player_id}: {z}"
        for d in p.glitched_dice:
            assert d.secret_pending or d.color == DieColor.GRAY, f"non-Secret die in Processing Box: {d}"
        for d in p.ready_for_release_dice + p.scanned_dice + p.in_production_dice:
            assert not d.secret_pending, "Secret-pending die outside the Processing Box"
        assert 0 <= p.vulnerability <= cfg.vuln_track_max, "Vulnerability out of range"
        if not p.is_patient_zero:
            assert 0 <= p.market_share <= p.market_share_max
        for d in p.in_production_dice:
            role = d.production_role.value if d.production_role is not None else "INCOME"
            assert "SHIELD" not in role, f"shield role deployed in v0.46.0: {role}"


def _pick(rng, seq):
    seq = list(seq)
    return rng.choice(seq) if seq else None


def _phase1(gc, pid, rng):
    meta = gc.player_meta[pid]
    caps = gc.get_action_capabilities(pid)
    if not meta["has_rolled"]:
        gc.roll_pool(pid)
        return
    rolled = meta["rolled_pool"]
    r = rng.random()
    if caps["can_override_face_helix"] and r < 0.25 and rolled:
        i = rng.randrange(len(rolled))
        legal = [k for k, f in enumerate(rolled[i].faces) if not f.is_star]
        gc.override_face(pid, i, rng.choice(legal), "helix")
        return
    if caps["can_override_face_release_l4"] and r < 0.4:
        i = rng.choice(caps["release_l4_gray_indices"])
        gc.override_face(pid, i, rng.randrange(len(rolled[i].faces)), "release_l4")
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
    decl = {i: rng.randrange(len(d.current_face.choices)) for i, d in enumerate(rolled)
            if d.current_face and d.current_face.is_choice}
    gc.lock_in(pid, decl)


def _phase3(gc, pid, rng):
    p = gc.state.players[pid]
    caps = gc.get_action_capabilities(pid)
    burn = None
    if caps["can_spook_burn"] and rng.random() < 0.5:
        owned = [d for d in p.total_dice if d.color == DieColor.GRAY]
        if owned:
            burn = rng.choice(owned).die_id
    if caps.get("can_capital_injection") and rng.random() < 0.5:
        gc.capital_injection(pid)
        return
    gc.confirm_income(pid, spook_burn_die_id=burn)


def _phase4(gc, pid, rng):
    ts = gc.last_attack_result["threat_summary"][pid]
    kw = {}
    aegis = ts["aegis"]
    if aegis["available"] and rng.random() < 0.7:
        opts = list(aegis["qualifying_colors"]) + (["green"] if aegis["green_hit"] else []) + ["none"]
        kw["aegis_color"] = rng.choice(opts)
    if ts["slush_fund"]["available"]:
        kw["use_slush_fund"] = rng.random() < 0.5
    ch = ts["signature_choices"]
    if ch.get("green_tracks") and rng.random() < 0.8:
        o = ch["green_tracks"]
        kw["signature_green_tracks"] = rng.sample([x["track"] for x in o["options"]], o["count"])
    if ch.get("red_recipients") and rng.random() < 0.8:
        kw["signature_red_recipient"] = rng.choice(ch["red_recipients"])
    gc.confirm_attacks(pid, **kw)


def _pipeline(gc, pid, rng):
    info = gc.pending_graduation[pid]
    if info.get("sprint_plan"):  # v0.48+: exactly current_picks Current + next_picks Next Sprint dice
        cur = [c["die_id"] for c in info["candidates"] if c["sprint"] == "current"]
        nxt = [c["die_id"] for c in info["candidates"] if c["sprint"] == "next"]
        grads = rng.sample(cur, info["current_picks"]) + rng.sample(nxt, info["next_picks"])
    else:
        ids = [c["die_id"] for c in info["candidates"]]
        k = rng.randint(0, info["n"])
        grads = rng.sample(ids, min(k, len(ids)))
    splice = None
    if info["splice_available"] and info["processing_box"] and rng.random() < 0.6:
        splice = rng.choice(info["processing_box"])["die_id"]
    gc.choose_graduates(pid, grads, splice_die_id=splice)


def _operations(gc, pid, rng):
    caps = gc.get_action_capabilities(pid)
    if caps["pending_breakthrough"] is not None:
        opts = caps["pending_breakthrough"]["options"]
        if rng.random() < 0.5 and opts.get("can_accept", opts.get("available", False)):
            gray = opts.get("gray_die_ids") or [None]
            gc.resolve_breakthrough(pid, accept=True, gray_die_id=gray[0], color=_pick(rng, opts.get("colors") or ["red"]))
        else:
            gc.resolve_breakthrough(pid, accept=False)
        return
    options = [("buy", c) for c, ok in caps["can_buy"].items() if ok]
    options += [("upgrade", t) for t, ok in caps["can_upgrade_track"].items() if ok]
    if caps["can_regain_market_share"]:
        options.append(("regain", None))
    if caps["can_pen_test"]:
        options += [("pen", None)] * 2
    for code in ("P1",):
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
    elif kind == "pen":
        gc.pen_test(pid, rng.randint(1, caps["pen_test_max_now"]))
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
    order = []
    for _ in range(max_steps):
        if gc.phase == phases.GAME_OVER:
            break
        ph = gc.phase
        if not order or order[-1] != (gc.state.current_round, ph):
            order.append((gc.state.current_round, ph))
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
            _phase4(gc, rng.choice([p for p in humans_alive if p not in gc.attack_resolved_pids]), rng)
        elif ph == phases.OPERATIONS:
            _operations(gc, gc.active_player_index, rng)
        elif ph == phases.PIPELINE_SHIFT:
            _pipeline(gc, rng.choice(list(gc.pending_graduation)), rng)
        else:
            raise AssertionError(f"unexpected phase {ph}")
        if check_each:
            check_invariants(gc)
        json.dumps(gc.get_full_state(), default=str)
    assert gc.phase == phases.GAME_OVER, f"seed {seed}: game did not finish"
    for (r1, p1), (r2, p2) in zip(order, order[1:]):
        assert (r2, p2) > (r1, p1), f"seed {seed}: phase order went {r1}.{p1} -> {r2}.{p2}"
    return gc


# ---------------------------------------------------------------------------
# Helpers for directed tests
# ---------------------------------------------------------------------------
def _fresh(n=2, seed=3, humans=(0,)):
    gc = GameController()
    gc.new_game(num_players=n, seed=seed, players_config=[{"is_human": i in humans} for i in range(n)])
    return gc


def _lock_in_all(gc):
    for pid, m in gc.player_meta.items():
        if m["is_human"] and not gc.state.players[pid].is_patient_zero:
            if not m["has_rolled"]:
                gc.roll_pool(pid)
            if not m["has_committed"]:
                gc.lock_in(pid, {})


def _to_phase4(gc):
    _lock_in_all(gc)
    gc.compile_drop()
    for pid, m in gc.player_meta.items():
        if gc.phase == 3 and m["is_human"] and not m.get("income_confirmed"):
            gc.confirm_income(pid)


class TestWebRedSignatureLowestRival(unittest.TestCase):
    """v0.47.0: Target Lock Red recipient choices are the post-drain lowest rivals (locked included, SETEC at 2P)."""

    def _setup(self, n, seed=3):
        from web.controller.phase4_attack_actions import _signature_choices
        gc = _fresh(n=n, seed=seed)
        _to_phase4(gc)
        return gc, _signature_choices

    def test_web_uses_v049_preset(self):
        cfg = _fresh().state.config
        self.assertEqual(cfg.signature_red_recipient_rule, "lowest_rival")
        self.assertTrue(cfg.signature_red_setec_eligible)
        self.assertTrue(cfg.sprint_plan_enabled)
        self.assertTrue(cfg.colored_vuln_lock and cfg.vuln_lock_gray)
        self.assertEqual(cfg.helix_bypass_mode, "REROLL_LOCKED")
        self.assertTrue(cfg.helix_bypass_once_per_game)

    def test_2p_tie_includes_setec(self):
        gc, choices = self._setup(2)
        s = gc.state
        if not getattr(s, "setec_corp_active", False):
            self.skipTest("no SETEC Corp at 2P")
        s.players[0].market_share = 5
        s.players[1].market_share = 9
        s.setec_market_share = 3  # locker 0 drops to 3 (not in own pool); pool = {1: 9, SETEC: 3}
        s.players[0].market_share = 5
        sig = {"dominant_color": "red", "locked_pids": [0]}
        self.assertIsNone(choices(gc, 0, sig)["red_recipients"])  # SETEC alone is lowest: no choice
        s.setec_market_share = 9
        self.assertEqual(sorted(choices(gc, 0, sig)["red_recipients"]), [-1, 1])

    def test_locked_rival_is_offered_post_drain(self):
        gc, choices = self._setup(3)
        s = gc.state
        for p, ms in zip(s.players, (6, 6, 4)):
            p.market_share = ms
        # players 0 and 1 locked: 1 drops to 4 and ties player 2 (4) as locker 0's lowest rival
        sig = {"dominant_color": "red", "locked_pids": [0, 1]}
        self.assertEqual(sorted(choices(gc, 0, sig)["red_recipients"]), [1, 2])

    def test_human_picks_setec(self):
        from web.controller.phase4_attack_actions import _human_signature_hooks
        gc, _ = self._setup(2)
        bot = gc.state.players[0].bot
        gc.player_meta[0]["signature_red_recipient"] = -1
        from sim.bots.base import SetecRecipient
        tied = [gc.state.players[1], SetecRecipient(market_share=4)]
        with _human_signature_hooks(gc):
            self.assertEqual(bot.choose_signature_red_recipient(gc.state.players[0], tied, gc.state).player_id, -1)



class TestWebV046Config(unittest.TestCase):
    def test_default_is_v049_only(self):
        gc = _fresh()
        cfg = gc.state.config
        self.assertTrue(cfg.is_vulnerability)
        self.assertTrue(cfg.operations_before_pipeline_shift)
        self.assertFalse(cfg.glitched_shield_slots_enabled)
        st = gc.get_full_state()
        self.assertEqual(st["rules_version"], "v0.49.0")
        self.assertEqual(st["phase_names"][5], "Operations")
        self.assertEqual(st["phase_names"][6], "CI/CD Pipeline Shift")
        self.assertEqual(st["vulnerability_track"]["min_target"], 5)
        self.assertEqual(st["vulnerability_track"]["safe_max"], 4)
        self.assertEqual([b["damage"] for b in st["vulnerability_track"]["bands"]], [1, 2, 3])

    def test_legacy_rules_versions_rejected(self):
        for v in ("v0.38.0", "v0.37.0", "v0.40.0", "v0.45.0", "v0.46.0", "v0.47.0", "v0.48.0"):
            with self.assertRaises(ValueError):
                GameController().new_game(num_players=2, seed=1, rules_version=v)
        GameController().new_game(num_players=2, seed=1, rules_version="v0.49.0")

    def test_no_shield_or_defense_grid_fields_serialized(self):
        gc = _fresh()
        gc.roll_pool(0)
        st = gc.get_full_state()
        p = st["players"][0]
        for key in ("defense_capacity", "glitched_shield_slots", "effective_defense_capacity", "shield_slots",
                    "production_slots", "commitments"):
            self.assertNotIn(key, p)
        self.assertNotIn("is_glitched_slots", st)
        for d in p["rolled_pool"]:
            self.assertNotIn("is_shield", d["current_face"])
            self.assertIn("vuln", d["current_face"])
        self.assertIn("vulnerability", p)
        self.assertNotIn("can_commit", st["action_capabilities"])
        self.assertIn("can_lock_in", st["action_capabilities"])


class TestWebV046Flow(unittest.TestCase):
    def test_lock_in_adds_vulnerability_per_icon(self):
        gc = _fresh(seed=11)
        gc.roll_pool(0)
        p = gc.state.players[0]
        icons = sum(vulnerability.face_vuln(d.current_face) for d in gc.player_meta[0]["rolled_pool"])
        before = p.vulnerability
        gc.lock_in(0, {})
        self.assertEqual(p.vulnerability, min(gc.state.config.vuln_track_max, before + icons))
        self.assertEqual(gc.phase, 2)

    def test_secret_face_goes_to_processing_box(self):
        for seed in range(40):
            gc = _fresh(seed=seed)
            gc.roll_pool(0)
            rolled = gc.player_meta[0]["rolled_pool"]
            secret = [d for d in rolled if d.current_face and d.current_face.secrets_pending]
            if not secret:
                continue
            gc.lock_in(0, {})
            p = gc.state.players[0]
            self.assertTrue(all(d in p.glitched_dice and d.secret_pending for d in secret))
            return
        self.skipTest("no Secret face rolled in 40 seeds")

    def test_phase_order_operations_then_pipeline_shift(self):
        gc = _fresh(seed=5)
        _to_phase4(gc)
        while gc.phase == 4:
            gc.confirm_attacks(0)
        if gc.phase == phases.GAME_OVER:
            self.skipTest("game ended in Phase 4")
        self.assertEqual(gc.phase, phases.OPERATIONS)
        self.assertEqual(gc.phase_name, "Operations")
        rnd = gc.state.current_round
        while gc.phase == phases.OPERATIONS:
            gc.end_turn(gc.active_player_index)
        if gc.phase == phases.PIPELINE_SHIFT:
            self.assertEqual(gc.phase_name, "CI/CD Pipeline Shift")
            while gc.pending_graduation:
                pid = next(iter(gc.pending_graduation))
                gc.choose_graduates(pid, [d["die_id"] for d in gc.pending_graduation[pid]["candidates"][:gc.pending_graduation[pid]["n"]]])
        self.assertIn(gc.phase, (1, phases.GAME_OVER))
        if gc.phase == 1:
            self.assertEqual(gc.state.current_round, rnd + 1)

    def test_purchase_goes_to_scanned_box(self):
        gc = _fresh(seed=8)
        _to_phase4(gc)
        while gc.phase == 4:
            gc.confirm_attacks(0)
        while gc.phase == phases.OPERATIONS and gc.active_player_index != 0:
            gc.end_turn(gc.active_player_index)
        if gc.phase != phases.OPERATIONS:
            self.skipTest("no human Operations Turn")
        p = gc.state.players[0]
        p.money = 20
        color = next(c for c in ("red", "blue", "green", "yellow") if gc.state.market.get(DieColor(c), 0) > 0)
        scanned = len(p.scanned_dice)
        gc.buy_die(0, color)
        self.assertEqual(len(p.scanned_dice), scanned + 1)
        with self.assertRaises(ValueError):  # 1 purchase per Operations Turn
            gc.buy_die(0, color)

    def test_pen_test_and_regain_for_cash(self):
        gc = _fresh(seed=9)
        _to_phase4(gc)
        while gc.phase == 4:
            gc.confirm_attacks(0)
        while gc.phase == phases.OPERATIONS and gc.active_player_index != 0:
            gc.end_turn(gc.active_player_index)
        if gc.phase != phases.OPERATIONS:
            self.skipTest("no human Operations Turn")
        p, cfg = gc.state.players[0], gc.state.config
        p.vulnerability, p.research_tokens = 6, 10
        caps = gc.get_action_capabilities(0)
        self.assertTrue(caps["can_pen_test"])
        self.assertEqual(caps["pen_test_limit"], 1)
        gc.pen_test(0, 1)
        self.assertEqual((p.vulnerability, p.research_tokens), (5, 10 - cfg.pen_test_cost))
        with self.assertRaises(ValueError):  # Pen Test limit 1 at Level 0
            gc.pen_test(0, 1)
        p.market_share, p.money = p.market_share_max - 3, 10
        r0 = p.research_tokens
        gc.regain_market_share(0)
        self.assertEqual((p.money, p.research_tokens), (10 - cfg.share_regain_cost_by_level[0], r0))

    def _human_operations_turn(self, seed):
        gc = _fresh(seed=seed)
        _to_phase4(gc)
        while gc.phase == 4:
            gc.confirm_attacks(0)
        while gc.phase == phases.OPERATIONS and gc.active_player_index != 0:
            gc.end_turn(gc.active_player_index)
        if gc.phase != phases.OPERATIONS:
            self.skipTest("no human Operations Turn")
        return gc

    def test_two_upgrades_per_turn_and_level4_capstone(self):
        gc = self._human_operations_turn(seed=12)
        p = gc.state.players[0]
        p.research_tokens, p.patent_level = 20, 3
        p.market_share = p.market_share_max - 5
        ms = p.market_share
        gc.upgrade_track(0, "patent")  # Public Relations L4 Capstone: +2 Market Share at once
        self.assertEqual(p.patent_level, 4)
        self.assertEqual(p.market_share, ms + 2)
        self.assertTrue(any("Capstone (Public Relations L4)" in e for e in gc.event_log))
        gc.upgrade_track(0, "release")
        with self.assertRaises(ValueError):  # at most 2 upgrades per Operations Turn
            gc.upgrade_track(0, "triage")

    def test_triage_level4_capstone_prompts_human(self):
        gc = self._human_operations_turn(seed=13)
        p = gc.state.players[0]
        p.research_tokens, p.triage_level = 20, 3
        grays = [d for d in p.in_production_dice if d.color == DieColor.GRAY]
        if not grays:
            self.skipTest("no Gray die to move")
        p.in_production_dice.remove(grays[0])
        p.scanned_dice.append(grays[0])  # the swap takes a Gray die from Processing / Scanned / Ready
        gc.upgrade_track(0, "triage")
        caps = gc.get_action_capabilities(0)
        self.assertIsNotNone(caps["pending_breakthrough"])
        self.assertEqual(caps["pending_breakthrough"]["level"], 4)
        with self.assertRaises(ValueError):  # resolve the prompt before another operation
            gc.pen_test(0, 1)
        opts = caps["pending_breakthrough"]["options"]
        gc.resolve_breakthrough(0, accept=True, gray_die_id=opts["gray_die_ids"][0], color=opts["colors"][0])
        self.assertIsNone(gc.get_action_capabilities(0)["pending_breakthrough"])
        self.assertNotIn(grays[0], p.scanned_dice)

    def test_triage_level4_capstone_without_gray_die_forfeits_without_prompt(self):
        gc = self._human_operations_turn(seed=13)
        p = gc.state.players[0]
        p.research_tokens, p.triage_level = 20, 3
        for zone in (p.glitched_dice, p.scanned_dice, p.ready_for_release_dice):
            zone[:] = [d for d in zone if d.color != DieColor.GRAY]
        gc.upgrade_track(0, "triage")
        self.assertIsNone(gc.get_action_capabilities(0)["pending_breakthrough"])
        self.assertTrue(any("Capstone (Triage L4)" in e and "forfeited" in e for e in gc.event_log))

    def test_green_hits_highest_vulnerability_and_resets(self):
        gc = _fresh(n=3, seed=21)
        _to_phase4(gc)
        if gc.phase != 4:
            self.skipTest("no Phase 4 this seed")
        gc.attack_strengths[CubeColor.GREEN] = 1
        gc.compile_result.exited_cubes[CubeColor.GREEN] = max(1, gc.compile_result.exited_cubes.get(CubeColor.GREEN, 0))
        ps = gc.state.players
        ps[0].vulnerability, ps[1].vulnerability, ps[2].vulnerability = 8, 5, 2
        secrets = ps[0].secrets
        gc.confirm_attacks(0)
        hits = gc.last_attack_result["green_hits"]
        self.assertEqual(hits[0]["pids"], [0])
        self.assertEqual(hits[0]["damage"], 2)
        self.assertEqual(ps[0].vulnerability, 0)
        self.assertLessEqual(ps[0].secrets, secrets - 2)

    def test_signature_attack_runs_in_web_phase4(self):
        """The web path now resolves Target Lock Signature Attacks (previously skipped)."""
        for seed in range(200):
            gc = _fresh(n=2, seed=seed)
            _to_phase4(gc)
            if gc.phase != 4 or gc.compile_result.buffer_overflow:
                continue
            p = gc.state.players[0]
            p.target_locked = True
            sig = gc.last_attack_result["signature"] if gc.last_attack_result else None
            from web.controller.phase4_attack_actions import _signature_view

            dom = _signature_view(gc)["dominant_color"]
            if dom != "black":
                continue
            before = len(gc.state.signature_attack_events)
            gc.confirm_attacks(0)
            self.assertEqual(len(gc.state.signature_attack_events), before + 1)
            self.assertEqual(gc.state.signature_attack_events[-1]["locked_pids"], [0])
            self.assertFalse(p.target_locked)  # cleared at the end of Phase 4
            self.assertTrue(any("Target Lock (Black dominant)" in e for e in gc.event_log))
            return
        self.skipTest("no Black-dominant tray in 200 seeds")

    def test_signature_green_human_track_choice(self):
        for seed in range(300):
            gc = _fresh(n=2, seed=seed)
            _to_phase4(gc)
            if gc.phase != 4 or gc.compile_result.buffer_overflow:
                continue
            from web.controller.phase4_attack_actions import _refresh_attack_result, _signature_view

            if _signature_view(gc)["dominant_color"] != "green":
                continue
            gc.state.players[0].target_locked = True
            _refresh_attack_result(gc)
            ch = gc.last_attack_result["threat_summary"][0]["signature_choices"]["green_tracks"]
            self.assertEqual(ch["count"], 2)
            with self.assertRaises(ValueError):
                gc.confirm_attacks(0, signature_green_tracks=["TRIAGE", "TRIAGE"])
            gc.confirm_attacks(0, signature_green_tracks=["TRIAGE", "RELEASE"])
            self.assertEqual(gc.state.players[0].encrypted_research_tracks, {"TRIAGE", "RELEASE"})
            self.assertFalse(hasattr(gc.state.players[0].bot.__dict__, "choose_signature_green_tracks"))
            self.assertNotIn("choose_signature_green_tracks", gc.state.players[0].bot.__dict__)
            return
        self.skipTest("no Green-dominant tray in 300 seeds")


class TestWebV046Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import threading
        from web.server import RogueAgentRequestHandler, create_server

        RogueAgentRequestHandler.controller = GameController()
        cls.server = create_server("127.0.0.1", 0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, path, data):
        import urllib.error
        import urllib.request

        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=json.dumps(data).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_endpoints(self):
        code, body = self._post("/api/game/new", {"num_players": 2, "seed": 4})
        self.assertEqual(code, 200)
        self.assertEqual(body["state"]["rules_version"], "v0.49.0")
        code, _ = self._post("/api/game/new", {"num_players": 2, "seed": 4, "rules_version": "v0.38.0"})
        self.assertEqual(code, 400)
        self._post("/api/game/new", {"num_players": 2, "seed": 4})
        self.assertEqual(self._post("/api/game/action/roll", {"player_id": 0})[0], 200)
        code, body = self._post("/api/game/action/lock_in", {"player_id": 0, "choice_declarations": {}})
        self.assertEqual(code, 200)
        self.assertEqual(body["state"]["phase"], 2)
        for retired in ("commit", "hotfix", "patent", "debug_unlock"):
            self.assertEqual(self._post(f"/api/game/action/{retired}", {"player_id": 0})[0], 404, retired)


class TestWebV049Rules(unittest.TestCase):
    """v0.49.0 in the web engine: Locked Dice, once-per-game Brute-Force Bypass, Sprint Plan setup and Sprint Review."""

    def _rolled_with_lock(self, company=None):
        for seed in range(60):
            gc = GameController()
            cfgs = [{"is_human": True, **({"company": company} if company else {})}, {"is_human": False}]
            gc.new_game(num_players=2, seed=seed, players_config=cfgs)
            if company and gc.state.players[0].company.code.value != company:
                self.skipTest(f"company {company} not assignable")
            gc.roll_pool(0)
            rolled = gc.player_meta[0]["rolled_pool"]
            locked = [i for i, d in enumerate(rolled) if d.is_locked]
            if locked:
                return gc, rolled, locked
        self.skipTest("no locked die rolled in 60 seeds")

    def test_vuln_faces_lock_and_cannot_be_rerolled(self):
        gc, rolled, locked = self._rolled_with_lock()
        for i, d in enumerate(rolled):
            self.assertEqual(d.is_locked, vulnerability.face_vuln(d.current_face) > 0, f"die {i}: {d.current_face.name}")
        with self.assertRaises(ValueError):
            gc.perform_reroll(0, [locked[0]])

    def test_helix_bypass_rerolls_locked_dice_once_per_game(self):
        gc, rolled, locked = self._rolled_with_lock("HELIX")
        p = gc.state.players[0]
        self.assertTrue(gc.get_action_capabilities(0)["can_prodigy"])
        gc.perform_reroll(0, [locked[0]], use_prodigy_ability=True)
        self.assertTrue(p.helix_bypass_used_game)
        # face-set after rerolls: any non-Star face (R&D allowed), and it ends the rerolls
        die = rolled[0]
        k = next(i for i, f in enumerate(die.faces) if not f.is_star)
        gc.override_face(0, 0, k, "helix")
        self.assertEqual(gc.player_meta[0]["rerolls_remaining"], 0)
        self.assertEqual(die.is_locked, vulnerability.face_vuln(die.faces[k]) > 0)
        # a new SETEC Version would refresh a per-Version Override, but the Bypass is once per game
        self.assertFalse(p.is_helix_bypass_available(gc.state.active_version.version_str))

    def test_setup_puts_three_gray_in_current_sprint(self):
        gc = _fresh()
        for p in gc.state.players:
            self.assertEqual(sum(d.color == DieColor.GRAY for d in p.ready_for_release_dice), 2)
            self.assertEqual(sorted(d.die_id for d in p.scanned_dice), sorted(p.current_sprint_ids))
            self.assertEqual(len(p.scanned_dice), 3)
        st = gc.get_full_state()
        me = next(x for x in st["players"] if x["player_id"] == 0)
        self.assertTrue(me["sprint_plan_enabled"])
        self.assertEqual(len(me["current_sprint_ids"]), 3)

    def test_sprint_review_releases_current_sprint_first(self):
        from sim.engine import sprint_plan

        for seed in range(30):
            gc = _fresh(seed=seed)
            _to_phase4(gc)
            while gc.phase == 4:
                gc.confirm_attacks(0)
            while gc.phase == phases.OPERATIONS:
                gc.end_turn(gc.active_player_index)
            if gc.phase != phases.PIPELINE_SHIFT or 0 not in gc.pending_graduation:
                continue
            info = gc.pending_graduation[0]
            p = gc.state.players[0]
            cur = [c["die_id"] for c in info["candidates"] if c["sprint"] == "current"]
            nxt = [c["die_id"] for c in info["candidates"] if c["sprint"] == "next"]
            self.assertEqual(info["current_picks"], min(len(cur), p.effective_release_bandwidth))
            if info["current_picks"] and nxt:
                with self.assertRaises(ValueError):  # skipping a forced Current Sprint die is illegal
                    gc.choose_graduates(0, nxt[:info["current_picks"] + info["next_picks"]])
            gc.choose_graduates(0, info["default_graduate_ids"])
            ready = {d.die_id for d in p.ready_for_release_dice}
            self.assertTrue(set(cur[:info["current_picks"]]) <= ready or info["current_picks"] == 0)
            triaged = set(gc.last_pipeline_result[0]["triaged_ids"])  # Conveyor Triage (after the review) -> Next Sprint
            self.assertEqual({d.die_id for d in sprint_plan.current_sprint(p)}, {d.die_id for d in p.scanned_dice} - triaged)
            self.assertEqual({d.die_id for d in sprint_plan.next_sprint(p)}, triaged)  # leftovers became Current
            return
        self.skipTest("no human Sprint Review choice in 30 seeds")


class TestRetiredTermsInWebUi(unittest.TestCase):
    RETIRED = [
        "Glitched Box", "Color-Specific Shield", "Red Shield", "Blue Shield", "Green Shield", "Two-Stage",
        "Hash Match", "Defensive Shield Sacrifice", "Consultancy", "Lead Consultant", "CISO", "Unpatched Zone",
        "Zero Wear Retention", "Malware Fizzle", "Net Wipeout Score", "Emergency Hotfix", "Passive Firewall",
        "Personal Reserve Procurement", "Unpaid Ransom", "Ransomware", "Financial Wiretap", "Cryptographic Patent",
        "Patent Filing", "FinSec", "Ransom Insurance", "Threat Bounty", "Short Squeeze",
        # retired in v0.46.0
        "Shield Slot", "Glitched Shield Slot", "Defense Grid", "Block 1 Any", "Critical Breach", "Generic (Any)",
        "Any Shield", "Commit Defenses", "Defense Track", "Defense Capacity",
        # retired in v0.48.0
        "Processing Box", "Scanned Box", "Secret face", "Scanned Graduation", "Lock-in", "Deep R&D Vault",
        # retired in v0.39.0
        "Redundant Crew",
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
                for m in re.finditer(re.escape(term), text, flags=re.IGNORECASE):
                    line = text[:m.start()].count("\n") + 1
                    bad.append(f"{name}:{line}: {term}")
        self.assertEqual(bad, [])


class TestRandomHumanFuzz(unittest.TestCase):
    GAMES = int(os.environ.get("WEB_FUZZ_GAMES", "240"))

    def test_random_human_games(self):
        stats = {"games": 0, "green_hits": 0, "signature": 0, "pen_test": 0, "collapse": 0}
        for seed in range(self.GAMES):
            try:
                gc = play_random_game(seed, check_each=(seed % 4 == 0))
            except Exception as exc:  # surface the seed
                raise AssertionError(f"fuzz seed {seed} failed: {type(exc).__name__}: {exc}") from exc
            stats["games"] += 1
            stats["green_hits"] += sum(1 for e in gc.state.green_hit_events if e["pids"])
            stats["signature"] += len(gc.state.signature_attack_events)
            stats["pen_test"] += sum(p.pen_test_steps for p in gc.state.players)
            stats["collapse"] += int(gc.final_result["end_reason"] == "market_collapse")
            self.assertIn(gc.final_result["end_reason"], {"patient_zero", "singularity", "market_collapse", "total_wipeout"})
        print(f"\nfuzz: {stats}")
        self.assertGreater(stats["green_hits"], 0)
        self.assertGreater(stats["signature"], 0)
        self.assertGreater(stats["pen_test"], 0)


if __name__ == "__main__":
    unittest.main()
