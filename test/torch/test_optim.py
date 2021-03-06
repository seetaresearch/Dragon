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
"""Test the optim module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from dragon.core.testing.unittest.common_utils import run_tests
from dragon.vm import torch


class TestOptimizer(unittest.TestCase):
    """Test the optimizer class."""

    def test_optimizer(self):
        buffer = torch.ones(1)
        weight = torch.ones(1, requires_grad=True)
        try:
            optimizer = torch.optim.Optimizer(weight, {})
        except TypeError:
            pass
        try:
            optimizer = torch.optim.Optimizer([], {})
        except ValueError:
            pass
        optimizer = torch.optim.Optimizer([weight], {})
        try:
            optimizer.add_param_group([weight])
        except TypeError:
            pass
        try:
            optimizer.add_param_group({'params': {'param': weight}})
        except TypeError:
            pass
        try:
            optimizer.add_param_group({'params': buffer})
        except ValueError:
            pass
        try:
            optimizer.add_param_group({'params': weight})
        except ValueError:
            pass
        _ = repr(optimizer)

    def test_adam(self):
        weight = torch.ones(1, requires_grad=True)
        entries = [(-0.1, (0., 0.), 1e-8, False),
                   (0.1, (0., 0.), -1e-8, False),
                   (0.1, (-0.9, 0.), 1e-8, False),
                   (0.1, (0.9, -0.999), 1e-8, False),
                   (0.1, (0.9, 0.999), 1e-8, False),
                   (0.1, (0.9, 0.999), 1e-8, True)]
        for lr, betas, eps, amsgrad in entries:
            try:
                _ = torch.optim.Adam([weight], lr=lr, betas=betas, eps=eps, amsgrad=amsgrad)
                _ = torch.optim.AdamW([weight], lr=lr, betas=betas, eps=eps, amsgrad=amsgrad)
            except (ValueError, NotImplementedError):
                pass

    def test_rmsprop(self):
        weight = torch.ones(1, requires_grad=True)
        entries = [(-0.1, (0., 0.), 1e-8, False),
                   (0.1, (0., 0.), -1e-8, False),
                   (0.1, (-0.99, 0.), 1e-8, False),
                   (0.1, (0.99, -0.9), 1e-8, False),
                   (0.1, (0.99, 0.9), 1e-8, False),
                   (0.1, (0.99, 0.9), 1e-8, True)]
        for lr, (alpha, momentum), eps, centered in entries:
            try:
                _ = torch.optim.RMSprop(
                    [weight], lr=lr, alpha=alpha, eps=eps,
                    momentum=momentum, centered=centered)
            except ValueError:
                pass

    def test_sgd(self):
        weight = torch.ones(1, requires_grad=True)
        entries = [(-0.1, 0., False), (0.1, -0.1, False), (0.1, 0., True)]
        for lr, momentum, nesterov in entries:
            try:
                _ = torch.optim.SGD([weight], lr=lr, momentum=momentum, nesterov=nesterov)
            except ValueError:
                pass

    def test_step(self):
        weight1 = torch.ones(1, requires_grad=True)
        weight2 = torch.ones(1, requires_grad=True)
        optimizer = torch.optim.SGD([weight1, weight2], 0.1)
        y = weight1 + 1
        y.backward(y)
        optimizer.step()
        self.assertLessEqual(float(weight1) - 0.8, 1e-5)
        optimizer.zero_grad()
        self.assertLessEqual(float(weight1.grad) - 0., 1e-5)
        optimizer.zero_grad(set_to_none=True)
        self.assertEqual(weight1.grad, None)
        for i in range(2):
            y = weight1 + 1
            y.backward(y)
            optimizer.sum_grad()
        optimizer.step()
        self.assertLessEqual(float(weight1) - 0.6, 1e-5)


if __name__ == '__main__':
    run_tests()
