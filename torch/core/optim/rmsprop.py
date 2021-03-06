# ------------------------------------------------------------
# Copyright (c) 2017-present, SeetaTech, Co.,Ltd.
#
# Licensed under the BSD 2-Clause License.
# You should have received a copy of the BSD 2-Clause License
# along with the software. If not, See,
#
#     <https://opensource.org/licenses/BSD-2-Clause>
#
# Codes are based on:
#
#     <https://github.com/pytorch/pytorch/blob/master/torch/optim/rmsprop.py>
#
# ------------------------------------------------------------
"""RMSprop optimizers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections

from dragon.vm.torch.core.optim.optimizer import Optimizer


class RMSprop(Optimizer):
    r"""The optimizer to apply RMSprop algorithm.
    `[Hinton et.al, 2013] <http://www.cs.utoronto.ca/~bonner/courses/2016s/csc321/lectures/lec6.pdf>`_.

    The **RMSprop** update is defined as:

    .. math::
        \text{RMSprop}(g) = -m_{t} \\
            \quad \\ \text{where}\quad
                \begin{cases}
                    v_{t} = \alpha * v_{t-1} + (1 - \alpha) * g^{2} \\
                    m_{t} = \text{momentum} * m_{t-1} +
                            \frac{\text{lr} * g}{\sqrt{v_{t}} + \epsilon}
                \end{cases}

    """

    def __init__(
        self,
        params,
        lr=1e-2,
        alpha=0.99,
        eps=1e-8,
        weight_decay=0,
        momentum=0,
        centered=False,
        scale=1,
        clip_norm=0,
    ):
        r"""Create a ``RMSprop`` optimizer.

        Parameters
        ----------
        params : Sequence[dragon.vm.torch.nn.Parameter]
            The parameters to optimize.
        lr : float, required
            The initial value to :math:`\text{lr}`.
        alpha : float, optional, default=0.99
            The initial value to :math:`\alpha`.
        eps : float, optional, default=1e-7
            The initial value to :math:`\epsilon`.
        weight_decay : float, optional, default=0
            The L2 penalty factor to weight.
        momentum : float, optional, default=0
            The initial value to :math:`\text{momentum}`.
        scale : float, optional, default=1
            The scaling factor to gradient.
        clip_norm : float, optional, default=0
            The maximum L2 norm to clip gradient.

        """
        if not 0. <= lr:
            raise ValueError("Invalid learning rate: {}".format(lr))
        if not 0. <= eps:
            raise ValueError("Invalid epsilon value: {}".format(eps))
        if momentum < 0.:
            raise ValueError("Invalid momentum value: {}".format(momentum))
        if not 0. <= alpha:
            raise ValueError("Invalid alpha value: {}".format(alpha))
        defaults = dict(lr=lr, momentum=momentum, alpha=alpha,
                        eps=eps, centered=centered, weight_decay=weight_decay,
                        scale=scale, clip_norm=clip_norm)
        super(RMSprop, self).__init__(params, defaults)
        self._hyper = {
            'lr': ('lr', collections.defaultdict(str)),
            'momentum': ('momentum', collections.defaultdict(str)),
            'alpha': ('decay', collections.defaultdict(str)),
            'eps': ('eps', collections.defaultdict(str)),
            'weight_decay': ('weight_decay', collections.defaultdict(str)),
            'scale': ('scale', collections.defaultdict(str)),
            'clip_norm': ('clip_norm', collections.defaultdict(str)),
        }
