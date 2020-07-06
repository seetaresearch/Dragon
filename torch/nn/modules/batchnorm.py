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

import inspect

from dragon.core import distributed
from dragon.vm.torch.nn import functional as F
from dragon.vm.torch.nn.modules.module import Module
from dragon.vm.torch.nn.parameter import Parameter
from dragon.vm.torch.ops.init import functional as init
from dragon.vm.torch.tensor import Tensor


class _BatchNorm(Module):
    def __init__(
        self,
        num_features,
        eps=1e-5,
        momentum=0.1,
        affine=True,
        track_running_stats=True,
    ):
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
            self.register_buffer('weight', init.ones(num_features))
            self.register_buffer('bias', init.zeros(num_features))
        self.register_buffer('running_mean', init.zeros(num_features))
        self.register_buffer('running_var', init.ones(num_features))
        self.inputs = [self.running_mean, self.running_var,
                       self.weight, self.bias]
        self.reset_parameters()

    def reset_parameters(self):
        if self.affine:
            self.weight.data.one_()
            self.bias.data.zero_()

    def extra_repr(self):
        return '{num_features}, eps={eps}, momentum={momentum}, affine={affine}, ' \
               'track_running_stats={track_running_stats}'.format(**self.__dict__)

    def forward(self, input):
        training = self.training or \
            not self.track_running_stats
        return F.batch_norm(
            input, *self.inputs,
            training=training,
            momentum=self.momentum,
            eps=self.eps
        )

    def _apply(self, fn):
        lambda_source = inspect.getsource(fn)
        if 'half_()' in lambda_source:
            # Float32 parameters are required.
            return
        return super(_BatchNorm, self)._apply(fn)


class BatchNorm1d(_BatchNorm):
    r"""Apply the batch normalization over 2d input.
    `[Ioffe & Szegedy, 2015] <https://arxiv.org/abs/1502.03167>`_.

    The normalization is defined as:

    .. math::
        y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The moving average of stats are calculated as:

    .. math::
        x_{moving} \leftarrow (1 - momentum) * x_{moving} + momentum * x_{stat}

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

    .. math::
        y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The moving average of stats are calculated as:

    .. math::
        x_{moving} \leftarrow (1 - momentum) * x_{moving} + momentum * x_{stat}

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

    .. math::
        y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The moving average of stats are calculated as:

    .. math::
        x_{moving} \leftarrow (1 - momentum) * x_{moving} + momentum * x_{stat}

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

    .. math::
        y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} * \gamma + \beta

    The moving average of stats are calculated as:

    .. math::
        x_{moving} \leftarrow (1 - momentum) * x_{moving} + momentum * x_{stat}

    Additionally, you can specify ``process_group`` to perform synchronization.

    If not, value returning from ``dragon.distributed.get_group(...)`` will be used.

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
        training = self.training or \
            not self.track_running_stats
        if training:
            return F.sync_batch_norm(
                input, *self.inputs,
                training=training,
                momentum=self.momentum,
                eps=self.eps,
                process_group=self.process_group
            )
        else:
            return F.batch_norm(
                input, *self.inputs,
                training=training,
                momentum=self.momentum,
                eps=self.eps
            )