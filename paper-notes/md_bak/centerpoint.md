# [CenterPoint: Center-based 3D Object Detection and Tracking](https://arxiv.org/abs/2006.11275)

_July 2020_

tl;dr: [CenterTrack](centertrack.md) for lidar 3D object detection.

#### Overall impression
The results are quite impressive. It almost doubles mAP from 30 [PointPillars](pointpillars.md) to 60 [CenterPoint](centerpoint.md) on nuScenes. Especially it improves the performance on buses and trucks. 

The anchor-free object detection of [AFDet](afdet.md) (winner of 2020 Waymo Open Dataset challenge) is very close to [CenterPoint](centerpoint.md).

#### Key ideas
- Detect center of objects and regress other attributes such as 3D size, 3D orientation and **velocity** (**offset vector** in [CenterTrack](centertrack.md)).
- Most of 3D space are without measurement. Need extra trick to make it work. Gaussian blur bigger. --> cf [AFDet](afdet.md)
	- Radius function has min of 2 pixels. 
- Representation matters!
	- Point representation does not have intrinsic orientation.
	- Using anchors for each object orientation works but is even more ugly and computation heavy.
	- This reduces the search space (roughly anchor design space) and allows the backbone to learn the **rotational invariance** of object and **rotational equivariance** of their property.
- Architecture
	- Off the shelf 3D encoders [VoxelNet](voxelnet.md) and PointPillars as backbone. VoxelNet backbone is heavier but still more accurate and PointPillars.
	- Use [CenterTrack](centertrack.md) head.
- Tracking with velocity (offset) prediction is done outside of neural network in a greedy fashion.
- Lidar aggregation: follow typical method ([PointPillars](pointpillars.md)) on nuscenes and agggregate 10 lidar frames within 0.5 seconds (20 Hz collection) to densify. 

#### Technical details
- Fast NMS by max-pooling in [centerNet](centernet.md) changed to polar NMS to reflect circular symmetry.
- Data aug 
	- During training
		- [0.95, 1.05] scaling, +/- 0.2 m translation, +/-pi/8 rotation.
	- During testing 
		- Double flipping testing: 4 TTA copies --> We can add mirroring as well
		- Simple average of heatmaps works without complicated NMS strategy
- higher resolution (0.1 m gird --> 0.075 m grid) helps 
- Learned velocity is much faster than Kalman filter (91 ms to 1 ms)


#### Notes
- [One cycle policy](https://sgugger.github.io/the-1cycle-policy.html). This trick is introduced in [CBGS](cbgs.md).
	- [Implementation in center point](https://github.com/tianweiy/CenterPoint/blob/b66c1bdb49c051e104b3088cb9b9bea3d7a904a8/det3d/solver/learning_schedules_fastai.py#L77)
	- Find best LR first 
	![](https://sgugger.github.io/images/art2_courbe_lr.png)
	- Then fix max_lr to the argmin(loss) value. min_lr is roughly 10% of max_lr.
	![](https://sgugger.github.io/images/art5_full_schedule.png)

