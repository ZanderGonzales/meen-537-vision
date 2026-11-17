from pathlib import Path
import glob

import numpy as np
import cv2 as cv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
images = sorted((PROJECT_ROOT / "data" / "20261113_033337_203318").glob("*.png"))

criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

objp = np.zeros((9 * 6, 3), np.float32)
objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)

objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.


for fname in images:
    img = cv.imread(str(fname))
    if img is None:
        print(f"Failed to read image: {fname}")
        continue

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    ret, corners = cv.findChessboardCorners(gray, (9, 6), None)

    if ret:
        objpoints.append(objp)

        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

        cv.drawChessboardCorners(img, (9, 6), corners2, ret)
        cv.imshow('img', img)
        cv.waitKey(50)

cv.destroyAllWindows()

ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

for i, fname in enumerate(images):
    img = cv.imread(str(fname))
    if img is None:
        print(f"Failed to read image: {fname}")
        continue

    h, w = img.shape[:2]
    newcameramtx, roi = cv.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))

    dst = cv.undistort(img, mtx, dist, None, newcameramtx)

    x, y, w, h = roi
    dst = dst[y:y + h, x:x + w]

    undistorted_image_path = PROJECT_ROOT / "data" / "undistorted_chessboards" / f"undistorted_{i+1:04d}.png"
    undistorted_image_path.parent.mkdir(parents=True, exist_ok=True)
    cv.imwrite(str(undistorted_image_path), dst)