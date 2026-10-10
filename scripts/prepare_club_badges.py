"""Copy only the club badges used by the app from an upstream checkout."""

import argparse
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from app_config import LEAGUE_LOGO_FOLDERS, TEAM_BADGES, TEAM_LOGO_ROOT, TEAM_LOGO_FILES  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to the upstream football-logos/logos directory",
    )
    source_root = parser.parse_args().source.resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Badge source directory missing: {source_root}")

    for (league, _club), filename in TEAM_LOGO_FILES.items():
        source = source_root / LEAGUE_LOGO_FOLDERS[league] / filename
        if not source.is_file():
            raise SystemExit(f"Badge source missing: {source}")

    for key, destination in TEAM_BADGES.items():
        league, _club = key
        source = source_root / LEAGUE_LOGO_FOLDERS[league] / TEAM_LOGO_FILES[key]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    print(f"Copied {len(TEAM_BADGES)} club badges to {TEAM_LOGO_ROOT}")


if __name__ == "__main__":
    main()
