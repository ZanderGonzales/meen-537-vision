# MeEn537 Final Project Proposal

**Authors:** Zander Gonzalez & Brock Gregersen  
**Instructor:** Dr. Killpack  
**Date:** 6 November 2026

### Project Description
We will use Baxter's integrated camera to generate a 3-D map of an object. This will include capturing images with the camera placed an known points, and developing an algorithm to stich the images together into a 3-D map.

### Success Measures
- Capture images of a subject with the camera at a known location using Baxter's integrated camera or our own camera mounted to Baxter
- Develop an algorithm that can construct a recognizable 3-D map of the subject using 2 captured images

#### Stretch Goals
- Implement support for more than 2 images

### Potential Pitfalls
- Camera lens distortion
- Insufficient camera quality from Baxter's integrated camera

### Timeline
|   Date   |      Task      |
|----------|----------------|
|2026-11-06|Project proposal|
|2026-11-09|Check image quality|
|2026-11-11|Correct lens distortion|
|2026-11-13|Initial image capture|
|2026-11-20|Implement feature detection|
|2026-11-25|Triangulate location of points|
|2026-11-26|Render point cloud|
|2026-12-04|Improve reconstruction, add additional viewpoints|

### Resources and Libraries
We will use Python libraries such as OpenCV and use the book *Robotics, Vision and Control* by Peter Corke as a reference.