# [Cam2BEV: A Sim2Real Deep Learning Approach for the Transformation of Images from Multiple Vehicle-Mounted Cameras to a Semantically Segmented Image in Bird's Eye View](https://arxiv.org/abs/2005.04078)

_September 2020_

tl;dr: Uses spatial transformer module with IPM feature transform to transform perspective features to BEV.

#### Overall impression
For surfaces, IPM can accurate transform image to a BEV. For 3D objects such as vehicles and VRUs, it is hard to estimate their position relative to the sensor. 

Uses semantic segmented images as input, which helps with bridging the sim2real domain gap. This step remove mostly unnecessary texture from real-world data by computing semantically segmented camera image. The idea of using semantic segmentation to bridge the sim2real gap is explored in many BEV semantic segmentation tasks such as [BEV-Seg](bev_seg.md), [CAM2BEV](cam2bev.md), [VPN](vpn.md).

The proposed uNetXST architecture transforms four perspective semantic segmented images into one aggregated BEV semantic segmentation image.

In [Learning to look around objects](learning_to_look_around_objects.md), the network is explicitly supervised to hallucinate, whereas [Cam2BEV](cam2bev.md) eliminates the occlude regions in order to make the problem better posed.


#### Key ideas
- **View transformation**: IPM
	- Homography image: IPM of semantic segmentation results and concatenated into a 360 deg BEV image.
- Uses synthetic data from VTD simulation environment.
- Baseline 1: Input semantic segmentation for perspective images, and homography image. Network's task is to correct the errors introduced by IPM.
- Baseline 2: Input semantic segmentation for perspective image alone. uNet with Spatial Transformer unit for transforming intermediate features.


#### Technical details
- Occlusion preprocessing of GT: 
	- Preprocess GT images to introduce the effect of occlusion. Some pixels are unobservable from onboard cameras. In order to formulate a well-posed problem, an additional semantic class needs to be introduced to the label images for areas in BEV, which are occluded in the camera perspectives.
	- Some rules for processing: building and trucks always block views, cars block sight except on taller objects behind them (such as truck or bus).
- Both input and output are recorded at a fixed resolution of 964x604, with about 7 cm per pixel. Data collected at 2Hz.

#### Notes
- [code on github](https://github.com/ika-rwth-aachen/Cam2BEV)
- [Blog on BEV-Net with CARLA simulator](https://medium.com/asap-report/from-semantic-segmentation-to-semantic-birds-eye-view-in-the-carla-simulator-1e636741af3f)

