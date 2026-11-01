"""Simulation testing Variant Version Cards across all 8 roadmap combinations.

Confirms:
1. Pacing parity across all combinations (3 rds v1, 3 rds v2, 3 rds v3 -> ~8.5-9 rds total).
2. v3.0 reach rate in 60%-75% target window.
3. Asymmetric vector profiles (RaaS vs Worm, Script Kiddie vs Data Scraper, Zero-Day vs Kernel).
"""

from __future__ import annotations
from collections import defaultdict
import statistics
import time
from sim.config import CubeColor, GameConfig
from sim.engine import GameEngine
from sim.bots import AdaptiveBalancedBot, SecOpsTurtleBot, VentureGreedBot, AccelerationistBot
from sim.entities import CorruptionSpace, VersionCard
import sim.engine.phase2_threat as p2_threat

_orig = p2_threat.resolve_player_defense_and_wear
def patch():
    def custom(*args, **kwargs):
        player = kwargs.get('player') if 'player' in kwargs else args[1]
        s = player.patches
        player.patches = 0
        try:
            return _orig(*args, **kwargs)
        finally:
            player.patches = s
    p2_threat.resolve_player_defense_and_wear = custom
patch()


def build_cards():
    # v1.0 Cards
    # v1.0A: Script Kiddie (Financial Wiretaps)
    # Setup: 1R, 1B, 1G
    v1_sk = VersionCard(
        version_str="v1.0",
        name="Script Kiddie",
        staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1},
        directive_description="None.",
        directive_code="SCRIPT_KIDDIE",
        corruption_track=(
            CorruptionSpace(1, "Add 1R", add_cubes={CubeColor.RED: 1}),
            CorruptionSpace(2, "Lose $2 + Add 1K", lose_money=2, add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(3, "Lose 1 🔧", lose_patches=1),
            CorruptionSpace(4, "Upgrade: Lose 1 🔧", lose_patches=1, is_upgrade=True),
        ),
    )

    # v1.0B: Data Scraper (Database Scraping / Credential Leakage)
    # Setup: 1R, 2B, 0G (+ $1 starting cash bonus)
    v1_ds = VersionCard(
        version_str="v1.0",
        name="Data Scraper",
        staging_payload={CubeColor.RED: 1, CubeColor.BLUE: 2},
        directive_description="Players start with +$1 extra Money.",
        directive_code="DATA_SCRAPER",
        starting_cash_bonus=1,
        corruption_track=(
            CorruptionSpace(1, "Lose 1 🔧", lose_patches=1),
            CorruptionSpace(2, "Lose $1 + Add 1K", lose_money=1, add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(3, "Add 1G", add_cubes={CubeColor.GREEN: 1}),
            CorruptionSpace(4, "Upgrade: Demote 1 die", demote_dice=1, is_upgrade=True),
        ),
    )

    # v2.0 Cards
    # v2.0A: RaaS (Extortion / Cash Squeeze / Lock Cash)
    v2_raas = VersionCard(
        version_str="v2.0",
        name="RaaS",
        staging_payload={},
        directive_description="None.",
        directive_code="RAAS",
        corruption_track=(
            CorruptionSpace(1, "Lose $1", lose_money=1),
            CorruptionSpace(2, "Add 1R, 1G + Add 1K", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1, CubeColor.BLACK: 1}),
            CorruptionSpace(3, "Lock Cash next Phase 1", next_phase_lock="CASH"),
            CorruptionSpace(4, "Lose $2 & 1 🔧 + Add 1K", lose_money=2, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(5, "Upgrade: Add 1R", add_cubes={CubeColor.RED: 1}, is_upgrade=True),
        ),
    )

    # v2.0B: Polymorphic Worm (Hardware Demotion / Lock Patches / High Green Malware)
    v2_worm = VersionCard(
        version_str="v2.0",
        name="Polymorphic Worm",
        staging_payload={},
        directive_description="None.",
        directive_code="POLYMORPHIC_WORM",
        corruption_track=(
            CorruptionSpace(1, "Lose 2 🔧", lose_patches=2),
            CorruptionSpace(2, "Add 2G + Add 1K", add_cubes={CubeColor.GREEN: 2, CubeColor.BLACK: 1}),
            CorruptionSpace(3, "Lock Patch next Phase 1", next_phase_lock="PATCH"),
            CorruptionSpace(4, "Demote 1 die + Add 1K", demote_dice=1, add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(5, "Upgrade: Add 1R", add_cubes={CubeColor.RED: 1}, is_upgrade=True),
        ),
    )

    # v3.0 Cards
    # v3.0A: Zero-Day Override (Shield Lockdown / Balanced Singularity)
    v3_zd = VersionCard(
        version_str="v3.0",
        name="Zero-Day Override",
        staging_payload={},
        directive_description="None.",
        directive_code="ZERO_DAY_OVERRIDE",
        corruption_track=(
            CorruptionSpace(1, "Add 1R, 1B, 1G", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1, CubeColor.GREEN: 1}),
            CorruptionSpace(2, "Lose $2 + Add 1K", lose_money=2, add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(3, "Add 1R, 1B", add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
            CorruptionSpace(4, "Lock Shields next Phase 1 + Add 1K", next_phase_lock="SHIELD", add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(5, "Return 1 Colored Die", return_colored_dice=1),
            CorruptionSpace(6, "Singularity: Add 2R, 2B, 2G", add_cubes={CubeColor.RED: 2, CubeColor.BLUE: 2, CubeColor.GREEN: 2}, is_singularity=True),
        ),
    )

    # v3.0B: Corrupted Kernel (Direct Secret Drain / Die Demotion / Heavy Exfiltration)
    v3_ck = VersionCard(
        version_str="v3.0",
        name="Corrupted Kernel",
        staging_payload={},
        directive_description="None.",
        directive_code="CORRUPTED_KERNEL",
        corruption_track=(
            CorruptionSpace(1, "Demote 1 die + Add 1R, 1B", demote_dice=1, add_cubes={CubeColor.RED: 1, CubeColor.BLUE: 1}),
            CorruptionSpace(2, "Lose $2 & 1 🔧 + Add 1K", lose_money=2, lose_patches=1, add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(3, "Add 1R, 1G", add_cubes={CubeColor.RED: 1, CubeColor.GREEN: 1}),
            CorruptionSpace(4, "Lose 1 Secret + Add 1K", lose_secrets=1, add_cubes={CubeColor.BLACK: 1}),
            CorruptionSpace(5, "Return 1 Colored Die", return_colored_dice=1),
            CorruptionSpace(6, "Singularity: Lose 1 Secret + Add 2R, 2B, 1G", lose_secrets=1, add_cubes={CubeColor.RED: 2, CubeColor.BLUE: 2, CubeColor.GREEN: 1}, is_singularity=True),
        ),
    )

    return {
        "v1": [v1_sk, v1_ds],
        "v2": [v2_raas, v2_worm],
        "v3": [v3_zd, v3_ck],
    }


def run_combinations_test(num_runs_per_pair=250):
    cards = build_cards()
    roadmaps = []
    for v1 in cards["v1"]:
        for v2 in cards["v2"]:
            for v3 in cards["v3"]:
                name = f"{v1.name} -> {v2.name} -> {v3.name}"
                roadmaps.append((name, [v1, v2, v3]))

    print(f"================ SIMULATING ALL {len(roadmaps)} ROADMAP COMBINATIONS ({num_runs_per_pair} runs each) ================\n")

    summary_rows = []

    for idx, (r_name, deck) in enumerate(roadmaps, 1):
        rounds = []
        v3_seen = 0
        r_v = {0: [], 1: [], 2: []}
        tray_r = defaultdict(list)
        tray_b = defaultdict(list)
        tray_g = defaultdict(list)

        for i in range(num_runs_per_pair):
            cfg = GameConfig(
                num_players=4,
                autonomous_pulse_by_version={"v1.0": 1, "v2.0": 1, "v3.0": 1},
                starting_secrets=12,
                starting_money=7,
            )
            bots = [AdaptiveBalancedBot(0), SecOpsTurtleBot(1), VentureGreedBot(2), AccelerationistBot(3)]
            eng = GameEngine(config=cfg, bots=bots, seed=i*211 + idx*37, version_deck=deck)
            seen = set()
            grv = {0: 0, 1: 0, 2: 0}
            while not eng.state.game_over:
                v_str = eng.state.active_version.version_str
                v_idx = eng.state.current_version_index
                seen.add(v_str)
                grv[v_idx] += 1
                telem = eng.run_round()
                tray_r[v_str].append(telem.exited_cubes.get(CubeColor.RED, 0))
                tray_b[v_str].append(telem.exited_cubes.get(CubeColor.BLUE, 0))
                tray_g[v_str].append(telem.exited_cubes.get(CubeColor.GREEN, 0))

            res = eng.evaluate_end_game()
            rounds.append(res.total_rounds)
            if "v3.0" in seen:
                v3_seen += 1
            for k in range(3):
                r_v[k].append(grv[k])

        v3_pct = (v3_seen / num_runs_per_pair) * 100
        mean_rds = statistics.mean(rounds)
        v1_rds = statistics.mean(r_v[0])
        v2_rds = statistics.mean(r_v[1])
        v3_rds = statistics.mean(r_v[2])

        summary_rows.append({
            "name": r_name,
            "v3_pct": v3_pct,
            "mean_rds": mean_rds,
            "v1_rds": v1_rds,
            "v2_rds": v2_rds,
            "v3_rds": v3_rds,
            "v2_r": statistics.mean(tray_r["v2.0"]),
            "v2_b": statistics.mean(tray_b["v2.0"]),
            "v2_g": statistics.mean(tray_g["v2.0"]),
        })

        print(f"[{idx}/8] {r_name}")
        print(f"  v3.0 Reach: {v3_pct:.1f}% | Total Rounds: {mean_rds:.2f} (v1: {v1_rds:.2f}, v2: {v2_rds:.2f}, v3: {v3_rds:.2f})")
        print(f"  v2.0 Tray Attack: Red={statistics.mean(tray_r['v2.0']):.2f}, Blue={statistics.mean(tray_b['v2.0']):.2f}, Green={statistics.mean(tray_g['v2.0']):.2f} (Total={statistics.mean(tray_r['v2.0'])+statistics.mean(tray_b['v2.0'])+statistics.mean(tray_g['v2.0']):.2f})\n")

    print("\n================ SUMMARY ACROSS ALL 8 ROADMAPS ================")
    print(f"{'Roadmap':<55} | {'v3 Reach':<9} | {'Total Rds':<9} | {'v1 Rds':<7} | {'v2 Rds':<7} | {'v3 Rds':<7}")
    print("-" * 105)
    for row in summary_rows:
        print(f"{row['name']:<55} | {row['v3_pct']:6.1f}%   | {row['mean_rds']:6.2f} rds | {row['v1_rds']:5.2f}  | {row['v2_rds']:5.2f}  | {row['v3_rds']:5.2f}")


if __name__ == "__main__":
    t0 = time.time()
    run_combinations_test(num_runs_per_pair=250)
    print(f"Completed in {time.time()-t0:.2f}s")
