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
"""Affine modules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dragon.vm.torch.core.nn import functional as F
from dragon.vm.torch.core.nn.modules.module import Module
from dragon.vm.torch.core.nn.parameter import Parameter
from dragon.vm.torch.core.ops.init import functional as init


class Affine(Module):
    r"""Apply the affine transformation.

    .. math:: y = Ax + b

    This transform is often taken as a post-processing of normalization.

    Examples:

    ```python
    m = torch.nn.Affine(5)

    # Apply a 2d transformation
    x2d = torch.ones(3, 5)
    y2d = m(x2d)

    # Apply a 3d transformation
    x3d = torch.ones(3, 5, 4)
    y3d = m(x3d)

    # Apply a 4d transformation
    x4d = torch.ones(3, 5, 2, 2)
    y4d = m(x4d)
    ```

    See Also
    --------
    `torch.nn.functional.affine(...)`_

    """

    def __init__(
        self,
        num_features,
        bias=True,
        fix_weight=False,
        fix_bias=False,
        inplace=False,
    ):
        """Create an ``Affine`` module.

        Parameters
        ----------
        num_features : int
            The number of channels.
        bias : bool, optional, default=True
            **True** to attach a bias.
        fix_weight : bool, optional, default=False
            **True** to frozen the ``weight``.
        fix_bias : bool, optional, default=False
            **True** to frozen the ``bias``.
        inplace : bool, optional, default=False
            Whether to do the operation in-place.

        """
        super(Affine, self).__init__()
        self.num_features = num_features
        self.inplace = inplace
        if not fix_weight:
            self.weight = Parameter(init.ones(num_features))
            if inplace:
                raise ValueError('In-place operation requires fixed weight.')
        else:
            self.register_buffer('weight', init.ones(num_features))
        if bias:
            if not fix_bias:
                self.bias = Parameter(init.zeros(num_features))
            else:
                self.register_buffer('bias', init.zeros(num_features))
        else:
            self.bias = None

    def extra_repr(self):
        """
        Return a string representation of - style.

        Args:
            self: (todo): write your description
        """
        s = '{num_features}, ' \
            'inplace={inplace}'.format(**self.__dict__)
        if self.bias is None:
            s += ', bias=False'
        return s

    def forward(self, input):
        """
        Forward computation

        Args:
            self: (todo): write your description
            input: (todo): write your description
        """
        return F.affine(input, self.weight, self.bias)
