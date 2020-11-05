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
"""Init ops library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dragon.core.framework.ops import Operator


class Initializer(Operator):
    """Initializer operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(Initializer, self).__init__(key, dev, **kwargs)
        self.ndim = kwargs.get('ndim', 0)
        self.dtype = kwargs.get('dtype', 'float32')

    def feed(self, ws, handle, shape):
        """
        Feed the shape of the given shape.

        Args:
            self: (todo): write your description
            ws: (todo): write your description
            handle: (todo): write your description
            shape: (int): write your description
        """
        for i, dim in enumerate(shape):
            self.feed_arg(
                ws, '{}/dims[{}]'.format(handle, i),
                dim, 'int64')

    def forward(self, shape, shape_as=None, out=None, trainable=None):
        """
        R forward forward forward computation.

        Args:
            self: (todo): write your description
            shape: (int): write your description
            shape_as: (int): write your description
            out: (array): write your description
            trainable: (bool): write your description
        """
        out = self.dispatch(
            [] if shape_as is None else [shape_as],
            [self.alloc(out)],
            callback=lambda ws, handle:
                self.feed(ws, handle, shape),
            no_grad=True,
        )
        if trainable is not None:
            out._requires_grad = trainable
        return out


class Eye(Initializer):
    """Eye operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(Eye, self).__init__(key, dev, **kwargs)
        self.k = kwargs.get('k', 0)

    def attributes(self):
        """
        : return : class : dict

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'Eye',
            'arguments': {
                'k': self.k,
                'dtype': self.dtype,
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'.format(n)
                    for n in range(self.ndim)],
            },
        }


class Fill(Initializer):
    def __init__(self, key, dev, **kwargs):
        """
        Initialize device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(Fill, self).__init__(key, dev, **kwargs)
        self.value = kwargs.get('value', 0.)

    def attributes(self):
        """
        A dictionary of attributes

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'Fill',
            'arguments': {
                'dtype': self.dtype,
                'value': float(self.value),
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'.format(n)
                    for n in range(self.ndim)],
            },
        }


class GlorotNormal(Initializer):
    """GlorotNormal operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(GlorotNormal, self).__init__(key, dev, **kwargs)
        self.scale = kwargs.get('scale', 2.)
        self.mode = kwargs.get('mode', 'fan_in')

    def attributes(self):
        """
        A dictionary of the attributes of the dataset.

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'GlorotNormal',
            'arguments': {
                'dtype': self.dtype,
                'scale': float(self.scale),
                'mode': self.mode.lower(),
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'.format(n)
                    for n in range(self.ndim)],
            },
        }


class GlorotUniform(Initializer):
    """GlorotUniform operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the scaling device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(GlorotUniform, self).__init__(key, dev, **kwargs)
        self.scale = kwargs.get('scale', 3.)
        self.mode = kwargs.get('mode', 'fan_in')

    def attributes(self):
        """
        A dictionary of the attributes of the dataset.

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'GlorotUniform',
            'arguments': {
                'dtype': self.dtype,
                'scale': float(self.scale),
                'mode': self.mode.lower(),
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'.format(n)
                    for n in range(self.ndim)],
            },
        }


class RandomNormal(Initializer):
    """RandomNormal operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(RandomNormal, self).__init__(key, dev, **kwargs)
        self.mean = kwargs.get('mean', 0.)
        self.std = kwargs.get('std', 1.)

    def attributes(self):
        """
        Returns a dictionary of the attributes.

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'RandomNormal',
            'arguments': {
                'dtype': self.dtype,
                'mean': float(self.mean),
                'std': float(self.std),
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'.format(n)
                    for n in range(self.ndim)],
            },
        }


class RandomUniform(Initializer):
    """RandomUniform operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(RandomUniform, self).__init__(key, dev, **kwargs)
        self.low = kwargs.get('low', 0.)
        self.high = kwargs.get('high', 1.)

    def attributes(self):
        """
        Return a dictionary of attributes

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'RandomUniform',
            'arguments': {
                'dtype': self.dtype,
                'low': float(self.low),
                'high': float(self.high),
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'.format(n)
                    for n in range(self.ndim)],
            },
        }


class TruncatedNormal(Initializer):
    """TruncatedNormal operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(TruncatedNormal, self).__init__(key, dev, **kwargs)
        self.mean = kwargs.get('mean', 0.)
        self.std = kwargs.get('std', 1.)

    def attributes(self):
        """
        Returns a dictionary of the attributes.

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'TruncatedNormal',
            'arguments': {
                'dtype': self.dtype,
                'mean': float(self.mean),
                'std': float(self.std),
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'.format(n)
                    for n in range(self.ndim)],
            },
        }
