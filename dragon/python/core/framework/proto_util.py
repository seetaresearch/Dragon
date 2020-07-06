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

"""Define some helpful protocol buffer makers here."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import sys

from google.protobuf.message import Message
import numpy

from dragon import backend
from dragon.core.framework import config
from dragon.core.framework import context
from dragon.core.proto import dragon_pb2


if sys.version_info >= (3, 0):
    def make_argument(key, value):
        argument = dragon_pb2.Argument()
        argument.name = key
        if type(value) is float:
            argument.f = value
        elif type(value) in (bool, int, numpy.int64):
            argument.i = value
        elif type(value) is bytes:
            argument.s = value
        elif type(value) is str:
            argument.s = str.encode(value)
        elif isinstance(value, Message):
            argument.s = value.SerializeToString()
        elif all(type(v) is float for v in value):
            argument.floats.extend(value)
        elif all(type(v) is int for v in value):
            argument.ints.extend(value)
        elif all(type(v) is str for v in value):
            argument.strings.extend([str.encode(v) for v in value])
        elif all(isinstance(v, Message) for v in value):
            argument.strings.extend([v.SerializeToString() for v in value])
        else:
            raise ValueError(
                'Unknown argument type: '
                'key = {}, value = {}, value_type = {}.'
                .format(key, value, type(value).__name__)
            )
        return argument
else:
    def make_argument(key, value):
        argument = dragon_pb2.Argument()
        argument.name = key
        if type(value) is float:
            argument.f = value
        elif type(value) in (bool, int, long, numpy.int64):
            argument.i = value
        elif type(value) is str:
            argument.s = value
        elif type(value) is unicode:
            argument.s = str(value)
        elif isinstance(value, Message):
            argument.s = value.SerializeToString()
        elif all(type(v) is float for v in value):
            argument.floats.extend(value)
        elif all(type(v) is int for v in value):
            argument.ints.extend(value)
        elif all(type(v) is long for v in value):
            argument.ints.extend(value)
        elif all(type(v) is str for v in value):
            argument.strings.extend(value)
        elif all(type(v) is unicode for v in value):
            argument.strings.extend([str(v) for v in value])
        elif all(isinstance(v, Message) for v in value):
            argument.strings.extend([v.SerializeToString() for v in value])
        else:
            raise ValueError(
                'Unknown argument type: '
                'key = {}, value = {}, value_type = {}.'
                .format(key, value, type(value).__name__)
            )
        return argument


def make_operator_def(
    op_type,
    inputs=(),
    outputs=(),
    name='',
    cache_key=None,
    device_option=None,
    arg=None,
    **kwargs
):
    op_def = dragon_pb2.OperatorDef()
    op_def.type, op_def.name = op_type, name
    op_def.input.extend([str(tensor) for tensor in inputs])
    op_def.output.extend([str(tensor) for tensor in outputs])
    if device_option is not None:
        op_def.device_option.CopyFrom(device_option)
    if 'random_seed' in kwargs:
        op_def.device_option.random_seed = kwargs['random_seed']
        del kwargs['random_seed']
    if cache_key is not None:
        op_def.cache_key = cache_key
    if arg is not None:
        op_def.arg.extend(arg)
    for k, v in kwargs.items():
        if v is None:
            continue
        op_def.arg.add().CopyFrom(make_argument(k, v))
    return op_def


def make_operator_cdef(
    op_type,
    inputs=(),
    outputs=(),
    name='',
    cache_key=None,
    device_option=None,
    arg=None,
    **kwargs
):
    op_def = backend.OperatorDef()
    op_def.ParseFrom(
        make_operator_def(
            op_type,
            inputs,
            outputs,
            name,
            cache_key,
            device_option,
            arg,
            **kwargs).SerializeToString())
    return op_def


def make_device_option(device_type, device_id, rng_seed=None):
    dev_opt = dragon_pb2.DeviceOption()
    dev_opt.device_type = device_type
    dev_opt.device_id = device_id
    if rng_seed is not None:
        dev_opt.random_seed = rng_seed
    return dev_opt


_PREDEFINED_DEVICE_LIMITS = 16
_PREDEFINED_DEVICE_DICT = {'cpu': 0, 'cuda': 1, 'cnml': 2}
_PREDEFINED_DEVICE_OPTION_DICT = {}


for i in range(_PREDEFINED_DEVICE_LIMITS):
    for device, identify in _PREDEFINED_DEVICE_DICT.items():
        _PREDEFINED_DEVICE_OPTION_DICT[(device, i)] = \
            make_device_option(identify, i)


def get_device_option(device_type, device_id=0, rng_seed=None):
    ctx = (device_type, device_id)
    option = _PREDEFINED_DEVICE_OPTION_DICT[ctx]
    if rng_seed is not None:
        option_copy = copy.deepcopy(option)
        option_copy.random_seed = rng_seed
        return option_copy
    return option


def get_default_device_option():
    dev_info = context.get_device_info()
    if dev_info is not None:
        return get_device_option(
            dev_info['device_type'],
            dev_info['device_index'],
        )
    return None


def get_global_device_option():
    cfg = config.config()
    return get_device_option(
        cfg.device_type,
        cfg.device_index,
    )