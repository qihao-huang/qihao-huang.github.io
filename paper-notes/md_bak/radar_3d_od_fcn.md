# [Object Detection and 3D Estimation via an FMCW Radar Using a Fully Convolutional Network](https://arxiv.org/abs/1902.05394) 

_July 2019_

tl;dr: Sensor fusion method using radar to estimate the range, doppler, and x and y position of the object in camera. 

#### Overall impression
Two steps in the pipeline: preprocessing (2D FFT and phase normalization) and CNN for detection and angle estimation. 

However **no physical extent was obtained**. This is one area we could focus on.

The paper provides interesting ideas, but not very practical, as there is only one object in the experiment setup.

#### Key ideas
- Pixel position form a camera image roughly represents the orientation of an object in 3D space (azimuth and elevation angles), while the cell position of range doppler map represents the range and velocity of the object.
- Phase normalization method for each range-doppler cell to make the phase of the first frame to be 0.
- Perform detection using U-Net on range-doppler map first for detection, then estimate the orientation with further convolution.
- **Annotation**: Use coupled (sync'ed) camera for annotation. Regress the x and y coordinates (roughly indicate azimuth and elevation angles) directly from the radar data across different antennas (angle finding).


#### Technical details
- Feed both FG signal and BG signal to the network --> BG signal is NOT available for most cases.
- There is no camera-radar cross sensor calibration, and reply NN to learn the coordinate mapping --> This is not a very general method.

#### Notes
- We could use the predicted heatmap in RD map as attention for angle estimation.
- Q: why use dice loss? The annotation of each of the objects should be a single point? Dice works better to balance the loss when there are objects of different sizes.
- Q: phase normalization: the phase along the channel is also mentioned in [deep radar detector](deep_radar_detector.md). We could use phase shift as data augmentation method.

