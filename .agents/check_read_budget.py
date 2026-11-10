import json
import sys

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    tool_call = payload.get("toolCall", {})
    args = tool_call.get("args", {})
    path = (args.get("Path") or args.get("path") or "").replace("\\", "/").lower()

    denied = False
    reason = ""
    if "/sim_results/" in path and path.endswith(".json"):
        denied = True
        reason = "Blocked by Context Budget (.claude/settings.json parity): Do not read raw sweep JSON in sim_results/. Use script summaries instead."
    elif "/tests/fixtures/" in path:
        denied = True
        reason = "Blocked by Context Budget (.claude/settings.json parity): Do not read raw test fixtures in tests/fixtures/."
    elif "/pnp/" in path and path.endswith(".pdf"):
        denied = True
        reason = "Blocked by Context Budget (.claude/settings.json parity): Do not read generated PDFs in pnp/."
    elif "/web/node_modules/" in path:
        denied = True
        reason = "Blocked by Context Budget (.claude/settings.json parity): Do not read files inside web/node_modules/."

    if denied:
        print(json.dumps({"decision": "deny", "reason": reason}))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
