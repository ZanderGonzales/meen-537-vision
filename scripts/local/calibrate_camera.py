"""Calibrate a camera from checkerboard images and save its parameters.

Example usage from the project root::

    python scripts/local/calibrate_camera.py \
        --input-dir data/20261113_033337_203318 \
        --output data/camera_calibration.npz

The checkerboard must contain 9 by 6 inner corners by default. Adjust the
board dimensions when necessary, for example::

    python scripts/local/calibrate_camera.py \
        --input-dir data/calibration_images \
        --columns 7 \
        --rows 5 \
        --square-size 25.0 \
        --display

The saved ``.npz`` file can be passed to ``undistort_chessboards.py`` for
undistorting other image sets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2 as cv
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "20261113_033337_203318"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "data" / "camera_calibration.npz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calibrate a camera using checkerboard images."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing checkerboard images.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output .npz file for the calibration parameters.",
    )
    parser.add_argument("--columns", type=int, default=9, help="Inner corners across.")
    parser.add_argument("--rows", type=int, default=6, help="Inner corners down.")
    parser.add_argument(
        "--square-size",
        type=float,
        default=1.0,
        help="Checkerboard square size in arbitrary consistent units.",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Display detected corners while processing.",
    )
    return parser.parse_args()


def main() -> None:
    """Find checkerboard corners, calibrate the camera, and save its parameters."""
    args = parse_args()
    board_size = (args.columns, args.rows)
    image_paths = sorted(
        path
        for pattern in ("*.png", "*.jpg", "*.jpeg")
        for path in args.input_dir.glob(pattern)
    )

    if not image_paths:
        raise FileNotFoundError(f"No image files found in {args.input_dir}")

    object_points_template = np.zeros(
        (args.columns * args.rows, 3), dtype=np.float32
    )
    object_points_template[:, :2] = (
        np.mgrid[0 : args.columns, 0 : args.rows].T.reshape(-1, 2)
        * args.square_size
    )

    criteria = (
        cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER,
        30,
        0.001,
    )
    object_points: list[np.ndarray] = []
    image_points: list[np.ndarray] = []
    image_size: tuple[int, int] | None = None
    failed_paths: list[Path] = []

    for image_path in image_paths:
        image = cv.imread(str(image_path))
        if image is None:
            failed_paths.append(image_path)
            print(f"Could not read {image_path}")
            continue

        height, width = image.shape[:2]
        current_size = (width, height)
        if image_size is None:
            image_size = current_size
        elif current_size != image_size:
            raise ValueError(
                f"Image {image_path} has size {current_size}; "
                f"expected {image_size}."
            )

        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        found, corners = cv.findChessboardCorners(gray, board_size, None)

        if not found:
            print(f"Checkerboard not found: {image_path.name}")
            continue

        refined_corners = cv.cornerSubPix(
            gray, corners, (11, 11), (-1, -1), criteria
        )
        object_points.append(object_points_template.copy())
        image_points.append(refined_corners)

        if args.display:
            preview = image.copy()
            cv.drawChessboardCorners(preview, board_size, refined_corners, found)
            cv.imshow("Detected checkerboard corners", preview)
            cv.waitKey(100)

    if args.display:
        cv.destroyAllWindows()

    if image_size is None:
        raise RuntimeError("No readable calibration images were found.")
    if len(object_points) < 3:
        raise RuntimeError(
            f"Only {len(object_points)} usable calibration images found; "
            "at least 3 are required."
        )

    rms, camera_matrix, distortion_coefficients, _, _ = cv.calibrateCamera(
        object_points,
        image_points,
        image_size,
        None,
        None,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        args.output,
        camera_matrix=camera_matrix,
        distortion_coefficients=distortion_coefficients,
        image_size=np.asarray(image_size, dtype=np.int32),
        board_size=np.asarray(board_size, dtype=np.int32),
        square_size=np.asarray(args.square_size, dtype=np.float32),
        rms=np.asarray(rms, dtype=np.float64),
    )

    print(f"Calibration images found: {len(image_paths)}")
    print(f"Usable calibration images: {len(object_points)}")
    print(f"Skipped images: {len(image_paths) - len(object_points)}")
    print(f"RMS reprojection error: {rms:.6f}")
    print(f"Saved calibration to {args.output}")
    if failed_paths:
        print(f"Unreadable images: {len(failed_paths)}")


if __name__ == "__main__":
    main()
