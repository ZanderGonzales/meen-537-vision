# MeEn573 Final Project

## Baxter image and pose capture

[`scripts/capture_right_camera.py`](./scripts/capture_right_camera.py) captures
an image from Baxter's `right_hand_camera` and records the right arm's
end-effector pose from `baxter_interface.Limb("right").endpoint_pose()`.
Each run writes `image_####.png` files and a `poses.csv` file. The CSV stores
the image timestamp, position in meters, and orientation as a quaternion in
Baxter's base frame.

### Development and robot environments

Develop the script in this repository, but run it inside the ROS/Baxter
environment on the machine connected to Baxter. The container must have:

- ROS 1 (the ROS distribution supported by the robot image)
- `baxter_interface` and `baxter_msgs`
- `rospy`, `sensor_msgs`, and `cv_bridge`
- OpenCV (`python-opencv`)

The Baxter SDK is ROS 1 and is normally used with Python 2.7 on the original
robot software. Do not install the current `baxter_interface` package into a
modern Python-only virtual environment; use the robot team's compatible ROS
Docker image or a matching Ubuntu/ROS host.

1. Clone this repository into the container or mount it as a workspace volume.
2. From the root of the BYU Baxter catkin workspace, source the lab
   environment:

   ```bash
   source baxter.sh
   source devel/setup.bash
   ```

3. Check that the robot is reachable and that the camera topic is publishing:

   ```bash
   rostopic list | grep right_hand_camera
   rostopic hz /cameras/right_hand_camera/image
   ```

4. Run the capture script:

   ```bash
   python scripts/robot/capture_right_camera.py
   ```

   Each run gets a timestamped subdirectory under
   `data/baxter_capture`. Set `BAXTER_CAPTURE_DIR` to choose another base
   directory. At each prompt, move Baxter to a safe pose and press Enter.
   Type `q` to finish.

The ROS master, the container, and Baxter must share the same network. The
exact `ROS_MASTER_URI`, host networking flags, device access, and ROS
distribution are deployment-specific; copy those settings from the lab's
existing Baxter Docker setup rather than guessing them. Keep the robot in
manual/safe mode while validating the camera topic, and test with the arm
stationary before collecting data.

### Python dependencies

The local pip-installable dependencies are listed in
[`dependencies.txt`](./dependencies.txt). Install them in the local virtual
environment:

```bash
source .venv/bin/activate
python -m pip install -r dependencies.txt
```

Do not install `rospy`, `cv_bridge`, `sensor_msgs`, or `baxter_interface` with
pip. Those packages are supplied by the ROS/Baxter workspace and must remain
compatible with the container's ROS distribution.

### Project structure

```text
scripts/robot/   Baxter/ROS capture programs
scripts/local/   Local command-line workflows
src/meen_vision/ Reusable local computer-vision code
data/            Local captures and generated results (ignored by Git)
```

Install the local package in the virtual environment before running local
scripts:

```bash
python -m pip install -e .
python scripts/local/calibrate_camera.py data/calibration/raw \
  --columns 9 --rows 6 --square-size-m 0.025
```
## Goal
The goal is to take photos with transformation matrices known between camera angles, and get 3D data from combining those photos

## Textbook
https://link.springer.com/book/10.1007/978-3-031-06469-2
