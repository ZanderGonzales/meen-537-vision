# Baxter Multi-View 3D Reconstruction Plan

## 1. Prepare the capture system

- Confirm the Baxter camera, ROS workspace, Docker environment, and network
  connection work reliably.
- Verify the right-arm camera topic and record the camera resolution and
  intrinsic calibration parameters.
- Measure or obtain the fixed transform between Baxter's right-arm
  end-effector frame and the camera frame.

## 2. Calibrate the camera with a checkerboard

- Print a flat checkerboard with a known number of inner corners and measure
  the square width accurately.
- Capture 15–30 sharp images of the checkerboard at the same resolution and
  camera settings used for reconstruction.
- Vary the board's distance, tilt, position in the image, and rotation so
  corners cover the center, edges, and image corners.
- Detect the checkerboard corners and associate them with their known
  coordinates on the board.
- Estimate the camera matrix and radial/tangential distortion coefficients
  with OpenCV calibration routines.
- Reject unusable images and repeat calibration if the reprojection error is
  high. Save the calibration parameters and image resolution with the
  dataset.
- Undistort all reconstruction images using the saved parameters and verify
  the correction visually near the image edges.

## 3. Characterize the camera

- Capture test images under the expected lighting and working-distance
  conditions.
- Check image quality, field of view, focus, exposure, and lens distortion.
- Apply distortion correction if the calibration data supports it.

## 4. Collect synchronized image and pose data

- Move the camera to several safe, distinct viewpoints around the subject.
- For each viewpoint, save the image, timestamp, joint state, and
  end-effector pose.
- Keep the subject and lighting fixed, and verify that every image has a
  corresponding valid pose.

## 5. Detect and match visual features

- Preprocess the images consistently.
- Detect repeatable features and match them between image pairs.
- Reject incorrect matches using descriptor checks and geometric
  outlier-rejection methods such as RANSAC.

## 6. Reconstruct 3D points

- Convert Baxter poses and camera calibration into camera projection matrices.
- Triangulate matched feature points from at least two viewpoints.
- Evaluate reprojection error and remove points with poor geometric
  consistency.

## 7. Validate and visualize

- Compare the reconstruction against known dimensions or measured reference
  points.
- Render the resulting point cloud or sparse 3D model.
- Document limitations caused by calibration, occlusion, image quality, and
  viewpoint selection.

## 8. Stretch goals

- Support more than two images and refine the camera poses and 3D points
  jointly.
- Improve the reconstruction with denser matching, additional viewpoints, or
  lens-distortion refinement.