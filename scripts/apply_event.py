#!/usr/bin/env python3
"""
Applies one OneDrive change to the local data/ folder. The change arrives
as the client_payload of a GitHub repository_dispatch event, sent by a
Power Automate flow that watches the OneDrive folder. Expected payload:

    {
      "action": "upsert" | "delete",
      "file_name": "JN090.csv",
      "content": "<base64-encoded file bytes>"   (only for "upsert")
    }
"""
import base64
import json
import os
import sys

DATA_DIR = "data"


def main() -> None:
    payload = json.loads(os.environ["EVENT_PAYLOAD"])
    file_name = payload.get("file_name")
    action = payload.get("action", "upsert")

    if not file_name or not file_name.lower().endswith(".csv"):
        print(f"Ignoring event with invalid file_name: {file_name!r}", file=sys.stderr)
        return

    os.makedirs(DATA_DIR, exist_ok=True)
    target = os.path.join(DATA_DIR, os.path.basename(file_name))

    if action == "delete":
        if os.path.exists(target):
            os.remove(target)
            print(f"Deleted {target}")
        else:
            print(f"{target} did not exist, nothing to delete")
        return

    content_b64 = payload.get("content", "")
    try:
        raw = base64.b64decode(content_b64)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to decode content for {file_name}: {exc}", file=sys.stderr)
        sys.exit(1)

    with open(target, "wb") as f:
        f.write(raw)
    print(f"Wrote {len(raw)} bytes to {target}")


if __name__ == "__main__":
    main()
