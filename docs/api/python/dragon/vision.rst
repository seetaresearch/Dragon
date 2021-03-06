dragon.vision
=============

.. only:: html

  Classes
  -------

  `class DataIterator <vision/DataIterator.html>`_
  : Iterator to return the batch of data for image classification.

  Functions
  ---------

  `extract_patches(...) <vision/extract_patches.html>`_
  : Extract the sliding patches from input.

  `resize(...) <vision/resize.html>`_
  : Resize input via interpolating neighborhoods.

  `roi_align(...) <vision/roi_align.html>`_
  : Apply the average roi align.
  `[He et.al, 2017] <https://arxiv.org/abs/1703.06870>`_.

  `roi_pool(...) <vision/roi_pool.html>`_
  : Apply the max roi pooling.
  `[Girshick, 2015] <https://arxiv.org/abs/1504.08083>`_.

.. toctree::
  :hidden:

  vision/DataIterator
  vision/extract_patches
  vision/resize
  vision/roi_align
  vision/roi_pool

.. raw:: html

  <style>
  h1:before {
    content: "Module: ";
    color: #103d3e;
  }
  </style>
