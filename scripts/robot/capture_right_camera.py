#!/usr/bin/env python
"""Capture images from Baxter's right-hand camera with endpoint poses.

The script waits for the operator to position Baxter's right arm, captures one
image from the right-hand camera, and records the right endpoint pose
corresponding to that image. Each run creates a timestamped output directory
containing PNG images and a ``poses.csv`` file with image timestamps, positions,
and orientations.

Run this script from the Baxter ROS environment after sourcing the workspace
and configuring the ROS network connection to Baxter. For example::

    source /home/student/ros_ws/baxter.sh
    source /home/student/ros_ws/devel/setup.bash
    export BAXTER_CAPTURE_DIR=/home/student/captures
    python3 scripts/robot/capture_right_camera.py

At each prompt, move Baxter to a safe, stationary pose and press Enter to
capture a sample. Type ``q`` and press Enter to stop. The script prints the
path of the output directory when it exits. The ``BAXTER_CAPTURE_DIR``
environment variable is optional; without it, captures are stored under
``data/baxter_capture`` in the current working directory.

The ROS packages used by this script (including ``rospy``, ``cv_bridge``,
``sensor_msgs``, and ``baxter_interface``) must be provided by the compatible
Baxter ROS workspace. They should not be installed only in a standalone
Python virtual environment.
    position = pose["position"]
    orientation = pose["orientation"]
    image_file = "image_{:04d}.png".format(sample_number)
    image_path = os.path.join(directory, image_file)
    if not cv2.imwrite(image_path
"""

from __future__ import print_function

import csv
import os
import time

import cv2

# pyright: reportMissingImports=false, reportMissingModuleSource=false
import rospy
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image

import baxter_interface


CAMERA_NAME = "right_hand_camera"
IMAGE_TOPIC = "/cameras/{}/image".format(CAMERA_NAME)
CSV_FIELDS = [
    "sample",
    "image_file",
    "image_stamp_sec",
    "x_m",
    "y_m",
    "z_m",
    "qx",
    "qy",
    "qz",
    "qw",
]


read_input = input


def output_directory():
    """Create and return a unique directory for the current capture run.

    The base directory is read from ``BAXTER_CAPTURE_DIR`` when set. Otherwise,
    the directory defaults to ``data/baxter_capture`` relative to the current
    working directory. A timestamp and microsecond suffix make each run's
    directory distinct. The returned directory is created before this function
    returns.

    Returns:
        str: The path to the newly created capture directory.
    """
    base_directory = os.environ.get(
        "BAXTER_CAPTURE_DIR",
        os.path.join(os.getcwd(), "data", "baxter_capture"),
    )
    run_id = "{}_{:06d}".format(
        time.strftime("%Y%m%d_%H%M%S"), int(time.time() * 1000000) % 1000000
    )
    directory = os.path.join(base_directory, run_id)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    return directory


def capture_sample(limb, bridge, sample_number, directory, writer):
    """Capture one camera image and the right endpoint pose.

    This function waits for the next message on the right-hand camera topic,
    converts it to an OpenCV BGR image, writes it as a PNG, and records the
    image timestamp and endpoint pose in the supplied CSV writer. The pose is
    read after the image message is received, so the robot should remain
    stationary during capture.

    Args:
        limb: Baxter right-limb interface used to read ``endpoint_pose()``.
        bridge: ``CvBridge`` instance used to convert the ROS image message.
        sample_number: One-based sample number used in the image filename and
            CSV row.
        directory: Existing directory where the PNG image will be written.
        writer: ``csv.DictWriter`` configured with ``CSV_FIELDS``.

    Returns:
        tuple: The image filename, position object, and orientation object
        returned by Baxter's endpoint pose.

    Raises:
        rospy.ROSException: If no camera message arrives within ten seconds.
        CvBridgeError: If the ROS image cannot be converted to OpenCV format.
        IOError: If OpenCV cannot write the captured image.
    """
    image_message = rospy.wait_for_message(IMAGE_TOPIC, Image, timeout=10.0)
    try:
        image = bridge.imgmsg_to_cv2(image_message, desired_encoding="bgr8")
    except CvBridgeError:
        raise

    pose = limb.endpoint_pose()
    position = pose["position"]
    orientation = pose["orientation"]
    image_file = "image_{:04d}.png".format(sample_number)
    image_path = os.path.join(directory, image_file)
    if not cv2.imwrite(image_path, image):
        raise IOError("OpenCV could not write {}".format(image_path))

    stamp = image_message.header.stamp.to_sec()
    writer.writerow(
        {
            "sample": sample_number,
            "image_file": image_file,
            "image_stamp_sec": "{:.9f}".format(stamp),
            "x_m": "{:.9f}".format(position.x),
            "y_m": "{:.9f}".format(position.y),
            "z_m": "{:.9f}".format(position.z),
            "qx": "{:.9f}".format(orientation.x),
            "qy": "{:.9f}".format(orientation.y),
            "qz": "{:.9f}".format(orientation.z),
            "qw": "{:.9f}".format(orientation.w),
        }
    )
    return image_file, position, orientation


def main():
    """Run the interactive right-camera capture workflow.

    Initializes the ROS node and Baxter interfaces, creates the output
    directory and CSV file, then repeatedly prompts the operator for a pose.
    Captures continue until the operator enters ``q``, ROS shuts down, or an
    exception interrupts the run. The camera is closed in all cases after it
    has been opened.
    """
    rospy.init_node("capture_right_camera")
    directory = output_directory()
    csv_path = os.path.join(directory, "poses.csv")
    bridge = CvBridge()
    limb = baxter_interface.Limb("right")
    camera = baxter_interface.CameraController(CAMERA_NAME)
    camera.open()

    try:
        with open(csv_path, "w") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            sample_number = 1
            while not rospy.is_shutdown():
                prompt = (
                    "Move Baxter to the desired pose, then press Enter "
                    "(or type q to finish): "
                )
                if read_input(prompt).strip().lower() == "q":
                    break
                image_file, position, orientation = capture_sample(
                    limb, bridge, sample_number, directory, writer
                )
                csv_file.flush()
                print(
                    "Saved {} at ({:.4f}, {:.4f}, {:.4f}) m".format(
                        image_file, position.x, position.y, position.z
                    )
                )
                print(
                    "Quaternion: ({:.4f}, {:.4f}, {:.4f}, {:.4f})".format(
                        orientation.x,
                        orientation.y,
                        orientation.z,
                        orientation.w,
                    )
                )
                sample_number += 1
    finally:
        camera.close()
        print("Capture data saved in {}".format(directory))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, rospy.ROSInterruptException):
        print("\nCapture stopped.")
