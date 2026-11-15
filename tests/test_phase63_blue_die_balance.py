"""Phase 63 Blue Die Secret & Economy Rebalance Test Suite (`v0.43.1`).

Validates invariants INV-P63-01 through INV-P63-04 and test cases TC-P63-01 through TC-P63-07
per docs/specs/phase63_blue_die_balance_spec.md:
- INV-P63-01: Blue Die Face Topology & Output Profile (V043_BLUE_TUNE)
- INV-P63-02: Phase 3 Income Resolution & Resource Attribution
- INV-P63-03: Conveyor Triage & Face 5 Banking Synergy
- INV-P63-04: Factory Hierarchy & Legacy Profile Preservation
"""

from __future__ import annotations

from types import SimpleNamespace
import unittest

from sim.bots import secret_face_policy as sfp
from sim.bots.accelerationist import AccelerationistBot
from sim.bots.adaptive_balanced import AdaptiveBalancedBot
from sim.bots.base import BaseBot
from sim.bots.reckless_saboteur import RecklessSaboteurBot
from sim.config import DieColor, GameConfig, PrPushParams
from sim.engine import GameEngine, phase3_income as p3, phase6_operations as p6, secret_faces as sf
from sim.entities import (
    COMPANIES,
    CompanyCode,
    WHITE_HATS,
    WhiteHatCode,
    create_colored_die,
    get_all_variant_cards,
    get_default_version_deck,
)

ALL_CARDS = get_all_variant_cards("MARKETING")


def _cards(**codes):
    code_to_color = {
        "R": DieColor.RED,
        "B": DieColor.BLUE,
        "G": DieColor.GREEN,
        "Y": DieColor.YELLOW,
    }
    out = {
        DieColor.RED: ALL_CARDS["R1"],
        DieColor.BLUE: ALL_CARDS["B1"],
        DieColor.GREEN: ALL_CARDS["G1"],
        DieColor.YELLOW: ALL_CARDS["Y1"],
    }
    for k, v in codes.items():
        color = code_to_color.get(k.upper())
        if color:
            out[color] = ALL_CARDS[v]
    return out


def _engine_v043_1(n=3, seed=1, cards=None, roster=False, **cfg_overrides):
    if roster:
        bots = [
            AdaptiveBalancedBot(0),
            AccelerationistBot(1),
            RecklessSaboteurBot(2),
            AdaptiveBalancedBot(3),
        ][:n]
        cfg = GameConfig.v043_1_roster(num_players=n, **cfg_overrides)
    else:
        bots = [BaseBot(i) for i in range(n)]
        cfg = GameConfig.v043_1(num_players=n, **cfg_overrides)
    companies = [
        COMPANIES[CompanyCode.PROMETHEUS],
        COMPANIES[CompanyCode.MERIDIAN],
        COMPANIES[CompanyCode.DTO],
        COMPANIES[CompanyCode.AEGIS],
    ][:n]
    white_hats = [
        WHITE_HATS[WhiteHatCode.OPERATOR],
        WHITE_HATS[WhiteHatCode.ACOUSTIC],
        WHITE_HATS[WhiteHatCode.SPOOK],
        WHITE_HATS[WhiteHatCode.PHREAKER],
    ][:n]
    return GameEngine(
        config=cfg,
        bots=bots,
        seed=seed,
        variant_cards=cards or _cards(),
        version_deck=get_default_version_deck(),
        companies=companies,
        white_hats=white_hats,
    )


class TestPhase63BlueDieBalance(unittest.TestCase):

    def test_tc_p63_01_config_factory_defaults(self):
        """TC-P63-01 / INV-P63-04: Config factory defaults & legacy profile preservation."""
        cfg = GameConfig.v043_1()
        self.assertEqual(cfg.die_face_profile, "V043_BLUE_TUNE")
        self.assertTrue(cfg.target_lock_enabled)
        self.assertEqual(cfg.signature_attack_mode, "dominant_color_effects")

        roster_cfg = GameConfig.v043_1_roster()
        self.assertTrue(roster_cfg.bot_pr_push)
        self.assertIsInstance(roster_cfg.bot_pr_push_params, PrPushParams)
        self.assertEqual(roster_cfg.die_face_profile, "V043_BLUE_TUNE")

        for legacy_factory in (
            GameConfig.v038f,
            GameConfig.v040,
            GameConfig.v041,
            GameConfig.v042,
            GameConfig.v043,
        ):
            legacy_cfg = legacy_factory()
            self.assertEqual(legacy_cfg.die_face_profile, "V038F")

    def test_tc_p63_02_blue_die_face_topology(self):
        """TC-P63-02 / INV-P63-01: Blue die face topology under V043_BLUE_TUNE."""
        for code in ("B1", "B2", "B3"):
            die = create_colored_die(
                DieColor.BLUE,
                die_id=1,
                variant_card=ALL_CARDS[code],
                face_profile="V043_BLUE_TUNE",
            )
            faces = die.faces
            self.assertEqual(len(faces), 6)

            # Face 1: +1 Corporate Secret
            self.assertEqual(faces[0].name, "+1 Corporate Secret")
            self.assertEqual(faces[0].secrets, 1)
            self.assertEqual(faces[0].patches, 0)
            self.assertEqual(faces[0].money, 0)
            self.assertFalse(faces[0].is_choice)
            self.assertFalse(faces[0].secrets_pending)
            self.assertFalse(faces[0].is_star)

            # Face 2: +2 🔬
            self.assertEqual(faces[1].name, "+2 🔬")
            self.assertEqual(faces[1].patches, 2)
            self.assertEqual(faces[1].secrets, 0)
            self.assertEqual(faces[1].money, 0)
            self.assertFalse(faces[1].is_choice)
            self.assertFalse(faces[1].secrets_pending)
            self.assertFalse(faces[1].is_star)

            # Face 3: +$2
            self.assertEqual(faces[2].name, "+$2")
            self.assertEqual(faces[2].money, 2)
            self.assertEqual(faces[2].secrets, 0)
            self.assertEqual(faces[2].patches, 0)
            self.assertFalse(faces[2].is_choice)
            self.assertFalse(faces[2].secrets_pending)
            self.assertFalse(faces[2].is_star)

            # Face 4: +1 🔬 / +$1 choice
            self.assertTrue(faces[3].is_choice)
            self.assertEqual(len(faces[3].choices), 2)
            self.assertEqual(faces[3].choices[0].patches, 1)
            self.assertEqual(faces[3].choices[1].money, 1)

            # Face 5: Secret face
            self.assertTrue(faces[4].secrets_pending)
            self.assertEqual(faces[4].name, "Secret")

            # Face 6: Blue ★
            self.assertTrue(faces[5].is_star)
            self.assertEqual(faces[5].star_code, code)

    def test_tc_p63_03_non_blue_die_invariance(self):
        """TC-P63-03 / INV-P63-01: Non-Blue dice remain invariant under V043_BLUE_TUNE."""
        green = create_colored_die(
            DieColor.GREEN, die_id=2, variant_card=ALL_CARDS["G1"], face_profile="V043_BLUE_TUNE"
        )
        self.assertEqual(green.faces[0].name, "+2 🔬")
        self.assertEqual(green.faces[0].patches, 2)

        red = create_colored_die(
            DieColor.RED, die_id=3, variant_card=ALL_CARDS["R1"], face_profile="V043_BLUE_TUNE"
        )
        self.assertTrue(red.faces[0].is_choice)
        for idx in (1, 2, 3):
            self.assertEqual(red.faces[idx].name, "+$2")
            self.assertEqual(red.faces[idx].money, 2)

        yellow = create_colored_die(
            DieColor.YELLOW, die_id=4, variant_card=ALL_CARDS["Y1"], face_profile="V043_BLUE_TUNE"
        )
        self.assertEqual(yellow.faces[0].market_share, 2)
        self.assertEqual(yellow.faces[2].money, 1)
        self.assertEqual(yellow.faces[2].market_share, 1)

        purple = create_colored_die(
            DieColor.PURPLE, die_id=5, variant_card=None, face_profile="V043_BLUE_TUNE"
        )
        for idx in (0, 1):
            self.assertEqual(purple.faces[idx].name, "Block 1 Any")
            self.assertEqual(purple.faces[idx].block_amount, 1)

    def test_tc_p63_04_phase3_income_resource_harvesting(self):
        """TC-P63-04 / INV-P63-02: Phase 3 income harvesting for Faces 1, 2, and 3."""
        engine = _engine_v043_1()
        player = engine.state.players[0]
        card = engine.variant_cards[DieColor.BLUE]

        # Face 1: +1 Corporate Secret ("blue_face"), stays In Production
        d1 = create_colored_die(DieColor.BLUE, die_id=101, variant_card=card, face_profile="V043_BLUE_TUNE")
        d1.current_face = d1.faces[0]
        d1.production_role = "INCOME"
        player.in_production_dice.append(d1)

        init_sec = player.secrets
        rec1 = p3.collect_player_production_income(engine, player)
        self.assertEqual(rec1.secrets, 1)
        self.assertEqual(player.secrets, init_sec + 1)
        self.assertEqual(player.secrets_by_source.get("blue_face"), 1)
        self.assertIn(d1, player.in_production_dice)
        self.assertNotIn(d1, player.glitched_dice)

        # Face 2: +2 🔬
        player.in_production_dice.clear()
        d2 = create_colored_die(DieColor.BLUE, die_id=102, variant_card=card, face_profile="V043_BLUE_TUNE")
        d2.current_face = d2.faces[1]
        d2.production_role = "INCOME"
        player.in_production_dice.append(d2)

        init_res = player.research
        rec2 = p3.collect_player_production_income(engine, player)
        self.assertEqual(rec2.research, 2)
        self.assertEqual(player.research, init_res + 2)

        # Face 3: +$2
        player.in_production_dice.clear()
        d3 = create_colored_die(DieColor.BLUE, die_id=103, variant_card=card, face_profile="V043_BLUE_TUNE")
        d3.current_face = d3.faces[2]
        d3.production_role = "INCOME"
        player.in_production_dice.append(d3)

        init_money = player.money
        rec3 = p3.collect_player_production_income(engine, player)
        self.assertEqual(rec3.money, 2)
        self.assertEqual(player.money, init_money + 2)

    def test_tc_p63_05_face5_banking_and_hardware_synergy(self):
        """TC-P63-05 / INV-P63-03: Face 5 banking yield & Face 2 Defense Grid upgrade synergy."""
        engine = _engine_v043_1()
        player = engine.state.players[0]
        cfg = engine.config
        card = engine.variant_cards[DieColor.BLUE]

        # Defense Grid < L3 -> +2 Secrets
        player.defense_level = 2
        self.assertEqual(sf.secret_yield(cfg, player, DieColor.BLUE), 2)
        d_f5_a = create_colored_die(DieColor.BLUE, die_id=201, variant_card=card, face_profile="V043_BLUE_TUNE")
        d_f5_a.current_face = d_f5_a.faces[4]
        sf.enter_processing_box(player, d_f5_a, 1)
        sec_before = player.secrets
        sf.bank(cfg, player, d_f5_a, engine.state)
        self.assertEqual(player.secrets, sec_before + 2)

        # Defense Grid >= L3 -> +3 Secrets
        player.defense_level = 3
        self.assertEqual(sf.secret_yield(cfg, player, DieColor.BLUE), 3)
        d_f5_b = create_colored_die(DieColor.BLUE, die_id=202, variant_card=card, face_profile="V043_BLUE_TUNE")
        d_f5_b.current_face = d_f5_b.faces[4]
        sf.enter_processing_box(player, d_f5_b, 2)
        sec_before = player.secrets
        sf.bank(cfg, player, d_f5_b, engine.state)
        self.assertEqual(player.secrets, sec_before + 3)

        # Face 2 research can be immediately allocated to Defense Grid in Phase 6
        player.defense_level = 0
        player.research = 0
        d_f2 = create_colored_die(DieColor.BLUE, die_id=203, variant_card=card, face_profile="V043_BLUE_TUNE")
        d_f2.current_face = d_f2.faces[1]
        d_f2.production_role = "INCOME"
        player.in_production_dice.append(d_f2)
        p3.collect_player_production_income(engine, player)
        self.assertGreaterEqual(player.research, 2)
        upgraded = p6.execute_track_upgrades(engine, player, SimpleNamespace(track_upgrades=["defense"]))
        self.assertEqual(upgraded, [("DEFENSE", 1)])
        self.assertEqual(player.defense_level, 1)

    def test_tc_p63_06_bot_valuation_and_rerolls(self):
        """TC-P63-06: Bot valuation, dynamic Face 2/3 evaluation, and Face 5 reroll protection."""
        eng_new = _engine_v043_1()
        eng_old = GameEngine(
            config=GameConfig.v043(num_players=3),
            bots=[BaseBot(i) for i in range(3)],
            seed=1,
            variant_cards=_cards(),
            version_deck=get_default_version_deck(),
            companies=[
                COMPANIES[CompanyCode.PROMETHEUS],
                COMPANIES[CompanyCode.MERIDIAN],
                COMPANIES[CompanyCode.DTO],
            ],
            white_hats=[
                WHITE_HATS[WhiteHatCode.OPERATOR],
                WHITE_HATS[WhiteHatCode.ACOUSTIC],
                WHITE_HATS[WhiteHatCode.SPOOK],
            ],
        )
        p_new = eng_new.state.players[0]
        p_old = eng_old.state.players[0]
        card = eng_new.variant_cards[DieColor.BLUE]

        die_new = create_colored_die(DieColor.BLUE, die_id=301, variant_card=card, face_profile="V043_BLUE_TUNE")
        die_old = create_colored_die(DieColor.BLUE, die_id=302, variant_card=card, face_profile="V038F")

        # Verify dynamic face_value evaluation for Face 2 (+2 🔬) and Face 3 (+$2)
        self.assertEqual(sfp.face_value(p_new, die_new.faces[1], eng_new.state), 2.0 * sfp.RESEARCH_VALUE)
        self.assertEqual(sfp.face_value(p_new, die_new.faces[2], eng_new.state), 2.0)

        # Under design weights (Cash=1.00, Research=1.20, Secret=1.60, p_L3=0.40 -> F5=2.40*1.60=3.84, Star=2.00):
        # V038F EV = (1.60 + 1.60 + 1.00 + 1.20 + 3.84 + 2.00) / 6 = 1.8733...
        # V043_BLUE_TUNE EV = (1.60 + 2.40 + 2.00 + 1.20 + 3.84 + 2.00) / 6 = 2.1733...
        def _design_ev(die):
            total = 0.0
            for f in die.faces:
                if f.secrets_pending:
                    total += 2.40 * 1.60
                elif f.is_star:
                    total += 2.00
                elif f.is_choice:
                    total += max(c.money * 1.00 + c.patches * 1.20 for c in f.choices)
                else:
                    total += f.money * 1.00 + f.patches * 1.20 + f.secrets * 1.60
            return total / 6.0

        self.assertAlmostEqual(_design_ev(die_old), 1.8733, places=3)
        self.assertAlmostEqual(_design_ev(die_new), 2.1733, places=3)
        self.assertGreater(_design_ev(die_new), _design_ev(die_old))

        # Policy mean_reroll_value is well-defined and below expected_bank_value
        mrv = sfp.mean_reroll_value(p_new, eng_new.state, die_new, 0)
        ebv = sfp.expected_bank_value(p_new, eng_new.state, DieColor.BLUE, 0)
        self.assertGreater(ebv, mrv)

        # Phase 1 adjust_rerolls must preserve Face 5 Secret face
        die_new.current_face = die_new.faces[4]
        for bot_cls in (AdaptiveBalancedBot, AccelerationistBot, RecklessSaboteurBot):
            bot = bot_cls(0)
            kept = sfp.adjust_rerolls(bot, p_new, [die_new], [0], eng_new.state, rerolls_remaining=2)
            self.assertNotIn(0, kept)

    def test_tc_p63_07_full_game_deterministic_smoke(self):
        """TC-P63-07: Deterministic smoke test across 2P, 3P, and 4P with v043_1_roster."""
        for n in (2, 3, 4):
            for seed in range(63000, 63010):
                e1 = _engine_v043_1(n=n, seed=seed, roster=True)
                e2 = _engine_v043_1(n=n, seed=seed, roster=True)
                s1 = e1.run_game()
                s2 = e2.run_game()

                self.assertTrue(e1.state.game_over)
                self.assertIn(
                    s1.end_reason.value,
                    ("singularity", "patient_zero", "market_collapse", "total_wipeout", "round_limit"),
                )
                self.assertEqual(s1.total_rounds, s2.total_rounds)
                self.assertEqual(s1.end_reason, s2.end_reason)
                self.assertEqual(
                    [r["secrets"] for r in s1.rankings],
                    [r["secrets"] for r in s2.rankings],
                )


if __name__ == "__main__":
    unittest.main()
