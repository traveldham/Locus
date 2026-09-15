"""Command line for the demo-profile generator.

    uv run python -m generator_data                      # write every archetype
    uv run python -m generator_data --keys bluebird-coffee riverside-grill
    uv run python -m generator_data --project "Demo fleet"
    uv run python -m generator_data --list
    uv run python -m generator_data --verify [--rules <key>]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date

from generator_data.archetypes import ARCHETYPES, KEYS


def parse(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="generator_data", description=__doc__)
    parser.add_argument("--keys", nargs="*", default=None, help="archetype keys, default all")
    parser.add_argument("--list", action="store_true", help="print the catalogue and exit")
    parser.add_argument("--verify", action="store_true", help="audit the archetypes and exit")
    parser.add_argument("--rules", default=None, help="with --verify: list one profile's verdicts")
    parser.add_argument(
        "--project",
        default=None,
        help="name of the project to attach the imported profiles to (created if absent)",
    )
    parser.add_argument(
        "--organization",
        default=None,
        help="organization slug to import into; defaults to the only one, or the seeded demo",
    )
    parser.add_argument(
        "--reference",
        default=None,
        help="ISO date the data is built around; defaults to today",
    )
    return parser.parse_args(argv)


def show_catalogue() -> int:
    print(f"{'key':<26}{'industry':<14}{'city':<18}{'grade':<6}{'headline problem'}")
    print("-" * 110)
    for a in ARCHETYPES:
        print(f"{a.key:<26}{a.industry:<14}{a.location:<18}{a.expected_grade:<6}{a.headline_problem}")
    return 0


async def do_import(args: argparse.Namespace) -> int:
    # Imported here so `--list` and `--verify` never open a database connection.
    from app.core.database import SessionLocal, engine
    from generator_data.importer import import_into_database

    reference = date.fromisoformat(args.reference) if args.reference else date.today()
    keys = args.keys or list(KEYS)
    unknown = [key for key in keys if key not in KEYS]
    if unknown:
        print(f"Unknown demo profile keys: {', '.join(unknown)}", file=sys.stderr)
        return 1
    try:
        async with SessionLocal() as db:
            result = await import_into_database(
                db,
                keys=keys,
                organization_slug=args.organization,
                project_name=args.project,
                reference=reference,
            )
    finally:
        await engine.dispose()

    print(f"Imported into organization {result.organization_name}")
    for line in result.lines:
        print(f"  {line}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse(argv)
    if args.list:
        return show_catalogue()
    if args.verify:
        from generator_data.verify import main as verify_main

        reference = date.fromisoformat(args.reference) if args.reference else None
        return verify_main(args.rules, reference)
    return asyncio.run(do_import(args))


if __name__ == "__main__":
    raise SystemExit(main())
