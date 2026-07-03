from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from zipfile import ZipFile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = PROJECT_ROOT / "assets"
DIRECTION_NAMES = {"D": "down", "S": "side", "U": "up"}


def _write_from_zip(archive: ZipFile, member: str, target: Path, overwrite: bool) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not overwrite:
        return False
    with archive.open(member) as source, target.open("wb") as destination:
        shutil.copyfileobj(source, destination)
    return True


def _copy_license(archive: ZipFile, label: str, overwrite: bool) -> int:
    copied = 0
    for member in archive.namelist():
        if member.startswith("__MACOSX/") or not member.endswith("License.txt"):
            continue
        target = ASSET_ROOT / "licenses" / f"{label}_LICENSE.txt"
        copied += int(_write_from_zip(archive, member, target, overwrite))
        break
    return copied


def import_tiles(zip_path: Path, overwrite: bool) -> int:
    copied = 0
    with ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if member.startswith("__MACOSX/"):
                continue
            name = Path(member).name
            if "/1 Tiles/" in member and name.startswith("FieldsTile") and name.endswith(".png"):
                copied += int(_write_from_zip(archive, member, ASSET_ROOT / "tiles" / "fields" / name, overwrite))
            elif member.endswith("/2 Objects/PlaceForTower1.png"):
                copied += int(_write_from_zip(archive, member, ASSET_ROOT / "tiles" / "objects" / "place_for_tower_1.png", overwrite))
            elif member.endswith("/2 Objects/PlaceForTower2.png"):
                copied += int(_write_from_zip(archive, member, ASSET_ROOT / "tiles" / "objects" / "place_for_tower_2.png", overwrite))
        copied += _copy_license(archive, "fields_tileset", overwrite)
    return copied


def import_enemies(zip_path: Path, overwrite: bool) -> int:
    copied = 0
    pattern = re.compile(r"^(?P<enemy>\d+)/(?P<direction>[DSU])_(?P<animation>[A-Za-z0-9]+)\.png$")
    with ZipFile(zip_path) as archive:
        for member in archive.namelist():
            match = pattern.match(member)
            if match is None:
                continue
            target = ASSET_ROOT / "enemies" / f"enemy_{match['enemy']}" / f"{DIRECTION_NAMES[match['direction']]}_{match['animation'].lower()}.png"
            copied += int(_write_from_zip(archive, member, target, overwrite))
        copied += _copy_license(archive, "field_enemies", overwrite)
    return copied


def import_towers(zip_path: Path, overwrite: bool) -> int:
    copied = 0
    idle_pattern = re.compile(r"^2 Idle/(?P<level>\d+)\.png$")
    upgrade_pattern = re.compile(r"^1 Upgrade/(?P<level>\d+)\.png$")
    unit_pattern = re.compile(r"^3 Units/(?P<unit>\d+)/(?P<direction>[DSU])_(?P<animation>[A-Za-z0-9]+)\.png$")
    arrow_pattern = re.compile(r"^3 Units/Arrow/(?P<frame>\d+)\.png$")

    with ZipFile(zip_path) as archive:
        for member in archive.namelist():
            match = idle_pattern.match(member)
            if match:
                target = ASSET_ROOT / "towers" / "idle" / f"archer_{match['level']}.png"
                copied += int(_write_from_zip(archive, member, target, overwrite))
                continue
            match = upgrade_pattern.match(member)
            if match:
                target = ASSET_ROOT / "towers" / "upgrade" / f"archer_{match['level']}.png"
                copied += int(_write_from_zip(archive, member, target, overwrite))
                continue
            match = unit_pattern.match(member)
            if match:
                target = ASSET_ROOT / "towers" / "units" / f"archer_{match['unit']}" / f"{DIRECTION_NAMES[match['direction']]}_{match['animation'].lower()}.png"
                copied += int(_write_from_zip(archive, member, target, overwrite))
                continue
            match = arrow_pattern.match(member)
            if match:
                target = ASSET_ROOT / "projectiles" / "arrows" / f"arrow_{match['frame']}.png"
                copied += int(_write_from_zip(archive, member, target, overwrite))
        copied += _copy_license(archive, "archer_towers", overwrite)
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="Imports the selected CraftPix assets into the project asset tree.")
    parser.add_argument("--tiles", type=Path, required=True)
    parser.add_argument("--enemies", type=Path, required=True)
    parser.add_argument("--towers", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    for path in (args.tiles, args.enemies, args.towers):
        if not path.is_file():
            parser.error(f"Archive not found: {path}")

    total = 0
    total += import_tiles(args.tiles, args.overwrite)
    total += import_enemies(args.enemies, args.overwrite)
    total += import_towers(args.towers, args.overwrite)
    print(f"Imported {total} file(s) into {ASSET_ROOT}")


if __name__ == "__main__":
    main()
