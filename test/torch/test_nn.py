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
"""Test the nn module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import os
import unittest

import numpy as np

from dragon.core.util import logging
from dragon.core.util import nest
from dragon.core.testing.unittest.common_utils import run_tests
from dragon.vm import torch
from dragon.vm.torch.core.nn import _reduction

# Fix the duplicate linked omp runtime
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# Fix the numpy seed
np.random.seed(1337)


class OpTestCase(unittest.TestCase):
    """The base test case."""

    precision = 1e-5

    def __init__(self, method_name='runTest'):
        """
        Initialize the method.

        Args:
            self: (todo): write your description
            method_name: (str): write your description
        """
        super(OpTestCase, self).__init__(method_name)

    def assertEqual(
        self,
        first,
        second,
        msg=None,
        prec=None,
    ):
        """
        Asserts that first numpy array.

        Args:
            self: (todo): write your description
            first: (todo): write your description
            second: (todo): write your description
            msg: (str): write your description
            prec: (todo): write your description
        """
        if prec is None:
            prec = self.precision
        inputs = nest.flatten(first)
        num_first = len(inputs)
        inputs += nest.flatten(second)
        num_second = len(inputs) - num_first
        for i, input in enumerate(inputs):
            if isinstance(input, torch.Tensor):
                inputs[i] = input.numpy()
        first = inputs[:num_first] if num_first > 1 else inputs[0]
        second = inputs[num_first:len(inputs)] if num_second > 1 else inputs[num_first]
        if isinstance(first, np.ndarray) and isinstance(second, np.ndarray):
            super(OpTestCase, self).assertEqual(first.shape, second.shape)
            if first.dtype == np.bool and second.dtype == np.bool:
                diff = first ^ second
                num_unique = len(np.unique(diff))
                self.assertLessEqual(num_unique, 1, msg)
            else:
                diff = np.abs(first - second)
                max_err = diff.max()
                self.assertLessEqual(max_err, prec, msg)
        elif nest.is_sequence(first) and nest.is_sequence(second):
            for a, b in zip(first, second):
                self.assertEqual(a, b, msg, prec)
        else:
            super(OpTestCase, self).assertEqual(first, second, msg)


class TestModule(unittest.TestCase):
    """Test the base module class."""

    def test_properties(self):
        """
        Test the test properties.

        Args:
            self: (todo): write your description
        """
        m = torch.nn.Module()
        m.add_module('sub1', torch.nn.Module().cuda().half())
        m.sub2 = torch.nn.Module().double()
        m.sub2.register_parameter('weight', torch.nn.Parameter(torch.tensor(1)))
        m.add_module('sub3', None)
        m.register_parameter('weight', torch.nn.Parameter(torch.tensor(1)))
        m.register_buffer('bias', torch.tensor(1))
        m.sub2 = None
        m.sub3 = torch.nn.Conv2d(2, 3, 3)
        m.cpu().float()
        self.assertEqual(m.train().training, True)
        self.assertEqual(m.eval().training, False)
        self.assertEqual(m.sub1.training, False)
        self.assertEqual(m.weight.requires_grad, True)
        self.assertEqual(m.bias.requires_grad, False)
        m.apply(lambda m: m.train())
        self.assertEqual(m.training, True)
        logging.set_verbosity('FATAL')
        m.load_state_dict(m.state_dict())
        logging.set_verbosity('INFO')
        m.load_state_dict(m.state_dict(to_numpy=True))
        try:
            m.load_state_dict({'!@#$%^&*()': 1})
        except RuntimeError:
            pass
        (m.sub3.weight + 1).sum().backward()
        m.zero_grad()
        for _, _ in m.named_modules():
            pass
        for _ in m.modules():
            pass
        for _, _ in m.named_parameters():
            pass
        for _, _ in m.named_buffers():
            pass
        for _ in m.parameters():
            pass
        for _ in m.buffers():
            pass
        _, _ = repr(m), repr(m.weight)

    def test_sequential(self):
        """
        Test for the sequence of sequences.

        Args:
            self: (todo): write your description
        """
        m1 = torch.nn.Sequential(torch.nn.Module())
        m2 = torch.nn.Sequential(collections.OrderedDict([
            ('sub1', torch.nn.Module()),
            ('sub2', torch.nn.Module()),
            ('sub3', torch.nn.Module())]))
        self.assertEqual(len(m2[1:]), 2)
        m2[-1] = m1[0]
        self.assertEqual(id(m2[-1]), id(m1[0]))
        del m2[0]
        del m2[0:2]
        self.assertEqual(len(m2), 0)

    def test_list(self):
        """
        List of the tests of the tests.

        Args:
            self: (todo): write your description
        """
        m = torch.nn.ModuleList([torch.nn.Module()])
        m.append(torch.nn.Module())
        m.extend([torch.nn.Module()])
        self.assertEqual(len(m[1:]), 2)
        m[-1] = torch.nn.Module()
        self.assertEqual(id(m[2]), id(m[-1]))
        del m[0]
        del m[0:2]
        self.assertEqual(len(m), 0)
        for _ in m:
            pass

    def test_forward_hook(self):
        """
        Run forward hook.

        Args:
            self: (todo): write your description
        """
        m = torch.nn.Module()
        with m.register_forward_hook(lambda m, inputs, outputs: [1, 2, 3]):
            self.assertEqual(m(), [1, 2, 3])
        self.assertEqual(m(), None)


class TestModules(OpTestCase):
    """Test the nn module class."""

    def test_affine_channel(self):
        """
        Test for affine affine features.

        Args:
            self: (todo): write your description
        """
        data1 = arange((2, 3, 4, 5))
        data2, data3 = arange((1, 3, 1, 1)), arange((1, 3, 1, 1))
        w, b = new_tensor(data2.flatten()), new_tensor(data3.flatten())
        entries = [(True, False, False),
                   (True, True, False),
                   (True, True, True),
                   (False, False, False),
                   (False, True, False)]
        for bias, fix_weight, fix_bias in entries:
            x = new_tensor(data1)
            try:
                m = torch.nn.AffineChannel(
                    num_features=3,
                    bias=bias,
                    fix_weight=fix_weight,
                    fix_bias=fix_bias,
                    inplace=True,
                )
            except ValueError:
                m = torch.nn.AffineChannel(
                    num_features=3,
                    bias=bias,
                    fix_weight=fix_weight,
                    fix_bias=fix_bias,
                    inplace=False,
                )
            m.weight.copy_(w)
            result = data1 * data2
            if bias:
                m.bias.copy_(b)
                result += data3
            y, _ = m(x), repr(m)
            self.assertEqual(y, result)

    def test_bce_with_logits_loss(self):
        """
        Compute the bce loss.

        Args:
            self: (todo): write your description
        """
        for reduction in ('mean', 'sum', 'none'):
            data1 = np.array([[0.2], [0.5], [0.7]], 'float32')
            data2 = -np.log(1. / data1 - 1.)
            data3 = np.array([[0], [1], [0]], 'float32')
            a, b = new_tensor(data2), new_tensor(data3)
            m = torch.nn.BCEWithLogitsLoss(reduction=reduction)
            y, _ = m(a, b), repr(m)
            result = reduce(
                -(data3 * np.log(data1) + (1 - data3) * np.log(1 - data1)),
                reduction=reduction)
            self.assertEqual(y, result)

    def test_batch_norm(self):
        """
        Batch normalization.

        Args:
            self: (todo): write your description
        """
        eps = 1e-5
        entries = [((4, 3), (1, 3), 0),
                   ((4, 3), (1, 3), 1),
                   ((4, 3, 2), (1, 3, 1), 0),
                   ((4, 3, 2), (1, 3, 1), 1),
                   ((4, 3, 2, 2), (1, 3, 1, 1), 0),
                   ((4, 3, 2, 2), (1, 3, 1, 1), 1),
                   ((4, 3, 2, 2, 2), (1, 3, 1, 1, 1), 0),
                   ((4, 3, 2, 2, 2), (1, 3, 1, 1, 1), 1)]
        for x_shape, w_shape, use_stats in entries:
            data1 = arange(x_shape) * .1
            data2, data3 = arange(w_shape, 1) * .1, arange(w_shape) * .1
            data4, data5 = arange(w_shape) * .1, arange(w_shape, 1) * .1
            x = new_tensor(data1)
            w, b = new_tensor(data2.flatten()), new_tensor(data3.flatten())
            rm, rv = new_tensor(data4.flatten()), new_tensor(data5.flatten())
            m = getattr(torch.nn, 'BatchNorm{}d'.format(max(1, len(x_shape) - 2)))(
                num_features=3, eps=eps, affine=use_stats == 1).half().float()
            m.weight.copy_(w)
            m.bias.copy_(b)
            m.running_mean.copy_(rm)
            m.running_var.copy_(rv)
            if use_stats == 0:
                axes = list(range(0, len(data1.shape)))
                axes.pop(1)
                mean = np.mean(data1, tuple(axes), keepdims=True)
                sig = np.sqrt(np.var(data1, tuple(axes), keepdims=True) + eps)
                result = (data1 - mean) / sig
                m.train()
            else:
                sig = np.sqrt(data5 + eps)
                result = (data1 - data4) / sig
                m.eval()
            result = result * data2 + data3
            y, _ = m(x), repr(m)
            self.assertEqual(y, result)

    def test_conv2d(self):
        """
        Test for 2d convolution.

        Args:
            self: (todo): write your description
        """
        entries = [((2, 2, 2, 2), (3, 2, 1, 1), (3,), 1, 1, 0, 1, 1),
                   ((2, 2, 2, 2), (3, 2, 3, 3), (3,), 3, 1, 1, 1, 1)]
        results = [[[[[0.04, 0.05], [0.06, 0.07]], [[0.22, 0.27], [0.32, 0.37]], [[0.4, 0.49], [0.58, 0.67]]],
                    [[[0.12, 0.13], [0.14, 0.15]], [[0.62, 0.67], [0.72, 0.77]], [[1.12, 1.21], [1.3, 1.39]]]],
                   [[[[3.8, 3.52], [2.96, 2.68]], [[8.94, 8.66], [8.1, 7.82]], [[14.08, 13.8], [13.24, 12.96]]],
                    [[[10.52, 9.6], [7.76, 6.84]], [[27.18, 26.26], [24.42, 23.5]], [[43.84, 42.92], [41.08, 40.16]]]]]
        for (x_shape, w_shape, b_shape, kernel_shape,
             strides, pads, dilations, group), result in zip(entries, results):
            data1, data2, data3 = arange(x_shape) * .1, arange(w_shape) * .1, arange(b_shape) * .1
            x, w, b = new_tensor(data1), new_tensor(data2), new_tensor(data3)
            m = torch.nn.Conv2d(2, 3, kernel_shape, strides, pads)
            m.weight.copy_(w)
            m.bias.copy_(b)
            y, _ = m(x), repr(m)
            self.assertEqual(y, np.array(result))

    def test_conv2d_transpose(self):
        """
        Test for 2d convolution.

        Args:
            self: (todo): write your description
        """
        entries = [((2, 2, 2, 2), (2, 3, 1, 1), (3,), 1, 1, 0, 1, 1),
                   ((2, 2, 2, 2), (2, 3, 3, 3), (3,), 3, 1, 1, 1, 1)]
        results = [[[[[0.12, 0.15], [0.18, 0.21]], [[0.26, 0.31], [0.36, 0.41]], [[0.4, 0.47], [0.54, 0.61]]],
                    [[[0.36, 0.39], [0.42, 0.45]], [[0.66, 0.71], [0.76, 0.81]], [[0.96, 1.03], [1.1, 1.17]]]],
                   [[[[6.36, 6.64], [7.2, 7.48]],
                     [[8.98, 9.26], [9.82, 10.1]],
                     [[11.6, 11.88], [12.44, 12.72]]],
                    [[[16.28, 17.2], [19.04, 19.96]],
                     [[24.66, 25.58], [27.42, 28.34]],
                     [[33.04, 33.96], [35.8, 36.72]]]]]
        for (x_shape, w_shape, b_shape, kernel_shape,
             strides, pads, dilations, group), result in zip(entries, results):
            data1, data2, data3 = arange(x_shape) * .1, arange(w_shape) * .1, arange(b_shape) * .1
            x, w, b = new_tensor(data1), new_tensor(data2), new_tensor(data3)
            m = torch.nn.ConvTranspose2d(2, 3, kernel_shape, strides, pads)
            m.weight.copy_(w)
            m.bias.copy_(b)
            y, _ = m(x), repr(m)
            self.assertEqual(y, np.array(result))

    def test_cross_entropy_loss(self):
        """
        Compute the cross entropy of the cross entropy.

        Args:
            self: (todo): write your description
        """
        for reduction in ('mean', 'sum', 'none'):
            data1 = np.log(np.array(
                [[0.2, 0.3, 0.5], [0.1, 0.7, 0.2]], 'float32'))
            data2 = np.array([0, 1], 'int64')
            a, b = new_tensor(data1), new_tensor(data2)
            m = torch.nn.CrossEntropyLoss(reduction=reduction)
            y, _ = m(a, b), repr(m)
            result = reduce(-data1[np.arange(2), data2], reduction=reduction)
            self.assertEqual(y, result)

    def test_dropout(self):
        """
        Dropout x is_drop

        Args:
            self: (todo): write your description
        """
        prob = 0.
        data = uniform((2, 3))
        x = new_tensor(data)
        m = torch.nn.Dropout(p=prob, inplace=True)
        y, _ = m(x), repr(m)
        self.assertEqual(y, data)

    def test_drop_block2d(self):
        """
        Drop - copy of x.

        Args:
            self: (todo): write your description
        """
        keep_prob = 1.
        data = uniform((2, 3, 4, 4))
        x = new_tensor(data)
        m = torch.nn.DropBlock2d(kp=keep_prob, block_size=2, inplace=True)
        y, _ = m(x), repr(m)
        self.assertEqual(y, data)

    def test_drop_path(self):
        """
        Drop test path

        Args:
            self: (todo): write your description
        """
        prob = 0.
        data = uniform((2, 3))
        x = new_tensor(data)
        m = torch.nn.DropPath(p=prob, inplace=True)
        y, _ = m(x), repr(m)
        self.assertEqual(y, data)

    def test_elu(self):
        """
        Compute the element of - wise test.

        Args:
            self: (todo): write your description
        """
        alpha = 1.
        data = np.array([-1., 0., 1.], 'float32')
        x = new_tensor(data)
        m = torch.nn.ELU(alpha=alpha, inplace=True)
        y, _ = m(x), repr(m)
        result = np.maximum(data, 0.) + alpha * (np.exp(np.minimum(data, 0.)) - 1.)
        self.assertEqual(y, result)

    def test_group_norm(self):
        """
        Compute the normalization.

        Args:
            self: (todo): write your description
        """
        eps = 1e-5
        entries = [((1, 4), (1, 4), 2, (2,)),
                   ((1, 4, 2), (1, 4, 1), 2, (2, 3))]
        for x_shape, w_shape, group, axes in entries:
            data1 = arange(x_shape) * .1
            data2, data3 = arange(w_shape, 1) * .1, arange(w_shape) * .1
            x = new_tensor(data1)
            w, b = new_tensor(data2.flatten()), new_tensor(data3.flatten())
            _ = torch.nn.GroupNorm(num_groups=group, num_channels=4, eps=eps, affine=False)
            m = torch.nn.GroupNorm(num_groups=group, num_channels=4, eps=eps).half().float()
            m.weight.copy_(w)
            m.bias.copy_(b)
            y, _ = m(x), repr(m)
            new_shape = list(x_shape[:])
            new_shape[1] //= group
            new_shape.insert(1, group)
            data1 = data1.reshape(new_shape)
            mean = np.mean(data1, axes, keepdims=True)
            sig = np.sqrt(np.var(data1, axes, keepdims=True) + eps)
            result = ((data1 - mean) / sig).reshape(x_shape)
            result = result * data2 + data3
            self.assertEqual(y, result)

    def test_gru_module(self):
        """
        Reset the module.

        Args:
            self: (todo): write your description
        """
        m = torch.nn.GRU(2, 3)
        m.reset_parameter(initializer='uniform')
        m.reset_parameters()
        _ = repr(m)

    def test_hardsigmoid(self):
        """
        Test hardsigmigmoid

        Args:
            self: (todo): write your description
        """
        alpha, beta = 1.0 / 6.0, 0.5
        data = np.array([--3., -2., -1., 0., 1., 2., 3], 'float32')
        x = new_tensor(data)
        m = torch.nn.Hardsigmoid(inplace=True)
        y, _ = m(x), repr(m)
        result = np.clip(alpha * data + beta, 0, 1)
        self.assertEqual(y, result)

    def test_hardswish(self):
        """
        Test the hardswishwish

        Args:
            self: (todo): write your description
        """
        alpha, beta = 1.0 / 6.0, 0.5
        data = np.array([-3., -2., -1., 0., 1., 2., 3], 'float32')
        x = new_tensor(data)
        m = torch.nn.Hardswish()
        y, _ = m(x), repr(m)
        result = data * np.clip(alpha * data + beta, 0, 1)
        self.assertEqual(y, result)

    def test_leaky_relu(self):
        """
        Test the leaky test test.

        Args:
            self: (todo): write your description
        """
        alpha = 0.2
        data = np.array([-1., 0., 1.], 'float32')
        x = new_tensor(data)
        m = torch.nn.LeakyReLU(negative_slope=alpha, inplace=True)
        y, _ = m(x), repr(m)
        result = np.maximum(data, 0.) + np.minimum(data, 0.) * alpha
        self.assertEqual(y, result)

    def test_linear(self):
        """
        Test if the linear regression.

        Args:
            self: (todo): write your description
        """
        entries = [((2, 3), (4, 3), (4,), False),
                   ((2, 3), (4, 3), (4,), True)]
        for x_shape, w_shape, b_shape, bias in entries:
            data1, data2, data3 = arange(x_shape), arange(w_shape), arange(b_shape)
            x, w, b = new_tensor(data1), new_tensor(data2), new_tensor(data3)
            m = torch.nn.Linear(w_shape[1], w_shape[0], bias=bias)
            m.weight.copy_(w)
            if bias:
                m.bias.copy_(b)
            y, _ = m(x), repr(m)
            result = np.matmul(data1, data2.T) + (data3 if bias else 0)
            self.assertEqual(y, result)

    def test_local_response_norm(self):
        """
        Compute local local local local local local response.

        Args:
            self: (todo): write your description
        """
        entries = [((2, 3, 2, 2), 5, 0.0001, 0.75, 1.)]
        for x_shape, size, alpha, beta, bias in entries:
            m = torch.nn.LocalResponseNorm(size=size, alpha=alpha, beta=beta, k=bias)
            _ = repr(m)

    def test_log_softmax(self):
        """
        Computes the softmax.

        Args:
            self: (todo): write your description
        """
        data = np.array([[0.2, 0.3, 0.5], [0.1, 0.7, 0.2]], 'float32')
        x = new_tensor(np.log(data))
        m = torch.nn.LogSoftmax(1)
        y, _ = m(x), repr(m)
        self.assertEqual(y, np.log(data))

    def test_lstm_module(self):
        """
        Test if lstm module.

        Args:
            self: (todo): write your description
        """
        m = torch.nn.LSTM(2, 3)
        _ = repr(m)

    def test_lstm_cell(self):
        """
        Test if lstm cell is a lstm cell.

        Args:
            self: (todo): write your description
        """
        m = torch.nn.LSTMCell(2, 3)
        _ = repr(m)

    def test_l1_loss(self):
        """
        Computes the l1 loss.

        Args:
            self: (todo): write your description
        """
        for reduction in ('mean', 'sum', 'none'):
            data1 = np.array([-1., 0., 1.], 'float32')
            data2 = np.array([1., 0., -1.], 'float32')
            a, b = new_tensor(data1), new_tensor(data2)
            m = torch.nn.L1Loss(reduction=reduction)
            y, _ = m(a, b), repr(m)
            result = reduce(np.abs(data1 - data2), reduction=reduction)
            self.assertEqual(y, result)

    def test_mse_loss(self):
        """
        Compute the loss.

        Args:
            self: (todo): write your description
        """
        for reduction in ('mean', 'sum', 'none'):
            data1 = np.array([-1., 0., 1.], 'float32')
            data2 = np.array([1., 0., -1.], 'float32')
            a, b = new_tensor(data1), new_tensor(data2)
            m = torch.nn.MSELoss(reduction=reduction)
            y, _ = m(a, b), repr(m)
            result = reduce(np.square(data1 - data2), reduction=reduction)
            self.assertEqual(y, result)

    def test_nll_loss(self):
        """
        Compute the loss of the loss.

        Args:
            self: (todo): write your description
        """
        for reduction in ('mean', 'sum', 'none'):
            data1 = np.log(np.array(
                [[0.2, 0.3, 0.5], [0.1, 0.7, 0.2]], 'float32'))
            data2 = np.array([0, 1], 'int64')
            a, b = new_tensor(data1), new_tensor(data2)
            m = torch.nn.NLLLoss(reduction=reduction)
            y, _ = m(a, b), repr(m)
            result = reduce(-data1[np.arange(2), data2], reduction=reduction)
            self.assertEqual(y, result)

    def test_pad(self):
        """
        Test if the input tensor is identical.

        Args:
            self: (todo): write your description
        """
        for ndim in (1, 2, 3):
            data = np.ones((2, 2, 2, 2), dtype='float32')
            x = new_tensor(data)
            m1 = getattr(torch.nn, 'ConstantPad{}d'.format(ndim))(1, 0)
            m2 = getattr(torch.nn, 'ReflectionPad{}d'.format(ndim))(1)
            m3 = getattr(torch.nn, 'ReplicationPad{}d'.format(ndim))(1)
            m4 = torch.nn.ZeroPad2d(1) if ndim == 2 else None
            _, _, _, _ = repr(m1), repr(m2), repr(m3), repr(m4)
            pads = [(0, 0)] * (4 - ndim) + [(1, 1)] * ndim
            self.assertEqual(m1(x), np.pad(data, pads, 'constant'))
            self.assertEqual(m2(x), np.pad(data, pads, 'reflect'))
            self.assertEqual(m3(x), np.pad(data, pads, 'edge'))
            if m4 is not None:
                self.assertEqual(m4(x), np.pad(data, pads, 'constant'))

    def test_pool2d(self):
        """
        Test pool2d pooling.

        Args:
            self: (todo): write your description
        """
        entries = [((2, 2, 2, 2), (2, 2), 2, 1, 'MAX'),
                   ((2, 2, 2, 2), (2, 2), 2, 1, 'AVG')]
        for x_shape, kernel_shape, strides, pads, mode in entries:
            data = arange(x_shape) * .1
            module_cls = torch.nn.AvgPool2d if mode == 'AVG' else torch.nn.MaxPool2d
            x = new_tensor(data)
            m = module_cls(kernel_shape, strides, pads)
            y, _ = m(x), repr(m)
            result = data / (np.prod(kernel_shape) if mode == 'AVG' else 1.)
            self.assertEqual(y, result)

    def test_prelu(self):
        """
        Prelu preprocessing.

        Args:
            self: (todo): write your description
        """
        entries = [((3,), (1,)),
                   ((3,), (3,)),
                   ((2, 3), (1,)),
                   ((2, 3), (3,)),
                   ((2, 3, 4, 4), (1,)),
                   ((2, 3, 4, 4), (1, 3, 1, 1))]
        for x_shape, w_shape in entries:
            data1 = uniform(x_shape)
            data2 = np.ones(w_shape, 'float32') * 0.25
            x, w = new_tensor(data1), new_tensor(data2.flatten())
            m = torch.nn.PReLU(w.numel())
            m.weight.copy_(w)
            y, _ = m(x), repr(m)
            result = np.maximum(data1, 0.) + np.minimum(data1, 0.) * data2
            self.assertEqual(y, result)

    def test_relu(self):
        """
        Test if the projection isochrone.

        Args:
            self: (todo): write your description
        """
        data = np.array([-1., 0., 1.], 'float32')
        x = new_tensor(data)
        m = torch.nn.ReLU(inplace=True)
        y, _ = m(x), repr(m)
        result = np.maximum(data, 0.)
        self.assertEqual(y, result)

    def test_relu6(self):
        """
        Perform a tensor.

        Args:
            self: (todo): write your description
        """
        data = np.array([-1., 0., 1., 6., 7.], 'float32')
        x = new_tensor(data)
        m = torch.nn.ReLU6(inplace=True)
        y, _ = m(x), repr(m)
        result = np.minimum(np.maximum(data, 0.), 6.)
        self.assertEqual(y, result)

    def test_rnn_module(self):
        """
        Test the rnn module

        Args:
            self: (todo): write your description
        """
        m = torch.nn.RNN(3, 2)
        _ = repr(m)

    def test_selu(self):
        """
        Perform a tensor.

        Args:
            self: (todo): write your description
        """
        alpha, gamma = 1.67326, 1.0507
        data = np.array([-1., 0., 1.], 'float32')
        x = new_tensor(data)
        m = torch.nn.SELU(inplace=True)
        y, _ = m(x), repr(m)
        result = gamma * (
            np.maximum(data, 0.) +
            alpha * (np.exp(np.minimum(data, 0.)) - 1.))
        self.assertEqual(y, result)

    def test_smooth_l1_loss(self):
        """
        Test the l1 loss.

        Args:
            self: (todo): write your description
        """
        for reduction in ('mean', 'sum', 'none'):
            for beta in (1.,):
                data1 = np.array([-1., 0., 1.], 'float32')
                data2 = np.array([1., 0., 1.01], 'float32')
                a, b = new_tensor(data1), new_tensor(data2)
                m = torch.nn.SmoothL1Loss(beta=beta, reduction=reduction)
                y, _ = m(a, b), repr(m)
                diff, abs_diff = data1 - data2, np.abs(data1 - data2)
                result = reduce(np.where(
                    abs_diff < beta,
                    0.5 * np.square(diff) / beta,
                    abs_diff - 0.5 * beta),
                    reduction=reduction)
                self.assertEqual(y, result)

    def test_sigmoid(self):
        """
        Test the sigmoid is a tensor.

        Args:
            self: (todo): write your description
        """
        data = np.array([0.2, 0.4, 0.6, 0.8, 1.], 'float32')
        x = new_tensor(data)
        m = torch.nn.Sigmoid(inplace=True)
        y, _ = m(x), repr(m)
        result = 1. / (1. + np.exp(-data))
        self.assertEqual(y, result)

    def test_sigmoid_focal_loss(self):
        """
        Computes the focaloid

        Args:
            self: (todo): write your description
        """
        pos_alpha, neg_alpha, gamma = 0.25, 0.75, 2.0
        for reduction in ('mean', 'sum', 'none'):
            data1 = np.array([[0.2, 0.3], [0.5, 0.1], [0.7, 0.2]], 'float32')
            data2 = -np.log(1. / data1 - 1.)
            data3 = np.array([0, 1, 0], 'int64')
            a, b = new_tensor(data2), new_tensor(data3)
            m = torch.nn.SigmoidFocalLoss(
                alpha=pos_alpha, gamma=gamma, reduction=reduction)
            y, _ = m(a, b), repr(m)
            pos_term = np.power((1. - data1), gamma) * np.log(data1)
            pos_term *= (-pos_alpha * np.eye(2, dtype='float32')[data3])
            neg_term = np.power(data1, gamma) * np.log(1. - data1)
            neg_term *= (-neg_alpha * np.invert(np.eye(2, dtype='bool')[data3]))
            result = reduce(pos_term + neg_term, reduction=reduction)
            self.assertEqual(y, result)

    def test_softmax(self):
        """
        Test the softmax is the softmax.

        Args:
            self: (todo): write your description
        """
        data = np.array([[0.2, 0.3, 0.5], [0.1, 0.7, 0.2]], 'float32')
        x = new_tensor(np.log(data))
        m = torch.nn.Softmax(dim=1, inplace=True)
        y, _ = m(x), repr(m)
        self.assertEqual(y, data)

    def test_swish(self):
        """
        Swish test isochrone

        Args:
            self: (todo): write your description
        """
        data = np.array([-3., -2., -1., 0., 1., 2., 3], 'float32')
        x = new_tensor(data)
        m = torch.nn.Swish()
        y, _ = m(x), repr(m)
        result = data * (1. / (1. + np.exp(-data)))
        self.assertEqual(y, result)

    def test_tanh(self):
        """
        Test if the cross - validation

        Args:
            self: (todo): write your description
        """
        data = np.array([0.2, 0.4, 0.6, 0.8, 1.], 'float32')
        x = new_tensor(data)
        m = torch.nn.Tanh(inplace=True)
        y, _ = m(x), repr(m)
        self.assertEqual(y, np.tanh(data))

    def test_upsample(self):
        """
        Perform anova of anova isochrone.

        Args:
            self: (todo): write your description
        """
        entries = [((2, 2, 1, 1), (2, 2), 'nearest'),
                   ((2, 2, 1, 1), (2, 2), 'bilinear'),
                   ((2, 2, 4, 4), (2, 2), 'nearest'),
                   ((2, 2, 4, 4), (2, 2), 'bilinear')]
        results = [[[[[0., 0.], [0., 0.]], [[0.1, 0.1], [0.1, 0.1]]],
                    [[[0.2, 0.2], [0.2, 0.2]], [[0.3, 0.3], [0.3, 0.3]]]],
                   [[[[0., 0.], [0., 0.]], [[0.1, 0.1], [0.1, 0.1]]],
                    [[[0.2, 0.2], [0.2, 0.2]], [[0.3, 0.3], [0.3, 0.3]]]],
                   [[[[0., 0.2], [0.8, 1.]], [[1.6, 1.8], [2.4, 2.6]]],
                    [[[3.2, 3.4], [4., 4.2]], [[4.8, 5.], [5.6, 5.8]]]],
                   [[[[0.25, 0.45], [1.05, 1.25]], [[1.85, 2.05], [2.65, 2.85]]],
                    [[[3.45, 3.65], [4.25, 4.45]], [[5.05, 5.25], [5.85, 6.05]]]]]
        for (x_shape, sizes, mode), result in zip(entries, results):
            data1 = arange(x_shape) * .1
            x = new_tensor(data1)
            _ = torch.nn.UpsamplingBilinear2d()
            _ = torch.nn.UpsamplingNearest2d()
            m = torch.nn.Upsample(size=sizes, mode=mode, align_corners=False)
            y, _ = m(x), repr(m)
            self.assertEqual(y, np.array(result))


class TestNNInit(OpTestCase):
    """Test the nn.init module."""

    def test_constant(self):
        """
        Test if the constant.

        Args:
            self: (todo): write your description
        """
        x = torch.nn.init.constant_(torch.Tensor(2, dtype=torch.float32), 1)
        self.assertEqual(x, np.ones((2,), dtype='float32'))

    def test_dirac(self):
        """
        Initialize all tensors in the tensor.

        Args:
            self: (todo): write your description
        """
        for ndim in range(2, 6):
            for groups in range(1, 4):
                try:
                    _ = torch.nn.init.dirac_(
                        torch.Tensor(*([2] * ndim), dtype=torch.float32),
                        groups=groups)
                except ValueError:
                    pass

    def test_eye(self):
        """
        Inverse of the tensor.

        Args:
            self: (todo): write your description
        """
        x = torch.nn.init.eye_(torch.Tensor(2, 3, dtype=torch.float32))
        self.assertEqual(x, np.eye(2, 3))
        try:
            _ = torch.nn.init.eye_(torch.Tensor(2, 3, 3, dtype=torch.float32))
        except ValueError:
            pass

    def test_random(self):
        """
        Initialize the random tensor.

        Args:
            self: (todo): write your description
        """
        _ = torch.nn.init.normal_(torch.Tensor(2, dtype=torch.float32))
        _ = torch.nn.init.uniform_(torch.Tensor(2, dtype=torch.float32))

    def test_variance_scaling(self):
        """
        Test for variance of - variance variance.

        Args:
            self: (todo): write your description
        """
        a = torch.Tensor(2, dtype=torch.float32)
        b = torch.Tensor(2, 3, dtype=torch.float32)
        c = torch.Tensor(2, 3, 3, dtype=torch.float32)
        entries = [('xavier_normal_', {}),
                   ('xavier_uniform_', {}),
                   ('kaiming_normal_', {}),
                   ('kaiming_normal_', {'nonlinearity': 'sigmoid'}),
                   ('kaiming_normal_', {'nonlinearity': 'tanh'}),
                   ('kaiming_normal_', {'nonlinearity': 'relu'}),
                   ('kaiming_normal_', {'nonlinearity': 'abc'}),
                   ('kaiming_normal_', {'a': None}),
                   ('kaiming_normal_', {'a': 'a'}),
                   ('kaiming_normal_', {'mode': 'fan_avg'}),
                   ('kaiming_uniform_', {})]
        for init_name, kwargs in entries:
            try:
                getattr(torch.nn.init, init_name)(c, **kwargs)
                getattr(torch.nn.init, init_name)(b, **kwargs)
                getattr(torch.nn.init, init_name)(a, **kwargs)
            except ValueError:
                pass


class TestReduction(unittest.TestCase):
    """Test the reduction utility."""

    def test_legacy_string(self):
        """
        Test if the legend.

        Args:
            self: (todo): write your description
        """
        entries = [(None, None, 'mean'),
                   (None, False, 'none'),
                   (None, True, 'mean'),
                   (False, None, 'sum'),
                   (False, False, 'none'),
                   (False, True, 'sum'),
                   (True, None, 'mean'),
                   (True, False, 'none'),
                   (True, True, 'mean')]
        logging.set_verbosity('FATAL')
        for size_average, reduce, reduction in entries:
            self.assertEqual(_reduction.legacy_get_string(
                size_average, reduce), reduction)
        logging.set_verbosity('INFO')


def arange(shape, start=0, dtype='float32'):
    """Return the arange data with given shape."""
    return np.arange(start, start + int(np.prod(shape)), dtype=dtype).reshape(shape)


def dropout(data, drop_ratio=0.5):
    """Return the random dropped data."""
    return data * np.random.binomial(1, 1. - drop_ratio, data.shape).astype(data.dtype)


def new_tensor(data, requires_grad=False):
    """Create a new tensor from data."""
    return torch.tensor(data, dtype=data.dtype, requires_grad=requires_grad)


def reduce(data, axes=None, reduction='sum'):
    """Reduce data."""
    if reduction == 'sum':
        result = data.sum(axes)
    elif reduction == 'mean':
        result = data.mean(axes)
    else:
        result = data
    if not isinstance(result, np.ndarray):
        result = np.array(result, data.dtype)
    return result


def uniform(shape, dtype='float32'):
    """Return the uniform data with given shape."""
    return np.random.uniform(-1., 1., size=shape).astype(dtype)


if __name__ == '__main__':
    run_tests()
