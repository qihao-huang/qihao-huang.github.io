# [CrowdHuman: A Benchmark for Detecting Human in a Crowd](https://arxiv.org/abs/1805.00123) 

_July 2020_

tl;dr: A large scale (15k training images) dataset for crowded/dense human detection.

#### Overall impression
Very solid technical report from megvii (face++). Related datasets: [WiderPerson](widerperson.md).

Previous datasets are more likely to annotate crowd human as a whole ignored region, which cannot be counted as valid samples in training and evaluation.

#### Key ideas
- 22 human per image.
- Full body bbox (amodal), visible bbox (only visible region), head bbox. They are bound (associated) for each human instance.
- occlusion ratio can be quantified by the two bbox. 
- evaluation metric:
	- AP
	- mMR (average log miss rate over FP per image)

#### Technical details
- Image crawled from google image search engine, cleaned and annotated. 
- Pervious datasets (CityPerson) annotates top of the head to the middle of the feet and generated a full bbox with fixed aspect ratio of 0.41.

#### Notes
- [AP vs MR](ap_mr.md) in object detection.