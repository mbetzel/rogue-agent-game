"""v0.47 post-telemetry GD probes (scripts only; monkeypatches, no engine edits). Quiet summary output.

--probe helix : Helix win / use / burn under Black-Signature variants (version-only burn, no hijack) and bot min-gain 0.
--probe pen   : PenTestRush and Adaptive focal vs Adaptive field (paired), base vs safe zone 0-3 vs pen cost 3.
--probe star  : P(star), locks, kept-⚠ by source, declined rerolls, v0.46 vs v0.47.
"""
from __future__ import annotations
import argparse, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from scripts import run_locked_vuln_sweep as s47  # noqa: E402
from scripts import run_v046_dominance_matrix as dm  # noqa: E402
from sim.engine import phase4_attack_resolution as p4  # noqa: E402

_ORIG_BLACK = p4._resolve_signature_black
BLACK_MODE = os.environ.get("PROBE_BLACK", "base")


def _is_helix(player):
    return getattr(getattr(player, "company", None), "code", None) == p4.CompanyCode.HELIX


def _black(engine, player):
    if BLACK_MODE == "base" or not _is_helix(player) or player.helix_bypass_used_game:
        return _ORIG_BLACK(engine, player)
    if BLACK_MODE == "version_only":  # Black blocks the bypass for the rest of this Version; the game use survives
        cfg = engine.config
        object.__setattr__(cfg, "helix_bypass_once_per_game", False)
        try:
            return _ORIG_BLACK(engine, player)
        finally:
            object.__setattr__(cfg, "helix_bypass_once_per_game", True)
    if BLACK_MODE == "no_hijack":  # Black cannot take the bypass; Helix loses 2 Secrets like any spent override
        player.helix_bypass_used_game = True
        try:
            return _ORIG_BLACK(engine, player)
        finally:
            player.helix_bypass_used_game = False
    raise ValueError(BLACK_MODE)


p4._resolve_signature_black = _black

# Optional: the once-per-game bypass also sets 1 die face (the v0.46 face-set rider), PROBE_HELIX_FACESET=1
from sim.engine import phase1_roll_deploy as p1  # noqa: E402
_ORIG_L4 = p1.resolve_release_l4_gray_face_override


def _l4(player, active_dice, game_state=None, *a, **k):
    if os.environ.get("PROBE_HELIX_FACESET") == "1" and getattr(player, "helix_bypass_active", False) and not a and not k:
        ov = player.bot.choose_helix_face_override_v038(player, active_dice, game_state)
        if ov:
            i, face = ov
            if 0 <= i < len(active_dice) and not face.is_star and face in active_dice[i].faces:
                active_dice[i].current_face = face
                active_dice[i].is_locked = False
                active_dice[i].chosen_choice_index = None
    return _ORIG_L4(player, active_dice, game_state, *a, **k)


p1.resolve_release_l4_gray_face_override = _l4


def helix(games, procs, extra):
    for pl in (2, 3, 4):
        m = s47.metrics47(s47.play_all("v046_locked_roster", "mixed1", pl, games, 42, dict(extra), procs, False), pl)
        print(f"  {pl}P black={BLACK_MODE} extra={extra}: Helix win {m['helix_win_pct']:.1f}  use {m['helix_use_share_pct']:.1f}%"
              f"  burned {m['helix_lost_to_black_pct']:.1f}%  ⚠ removed/use {s47.f(m['helix_mean_vuln_removed'])}"
              f"  rounds-hist {m['helix_round_hist']}  seats {m['helix_seats']}")


def pen(games, procs, overrides, label):
    for pl in (2, 3):
        cells = {f: dm.run_cell(pl, games, 42, f, "Adaptive", procs, overrides, "v046_locked_roster") for f in ("Adaptive", "PenTestRush")}
        a = dm.cell_stats(cells["Adaptive"], pl)
        p = dm.cell_stats(cells["PenTestRush"], pl)
        d, lo, hi = dm.paired_win_delta(cells["PenTestRush"], cells["Adaptive"])
        print(f"  {label} {pl}P: Adaptive {a['vs_fair_pp']:+.1f}  PenTestRush {p['vs_fair_pp']:+.1f}  paired {d:+.1f} [{lo:+.1f},{hi:+.1f}]"
              f"  green lost PTR {p['green_lost']:.2f} / Ad {a['green_lost']:.2f}  pen steps {p['pen_steps']:.2f} / {a['pen_steps']:.2f}")


def star(games, procs):
    for cfgname in ("v046_roster", "v046_locked_roster"):
        m = s47.metrics47(s47.play_all(cfgname, "mixed1", 3, games, 42, {}, procs, False), 3)
        print(f"  {cfgname} 3P: P(star) {s47.f(m['p_star_per_colored_die'], 3)} by colour "
              + " ".join(f"{k}={s47.f(v, 3)}" for k, v in m["p_star_by_color"].items()))
        print("    kept ⚠/die by colour " + " ".join(f"{k}={s47.f(v, 3)}" for k, v in m["kept_vuln_per_die_by_color"].items()))
        print("    kept ⚠/player-round by source " + " ".join(f"{k}={s47.f(v, 3)}" for k, v in m["kept_vuln_per_player_round_by_source"].items()))
        print("    declined/player-round " + (" ".join(f"{k}={s47.f(v, 3)}" for k, v in m["declined_per_player_round"].items()) or "none"))
        print(f"    locks/player-round {s47.f(m['locks_per_player_round'], 3)}  keep rate {s47.f(m.get('keep_rate_pct'), 1)}"
              f"  liquid {s47.f(m.get('liquid_per_player_round'))}  bought/game {s47.f(m['colored_dice_bought_per_game'])}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", choices=("helix", "pen", "star"), required=True)
    ap.add_argument("--games", type=int, default=1200)
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--set", default=None)
    ap.add_argument("--vuln-params", default=None)
    ap.add_argument("--label", default="base")
    a = ap.parse_args()
    if a.probe == "helix":
        helix(a.games, a.procs, s47.parse_overrides(a.set, a.vuln_params))
    elif a.probe == "pen":
        import json
        ov = dm.tbl.coerce_overrides(json.loads(a.set)) if a.set else {}
        pen(a.games, a.procs, ov, a.label)
    else:
        star(a.games, a.procs)
