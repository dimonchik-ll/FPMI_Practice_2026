from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


ROWS = {
    "up_walk.png": 0,
    "down_walk.png": 1,
    "left_walk.png": 2,
    "right_walk.png": 3,
}

FRAME_COUNT = 6
ROW_COUNT = 4
OUTPUT_FRAME_SIZE = 48
PADDING = 4
BASELINE_PADDING = 3


def make_light_checkerboard_transparent(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]

            is_light_checkerboard = (
                red >= 190
                and green >= 190
                and blue >= 190
                and abs(red - green) <= 22
                and abs(green - blue) <= 22
            )

            if is_light_checkerboard:
                pixels[x, y] = (red, green, blue, 0)

    return image


def trim_to_content(frame: Image.Image) -> Image.Image:
    alpha = frame.getchannel("A")
    bbox = alpha.getbbox()

    if bbox is None:
        return frame

    return frame.crop(bbox)


def collect_cells(source: Image.Image) -> list[list[Image.Image]]:
    sheet_width, sheet_height = source.size
    cell_width = sheet_width // FRAME_COUNT
    cell_height = sheet_height // ROW_COUNT

    cells: list[list[Image.Image]] = []

    for row in range(ROW_COUNT):
        row_cells: list[Image.Image] = []

        for column in range(FRAME_COUNT):
            frame = source.crop(
                (
                    column * cell_width,
                    row * cell_height,
                    (column + 1) * cell_width,
                    (row + 1) * cell_height,
                )
            )
            row_cells.append(trim_to_content(frame))

        cells.append(row_cells)

    return cells


def common_scale(cells: list[list[Image.Image]]) -> float:
    max_width = max(frame.width for row in cells for frame in row)
    max_height = max(frame.height for row in cells for frame in row)

    max_output = OUTPUT_FRAME_SIZE - PADDING

    return min(max_output / max_width, max_output / max_height)


def fit_frame_into_48(frame: Image.Image, scale: float) -> Image.Image:
    new_size = (
        max(1, int(round(frame.width * scale))),
        max(1, int(round(frame.height * scale))),
    )

    frame = frame.resize(new_size, Image.Resampling.NEAREST)

    result = Image.new(
        "RGBA",
        (OUTPUT_FRAME_SIZE, OUTPUT_FRAME_SIZE),
        (0, 0, 0, 0),
    )

    x = (OUTPUT_FRAME_SIZE - frame.width) // 2
    y = OUTPUT_FRAME_SIZE - BASELINE_PADDING - frame.height

    result.paste(frame, (x, y), frame)

    return result


def split_sheet(input_path: Path, output_dir: Path) -> None:
    source = Image.open(input_path)
    source = make_light_checkerboard_transparent(source)

    cells = collect_cells(source)
    scale = common_scale(cells)

    output_dir.mkdir(parents=True, exist_ok=True)

    for filename, row in ROWS.items():
        row_sheet = Image.new(
            "RGBA",
            (OUTPUT_FRAME_SIZE * FRAME_COUNT, OUTPUT_FRAME_SIZE),
            (0, 0, 0, 0),
        )

        for column, frame in enumerate(cells[row]):
            fitted_frame = fit_frame_into_48(frame, scale)
            row_sheet.paste(
                fitted_frame,
                (column * OUTPUT_FRAME_SIZE, 0),
                fitted_frame,
            )

        row_sheet.save(output_dir / filename)
        print(f"saved: {output_dir / filename}")


def main() -> None:
    if len(sys.argv) != 3:
        print(
            "Usage: python tools/split_enemy_direction_sheet.py "
            "<input_4x6_sheet.png> <output_enemy_dir>"
        )
        raise SystemExit(1)

    split_sheet(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
