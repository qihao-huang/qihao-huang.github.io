# internship-summary-in-xyz-robotics 

Mission: Pick Anything, Place Anywhere.

在 XYZ Robotics 作为实习视觉算法工程师负责过两个项目，分别是**拣选** (picking) 和**拆垛**(depalletizing)。

##  Highly Packed Picking

第一阶段最主要的任务是将创始团队在 [Amazon picking challenge](http://arc.cs.princeton.edu/) 里的项目和[论文](https://arxiv.org/abs/1710.01330/)工程化。团队早期研发的模型已经可以熟练且高效地面对**混乱摆放**的料箱，然而在实际工业场景中存在另一个棘手的问题——**密集排列的场景**. [XYZ Robotics 3D AI Vision Processor](https://www.xyzrobotics.ai/3d-ai-vision-processor/) 网站。

### Qualitative or Quantitative

**早期探索**时，无论是**数据的收集**、**模型的验证**，再未敲定研发投入方向前，**qualitative** 的方式对**方案迭代**、**团队沟通**来说都更为便捷，eye-ball 的方式，也未必不可采用。而当**初步敲定了方向后**，必须开始引入**合适且明确的量化 metrics**，明确做事情的方向，才能**高效率地推动**后续的讨论和方案的改进，而不是在“我觉得”，“看起来”…中进度堪忧。work 这个词，大家的理解都大有不同。

### 问题分解

一个系统工程必然由多个模块堆叠而成，**优秀的系统设计**对**成熟的项目管理**和**工程团队间的配合**都大有裨益。例如对于**视觉工程师**而言，如何**反馈、分析**低质量的视觉预测，并将整体的结果分解到 perception 模块中。简单来说，就是透过现象看问题，一个现象，可能是一个软件 bug，也可能只是一个硬件故障，还是起初的 assumption 太理想……

### 团队合作

- 水平（横向）
  -  inter-class 软硬件团队间
    - 工程方案中，经常需要尝试并验证不同的思路和方案。不论是传统的视觉、图像处理方法，还是 deep 的方法，都与相机、机械部件密切相关。是采用 RGB 俯视相机，还是 RGB-D 或者 ToF 相机，机械臂干扰，料箱进出通道规划与视觉模块如何协作？这些都需要软硬件团队**反复权衡硬件和产品的可实施性**，在成本、性能、预期效果间不断尝试和讨论。
  - Intra-class 视觉团队内
    - 在协作、参与者渐多时，需要引入高效的协同工具，确保**沟通**，是一门大课题了。
    - Contributed to design and deploy a company-wise dataset, model version control pipeline for deep cooperation. 
-  垂直（纵向）
  - 能够明显地感受到，早期团队规模尚未扩张前，或者说仍在打磨产品、攻坚克难时，技术团队以及创始团队的主要精力都投入在推进研发上。也是那段时间，mentor 于我的指导、沟通、反馈也更为 instant，每天都能在反馈中看到点滴的进步，以及感染到 mentor 的人格魅力、做事态度。同样的，这种微管理的方式在早期占用了 mentor 大量的时间，我们双方都没有足够多的时间在更 global 的视角思考问题。后期稍见曙光，确认方向正确后便一周两次 meeting 和 pre 报告进度和讨论，团队更为契合和高效了。
- 自我（时间管理）
  - 实习期间前后跟进了两个项目。事实告诉我们，起初规划的方向并不一定是最合理、有效的方向。
  - 每天上班第一件事情就是啃着黄桃酸奶，然后想一想今天的 **scrum** 和 **OKR** ，然后schedule 合作和自己项目的进度和问题。

### Industry or Academia

对于工业界来说，并不需要特别复杂的网络，特别多的创新点，但提出的想法一定要切切实实地提高性能。目前来看，当时的模型性能，并不能 100% 泛化到天猫超市中所有的中小型物体，怎么定义 work，工业界和学术界的定义是不同的，各种 abnormal 的场景的需求也不同。

## Depalletizing

第二阶段的项目是拆垛，和波士顿动力去年收购的 kynema 的[拆垛机器人](https://www.bostondynamics.com/pick)很相似。在整个过程中，从0到1，收集→整理→清洗→维护了一个工业数据库。在方案选择和开发过程中，还根据 RGB-D 相机的 API 去调整相机参数、标定相机，点云处理等等。还在研发过程中，不谈细节了。

## Future discussion

团队 mission（**Pick Anything, Place Anywhere.** ）中的 picking 在一步步地完善，工业场景中如何推向 place 是一个值得探索的方向。

### RGB or Depth

对于更常见的混乱推放的物料盒，是否一定要采取深度图呢？Two branch 粗暴地 concatenate feature map 需要更多地计算量，如果可以直接从 RGB 中学到物体的形状信息，那么就可以去掉 depth，加速 inference，采用更好的 RGB 相机，而不是现在制约性能的 RGB-D 相机。

### Deep and Synthesis

对于一些 abnormal，棘手的 case，例如黑色、反光、透明、半透明就需要采取一些传统的视觉方案去处理。除了网络结构外，数据量是最重要的，包括正反样本的平衡。我们尝试过一些物理引擎，渲染一些真实的混乱、整齐叠放的图片，但没有量化的方法、或者理论去 claim 混合真实、渲染的百分比和情景，因此还处于实验阶段。

### low-level methods

我们尝试过一些 low-level 的方法，比如直接 predict 这些物体的 edge，但是计算机视觉发展到今天，

还是无法完全地解决这个问题。又例如，double pick，我们不小心吸取到了边缘，pick 了两个物体，我们希望通过 active vision 去检测，我们到底吸取了几个物体，目前用过点云、形状的方案都不是很稳定。