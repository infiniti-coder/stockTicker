"""Regenerate MarketDataFeed_pb2.py from MarketDataFeed.proto.

Run from backend/ with the venv active:

    python -m app.upstox_client.proto.generate

Re-run this whenever the .proto source is updated (e.g. Upstox revs the feed
schema — re-download from
https://assets.upstox.com/feed/market-data-feed/v3/MarketDataFeed.proto first).
"""

import subprocess
import sys
from pathlib import Path

PROTO_DIR = Path(__file__).parent


def main() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{PROTO_DIR}",
            f"--python_out={PROTO_DIR}",
            str(PROTO_DIR / "MarketDataFeed.proto"),
        ],
        check=True,
    )
    print(f"Wrote {PROTO_DIR / 'MarketDataFeed_pb2.py'}")


if __name__ == "__main__":
    main()
