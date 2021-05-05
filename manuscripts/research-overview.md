# Research Overview

[TOC]

## 找到自己的问题

### 如何看paper

在博士第一年时需要看很多 paper，掌握 state-of-the-art，从而了解整个领域的发展。看别人还有什么没有做或者做得不是很好。但需要在这过程中需要注意： 
- 这样很容易沉迷于 "收集" 最新的技术；
- 觉得别人把能做的都做完啦，感到自己没有什么可以做的；
- 认为可以 follow 别人论文中的 "future work"，把它们作为指路明灯；
- 一直看 paper，却从不思考，不动手；
- 沉迷于一些细节上的改进，给别人的工作做加法。
#### 针对上述问题，有几点建议

- 带着问题去看 paper：在看所有 paper 之前，要思考如果自己来做会怎么做，再对照别人的"解法"，有是什么异同；
- 时刻记得，要用逻辑去验证别人的工作，例如用思想试验、反例、极端简单情况等，不要轻信别人的 claim 或者结果（并不是乱怀疑）；
- 大致了解别人的工作后，可以试一试、动动手；
- 要多想一下别人论文中隐含的假设（为什么要这样简化，为什么不那么做？）要敢于怀疑这个问题或解法的合理性；
- 要看一些经典的paper，知道潮流是怎么来的；
- Read these papers, understand the old ideas, understand the original problems, these are common ways these days;
- If you can find another way;
- If you can resolve some main limitation, or add some weak constraints but get stronger results.
- 设计和采用最合适的技术而不是最新、最高深的技术。
#### 总之
- 从问题本源去看去想，才能摆脱跟随潮流、觉得别人把能做的都做完了的困境，摆脱只有一些小 idea 的局限；
- 做一些系统化的的工作，而不是零零碎碎的小工作。 
### 学习和研究的关系
学习是 consume knowledge，而研究是 produce knowledge，如果不带着问题，不带着自己的想法，去泛泛地看一本书、学一门公开课、一大堆 paper，很容易给自己的一种虚假的充实感，但事实上很难促进自己的研究进展。因此，要带着自己的问题去寻找已有的工作，去寻找相应的工具，带着自己已有的大概的想法，去找别人有没有类似的思路。
### 问题从哪里来
- 从实际中提炼出一个新问题（问题创新）；
- 从一个新的角度去看一个老问题（问题创新）；
- 用全新的方法去解决一个问题（方法创新）；
- 去掉所有限制，去掉所有约束，考虑最坏的情况，该如何解决（问题创新+方法创新）。
看实际生活中有什么可以解决的，尝试去解决它？因为有用的东西才能自圆其说，才能越走越宽。不过要小心：
- 觉得自己做的东西和实际相差太远，没有任何用处；
- 觉得自己做的东西太实际了，应用面非常狭窄；
- 沉迷于把东西“做出来”，止步于工程的实现，觉得没啥可做了；
- 觉得实际问题太苦难了，做不动。
#### 有几点建议 
- 实际和 paper 之间的 gap 必然存在，但往往不是你做的方向和实际相差太远，而是你的工作或者已有工作给出的解决方案太理想化了；
- 如何简化问题是一门艺术：需要考虑非常多的因素，如果简化不够，那么很难抓住主要矛盾，工作没有一般性；过于简化问题，那么得到的结果一般，没有办法实际应用；
- 适当的简化可以提取主要矛盾，得到尽可能一般的方法，缩小实际和 paper 之间的 gap.

### 什么样的问题是一个好问题
- 能够和其他已有的 topic 有 rich interaction;
- 能够带来让人耳目一新的 change;
- 对应的 change 可以有很好的后续性：the important thing is finding wet snow and reallly long hill;
- 对应的 change 能够真正解决一个重要的应用；
- 能够用一整套理论去解决一个新问题 。
### 如何问问题
- Ask simple questions first, you can start from there;
- Ask "stupid" questions, may not be stupid;
- Don't be afraid of asking crazy questions; solve big problems;
- Suggestion: Keep a list of simple and crazy questions, and track them, think whenever you have time.
## 解决这个问题
- solve simple questions, then find more questions;
- Rethink your problem many times;
- Solve harder problems;
- Rethink your problem many times.
### 如果脑中只有一堆很小的想法
- 那么我们可以先做一个简单的系统；
- 并且在过程中继续发现问题；
- 很少有人可以一下子有一个非常大的想法，大部分情况下都是一些空想；
- 认识需要不断加深。
解决问题中是数学越高深越好吗，是机器学习用的越多越好吗？并不是。
要舍得放弃一些小的想法，每个人的时间是有限的，可以让第一年的同学去做这些小的想法。
另外，在写论文时，刻意去讲故事是不容易成功的，虽然有时候我们不得不去讲一个故事去包装，但是包装不是目的。

### 在解决问题时遇到了困难怎么办
#### Find bugs, find mistakes

- test each component first
- try simple case first
- try extreme case first
- try case with analytical or easy to judge results first
- 反复检查代码是最低效的解决方法
- 多写测试 case，使用 unit test
- 多写 visualization， 在调试和 paper 里都可以用
- debug 的过程需要 evidence，而不是呆着看代码
#### working, reading, writing
- 每天一部分的时间用来 working on the project，一部分时间用来 reading，一部分时间用 writing;
- writing 可以迫使自己让想法更加清晰化、具体化，也容易发现过程中的错误和疏漏；
- reading 可以不时给自己一点新的启发。
## 什么是好的研究
### 坚持自我
机器学习目前的确有更多的 citation，也很热闹，但是还是要有自己的核心，而不是随大流的工作，要用工作质量来衡量。在一个热闹的领域里，没有自己的核心 idea 和特点是没有办法去成体系地跟上的。要有自己的坚持，坚持到底，做漂亮做完整的工作。paper 写作时，要主要示意图是不是容易理解，看 paper 时也要看一看哪些写作是比较好的。
## 理想的 schedule

#### 第一年
- 一个具体的小想法；
- 完成基本的软件、硬件平台的搭建；
- 对整个领域有了解；
- 开始思考自己的 "大问题"。
#### 第二年
- 在 "大问题" 上有初步的想法，提出一两个初步的步骤，去开始一定的探索；
- 一些简单的情况怎么处理；
- 加一些合适的简化；
- 希望从这个时候开始老师从学生那里学校一点东西（新想法、新观点、新事实）。
#### 第三、四年
- 在解决这个大问题上有比较大的进展；
- 有自己独立的想法和 idea.
### 做加法的局限
- 完美的子系统的串联 ≠ 高质量的整体系统；
- 子问题也许在解决一个比原问题更难的问题，通过一个更难问题的低质量的解来得到目标问题的解， 或者直接解决目标问题；
- 子问题的难点可能在于没有考虑其他部分的交互。