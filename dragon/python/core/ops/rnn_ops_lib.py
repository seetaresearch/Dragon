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
"""RNN ops library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dragon.core.framework.ops import Operator


class LSTMCell(Operator):
    """LSTMCell operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(LSTMCell, self).__init__(key, dev, **kwargs)

    def attributes(self):
        """
        A dict of attributes.

        Args:
            self: (todo): write your description
        """
        return {'op_type': 'LSTMCell', 'arguments': {}}

    def forward(self, inputs):
        """
        Calculate the forward computation.

        Args:
            self: (todo): write your description
            inputs: (todo): write your description
        """
        outputs = [self.alloc() for _ in range(2)]
        return self.dispatch(inputs, outputs)


class Recurrent(Operator):
    """Recurrent operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize the device initialization.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(Recurrent, self).__init__(key, dev, **kwargs)
        self.mode = kwargs.get('mode', 'rnn_tanh')
        self.num_layers = kwargs.get('num_layers', 1)
        self.hidden_size = kwargs.get('hidden_size', 0)
        self.bidirectional = kwargs.get('bidirectional', False)
        self.dropout_ratio = kwargs.get('dropout_ratio', 0.)
        self.is_training = kwargs.get('is_training', False)

    def attributes(self):
        """
        Returns a dict of attributes of the attribute

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'Recurrent',
            'arguments': {
                'rnn_mode': self.mode,
                'num_layers': self.num_layers,
                'hidden_size': self.hidden_size,
                'bidirectional': self.bidirectional,
                'rnn_input_mode': 'linear',
                'dropout_ratio': self.dropout_ratio,
                'phase': 'TRAIN' if self.is_training else 'TEST'
            }
        }

    def forward(self, inputs):
        """
        Parse the model.

        Args:
            self: (todo): write your description
            inputs: (todo): write your description
        """
        return self.dispatch(inputs, [self.alloc()])


class RNNParamSet(Operator):
    """RNNParamSet operator."""

    def __init__(self, key, dev, **kwargs):
        """
        Initialize layer.

        Args:
            self: (todo): write your description
            key: (str): write your description
            dev: (todo): write your description
        """
        super(RNNParamSet, self).__init__(key, dev, **kwargs)
        self.param_type = kwargs.get('param_type', 'matrix')
        self.num_layers = kwargs.get('num_layers', 1)
        self.num_directions = kwargs.get('num_directions', 1)
        self.input_size = kwargs.get('input_size', 0)
        self.hidden_size = kwargs.get('hidden_size', 0)
        self.layer_id = kwargs.get('layer_id', 0)
        self.param_id = kwargs.get('param_id', 0)
        self.mode = kwargs.get('mode', 'rnn_tanh')

    def attributes(self):
        """
        A dict of layers.

        Args:
            self: (todo): write your description
        """
        return {
            'op_type': 'RNNParamSet',
            'arguments': {
                'param_type': self.param_type,
                'num_layers': self.num_layers,
                'num_directions': self.num_directions,
                'input_size': self.input_size,
                'hidden_size': self.hidden_size,
                'layer_id': self.layer_id,
                'param_id': self.param_id,
                'rnn_mode': self.mode,
            }
        }

    def forward(self, inputs):
        """
        Perform a forward.

        Args:
            self: (todo): write your description
            inputs: (todo): write your description
        """
        return self.dispatch([inputs[1]], [inputs[0]], no_grad=True)
