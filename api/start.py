import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_SEED_RECORDS = 300_000
DEFAULT_SEED_BATCH_SIZE = 5_000


def run_command(command: list[str], *, description: str) -> None:
    print("")
    print(f"==> {description}")
    print(f"    {' '.join(command)}")
    print("")

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=os.environ.copy(),
    )

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}")


def run_migrations() -> None:
    run_command(
        ["uv", "run", "alembic", "upgrade", "head"],
        description="Applying database migrations",
    )


def run_seed(*, records: int, batch_size: int, reset_seed: bool) -> None:
    command = [
        "uv",
        "run",
        "python",
        "seed.py",
        "--records",
        str(records),
        "--batch-size",
        str(batch_size),
    ]

    if reset_seed:
        command.append("--reset")

    run_command(
        command,
        description="Ensuring demo seed data exists",
    )


def start_service() -> None:
    run_command(
        ["uv", "run", "python", "run.py"],
        description="Starting API service",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run migrations, seed demo data if needed, and start the service."
    )

    parser.add_argument(
        "--records",
        type=int,
        default=DEFAULT_SEED_RECORDS,
        help=f"Number of demo metric events to seed. Default: {DEFAULT_SEED_RECORDS}",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_SEED_BATCH_SIZE,
        help=f"Seed insert batch size. Default: {DEFAULT_SEED_BATCH_SIZE}",
    )

    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip demo data seeding.",
    )

    parser.add_argument(
        "--reset-seed",
        action="store_true",
        help="Delete and recreate demo seed data.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        run_migrations()

        if not args.skip_seed:
            run_seed(
                records=args.records,
                batch_size=args.batch_size,
                reset_seed=args.reset_seed,
            )

        start_service()

    except KeyboardInterrupt:
        print("")
        print("Service stopped.")
    except Exception as exc:
        print("")
        print(f"Startup failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()