"""Unit tests for v0.45.0 Glitched Shield Slots Rework, Defense Grid Overflow & 2P SETEC Black Cube."""

import unittest

from sim.bots.base import Phase3ActionPlan
from sim.config import GameConfig
from sim.engine import end_game, market_share, phase3_income, phase4_attack_resolution, phase6_operations, research_tracks, secret_faces
from sim.engine.core import GameEngine
from sim.engine.state import CompileResult, ProductionRole
from sim.entities import (
    COMPANIES,
    WHITE_HATS,
    CompanyCode,
    CubeColor,
    Die,
    DieColor,
    Face,
    ShieldColor,
    WhiteHatCode,
    create_colored_die,
    create_gray_die,
)


def _purple_die(die_id: int) -> Die:
    return create_colored_die(DieColor.PURPLE, die_id=die_id)


def _purple_star_die(die_id: int) -> Die:
    d = _purple_die(die_id=die_id)
    d.current_face = Face(name="Purple Star", is_star=True, star_code="PURPLE_STAR")
    d.production_role = ProductionRole.INCOME
    return d


class TestV450GlitchedShieldSlotsRework(unittest.TestCase):
    """Covers TEST-OP-01..03, TEST-MER-01, TEST-P3-01, TEST-DGO-01..06, TEST-SEC-01, TEST-SET-01..05."""

    # --- 1. WS-OPERATOR: Logistics Bounty ---

    def test_operator_empty_scanned_box(self) -> None:
        """TEST-OP-01: Scanned Box empty -> 0 research awarded."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=1)
        p0 = eng.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.OPERATOR]
        p0.scanned_dice.clear()
        p0.in_production_dice.append(_purple_star_die(901))
        rec = phase3_income.execute_player_income(eng, p0)
        self.assertEqual(rec.research, 0)
        self.assertEqual(p0.research_tokens, 0)

    def test_operator_duplicate_colors(self) -> None:
        """TEST-OP-02: Scanned Box [Gray, Gray, Purple] -> 2 distinct colors -> +2 research."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=2)
        p0 = eng.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.OPERATOR]
        p0.scanned_dice = [create_gray_die(1), create_gray_die(2), _purple_die(3)]
        p0.in_production_dice.append(_purple_star_die(902))
        rec = phase3_income.execute_player_income(eng, p0)
        self.assertEqual(rec.research, 2)
        self.assertEqual(p0.research_tokens, 2)
        self.assertEqual(p0.operator_scanned_colors_count, 2)
        self.assertEqual(p0.operator_research_harvested, 2)

    def test_operator_all_colors_inclusive(self) -> None:
        """TEST-OP-03: Scanned Box with Gray, Purple, Red, Blue, Green, Yellow -> 6 colors -> +6 research."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=3)
        p0 = eng.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.OPERATOR]
        p0.scanned_dice = [
            create_gray_die(1),
            _purple_die(2),
            create_colored_die(DieColor.RED, 3),
            create_colored_die(DieColor.BLUE, 4),
            create_colored_die(DieColor.GREEN, 5),
            create_colored_die(DieColor.YELLOW, 6),
        ]
        p0.in_production_dice.append(_purple_star_die(903))
        rec = phase3_income.execute_player_income(eng, p0)
        self.assertEqual(rec.research, 6)
        self.assertEqual(p0.research_tokens, 6)

    # --- 2. COMP-MERIDIAN & 3. Phase 3 Die Ability Alignment ---

    def test_meridian_capital_injection_clean(self) -> None:
        """TEST-MER-01: Meridian earns +$3 Cash once per Version in Phase 3."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=4)
        p0 = eng.state.players[0]
        p0.company = COMPANIES[CompanyCode.MERIDIAN]
        start_money = p0.money
        res = phase3_income.resolve_meridian_capital_injection(eng, p0, record=phase3_income.IncomeRecord())
        self.assertTrue(res)
        self.assertEqual(p0.money, start_money + 3)
        # Second call in same version does not pay again
        res2 = phase3_income.resolve_meridian_capital_injection(eng, p0, record=phase3_income.IncomeRecord())
        self.assertFalse(res2)
        self.assertEqual(p0.money, start_money + 3)
        self.assertNotIn("[TUNE]", COMPANIES[CompanyCode.MERIDIAN].description)

    def test_phase3_die_abilities_exclusive(self) -> None:
        """TEST-P3-01: Legacy Phase 6 protocol/R2 triggers do not fire in v0.45.0."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=5)
        p0 = eng.state.players[0]
        p0.white_hat = WHITE_HATS[WhiteHatCode.SPOOK]
        g_die = create_gray_die(501)
        p0.glitched_dice.append(g_die)
        p0.purple_star_available = True
        p0.r2_actions_available = 1
        p0.money = 10
        start_ms = p0.market_share
        plan = Phase3ActionPlan(spook_burn_die_id=501, use_r2_share=1)
        phase6_operations.execute_player_operations_turn(eng, p0, plan)
        # Neither Spook Burn Notice nor R2 Ad Campaign executes in Phase 6
        self.assertIn(g_die, p0.glitched_dice)
        self.assertEqual(p0.market_share, start_ms)

    # --- 4. Glitched Shield Slots Rework (Defense Grid Overflow) ---

    def test_initial_shield_slot_state(self) -> None:
        """TEST-DGO-01: Player starts with [1, 0] (1 glitched slot with 1 cube, 1 clean slot)."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=6)
        for p in eng.state.players:
            self.assertEqual(p.shield_slots, [1, 0])
            self.assertEqual(p.glitched_shield_slots_count, 1)
            self.assertEqual(p.clean_shield_slots_count, 1)
            self.assertEqual(p.total_green_cubes, 1)
            self.assertEqual(p.max_green_capacity, 4)

    def test_even_cube_distribution(self) -> None:
        """TEST-DGO-02: [1, 0] + 1 Green -> [1, 1]; +1 Green -> [2, 1]."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=7)
        p0 = eng.state.players[0]
        self.assertEqual(p0.shield_slots, [1, 0])
        overflow1 = secret_faces.apply_green_cube_infections(p0, 1)
        self.assertEqual(overflow1, 0)
        self.assertEqual(p0.shield_slots, [1, 1])
        overflow2 = secret_faces.apply_green_cube_infections(p0, 1)
        self.assertEqual(overflow2, 0)
        self.assertEqual(p0.shield_slots, [2, 1])

    def test_defense_grid_overflow_trigger(self) -> None:
        """TEST-DGO-03: [2, 2] + 1 Green -> slots remain [2, 2], player loses 1 Secret."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=8)
        p0 = eng.state.players[0]
        p0.shield_slots = [2, 2]
        start_secrets = p0.secrets
        overflow = secret_faces.apply_green_cube_infections(p0, 1, round_num=2)
        self.assertEqual(overflow, 1)
        self.assertEqual(p0.shield_slots, [2, 2])
        self.assertEqual(p0.secrets, start_secrets - 1)
        self.assertEqual(p0.defense_grid_overflow_count, 1)
        self.assertEqual(p0.secrets_lost_to_overflow, 1)

    def test_defense_grid_overflow_wipeout(self) -> None:
        """TEST-DGO-04: Player at 1 Secret suffering overflow drops to 0 Secrets and becomes Patient Zero."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=9)
        p0 = eng.state.players[0]
        p0.shield_slots = [2, 2]
        p0.secrets = 1
        overflow = secret_faces.apply_green_cube_infections(p0, 1, round_num=3)
        self.assertEqual(overflow, 1)
        self.assertEqual(p0.secrets, 0)
        self.assertTrue(p0.is_patient_zero)
        self.assertEqual(p0.elimination_round, 3)

    def test_purging_shield_clears_all_cubes(self) -> None:
        """TEST-DGO-05: Assigning 1 Shield to a slot with 2 Green cubes clears both cubes to 0."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=10)
        p0 = eng.state.players[0]
        p0.shield_slots = [2, 1]
        purge_die = create_gray_die(701)
        purge_die.current_face = Face(name="Shield", shield_color=ShieldColor.ANY)
        purge_die.production_role = ProductionRole.PURGING_SHIELD
        p0.in_production_dice = [purge_die]

        phase4_attack_resolution.resolve_player_defense_and_wear(
            engine=eng,
            player=p0,
            rolled_dice=[purge_die],
            commitments={0: ShieldColor.ANY},
            attack_strengths={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0},
            active_directive=eng.state.active_directive_code,
        )
        # Prioritizes 2-cube slot [0] -> clears both cubes to 0, leaving [0, 1]
        self.assertEqual(p0.shield_slots, [0, 1])
        self.assertEqual(p0.slots_purged_by_shields_total, 1)
        self.assertEqual(p0.cubes_purged_by_shields_total, 2)
        self.assertIn(purge_die, p0.scanned_dice)

    def test_capacity_upgrade_arrives_clean(self) -> None:
        """TEST-DGO-06: Defense Grid advancing to Level 2 expands slots from [c0, c1] to [c0, c1, 0]."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=11)
        p0 = eng.state.players[0]
        p0.shield_slots = [2, 1]
        research_tracks.apply_level(cfg, p0, "DEFENSE", 2, round_number=2)
        self.assertEqual(p0.defense_capacity, 3)
        self.assertEqual(p0.shield_slots, [2, 1, 0])

    # --- 5. Unified Starting Corporate Secrets ---

    def test_starting_secrets_flat_4(self) -> None:
        """TEST-SEC-01: 2P, 3P, and 4P configurations all initialize players with 4 Corporate Secrets."""
        for n in (2, 3, 4):
            cfg = GameConfig.v045(num_players=n)
            eng = GameEngine(cfg, seed=12 + n)
            self.assertEqual(len(eng.state.players), n)
            for p in eng.state.players:
                self.assertEqual(p.secrets, 4)

    # --- 6. 2P SETEC Corp Neutral Black Cube ---

    def test_setec_corp_inactive_in_3p_4p(self) -> None:
        """TEST-SET-01: SETEC Corp is disabled when num_players >= 3."""
        for n in (3, 4):
            cfg = GameConfig.v045(num_players=n)
            eng = GameEngine(cfg, seed=20 + n)
            self.assertFalse(eng.state.setec_corp_active)
            cr = CompileResult(
                staged_before={},
                stuck_before={},
                exited_cubes={CubeColor.RED: 2, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
                stuck_after={},
            )
            phase4_attack_resolution.finalize_attack_resolution(eng, cr)
            self.assertEqual(eng.state.setec_market_share, 0)

    def test_setec_corp_phase4_red_advance(self) -> None:
        """TEST-SET-02: 2P: 1+ Red exited -> SETEC MS +1. 0 Red exited -> SETEC MS +0."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=25)
        self.assertTrue(eng.state.setec_corp_active)
        self.assertEqual(eng.state.setec_market_share, 0)

        cr_no_red = CompileResult(
            staged_before={},
            stuck_before={},
            exited_cubes={CubeColor.RED: 0, CubeColor.BLUE: 2, CubeColor.GREEN: 1, CubeColor.BLACK: 0},
            stuck_after={},
        )
        phase4_attack_resolution.finalize_attack_resolution(eng, cr_no_red)
        self.assertEqual(eng.state.setec_market_share, 0)

        cr_with_red = CompileResult(
            staged_before={},
            stuck_before={},
            exited_cubes={CubeColor.RED: 3, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 0},
            stuck_after={},
        )
        phase4_attack_resolution.finalize_attack_resolution(eng, cr_with_red)
        self.assertEqual(eng.state.setec_market_share, 1)
        self.assertEqual(eng.state.setec_corp_advances_total, 1)

    def test_setec_corp_absorbs_mlb_first(self) -> None:
        """TEST-SET-03: SETEC MS 15, P1 MS 12, P2 MS 10 -> SETEC takes 1st (+3 absorbed), P1 gets +1, P2 gets +0."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=26)
        eng.state.setec_market_share = 15
        eng.state.players[0].market_share = 12
        eng.state.players[1].market_share = 10
        eng.state.red_secret_banked_this_round = True

        awards = secret_faces.red_secret_payout_awards(cfg, eng.state)
        self.assertEqual(awards[market_share.SETEC_CORP_ID], (1, 3))
        self.assertEqual(awards[0], (2, 1))
        self.assertEqual(awards[1], (3, 0))

        p0_before, p1_before = eng.state.players[0].secrets, eng.state.players[1].secrets
        secret_faces.fire_round_payout(cfg, eng.state)
        self.assertEqual(eng.state.players[0].secrets, p0_before + 1)
        self.assertEqual(eng.state.players[1].secrets, p1_before)
        self.assertEqual(eng.state.setec_corp_mlb_1st_places, 1)
        self.assertEqual(eng.state.setec_corp_mlb_secrets_absorbed, 3)

        # Also verify end-game ranking places SETEC 1st, P0 2nd, P1 3rd
        res = end_game.evaluate_end_game(eng)
        by_pid = {r["player_id"]: r for r in res.rankings}
        self.assertEqual(by_pid[0]["market_share_place"], 2)
        self.assertEqual(by_pid[1]["market_share_place"], 3)

    def test_setec_corp_tied_first_shares_place(self) -> None:
        """TEST-SET-04: SETEC MS 14, P1 MS 14, P2 MS 10 -> P1 shares 1st (+3), P2 is 3rd (+0)."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=27)
        eng.state.setec_market_share = 14
        eng.state.players[0].market_share = 14
        eng.state.players[1].market_share = 10

        awards = secret_faces.red_secret_payout_awards(cfg, eng.state)
        self.assertEqual(awards[market_share.SETEC_CORP_ID], (1, 3))
        self.assertEqual(awards[0], (1, 3))
        self.assertEqual(awards[1], (3, 0))

    def test_setec_corp_no_market_collapse(self) -> None:
        """TEST-SET-05: SETEC Corp at 0 Market Share does not trigger Market Collapse."""
        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=28)
        eng.state.setec_market_share = 0
        eng.state.players[0].market_share = 10
        eng.state.players[1].market_share = 10
        collapsed = market_share.check_market_collapse(eng)
        self.assertFalse(collapsed)
        self.assertFalse(eng.state.is_final_round)

    def test_v045_full_game_smoke_2p_3p_4p(self) -> None:
        """Full simulation smoke test for GameConfig.v045_roster across 2P, 3P, 4P."""
        for n in (2, 3, 4):
            cfg = GameConfig.v045_roster(num_players=n)
            eng = GameEngine(cfg, seed=100 + n)
            res = eng.run_game()
            self.assertTrue(eng.state.current_round >= 1)
            self.assertEqual(len(res.rankings), n)

    def test_bot_generic_shield_blocks_lethal_green_overflow(self) -> None:
        """Bot Generic shield values lethal Green overflow at [2, 2] above non-lethal Red/Blue."""
        from sim.bots import market_share_policy as msp

        cfg = GameConfig.v045_roster(num_players=2)
        eng = GameEngine(cfg, seed=201)
        p0 = eng.state.players[0]
        p0.shield_slots = [2, 2]
        p0.secrets = 1
        p0.market_share = 10
        rem = {CubeColor.RED: 1, CubeColor.BLUE: 0, CubeColor.GREEN: 1}
        val_green = msp.marginal_block_value(CubeColor.GREEN, rem, p0, eng.state, dict(rem), msp.MarketSharePolicy())
        val_red = msp.marginal_block_value(CubeColor.RED, rem, p0, eng.state, dict(rem), msp.MarketSharePolicy())
        self.assertGreater(val_green, val_red)
        self.assertEqual(val_green, 100.0)
        alloc = msp.default_any_shield_allocation(p0, dict(rem), 1, eng.state, dict(rem))
        self.assertEqual(alloc.get(CubeColor.GREEN, 0), 1)

    def test_phase2_corruption_overflow_sets_elimination_round_and_breached_pids(self) -> None:
        """Phase 2 corruption demote_dice overflow sets elimination_round and populates cr.breached_pids."""
        from sim.engine import phase2_compiler
        from sim.entities import CorruptionSpace

        cfg = GameConfig.v045(num_players=2)
        eng = GameEngine(cfg, seed=202)
        eng.state.current_round = 3
        p0 = eng.state.players[0]
        p0.shield_slots = [2, 2]
        p0.secrets = 1
        # Force corruption track to land on a demote_dice=1 space when 1 black cube drops
        import dataclasses
        ver = eng.state.active_version
        eng.state.version_deck[eng.state.current_version_index] = dataclasses.replace(
            ver, corruption_track=[CorruptionSpace(index=1, label="Glitch", demote_dice=1)]
        )
        eng.state.corruption_track = 0
        eng.state.staging_cup = {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 1}
        eng.state.tower.drop = lambda cup, rng, **kw: {CubeColor.RED: 0, CubeColor.BLUE: 0, CubeColor.GREEN: 0, CubeColor.BLACK: 1}
        cr = phase2_compiler.execute_compiler_drop(eng, {})
        self.assertTrue(p0.is_patient_zero)
        self.assertEqual(p0.elimination_round, 3)
        self.assertIn(p0.player_id, cr.breached_pids)

    def test_fast_clone_isolation_shield_slots_and_setec_ms(self) -> None:
        """fast_clone.clone_engine isolates shield_slots and setec_market_share."""
        from sim.engine import fast_clone

        cfg = GameConfig.v045_roster(num_players=2)
        eng = GameEngine(cfg, seed=203)
        eng.state.players[0].shield_slots = [2, 1]
        eng.state.setec_market_share = 5
        clone, _ = fast_clone.clone_engine(eng)
        clone.state.players[0].shield_slots[0] = 0
        clone.state.setec_market_share = 12
        self.assertEqual(eng.state.players[0].shield_slots, [2, 1])
        self.assertEqual(eng.state.setec_market_share, 5)


if __name__ == "__main__":
    unittest.main()
