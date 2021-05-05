# [RAFT-3D: Scene Flow using Rigid-Motion Embeddings](https://arxiv.org/pdf/2012.00726.pdf)

_Decemeber 2020_

tl;dr: Summary of the main idea.
estimates pixelwise 3D motion from stereo or RGB-D video

#### Overall impression
Describe the overall impression of the paper. 
RAFT-3D is built on top of RAFT, a state-of-the-art optical ﬂow architecture that builds all-pairs correlation volumes and uses a recurrent unit to iteratively reﬁne a 2D ﬂow ﬁeld.

When projected onto the image, our SE3 motion vectors give more accurate optical ﬂow than RAFT.

#### Key ideas
- Summaries of the key ideas
- rigid-motion embeddings: per-pixel vectors that represent a soft grouping of pixels into rigid objects. During inference, RAFT-3D iteratively updates the rigid-motion embeddings such that pixels with similar embeddings belong to the same rigid object and follow the same SE3 motion.
- 

#### Technical details
- Summary of technical details

#### Notes
- Questions and notes on how to improve/revise the current work  

