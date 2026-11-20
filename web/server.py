"""Pure Python 3 standard library ThreadingHTTPServer serving web/static/ and routing /api/game/*."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from web.game_controller import GameController
from web.schemas import error_response, parse_request_json, success_response

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))


class RogueAgentRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler routing /api/game/* endpoints and serving static assets."""

    controller: GameController = GameController()
    controller_lock: threading.RLock = threading.RLock()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        """Custom log message formatting (suppressed or concise)."""
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def _send_json_response(self, payload: Dict[str, Any], status_code: int = 200) -> None:
        """Sends a JSON response with proper headers."""
        data_bytes = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data_bytes)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(data_bytes)

    def do_OPTIONS(self) -> None:
        """Handles CORS preflight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Routes GET requests to API or static asset handler."""
        clean_path = self.path.split("?")[0]

        if clean_path == "/api/game/state":
            try:
                with self.controller_lock:
                    state = self.controller.get_full_state()
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)
            except Exception as exc:
                payload, code = error_response(str(exc), 500)
                self._send_json_response(payload, code)
            return

        # Serve static assets
        if clean_path == "/":
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self) -> None:
        """Routes POST requests to /api/game/* endpoints."""
        clean_path = self.path.split("?")[0]

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b""
        data, err = parse_request_json(raw_body)
        if err:
            payload, code = error_response(err, 400)
            self._send_json_response(payload, code)
            return

        assert data is not None

        try:
            with self.controller_lock:
                # Helper to resolve player_id if not explicitly provided in the request
                def get_target_pid(default_to_human: bool = False) -> int:
                    if "player_id" in data:
                        return int(data["player_id"])
                    if default_to_human:
                        for pid, meta in self.controller.player_meta.items():
                            if meta.get("is_human", False):
                                return pid
                    return self.controller.active_player_index

                if clean_path == "/api/game/new":
                    num_players = int(data.get("num_players", 4))
                    players_config = data.get("players")
                    seed = data.get("seed")
                    if seed is not None:
                        seed = int(seed)
                    randomize_cards = bool(data.get("randomize_cards", False))
                    enable_corporate_asymmetry = bool(data.get("enable_corporate_asymmetry", True))
                    rules_version = data.get("rules_version")

                    state = self.controller.new_game(
                        num_players=num_players,
                        players_config=players_config,
                        seed=seed,
                        randomize_cards=randomize_cards,
                        enable_corporate_asymmetry=enable_corporate_asymmetry,
                        rules_version=rules_version,
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/hire_contractors":
                    pid = get_target_pid(default_to_human=True)
                    count = int(data.get("count", 1))
                    use_op = bool(data.get("use_operator_ability", False))
                    buy_3rd = bool(data.get("buy_third_die", False))
                    state = self.controller.hire_contractors(
                        pid, count, use_operator_ability=use_op, buy_third_die=buy_3rd
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/reroll":
                    pid = get_target_pid(default_to_human=True)
                    reroll_indices = data.get("reroll_indices", [])
                    use_prodigy = bool(data.get("use_prodigy_ability", False))
                    state = self.controller.perform_reroll(
                        pid, reroll_indices, use_prodigy_ability=use_prodigy
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/roll":
                    pid = get_target_pid(default_to_human=True)
                    state = self.controller.roll_pool(pid)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/lock_in":
                    # Phase 1 Step 4: Deploy Dice (Choice Face declarations by rolled-pool index)
                    pid = get_target_pid(default_to_human=True)
                    decls = data.get("choice_declarations")
                    if decls is not None and not isinstance(decls, dict):
                        payload, code = error_response("choice_declarations must be an object {die_index: option}", 400)
                        self._send_json_response(payload, code)
                        return
                    state = self.controller.lock_in(pid, decls)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/override_face":
                    pid = get_target_pid(default_to_human=True)
                    if "die_index" not in data or "face_index" not in data:
                        payload, code = error_response("Missing required fields 'die_index' and 'face_index'", 400)
                        self._send_json_response(payload, code)
                        return
                    state = self.controller.override_face(
                        pid, int(data["die_index"]), int(data["face_index"]), str(data.get("source", "helix")))
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/compile":
                    state = self.controller.compile_drop()
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/capital_injection":
                    # Phase 3: Meridian Capital Injection
                    pid = get_target_pid(default_to_human=True)
                    state = self.controller.capital_injection(pid)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/confirm_income":
                    # Phase 3: Income
                    pid = get_target_pid(default_to_human=True)
                    state = self.controller.confirm_income(
                        pid,
                        spook_burn_die_id=data.get("spook_burn_die_id"),
                        phreaker_die_id=data.get("phreaker_die_id"),
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/confirm_attacks":
                    # Phase 4: Attack Resolution
                    pid = get_target_pid(default_to_human=True)
                    aegis_color = data.get("aegis_color")
                    if aegis_color is not None and str(aegis_color).lower() not in ("red", "blue", "green", "none", "decline"):
                        payload, code = error_response("aegis_color must be one of red, blue, green, none", 400)
                        self._send_json_response(payload, code)
                        return
                    tracks = data.get("signature_green_tracks")
                    if tracks is not None and not isinstance(tracks, list):
                        payload, code = error_response("signature_green_tracks must be a list of track names", 400)
                        self._send_json_response(payload, code)
                        return
                    recipient = data.get("signature_red_recipient")
                    state = self.controller.confirm_attacks(
                        pid, aegis_color=aegis_color,
                        use_slush_fund=(bool(data["use_slush_fund"]) if data.get("use_slush_fund") is not None else None),
                        aegis_green=data.get("aegis_green"),
                        signature_green_tracks=tracks,
                        signature_red_recipient=int(recipient) if recipient is not None else None,
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/choose_graduates":
                    # Phase 6: CI/CD Pipeline Shift (Sprint Review, <= Release Bandwidth)
                    pid = get_target_pid(default_to_human=True)
                    grads = data.get("graduate_die_ids")
                    if not isinstance(grads, list):
                        payload, code = error_response("Missing required list field 'graduate_die_ids'", 400)
                        self._send_json_response(payload, code)
                        return
                    splice = data.get("splice_die_id")
                    state = self.controller.choose_graduates(
                        pid,
                        [int(x) for x in grads],
                        splice_die_id=int(splice) if splice is not None else None,
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/buy":
                    pid = get_target_pid(default_to_human=False)
                    if "color" not in data:
                        payload, code = error_response("Missing required field 'color'", 400)
                        self._send_json_response(payload, code)
                        return
                    color_str = str(data["color"])
                    use_cipher = bool(data.get("use_cipher_ability", False))
                    state = self.controller.buy_die(pid, color_str, use_cipher_ability=use_cipher)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/dirty_income":
                    pid = get_target_pid(default_to_human=False)
                    backlash_raw = data.get("backlash_die_index")
                    backlash_idx = int(backlash_raw) if backlash_raw is not None else 0
                    backlash_id_raw = data.get("backlash_die_id")
                    backlash_die_id = int(backlash_id_raw) if backlash_id_raw is not None else None
                    use_cipher = bool(data.get("use_cipher_ability", False))
                    state = self.controller.take_dirty_income(
                        pid,
                        backlash_idx,
                        use_cipher_ability=use_cipher,
                        backlash_die_id=backlash_die_id,
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/cipher":
                    pid = get_target_pid(default_to_human=False)
                    state = self.controller.use_cipher_ability(pid)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/phreaker":
                    pid = get_target_pid(default_to_human=False)
                    count = int(data.get("count", 1))
                    die_idx_raw = data.get("die_index")
                    die_idx = int(die_idx_raw) if die_idx_raw is not None else 0
                    die_id_raw = data.get("die_id")
                    die_id = int(die_id_raw) if die_id_raw is not None else None
                    state = self.controller.use_phreaker_ability(
                        pid, count=count, die_index=die_idx, die_id=die_id
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/acoustic":
                    pid = get_target_pid(default_to_human=False)
                    if "color" not in data:
                        payload, code = error_response("Missing required field 'color'", 400)
                        self._send_json_response(payload, code)
                        return
                    color_str = str(data["color"])
                    state = self.controller.use_acoustic_ability(pid, color_str)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/spook":
                    pid = get_target_pid(default_to_human=False)
                    dollars_raw = data.get("dollars", 0)
                    dollars = int(dollars_raw) if dollars_raw is not None else 0
                    state = self.controller.use_spook_ability(pid, dollars)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/spook_burn":
                    pid = get_target_pid(default_to_human=False)
                    if "die_id" not in data:
                        payload, code = error_response("Missing required field 'die_id'", 400)
                        self._send_json_response(payload, code)
                        return
                    die_id = int(data["die_id"])
                    state = self.controller.spook_burn(pid, die_id)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/phreaker_diagnostics":
                    pid = get_target_pid(default_to_human=False)
                    die_id_raw = data.get("die_id")
                    die_id = int(die_id_raw) if die_id_raw is not None else None
                    state = self.controller.phreaker_diagnostics(pid, die_id)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/star":
                    pid = get_target_pid(default_to_human=False)
                    action_type = str(data.get("action_type", ""))
                    cube_color = data.get("cube_color")
                    state = self.controller.execute_star_action(pid, action_type, cube_color)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/upgrade_track":
                    pid = get_target_pid(default_to_human=False)
                    track_type = str(data.get("track_type", ""))
                    state = self.controller.upgrade_track(pid, track_type)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/breakthrough":
                    pid = get_target_pid(default_to_human=False)
                    gray_id = data.get("gray_die_id")
                    state = self.controller.resolve_breakthrough(
                        pid,
                        accept=bool(data.get("accept", True)),
                        gray_die_id=int(gray_id) if gray_id is not None else None,
                        color=data.get("color"),
                    )
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/regain_market_share":
                    pid = get_target_pid(default_to_human=False)
                    state = self.controller.regain_market_share(pid)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/pen_test":
                    # Phase 5: Pen Test Track (-1 Vulnerability per step)
                    pid = get_target_pid(default_to_human=False)
                    state = self.controller.pen_test(pid, int(data.get("steps", 1)))
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/system_reboot":
                    payload, code = error_response(
                        "System Reboot has been deprecated in v0.22.0. Soft-locks are eliminated by the CI/CD conveyor.",
                        410,
                    )
                    self._send_json_response(payload, code)

                elif clean_path == "/api/game/action/end_turn":
                    pid = get_target_pid(default_to_human=False)
                    state = self.controller.end_turn(pid)
                    payload, code = success_response({"state": state})
                    self._send_json_response(payload, code)

                else:
                    payload, code = error_response(f"Unknown endpoint: {clean_path}", 404)
                    self._send_json_response(payload, code)

        except ValueError as exc:
            payload, code = error_response(str(exc), 400)
            self._send_json_response(payload, code)
        except Exception as exc:
            payload, code = error_response(f"Internal server error: {str(exc)}", 500)
            self._send_json_response(payload, code)


def create_server(host: str = "127.0.0.1", port: int = 8080, randomize_cards: bool = False) -> ThreadingHTTPServer:
    """Creates a ThreadingHTTPServer instance for the Rogue Agent web app."""
    # Initialize default game upon server start
    RogueAgentRequestHandler.controller.new_game(randomize_cards=randomize_cards)
    server = ThreadingHTTPServer((host, port), RogueAgentRequestHandler)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Rogue Agent Web Playtesting Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()

    server = create_server(args.host, args.port, randomize_cards=True)
    print(f"Rogue Agent Web Server running at http://{args.host}:{args.port}/")
    print(f"Serving static assets from: {STATIC_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()
