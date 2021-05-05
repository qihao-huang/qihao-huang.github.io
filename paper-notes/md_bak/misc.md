# Machine Learning Papers Notes (Other than CNN)

## General Neural Networks
### General intro
- [A hacker's guide to neural networks](http://karpathy.github.io/neuralnets/) is also worth a read. A lot of code snippets but little math.

### Backpropagatoion
- [Chris Colah's blog post on Backpropagation](http://colah.github.io/posts/2015-08-Backprop/) explains what is forward-mode differentiation (propagating $\partial / \partial x$ from input to output) vs back-mode differentiation, or backpropagation (propagating $\partial z/\partial$) from input to output. 
	- Backprop uses dynamic programming trick to share computation among different paths. It gets results for all inputs simultaneously. It is much faster when the input count is much larger than the output count, which is generally the case with DNN.
	- Forward-mode differentiation could be much faster when the number of output is much larger than the input. 
- [Michael Nielsen's blog chapter on backpropagation](http://neuralnetworksanddeeplearning.com/chap2.html)
	- Define $a^l = \sigma(w^l a^{l-1} + b^l) \equiv \sigma (z^l)$, then 
	- Cost function needs to meet two requirements: it has to be written as average/aggregation of cost for individual training examples; it has to be written in forms of the network output (predictions).
	- Hadamard product $s \odot t$ is element wise operation, i.e., $(s \odot t)_i = s_i t_i$. It is almost the same as the dot product, skipping the final summation step.
	- The weight connecting two layers will learn slowly if either the input neuron is low-activation, or if the output neuron has saturated, i.e., is either high- or low-activation. The saturation statement is only for a sigmoid activation function. 
	\\[
		\delta^L = \nabla_a C \odot \sigma'(z^L)
	\\]
	\\[
		\delta^l = ((w^{l+1})^T \delta^{l+1}) \odot \sigma'(z^l)
	\\]
	\\[
		\frac{\partial C}{\partial w^l_{jk}} = a_k^{l-1} \delta_j^l, \quad \frac{\partial C}{\partial b_j^l} = \delta_j^l
	\\]



## RNN
### [The Unreasonable Effectiveness of Recurrent Neural Networks](http://karpathy.github.io/2015/05/21/rnn-effectiveness/)
- This blog post enumerates impressive ways to leverage power of RNN

### [Understanding LSTM Networks](http://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- This blog post explains the basic principles of LSTM networks, a very popular and effective RNN architecture

### [Google’s Neural Machine Translation System: Bridging the Gap between Human and Machine Translation](https://arxiv.org/pdf/1609.08144.pdf)
- Three inherent weaknesses of Neural Machine Translation (that prohibited NMT to overtake phrase based machine translation):
	1. Slower training and inference speed;
		- To improve training time: GNMT is based on LSTM RNNs, which have 8 layers with residual connections between the layers to encourage gradient flow. To improve inference time, low-precision arithmetic are used, further accelerated by google's TPU.
	2. ineffectiveness in dealing with rare words;  
		- To effectively deal with rare words: sub-word units ("wordpieces") were used for inputs and outputs.
	3. failure to translate all words in the source.
		- To translate all of the provided input, a beam search technique and a coverage penalty are used.
- Phrase-based machine translation (PBMT), as a type pf statistical machine translation method, has dominated machine translation for decades. NMT has been used as part of the PBMT and achieve promising results, but end-to-end learning based on NMT for machine translation has only started to surpass PBMT recently.
	- attention mechanism, character decoder, character encoder, subword units have been proposed to deal with rare words.
- GNMT is a sequence-to-sequence learning framework with attention. In order to achieve high accuracy, GNMT has to have deep enough encoder and decoder to capture subtle irregularities in the source and target.
- TBC
	