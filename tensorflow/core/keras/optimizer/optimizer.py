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

from dragon.core.eager import context as eager_context
from dragon.core.framework import context
from dragon.core.framework import types
from dragon.core.framework import workspace
from dragon.core.training import optimizer as optimizer_v1
from dragon.core.util import six
from dragon.vm.tensorflow.core.framework import dtypes
from dragon.vm.tensorflow.core.keras import initializers
from dragon.vm.tensorflow.core.keras.utils import generic_utils
from dragon.vm.tensorflow.core.ops import variables


class Optimizer(optimizer_v1.Optimizer):
    """The base class for optimizers."""

    BASE_WEIGHT_DECAY = 0.0001

    def __init__(self, name=None, **kwargs):
        """Create a ``Optimizer``.

        Parameters
        ----------
        name : str, optional
            The optional optimizer name.

        """
        self._init_set_name(name)
        super(Optimizer, self).__init__(
            name=self._name,
            weight_decay=self.BASE_WEIGHT_DECAY,
        )
        allowed_kwargs = {'scale', 'clipnorm', 'lr'}
        for k in kwargs:
            if k not in allowed_kwargs:
                raise TypeError('Unexpected keyword argument: ' + str(k))
            if kwargs[k] < 0:
                raise ValueError("Expected {} >= 0, received: {}".format(k, kwargs[k]))

        self._hyper = {}
        self._alias = {}
        self._weights = []
        self._iterations = 0

        # Register the common hyper parameters.
        if 'scale' in kwargs:
            self._defaults['scale'] = kwargs.pop('scale')
        if 'clipnorm' in kwargs:
            self._defaults['clip_norm'] = kwargs.pop('clipnorm')
        for k, v in self._defaults.items():
            self._set_hyper(k, v, k)
        self._hypers_created = False

    @property
    def iterations(self):
        """Return the number of steps has run.

        Returns
        -------
        int
            The iterations.

        """
        return self._iterations

    @iterations.setter
    def iterations(self, variable):
        """
        Iterate over all variables.

        Args:
            self: (todo): write your description
            variable: (todo): write your description
        """
        self._iterations = variable

    def apply_gradients(self, grads_and_vars):
        """Apply the gradients to update variables.

        Parameters
        ----------
        grads_and_vars : Sequence[Sequence[dragon.Tensor]]
            The gradients and variables.

        Returns
        -------
        dragon.vm.tensorflow.keras.optimizers.Optimizer
            The self to generate the update operations.

        """
        # Create the hyper parameters if necessary.
        with context.name_scope(self._name):
            self._create_hypers()

        # Apply one-step update.
        if eager_context.executing_eagerly():
            # Filter value whose grad is missing.
            for g, v in grads_and_vars:
                if g is not None:
                    decay_mult = 0.
                    regularizer = getattr(v, '_regularizer', None)
                    if regularizer is not None:
                        decay_mult = regularizer.l2 / self.BASE_WEIGHT_DECAY
                    self._run_update(v, g, decay_mult=decay_mult)
        else:
            # Store for the lazy compilation.
            for g, v in grads_and_vars:
                decay_mult = 0.
                regularizer = getattr(v, '_regularizer', None)
                if regularizer is not None:
                    decay_mult = regularizer.l2 / self.BASE_WEIGHT_DECAY
                self._add_update(v, g, decay_mult=decay_mult)

        # Increase the iterations.
        self._iterations += 1
        return self

    def _create_hypers(self):
        """
        Create all accuracy for all hypergraph.

        Args:
            self: (todo): write your description
        """
        if self._hypers_created:
            return
        current_ws = workspace.get_workspace()
        for name, value in sorted(self._hyper.items()):
            if types.is_tensor(value) or callable(value):
                pass
            else:
                self._hyper[name] = \
                    self._create_weight(
                        name,
                        shape=[],
                        dtype=dtypes.float32,
                        trainable=False,
                        initializer=value)
            hyper = self._hyper[name]
            alias = self._alias.get(name, None)
            if alias is not None:
                current_ws.register_alias(hyper, alias)
        self._hypers_created = True

    @staticmethod
    def _create_weight(
        name,
        shape,
        dtype=None,
        initializer='zeros',
        trainable=None,
    ):
        """
        Create a weight function.

        Args:
            name: (str): write your description
            shape: (list): write your description
            dtype: (str): write your description
            initializer: (todo): write your description
            trainable: (str): write your description
        """
        if isinstance(initializer, six.string_types) or callable(initializer):
            initializer = initializers.get(initializer)

        return variables.get_variable(
            name=name,
            shape=shape,
            initializer=initializer,
            dtype=dtype if dtype is not None else dtypes.float32,
            trainable=trainable if trainable is not None else True,
            use_resource=True,
        )

    def _get_hyper(self, name):
        """Return the specific hyper parameter."""
        if not self._hypers_created:
            self._create_hypers()
        return float(self._hyper[name].numpy(True))

    def _init_set_name(self, name, zero_based=True):
        """Set a name for sharing weights."""
        if not name:
            self._name = workspace.get_workspace().unique_name(
                name=generic_utils.to_snake_case(
                    self.__class__.__name__),
                namespace='Object',
                zero_based=zero_based,
            )
        else:
            self._name = name

    def _set_hyper(self, name, value, alias=None):
        """Set the specific hyper parameter."""
        if name not in self._hyper:
            self._hyper[name] = value
        else:
            if types.is_tensor(self._hyper[name]):
                workspace.get_workspace().feed_tensor(
                    self._hyper[name].id,
                    value,
                    dtype='float32',
                    enforce_cpu=True,
                )
            else:
                self._hyper[name] = value
        if alias and name not in self._alias:
            self._alias[name] = '/share/hyper/%s/%s' % (self._op_handle, alias)

    def __getattr__(self, item):
        """
        Returns the value of an attribute.

        Args:
            self: (todo): write your description
            item: (str): write your description
        """
        if item == 'lr':
            item = 'learning_rate'
        hyper = self.__dict__.get('_hyper')
        if hyper and item in hyper:
            return self._get_hyper(item)
        return self.__dict__[item]

    def __setattr__(self, key, value):
        """
        Sets a hyperparameter attribute.

        Args:
            self: (todo): write your description
            key: (str): write your description
            value: (todo): write your description
        """
        if key == 'lr':
            key = 'learning_rate'
        hyper = self.__dict__.get('_hyper')
        if hyper and key in hyper:
            self._set_hyper(key, value)
        else:
            object.__setattr__(self, key, value)
