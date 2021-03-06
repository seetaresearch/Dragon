# ------------------------------------------------------------
# Copyright (c) 2017-present, SeetaTech, Co.,Ltd.
# Copyright (c) 2016-2018, The TensorLayer contributors.
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

from dragon.core.ops import math_ops
from dragon.vm.tensorlayer.core.engine import layer


class Dense(layer.Layer):
    r"""Fully connected layer.

    Examples:

    ```python
    # Define and call a dense layer with the input
    input = tl.layers.Input([100, 50])
    output = tl.layers.Dense(n_units=800)(input)
    ```

    """

    def __init__(
        self,
        n_units,
        act=None,
        W_init='glorot_uniform',
        b_init='zeros',
        in_channels=None,
        name=None,
    ):
        """Create a ``Dense`` layer.

        Parameters
        ----------
        n_units : int, required
            The number of output units.
        act : callable, optional
            The optional activation function.
        W_init : Union[callable, str], optional
            The initializer for weight matrix.
        b_init : Union[callable, str], optional
            The initializer for bias vector.
        in_channels : int, optional
            The number of input units.
        name : str, optional
            The layer name.

        """
        super(Dense, self).__init__(name, act=act)
        self.n_units = n_units
        self.act = act
        self.W_init = W_init
        self.b_init = b_init
        self.in_channels = in_channels
        self.W = None
        self.b = None
        if self.in_channels is not None:
            self.build((None, None))
            self._built = True

    def __repr__(self):
        act_str = self.act.__name__ if self.act is not None else 'No Activation'
        s = ('{classname}(n_units={n_units}, ' + act_str)
        if self.in_channels is not None:
            s += ', in_channels=\'{in_channels}\''
        if self.name is not None:
            s += ', name=\'{name}\''
        s += ')'
        return s.format(classname=self.__class__.__name__, **self.__dict__)

    def build(self, inputs_shape):
        if self.in_channels is None and len(inputs_shape) != 2:
            raise AssertionError('The input dimension must be rank 2.'
                                 'Please reshape or flatten it.')
        if self.in_channels:
            shape = [self.in_channels, self.n_units]
        else:
            self.in_channels = inputs_shape[1]
            shape = [inputs_shape[1], self.n_units]
        self.W = self.add_weight('weights', shape, init=self.W_init)
        if self.b_init:
            self.b = self.add_weight('biases', [self.n_units], init=self.b_init)

    def forward(self, inputs):
        outputs = math_ops.gemm(
            [inputs, self.W] + ([self.b] if self.b_init else []))
        if self.act:
            outputs = self.act(outputs)
        return outputs
