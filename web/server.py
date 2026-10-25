"""Pure Python 3 standard library ThreadingHTTPServer serving web/static/ and routing /api/game/*."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from web.game_controller import GameController
from web.schemas import error_response, parse_request_json, success_response

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))


class RogueAgentRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler routing /api/game/* endpoints and serving static assets."""

    controller: GameController = GameController()

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

                state = self.controller.new_game(
                    num_players=num_players,
                    players_config=players_config,
                    seed=seed,
                )
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/roll":
                pid = get_target_pid(default_to_human=True)
                state = self.controller.roll_pool(pid)
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/hotfix":
                pid = get_target_pid(default_to_human=True)
                if "die_index" not in data:
                    payload, code = error_response("Missing required field 'die_index'", 400)
                    self._send_json_response(payload, code)
                    return
                die_idx = int(data["die_index"])
                state = self.controller.hotfix_reroll(pid, die_idx)
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/commit":
                pid = get_target_pid(default_to_human=True)
                commitments = data.get("commitments", {})
                state = self.controller.commit_defenses(pid, commitments)
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/compile":
                state = self.controller.compile_drop()
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/buy":
                pid = get_target_pid(default_to_human=False)
                if "color" not in data:
                    payload, code = error_response("Missing required field 'color'", 400)
                    self._send_json_response(payload, code)
                    return
                color_str = str(data["color"])
                state = self.controller.buy_die(pid, color_str)
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/patch":
                pid = get_target_pid(default_to_human=False)
                if "die_index" not in data:
                    payload, code = error_response("Missing required field 'die_index'", 400)
                    self._send_json_response(payload, code)
                    return
                die_idx = int(data["die_index"])
                use_cash = bool(data.get("use_cash", False))
                state = self.controller.patch_die(pid, die_idx, use_cash)
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/dirty_income":
                pid = get_target_pid(default_to_human=False)
                backlash_idx = int(data.get("backlash_die_index", 0))
                state = self.controller.take_dirty_income(pid, backlash_idx)
                payload, code = success_response({"state": state})
                self._send_json_response(payload, code)

            elif clean_path == "/api/game/action/star":
                pid = get_target_pid(default_to_human=False)
                action_type = str(data.get("action_type", ""))
                cube_color = data.get("cube_color")
                state = self.controller.execute_star_action(pid, action_type, cube_color)
                payload, code = success_response({"state": state})
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


def create_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Creates a ThreadingHTTPServer instance for the Rogue Agent web app."""
    # Initialize default game upon server start
    RogueAgentRequestHandler.controller.new_game()
    server = ThreadingHTTPServer((host, port), RogueAgentRequestHandler)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description="Rogue Agent Web Playtesting Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    print(f"Rogue Agent Web Server running at http://{args.host}:{args.port}/")
    print(f"Serving static assets from: {STATIC_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()
