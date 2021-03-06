vm.tensorlayer.layers
=====================

.. only:: html

  Classes
  -------

  `class BatchNorm <layers/BatchNorm.html>`_
  : Batch normalization layer.
  `[Ioffe & Szegedy, 2015] <https://arxiv.org/abs/1502.03167>`_.

  `class Concat <layers/Concat.html>`_
  : Layer to concat tensors according to the given axis.

  `class Conv2d <layers/Conv2d.html>`_
  : 2d convolution layer.

  `class Dense <layers/Dense.html>`_
  : Fully connected layer.

  `class Elementwise <layers/Elementwise.html>`_
  : Layer to combine inputs by applying element-wise operation.

  `class Flatten <layers/Flatten.html>`_
  : Layer to reshape input into a matrix.

  `class GlobalMaxPool2d <layers/GlobalMaxPool2d.html>`_
  : 2d global max pooling layer.

  `class GlobalMeanPool2d <layers/GlobalMeanPool2d.html>`_
  : 2d global mean pooling layer.

  `class MaxPool2d <layers/MaxPool2d.html>`_
  : 2d max pooling layer.

  `class MeanPool2d <layers/MeanPool2d.html>`_
  : 2d mean pooling layer.

  `class Layer <layers/Layer.html>`_
  : The base layer class.

  `class LayerList <layers/LayerList.html>`_
  : Layer to stack a group of layers.

  `class Relu <layers/Relu.html>`_
  : Layer to apply the rectified linear unit.
  `[Nair & Hinton, 2010] <http://www.csri.utoronto.ca/~hinton/absps/reluICML.pdf>`_.

  `class Reshape <layers/Reshape.html>`_
  : Layer to change the dimensions of input.

  `class Transpose <layers/Transpose.html>`_
  : Layer to permute the dimensions of input.

  Functions
  ---------
  `Input(...) <layers/Input.html>`_
  : Create a placeholder as input.

.. toctree::
  :hidden:
  
  layers/BatchNorm
  layers/Concat
  layers/Conv2d
  layers/Dense
  layers/Elementwise
  layers/Flatten
  layers/GlobalMaxPool2d
  layers/GlobalMeanPool2d
  layers/MaxPool2d
  layers/MeanPool2d
  layers/Input
  layers/Layer
  layers/LayerList
  layers/Relu
  layers/Reshape
  layers/Transpose

.. raw:: html

  <style>
  h1:before {
    content: "Module: ";
    color: #103d3e;
  }
  </style>
