# [Deep3dBox: 3D Bounding Box Estimation Using Deep Learning and Geometry](https://arxiv.org/pdf/1612.00496.pdf)

_July 2019_

tl;dr: Monocular 3d object detection (3dod) by using 2d bbox and geometry constraints.

#### Overall impression
This paper proposed the famous discrete-continous loss (or multi-bin loss, or hybrid classification/regression loss) that has become standard for regress large range of target or multi-modal regression problem. In retrospect, it is the same as using **anchors** such as those in object detection. 

This is not end-to-end. NN is used to estimate 2D bbox and dimensions and orientations of the bbox. Then the distance (translational vector) is obtained by solving for linear equation posed by the constraint of the corners touching four sides of 2D bbox.

A simpler version for 3d proposal generation based on 2d bbox and viewpoint classification is in [semantic 3d slam](semantic_3d_slam.md).

#### Key ideas
- **Yaw and observation angle are different!** The observation angle determines the appearance, not the yaw itself.
- **Multi-Bin loss**. The authors cited anchor box as intuition. First the regression target is discretized into multiple bins. Then the residual angle is regressed as sine and cosine. However the bins are **overlapping**, which seem to be different from what is used in later work. During training, there might be multiple bins corresponding to the same GT angle, but during inference, only the bin with the largest confidence score is picked and the regressed residual is applied.
	-  Multi-bin loss can be also found in this earlier [viewpoint estimation paper](https://arxiv.org/pdf/1609.03894.pdf). Another way to predict angle is the [geometrically structure aware loss](https://www.cv-foundation.org/openaccess/content_iccv_2015/papers/Su_Render_for_CNN_ICCV_2015_paper.pdf).
	-  This can also be modified in inference time to get the weighted average from different bins. See [3D RCNN](3d_rcnn.md).
	-  This is also used in depth/disparity estimation, such as in [TW-SMNet](twsm_net.md).
- **Representation matters**. 
	- Regress dimension and orientation first. 
	- The authors tried regressing dimension and distance at the same time but found it to be highly sensitive to input errors. --> This is understandable as dim and distance are highly correlated in determining the dimension of the bbox. (c.f. [depth in the wild](learnk.md) to understand the coupling of estimation parameters. Sometimes an overall supervision signal is given to two tightly coupled parameters and it is not enough to get accurate estimate for both parameters)
- Orientation of a car can be estimated fairly accurately, given ground truth (from lidar annotation). Angle errors are: 3 degrees for easy case, 6 for moderate and 8 for hard cases.
- The translational vector (center of the 3dbbox) is calculated deterministically from solving linear equations. However the center of the 3dbbox can be calculated fairly easily with reprojecting the 2d bbox height and the center to the 3d world. See [monoPSR](monopsr.md) for a rough estimate of the 3D position.

#### Technical details
- Orientation KPI is AOS (average orientation similarity), average cosine similarity between predicted and gt orientations. 
- Additional KPIs in 3D bbox: center error, and error in predicting the nearest point in 3D bbox.

#### Notes
- Q: Calculating the 3d translational vector directly from the 4 geometry constraint equation seems to be a bit weird. If the orientation prediction is wrong, then the x, y, z (from which you can calculate the depth) may be completely off, especially lateral position. Lateral position (u in the (u, v) tuple) of the object with respect to the principal point of the camera (obtained from the intrinsics) is a very strong prior to the x distance. Why not use this constraint and completely relying on the orientation estimation? --> A: actually as we bound the 3d bbox in the 2d bbox, this already limits the x, y and z to a tight range. 
- The drawback of the method is that any inaccuracy in 2D object detection is locked in to 3D estimation as the geometry constraint is solved deterministically.
- [Blog on detailed implementation](https://towardsdatascience.com/geometric-reasoning-based-cuboid-generation-in-monocular-3d-object-detection-5ee2996270d1)