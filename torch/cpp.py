# ------------------------------------------------------------
# Copyright (c) 2017-present, SeetaTech, Co.,Ltd.
#
# Licensed under the BSD 2-Clause License.
# You should have received a copy of the BSD 2-Clause License
# along with the software. If not, See,
#
#    <https://opensource.org/licenses/BSD-2-Clause>
#
# ------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import importlib
import numpy

from dragon.core.framework import proto_util
tensor_module = importlib.import_module('dragon.vm.torch.tensor')


class Size(tuple):
    """Represent the a sequence of dimensions."""

    def __init__(self, sizes):
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
        return int(numpy.prod(self))

    def __setitem__(self, key, value):
        raise TypeError("'torch.Size' object does not support item assignment.")

    def __getitem__(self, item):
        if not isinstance(item, (slice, tuple)):
            return super(Size, self).__getitem__(item)
        return Size(super(Size, self).__getitem__(item))

    def __repr__(self):
        return 'torch.Size([{}])'.format(', '.join([str(s) for s in self]))


class device(object):
    """Represent the device where tensor will be allocated."""

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
            self._proto = proto_util.get_device_option(
                self.type, self.index)
        if serialized:
            if self._serialized_proto is None:
                self._serialized_proto = self._proto.SerializeToString()
            return self._serialized_proto
        return self._proto

    def __eq__(self, other):
        return self.type == other.type and self.index == other.index

    def __str__(self):
        return '{}:{}'.format(self.type, self.index)

    def __repr__(self):
        return 'device(type={}, index={})'.format(self.type, self.index)


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