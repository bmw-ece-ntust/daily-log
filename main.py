from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    src = root / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))

    # Auto-append --config env.yaml when present and not already given.
    default_cfg = root / "env.yaml"
    if default_cfg.exists() and "--config" not in sys.argv:
        sys.argv.extend(["--config", str(default_cfg)])

    from dailylog.cli import main as cli_main

    return int(cli_main())


if __name__ == "__main__":
    raise SystemExit(main())
