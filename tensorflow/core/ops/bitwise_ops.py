# ------------------------------------------------------------
# Copyright (c) 2017-present, SeetaTech, Co.,Ltd.
#
# Licensed under the BSD 2-Clause License.
# You should have received a copy of the BSD 2-Clause License
# along with the software. If not, See,
#
#    <https://opensource.org/licenses/BSD-2-Clause>
#
# Codes are based on:
#
#    <https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/ops/bitwise_ops.py>
#
# ------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dragon.core.ops import math_ops


def bitwise_and(x, y, name=None):
    r"""Compute the element-wise AND bitwise operation.

    .. math:: \text{out} = x \mathbin{\&} y

    Examples:

    ```python
    x = tf.constant([False, True, False, True])
    y = tf.constant([False, True, True, False])
    print(tf.bitwise.bitwise_and(x, y))  # False, True, False, False
    print(x * y)  # Equivalent operation
    ```

    Parameters
    ----------
    x : dragon.Tensor
        The tensor :math:`x`.
    y : dragon.Tensor
        The tensor :math:`y`.
    name : str, optional
        A optional name for the operation.

    Returns
    -------
    dragon.Tensor
        The output tensor.

    """
    return math_ops.bitwise_and([x, y], name=name)


def bitwise_or(x, y, name=None):
    r"""Compute the element-wise OR bitwise operation.

    .. math:: \text{out} = x \mathbin{|} y

    Examples:

    ```python
    x = tf.constant([False, True, False, True])
    y = tf.constant([False, True, True, False])
    print(tf.bitwise.bitwise_or(x, y))  # False, True, True, True
    print(x + y)  # Equivalent operation
    ```

    Parameters
    ----------
    x : dragon.Tensor
        The tensor :math:`x`.
    y : dragon.Tensor
        The tensor :math:`y`.
    name : str, optional
        A optional name for the operation.

    Returns
    -------
    dragon.Tensor
        The output tensor.

    """
    return math_ops.bitwise_or([x, y], name=name)


def bitwise_xor(x, y, name=None):
    r"""Compute the element-wise XOR bitwise operation.

    .. math:: \text{out} = x \oplus y

    Examples:

    ```python
    x = tf.constant([False, True, False, True])
    y = tf.constant([False, True, True, False])
    print(tf.bitwise.bitwise_xor(x, y))  # False, False, True, True
    print(x - y)  # Equivalent operation
    ```

    Parameters
    ----------
    x : dragon.Tensor
        The tensor :math:`x`.
    y : dragon.Tensor
        The tensor :math:`y`.
    name : str, optional
        A optional name for the operation.

    Returns
    -------
    dragon.Tensor
        The output tensor.

    """
    return math_ops.bitwise_xor([x, y], name=name)


def invert(x, name=None):
    r"""Invert each bit of input.

    .. math:: \text{out} = \,\,\sim x

    Examples:

    ```python
    # Typically, ``x`` is a bool tensor
    print(tf.bitwise.invert(tf.constant([0, 1], 'bool')))  # [True, False]

    # Otherwise, integral types are required (unsigned or signed)
    # 00001101 (13) -> 11110010 (?)
    print(tf.bitwise.invert(tf.constant(13, 'uint8')))  # 242
    print(tf.bitwise.invert(tf.constant(13, 'int8')))   # -14
    ```

    Parameters
    ----------
    x : dragon.Tensor
        The tensor :math:`x`.
    name : str, optional
        A optional name for the operation.

    Returns
    -------
    dragon.Tensor
        The output tensor.

    """
    return math_ops.invert(x, name=name)