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

from dragon.vm.torch.autograd import function


class ArgReduce(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(ArgReduce, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', None)
        self.keep_dims = kwargs.get('keep_dims', True)
        self.top_k = kwargs.get('top_k', 1)
        self.operation = kwargs.get('operation', 'MAX')

    def attributes(self):
        return {
            'op_type': 'ArgReduce',
            'arguments': {
                'axis': self.axis,
                'top_k': self.top_k,
                'keep_dims': self.keep_dims,
                'operation': self.operation,
            },
        }

    def forward(self, input, out=None):
        outputs = [out] if out else [self.alloc()]
        return self.dispatch([input], outputs, no_grad=True)


class Assign(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Assign, self).__init__(key, dev, **kwargs)
        self.ndim = kwargs.get('ndim', 0)

    def attributes(self):
        return {
            'op_type': 'Assign',
            'arguments': {
                'starts_descs': [
                    '${{HANDLE}}/starts[{}]'
                    .format(n) for n in range(self.ndim)],
                'sizes_descs': [
                    '${{HANDLE}}/sizes[{}]'
                    .format(n) for n in range(self.ndim)],
            },
        }

    def feed(self, ws, handle, starts, sizes):
        for i in range(self.ndim):
            self.feed_arg(
                ws,
                '{}/starts[{}]'.format(handle, i),
                starts[i], 'int64',
            )
            self.feed_arg(
                ws,
                '{}/sizes[{}]'.format(handle, i),
                sizes[i], 'int64',
            )

    def forward(self, out, starts, sizes, input):
        self._check_device([input, out])
        return self.dispatch(
            [input], [out],
            callback=lambda ws, handle:
                self.feed(ws, handle, starts, sizes),
            no_grad=True,
            check_device=False,
        )


class Cast(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Cast, self).__init__(key, dev, **kwargs)
        self.dtype = kwargs.get('dtype', 'float32')

    def attributes(self):
        return {
            'op_type': 'Cast',
            'arguments': {
                'dtype': self.dtype,
            },
        }

    def forward(self, input, inplace=False):
        if input.dtype == self.dtype:
            return input
        if inplace:
            return self.dispatch([], [input], no_grad=True)
        return self.dispatch([input], [self.alloc()])


class ChannelNormalize(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(ChannelNormalize, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', -1)
        self.ndim = kwargs.get('ndim', 0)
        self.mean = kwargs.get('mean', None)
        self.std = kwargs.get('std', None)
        self.dtype = kwargs.get('dtype', 'float32')

    def attributes(self):
        return {
            'op_type': 'ChannelNormalize',
            'arguments': {
                'axis': self.axis,
                'mean': self.mean,
                'std': self.std,
                'dtype': self.dtype,
                'perm_descs': [
                    '${{HANDLE}}/perm[{}]'
                    .format(n) for n in range(self.ndim)
                ],
            }
        }

    def feed(self, ws, handle, perm):
        for i in range(self.ndim):
            self.feed_arg(
                ws,
                '{}/perm[{}]'.format(handle, i),
                perm[i], 'int64',
            )

    def forward(self, input, perm):
        return self.dispatch(
            [input], [self.alloc()],
            callback=lambda ws, handle:
                self.feed(ws, handle, perm),
        )


class ChannelShuffle(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(ChannelShuffle, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', 0)
        self.group = kwargs.get('group', 1)

    def attributes(self):
        return {
            'op_type': 'ChannelShuffle',
            'arguments': {
                'axis': self.axis,
                'group': self.group,
            },
        }

    def forward(self, input, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input], [out])


class Concat(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Concat, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', 0)

    def attributes(self):
        return {
            'op_type': 'Concat',
            'arguments': {
                'axis': self.axis,
            },
        }

    def forward(self, seq, out=None):
        out = out if out else self.alloc()
        return self.dispatch(seq, [out])


class Cumulative(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Cumulative, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', 0)
        self.exclusive = kwargs.get('exclusive', False)
        self.reverse = kwargs.get('reverse', False)
        self.operation = kwargs.get('operation', 'Sum')

    def attributes(self):
        return {
            'op_type': 'Cum' + self.operation,
            'arguments': {
                'axis': self.axis,
                'exclusive': self.exclusive,
                'reverse': self.reverse,
            }
        }

    def forward(self, input, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input], [out])


class Expand(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Expand, self).__init__(key, dev, **kwargs)
        self.ndim = kwargs.get('ndim', 0)

    def attributes(self):
        return {
            'op_type': 'Expand',
            'arguments': {
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'
                    .format(n) for n in range(self.ndim)
                ],
            },
        }

    def feed(self, ws, handle, times):
        for i in range(self.ndim):
            self.feed_arg(
                ws,
                '{}/dims[{}]'.format(handle, i),
                times[i], 'int64',
            )

    def forward(self, input, dims):
        return self.dispatch(
            [input], [self.alloc()],
            callback=lambda ws, handle:
                self.feed(ws, handle, dims),
        )


class IndexSelect(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(IndexSelect, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', 0)
        self.num_axes = kwargs.get('num_axes', 1)

    def attributes(self):
        return {
            'op_type': 'IndexSelect',
            'arguments': {
                'axis': self.axis,
                'num_axes': self.num_axes,
            },
        }

    def forward(self, input, indices, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input, indices], [out])


class MaskedAssign(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(MaskedAssign, self).__init__(key, dev, **kwargs)

    def attributes(self):
        return {'op_type': 'MaskedAssign', 'arguments': {}}

    def forward(self, out, mask, input):
        return self.dispatch([input, mask], [out])


class MaskedSelect(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(MaskedSelect, self).__init__(key, dev, **kwargs)

    def attributes(self):
        return {'op_type': 'MaskedSelect', 'arguments': {}}

    def forward(self, input, mask, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input, mask], [out])


class Multinomial(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Multinomial, self).__init__(key, dev, **kwargs)
        self.eps = kwargs.get('eps', 0.)
        self.num_samples = kwargs.get('num_samples', 1)

    def attributes(self):
        return {
            'op_type': 'Multinomial',
            'arguments': {
                'eps': self.eps,
                'normalize': False,
                'num_samples': self.num_samples,
            },
        }

    def forward(self, input, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input], [out], no_grad=True)


class NonZero(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(NonZero, self).__init__(key, dev, **kwargs)

    def attributes(self):
        return {'op_type': 'NonZero', 'arguments': {}}

    def forward(self, input, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input], [out], no_grad=True)


class OneHot(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(OneHot, self).__init__(key, dev, **kwargs)
        self.depth = kwargs.get('depth', 1)

    def attributes(self):
        return {
            'op_type': 'OneHot',
            'arguments': {
                'depth': self.depth,
            },
        }

    def forward(self, input):
        return self.dispatch([input], [self.alloc()], no_grad=True)


class Reduce(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Reduce, self).__init__(key, dev, **kwargs)
        self.axes = kwargs.get('axes', None)
        self.keep_dims = kwargs.get('keep_dims', True)
        self.operation = kwargs.get('operation', 'Sum')

    def attributes(self):
        return {
            'op_type': 'Reduce' + self.operation,
            'arguments': {
                'axes': self.axes,
                'keep_dims': self.keep_dims,
            },
        }

    def forward(self, input, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input], [out])


class Reshape(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Reshape, self).__init__(key, dev, **kwargs)
        self.ndim = kwargs.get('ndim', 0)

    def attributes(self):
        return {
            'op_type': 'Reshape',
            'arguments': {
                'dims_descs': [
                    '${{HANDLE}}/dims[{}]'
                    .format(n) for n in range(self.ndim)
                ],
            },
        }

    def feed(self, ws, handle, shape):
        for i in range(self.ndim):
            self.feed_arg(
                ws,
                '{}/dims[{}]'.format(handle, i),
                shape[i], 'int64',
            )

    def forward(self, input, shape, out=None):
        out = out if out else self.alloc()
        return self.dispatch(
            [input], [out],
            callback=lambda ws, handle:
                self.feed(ws, handle, shape),
        )


class Slice(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Slice, self).__init__(key, dev, **kwargs)
        self.ndim = kwargs.get('ndim', 0)

    def attributes(self):
        return {
            'op_type': 'Slice',
            'arguments': {
                'starts_descs': [
                    '${{HANDLE}}/starts[{}]'
                    .format(n) for n in range(self.ndim)
                ],
                'sizes_descs': [
                    '${{HANDLE}}/sizes[{}]'
                    .format(n) for n in range(self.ndim)
                ],
            },
        }

    def feed(self, ws, handle, starts, sizes):
        for i in range(self.ndim):
            self.feed_arg(
                ws,
                '{}/starts[{}]'.format(handle, i),
                starts[i], 'int64',
            )
            self.feed_arg(
                ws,
                '{}/sizes[{}]'.format(handle, i),
                sizes[i], 'int64',
            )

    def forward(self, input, starts, sizes):
        return self.dispatch(
            [input], [self.alloc()],
            callback=lambda ws, handle:
                self.feed(ws, handle, starts, sizes)
        )


class Split(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Split, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', 0)
        self.size_splits = kwargs.get('size_splits', None)

    def attributes(self):
        return {
            'op_type': 'Split',
            'arguments': {
                'axis': self.axis,
                'size_splits': self.size_splits,
            },
        }

    def forward(self, input, chunks):
        outs = [self.alloc() for _ in range(chunks)]
        return self.dispatch([input], outs)


class Stack(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Stack, self).__init__(key, dev, **kwargs)
        self.axis = kwargs.get('axis', 0)

    def attributes(self):
        return {
            'op_type': 'Stack',
            'arguments': {
                'axis': self.axis,
            },
        }

    def forward(self, seq, out=None):
        out = out if out else self.alloc()
        return self.dispatch(seq, [out])


class Squeeze(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Squeeze, self).__init__(key, dev, **kwargs)
        self.axes = kwargs.get('axes', None)

    def attributes(self):
        return {
            'op_type': 'Squeeze',
            'arguments': {
                'axes': self.axes,
            },
        }

    def forward(self, input, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input], [out])


class Tile(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Tile, self).__init__(key, dev, **kwargs)
        self.ndim = kwargs.get('ndim', 0)

    def attributes(self):
        return {
            'op_type': 'Tile',
            'arguments': {
                'multiples_descs': [
                    '${{HANDLE}}/multiples[{}]'
                    .format(n) for n in range(self.ndim)
                ],
            },
        }

    def feed(self, ws, handle, times):
        for i in range(self.ndim):
            self.feed_arg(
                ws,
                '{}/multiples[{}]'.format(handle, i),
                times[i], 'int64',
            )

    def forward(self, input, times):
        return self.dispatch(
            [input], [self.alloc()],
            callback=lambda ws, handle:
                self.feed(ws, handle, times),
        )


class Transpose(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Transpose, self).__init__(key, dev, **kwargs)
        self.ndim = kwargs.get('ndim', 0)

    def attributes(self):
        return {
            'op_type': 'Transpose',
            'arguments': {
                'perm_descs': [
                    '${{HANDLE}}/perm[{}]'
                    .format(n) for n in range(self.ndim)
                ],
            },
        }

    def feed(self, ws, handle, perm):
        for i in range(self.ndim):
            self.feed_arg(
                ws,
                '{}/perm[{}]'.format(handle, i),
                perm[i], 'int64',
            )

    def forward(self, input, perm):
        return self.dispatch(
            [input], [self.alloc()],
            callback=lambda ws, handle:
                self.feed(ws, handle, perm),
        )


class UnSqueeze(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(UnSqueeze, self).__init__(key, dev, **kwargs)
        self.axes = kwargs.get('axes', None)

    def attributes(self):
        return {
            'op_type': 'ExpandDims',
            'arguments': {
                'axes': self.axes,
            },
        }

    def forward(self, input, out=None):
        out = out if out else self.alloc()
        return self.dispatch([input], [out])


class Where(function.Function):
    def __init__(self, key, dev, **kwargs):
        super(Where, self).__init__(key, dev, **kwargs)

    def attributes(self):
        return {'op_type': 'Where', 'arguments': {}}

    def forward(self, condition, x, y):
        return self.dispatch([x, y, condition], [self.alloc()])