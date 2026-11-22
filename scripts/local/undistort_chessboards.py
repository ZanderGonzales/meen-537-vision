"""Undistort images using previously saved camera calibration parameters.

Example usage from the project root::

    python scripts/local/undistort_chessboards.py \
        --calibration data/camera_calibration.npz \
        --input-dir data/20261113_033337_203318 \
        --output-dir data/undistorted_chessboards

Use ``--alpha`` to control the balance between cropping invalid borders and
preserving the original field of view when cropping is enabled. For example::

    python scripts/local/undistort_chessboards.py \
        --calibration data/camera_calibration.npz \
        --input-dir data/new_images \
        --output-dir data/new_images_undistorted \
        --alpha 0.5 \
        --crop

Cropping is disabled by default, so the complete undistorted frame—including
any black border pixels—is kept unless ``--crop`` is provided.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2 as cv
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "data" / "20261113_033337_203318"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "undistorted_chessboards"
DEFAULT_CALIBRATION_FILE = PROJECT_ROOT / "data" / "camera_calibration.npz"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Undistort images using saved camera calibration parameters."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing images to undistort.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for undistorted images.",
    )
    parser.add_argument(
        "--calibration",
        type=Path,
        default=DEFAULT_CALIBRATION_FILE,
        help="Calibration .npz file created by calibrate_camera.py.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.0,
        help="New-camera-matrix balance: 0 crops invalid borders; 1 keeps all pixels.",
    )
    parser.add_argument(
        "--crop",
        action="store_true",
        help="Crop the output to the valid region and remove black borders.",
    )
    return parser.parse_args()


def main() -> None:
    """Load calibration parameters and undistort every image in the input folder."""
    args = parse_args()
    if not 0.0 <= args.alpha <= 1.0:
        raise ValueError("--alpha must be between 0 and 1.")

    image_paths = sorted(
        path
        for pattern in ("*.png", "*.jpg", "*.jpeg")
        for path in args.input_dir.glob(pattern)
    )
    if not image_paths:
        raise FileNotFoundError(f"No image files found in {args.input_dir}")

    with npz_file(args.calibration) as calibration:
        camera_matrix = calibration["camera_matrix"]
        distortion_coefficients = calibration["distortion_coefficients"]
        calibration_size = tuple(
            int(value) for value in calibration["image_size"]
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    processed = 0
    skipped = 0
    new_camera_matrix = None
    roi = None

    for image_path in image_paths:
        image = cv.imread(str(image_path))
        if image is None:
            print(f"Could not read {image_path}")
            skipped += 1
            continue

        height, width = image.shape[:2]
        image_size = (width, height)
        if image_size != calibration_size:
            raise ValueError(
                f"{image_path} has size {image_size}, but calibration was created "
                f"for {calibration_size}."
            )

        if new_camera_matrix is None:
            new_camera_matrix, roi = cv.getOptimalNewCameraMatrix(
                camera_matrix,
                distortion_coefficients,
                image_size,
                args.alpha,
                image_size,
            )
            print(f"Using ROI {roi} for image size {image_size}")

        valid_new_camera_matrix = new_camera_matrix
        valid_roi = roi
        if valid_new_camera_matrix is None or valid_roi is None:
            raise RuntimeError("Failed to compute the undistortion transform.")

        undistorted = cv.undistort(
            image,
            camera_matrix,
            distortion_coefficients,
            None,
            valid_new_camera_matrix,
        )

        if args.crop:
            x, y, roi_width, roi_height = valid_roi
            undistorted = undistorted[
                y : y + roi_height,
                x : x + roi_width,
            ]

        output_path = args.output_dir / image_path.name
        if not cv.imwrite(str(output_path), undistorted):
            raise OSError(f"Could not write {output_path}")
        processed += 1
        print(f"{image_path.name} -> {output_path}")

    print(f"Processed {processed} images; skipped {skipped}.")


def npz_file(path: Path) -> np.lib.npyio.NpzFile:
    """Load a calibration archive with a clear missing-file error."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Calibration file not found: {path}. "
            "Run calibrate_camera.py first."
        )
    return np.load(path)


if __name__ == "__main__":
    main()
