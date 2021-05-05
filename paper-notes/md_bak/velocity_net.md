# [Monocular Velocity: Camera-based vehicle velocity estimation from monocular video](https://arxiv.org/abs/1802.07094)

_July 2020_

tl;dr: Relative velocity estimation from a sequence of monocular images, taken with a moving camera. 

#### Overall impression
This is the winning entry to the monocular velocity estimation challenge. **Lightweight trajectory based features (list of bbox location) are good enough.** Better than full solution with depth and optical flow features. 

The SOTA error is around 1.12 m/s, as compared to the GT error of 0.71 m/s. 

#### Key ideas
- [TuSimple dataset](https://github.com/TuSimple/tusimple-benchmark/issues/3):
	- 20 fps, 40 frames long
	- distance ranging from 5 to 90 meters
	- bbox annotated on the last frame
- Input: two stacked images
- Off the shelf tools:
	- Tracking with openCV lib (Median Flow + MIL). 
	- Depth with [Monodepth](monodepth.md)
	- Optical flow with [FlowNet2](flownet2.md).
- Feature extraction: 
	- Spatial: shrink the bbox by 10% then calculate the mean
	- Temporal: Gaussian smoothed with width=5.
- Location and velocity prediction:
	- MLP: 4-layer
	- Split into 3 distance bins based on bbox size (20m, 45m as separator)
- 3 Models in different distance bins is better than one combined model

#### Technical details
- Both depth and optical flow degrades beyond near range (> 20m). It can achieve the best performance in near range (< 20m)
- Joint training with location leads to slightly better performance due to small dataset size
- Ensemble of 5 models for each of the 3 distance bins (from 5-fold cross validation)

#### Notes
- [Presentation Slides](https://feichtenhofer.github.io/pubs/Feichtenhofer_AutonomousDrivingChallenge_Talk_CVPR17.pdf)

