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
"""BatchNorm modules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import inspect

from dragon.core import distributed
from dragon.vm.torch.core.nn import functional as F
from dragon.vm.torch.core.nn.modules.module import Module
from dragon.vm.torch.core.nn.parameter import Parameter
from dragon.vm.torch.core.ops.init import functional as init_funcs
from dragon.vm.torch.core.tensor import Tensor


class _BatchNorm(Module):
    def __init__(
        self,
        num_features,
        eps=1e-5,
        momentum=0.1,
        affine=True,
        track_running_stats=True,
    ):
        """
        Initialize the device.

        Args:
            self: (todo): write your description
            num_features: (int): write your description
            eps: (float): write your description
            momentum: (array): write your description
            affine: (array): write your description
            track_running_stats: (todo): write your description
        """
        super(_BatchNorm, self).__init__()
        self.num_features = num_features
        self.eps = eps
        self.momentum = momentum
        self.affine = affine
        self.track_running_stats = track_running_stats
        if self.affine:
            self.weight = Parameter(Tensor(num_features))
            self.bias = Parameter(Tensor(num_features))
        else:
            self.register_buffer('weight', init_funcs.ones(num_features))
            self.register_buffer('bias', init_funcs.zeros(num_features))
        self.register_buffer('running_mean', init_funcs.zeros(num_features))
        self.register_buffer('running_var', init_funcs.ones(num_features))
        self.inputs = [self.running_mean, self.running_var, self.weight, self.bias]
        self.reset_parameters()

    def reset_parameters(self):
        """
        Reset hyperparameter parameters.

        Args:
            self: (todo): write your description
        """
        if self.affine:
            self.weight.data.one_()
            self.bias.data.zero_()

    def reset_running_stats(self):
        """
        Reset the statistics statistics.

        Args:
            self: (todo): write your description
        """
        if self.track_running_stats:
            self.running_mean.zero_()
            self.running_var.fill_(1)

    def extra_repr(self):
        """
        Return a human - readable representation.

        Args:
            self: (todo): write your description
        """
        return '{num_features}, ' \
               'eps={eps}, ' \
               'momentum={momentum}, ' \
               'affine={affine}, ' \
               'track_running_stats={track_running_stats}' \
               .format(**self.__dict__)

    def forward(self, input):
        """
        Forward computation.

        Args:
            self: (todo): write your description
            input: (todo): write your description
        """
        return F.batch_norm(
            input, *self.inputs,
            training=self.training,
            momentum=self.momentum,
            eps=self.eps
        )

    def _apply(self, fn):
        """
        Apply fn to fn.

        Args:
            self: (todo): write your description
            fn: (array): write your description
        """
        lambda_source = inspect.getsource(fn)
        if 'half_()' in lambda_source:
            return self  # Float32 parameters are required.
        return super(_BatchNorm, self)._apply(fn)


class BatchNorm1d(_BatchNorm):
    r"""Apply the batch normalization over 2d input.
    `[Ioffe & Szegedy, 2015] <https://arxiv.org/abs/1502.03167>`_.

    The normalization is defined as:

    .. math:: y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The running average of statistics are calculated as:

    .. math:: x_{\text{running}} = (1 - \text{momentum}) * x_{\text{running}} + \text{momentum} * x_{\text{stat}}

    See Also
    --------
    `torch.nn.functional.batch_norm(...)`_

    """

    def __init__(
        self,
        num_features,
        eps=1e-5,
        momentum=0.1,
        affine=True,
        track_running_stats=True,
    ):
        """Create a ``BatchNorm1d`` module.

        Parameters
        ----------
        num_features : int
            The number of channels.
        eps : float, optional, default=1e-5
            The epsilon value.
        momentum : float, optional, default=0.1
            The momentum of moving average.
        affine : bool, optional, default=True
            **True** to apply a affine transformation.
        track_running_stats : bool, optional, default=True
            **True** to using stats when switching to ``eval``.

        """
        super(BatchNorm1d, self).__init__(
            num_features,
            eps, momentum,
            affine, track_running_stats,
        )


class BatchNorm2d(_BatchNorm):
    r"""Apply the batch normalization over 3d input.
    `[Ioffe & Szegedy, 2015] <https://arxiv.org/abs/1502.03167>`_.

    The normalization is defined as:

    .. math:: y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The running average of statistics are calculated as:

    .. math:: x_{\text{running}} = (1 - \text{momentum}) * x_{\text{running}} + \text{momentum} * x_{\text{stat}}

    See Also
    --------
    `torch.nn.functional.batch_norm(...)`_

    """

    def __init__(
        self,
        num_features,
        eps=1e-5,
        momentum=0.1,
        affine=True,
        track_running_stats=True,
    ):
        """Create a ``BatchNorm2d`` module.

        Parameters
        ----------
        num_features : int
            The number of channels.
        eps : float, optional, default=1e-5
            The epsilon value.
        momentum : float, optional, default=0.1
            The momentum of moving average.
        affine : bool, optional, default=True
            **True** to apply a affine transformation.
        track_running_stats : bool, optional, default=True
            **True** to using stats when switching to ``eval``.

        """
        super(BatchNorm2d, self).__init__(
            num_features,
            eps, momentum,
            affine, track_running_stats,
        )


class BatchNorm3d(_BatchNorm):
    r"""Apply the batch normalization over 4d input.
    `[Ioffe & Szegedy, 2015] <https://arxiv.org/abs/1502.03167>`_.

    The normalization is defined as:

    .. math:: y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The running average of statistics are calculated as:

    .. math:: x_{\text{running}} = (1 - \text{momentum}) * x_{\text{running}} + \text{momentum} * x_{\text{stat}}

    See Also
    --------
    `torch.nn.functional.batch_norm(...)`_

    """

    def __init__(
        self,
        num_features,
        eps=1e-5,
        momentum=0.1,
        affine=True,
        track_running_stats=True,
    ):
        """Create a ``BatchNorm3d`` module.

        Parameters
        ----------
        num_features : int
            The number of channels.
        eps : float, optional, default=1e-5
            The epsilon value.
        momentum : float, optional, default=0.1
            The momentum of moving average.
        affine : bool, optional, default=True
            **True** to apply a affine transformation.
        track_running_stats : bool, optional, default=True
            **True** to using stats when switching to ``eval``.

        """
        super(BatchNorm3d, self).__init__(
            num_features,
            eps, momentum,
            affine, track_running_stats,
        )


class SyncBatchNorm(_BatchNorm):
    r"""Apply the sync batch normalization over input.
    `[Ioffe & Szegedy, 2015] <https://arxiv.org/abs/1502.03167>`_.

    The normalization is defined as:

    .. math:: y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The running average of statistics are calculated as:

    .. math:: x_{\text{running}} = (1 - \text{momentum}) * x_{\text{running}} + \text{momentum} * x_{\text{stat}}

    Additionally, specify ``process_group`` to perform synchronization.

    If not, value returning from ``dragon.distributed.get_group(...)`` will be used.

    See Also
    --------
    `torch.nn.functional.batch_norm(...)`_

    """

    def __init__(
        self,
        num_features,
        eps=1e-5,
        momentum=0.1,
        affine=True,
        track_running_stats=True,
        process_group=None,
    ):
        """Create a ``SyncBatchNorm`` module.

        Parameters
        ----------
        num_features : int
            The number of channels.
        eps : float, optional, default=1e-5
            The epsilon value.
        momentum : float, optional, default=0.1
            The momentum of moving average.
        affine : bool, optional, default=True
            **True** to apply a affine transformation.
        track_running_stats : bool, optional, default=True
            **True** to using stats when switching to ``eval``.
        process_group : ProcessGroup, optional
            The group for communication.

        """
        super(SyncBatchNorm, self).__init__(
            num_features, eps, momentum,
            affine, track_running_stats,
        )
        if process_group is None:
            process_group = distributed.get_group()
        self.process_group = process_group

    def forward(self, input):
        """
        Forward computation.

        Args:
            self: (todo): write your description
            input: (todo): write your description
        """
        if self.training:
            return F.sync_batch_norm(
                input, *self.inputs,
                training=self.training,
                momentum=self.momentum,
                eps=self.eps,
                process_group=self.process_group
            )
        else:
            return F.batch_norm(
                input, *self.inputs,
                training=self.training,
                momentum=self.momentum,
                eps=self.eps
            )
