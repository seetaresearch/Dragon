# ------------------------------------------------------------
# Copyright (c) 2017-present, SeetaTech, Co.,Ltd.
#
# Licensed under the BSD 2-Clause License.
# You should have received a copy of the BSD 2-Clause License
# along with the software. If not, See,
#
#     <https://opensource.org/licenses/BSD-2-Clause>
#
# ------------------------------------------------------------
"""NN implementation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dragon.core.ops import activation_ops
from dragon.core.ops import array_ops
from dragon.core.ops import normalization_ops


def batch_normalization(
    x,
    moving_mean,
    moving_variance,
    offset,
    scale,
    axis=-1,
    momentum=0.9,
    variance_epsilon=1e-5,
    trainable=False,
    name=None,
):
    r"""Apply the batch normalization.
    `[Ioffe & Szegedy, 2015] <https://arxiv.org/abs/1502.03167>`_.

    The normalization is defined as:

    .. math:: y = \frac{x - \mathrm{E}[x]}
                       {\sqrt{\mathrm{Var}[x] + \epsilon}}
                  * \gamma + \beta

    The moving average of stats are calculated as:

    .. math:: x_{\text{moving}} = \text{momentum} * x_{\text{moving}} +
                                  + (1 - \text{momentum}) * x_{\text{batch}}

    Parameters
    ----------
    x : dragon.Tensor
        The input tensor.
    moving_mean : dragon.Tensor
        The moving mean.
    moving_variance : dragon.Tensor
        The moving variance.
    offset : dragon.Tensor
        The :math:`\beta` tensor.
    scale : dragon.Tensor
        The :math:`\gamma` tensor.
    axis : int, optional, default=-1
        The channel axis.
    momentum : Union[float, dragon.Tensor], optional
        The value to :math:`\text{momentum}`.
    variance_epsilon : float, optional, default=1e-5
        The value to :math:`\epsilon`.
    trainable : bool, optional, default=False
        The optional training flag.
    name : str, optional
        The operation name.

    Returns
    -------
    dragon.Tensor
        The output tensor.

    """
    return normalization_ops.batch_norm([
        x,
        scale,
        offset,
        moving_mean,
        moving_variance],
        axis=axis,
        momentum=momentum,
        epsilon=variance_epsilon,
        use_stats=not trainable,
        name=name,
    )


def l2_normalize(x, axis=None, epsilon=1e-12, name=None):
    r"""Apply the l2 normalization.

    The **L2-Normalization** is defined as:

    .. math:: y = \frac{x}{\left\|x\right\|_{2} + \epsilon}

    The argument ``axis`` could be negative or **None**:

    ```python
    x = tf.constant([[1, 2, 3], [4, 5, 6]], 'float32')

    # A negative ``axis`` is the last-k axis
    print(tf.math.l2_normalize(x, 1))
    print(tf.math.l2_normalize(x, -1))  # Equivalent

    # If ``axis`` is None, the vector-style reduction
    # will be applied to compute a norm scalar
    print(tf.math.l2_normalize(x))

    # Also, ``axis`` could be a sequence of integers
    print(tf.math.l2_normalize(x, [0, 1]))
    ```

    Parameters
    ----------
    x : dragon.Tensor
        The tensor :math:`x`.
    axis : Union[int, Sequence[int]], optional
        The axis to compute norm.
    epsilon : float, optional, default=1e-5
        The value to :math:`\epsilon`.
    name : str, optional
        The operation name.

    Returns
    -------
    dragon.Tensor
        The output tensor.

    """
    return normalization_ops.lp_normalize(
        x,
        p=2,
        axis=axis,
        epsilon=epsilon,
        name=name,
    )


def moments(x, axes=None, keepdims=False, name=None):
    r"""Compute the mean and variance of input along the given axis.

    .. math::
        \begin{cases}
            \mathrm{E}[x] = \frac{1}{n}\sum(x) \\
            \mathrm{Var}[x] = \frac{1}{n}\sum(x - \mathrm{E}[x])^{2}
        \end{cases}

    :attr:`axes` could be negative or ``None``:

    ```python
    x = tf.constant([[1, 2, 3], [4, 5, 6]])

    # A negative axis is the last-k axis
    print(tf.nn.moments(x, 1))
    print(tf.nn.moments(x, -1))  # Equivalent

    # If axes is None, reduce as a vector and return scalars
    print(tf.nn.moments(x))  # mean is 3.5, var is 2.916667

    # Also, axes could be a sequence of integers
    print(tf.nn.moments(x, [0, 1]))  # mean is 3.5, var is 2.916667
    ```

    Parameters
    ----------
    x : dragon.Tensor
        The input tensor.
    axes : Union[int, Sequence[int]], optional
        The axis to reduce.
    keepdims : bool, optional, default=False
        Keep the reduced dimensions or not.
    name : str, optional
        The operation name.

    Returns
    -------
    dragon.Tensor
        The mean tensor.
    dragon.Tensor
        The variance tensor.

    """
    return array_ops.moments(x, axis=axes, keepdims=keepdims, name=name)


def swish(features):
    r"""Apply the swish function.
    `[Ramachandran et.al, 2017] <https://arxiv.org/abs/1710.05941>`_.

    The **Swish** function is defined as:

    .. math:: \text{Swish}(x) = x \cdot \frac{1}{1 + \exp(-x)}

    Examples:

    ```python
    x = tf.constant([-2.5, -1.0, 0.0, 1.0, 2.5])
    print(tf.nn.swish(x))
    ```

    Parameters
    ----------
    features : dragon.Tensor
        The input tensor.

    Returns
    -------
    dragon.Tensor
        The output tensor.

    """
    return activation_ops.swish(features)
