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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy

from dragon.core.framework import proto_util
from dragon.core.util import math_util
from dragon.vm.torch.core import tensor as tensor_module


class Size(tuple):
    """Represent the a sequence of dimensions."""

    def __init__(self, sizes=None):
        """Create a ``Size``.

        Parameters
        ----------
        sizes : Sequence[int]
            The dimensions.

        """
        super(Size, self).__init__()

    def numel(self):
        """Return the total number of elements.

        Returns
        -------
        int
            The number of elements.

        """
        return math_util.prod(self)

    def __getitem__(self, item):
        """
        Returns the size.

        Args:
            self: (todo): write your description
            item: (str): write your description
        """
        if not isinstance(item, (slice, tuple)):
            return super(Size, self).__getitem__(item)
        return Size(super(Size, self).__getitem__(item))

    def __repr__(self):
        """
        Return a repr representation of - repr representation of this object.

        Args:
            self: (todo): write your description
        """
        return 'torch.Size([{}])'.format(', '.join([str(s) for s in self]))


class device(object):
    """Represent the device spec."""

    def __init__(self, type='cpu', index=0):
        """Create a ``device``.

        Parameters
        ----------
        type : str, optional, default='cpu'
            The device type.
        index : int, optional, default=0
            The device index.

        """
        self.type, self.index = type, index
        self._proto = None
        self._serialized_proto = None

    def copy(self):
        """Return a clone device."""
        return device(self.type, self.index)

    def to_proto(self, serialized=True):
        """Return the device proto."""
        if self._proto is None:
            self._proto = proto_util.get_device_option(self.type, self.index)
        if serialized:
            if self._serialized_proto is None:
                self._serialized_proto = self._proto.SerializeToString()
            return self._serialized_proto
        return self._proto

    def __eq__(self, other):
        """
        Determine if two index objects are equal.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        return self.type == other.type and self.index == other.index

    def __str__(self):
        """
        Return the string representation of this index.

        Args:
            self: (todo): write your description
        """
        return '{}:{}'.format(self.type, self.index)

    def __repr__(self):
        """
        Return a human - readable for a repr.

        Args:
            self: (todo): write your description
        """
        return "device(type='{}', index={})".format(self.type, self.index)


class dtype(str):
    """The basic data type.

    Following data types are defined:

    * ``torch.float16`` or ``torch.half``: 16-bit half-precision floating-point.

    * ``torch.float32`` or ``torch.float``: 32-bit single-precision floating-point.

    * ``torch.float64`` or ``torch.double``: 64-bit double-precision floating-point.

    * ``torch.bfloat16``: 16-bit truncated floating-point.

    * ``torch.complex32``: 32-bit single-precision complex.

    * ``torch.complex64``: 64-bit single-precision complex.

    * ``torch.complex128``: 128-bit double-precision complex.

    * ``torch.int8``: 8-bit signed integer.

    * ``torch.uint8``: 8-bit unsigned integer.

    * ``torch.int16`` or ``torch.short``: 16-bit signed integer.

    * ``torch.int32`` or ``torch.int``: 32-bit signed integer.

    * ``torch.int64`` or ``torch.long``: 64-bit signed integer.

    * ``torch.bool``: Boolean.

    * ``torch.qint8``: Quantized 8-bit signed integer.

    * ``torch.quint8``: Quantized 8-bit unsigned integer.

    * ``torch.qint32``: Quantized 32-bit signed integer.

    """

    def __init__(self, s):
        """Create a ``dtype``.

        Parameters
        ----------
        s : str
            The data type descriptor.

        """
        super(dtype, self).__init__()


def from_numpy(array):
    """Create a tensor from the given numpy array.

    Parameters
    ----------
    array : numpy.ndarray
        The numpy array data.

    Return
    ------
    dragon.vm.torch.Tensor
        The torch tensor.

    """
    if not isinstance(array, numpy.ndarray):
        raise TypeError('The <array> should be a numpy ndarray.')
    return tensor_module.Tensor(array, copy=False)
