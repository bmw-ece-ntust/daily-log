from __future__ import annotations


def main() -> int:
    from .cli import main as cli_main

    return int(cli_main())


if __name__ == "__main__":
    raise SystemExit(main())
