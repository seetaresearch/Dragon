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
"""Operator implementations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy

from dragon.core.autograph import tape
from dragon.core.autograph.op_schema import OpSchema
from dragon.core.framework import context
from dragon.core.framework import proto_util
from dragon.core.framework import workspace
from dragon.core.framework.tensor import Tensor
from dragon.core.util import nest


class ExecutionCache(object):
    """Container of cached executions."""

    _created_instances = {}

    def __init__(self, op_type):
        self._op_type = op_type
        self._ignore_keys = {'outputs', 'name'}
        def_args = {}
        def_args_getter = OpSchema.get_args(op_type)
        if def_args_getter is not None:
            def_args = def_args_getter()
        for k, v in def_args.items():
            if k.endswith('_desc'):
                self._ignore_keys.add(k.split('_desc')[0])
        self._cache_dict = {}

    @classmethod
    def get_cache(cls, op_type):
        try:
            instance = cls._created_instances[op_type]
        except KeyError:
            instance = ExecutionCache(op_type)
            cls._created_instances[op_type] = instance
        return instance

    def get_config(self, **kwargs):
        """Return the config from given arguments."""
        device = context.get_device()
        cache_key = self._op_type + '/' + str(device)
        for k, v in kwargs.items():
            if k not in self._ignore_keys:
                cache_key += '/' + str(v)
        try:
            return self._cache_dict[cache_key]
        except KeyError:
            def_args, feed_dict = {}, {}
            def_args_getter = OpSchema.get_args(self._op_type)
            if def_args_getter is not None:
                def_args = def_args_getter(**kwargs)
            device = def_args.pop('device', device)
            no_grad = def_args.pop('no_grad', False)
            for k, v in def_args.items():
                if k.endswith('_desc') and v:
                    name = k.split('_desc')[0]
                    feed_dict[name] = v
                    def_args[k] = '$HANDLE/' + name
            op_def = proto_util.make_operator_def(
                op_type=self._op_type,
                name=kwargs.get('handle', ''),
                device_option=device.to_proto(False),
                cache_key=cache_key,
                to_impl=True, **def_args)
            cache_value = {'def': op_def,
                           'device': device,
                           'no_grad': no_grad,
                           'feed_dict': feed_dict}
            self._cache_dict[cache_key] = cache_value
            return cache_value


class OpLib(object):
    """Library to apply the registered operators."""

    @staticmethod
    def add(op_type, inputs, **kwargs):
        """Add operator to output symbols."""
        op_tape = tape.OrderedTape()
        execute_ws = workspace.get_workspace()
        grad_tape = tape.get_tape()

        # Add inputs.
        enable_grad = False
        inputs = nest.flatten(inputs)
        for input in inputs:
            op_tape.add_source(input)
            if grad_tape and (input.requires_grad or
                              grad_tape.is_target(id(input))):
                enable_grad = True

        # Add extra inputs.
        for input in nest.flatten(kwargs.pop('extra_inputs', [])):
            op_tape.add_source(input)
            op_tape.add_target(input.id)

        # Add outputs.
        name = kwargs.pop('name', None)
        num_outputs = kwargs.pop('num_outputs', 1)
        outputs = []
        for i in range(num_outputs):
            outputs.append(Tensor(
                impl=execute_ws.create_tensor(scope='Symbol'),
                name=name if name else op_type + ':%d' % i,
                symbolic=True))

        # Create def.
        op_def = proto_util.make_operator_def(
            op_type=op_type,
            inputs=[input.id for input in inputs],
            outputs=[output.id for output in outputs],
            device_option=proto_util.get_default_device_option(),
            name=execute_ws._handle_pool.create('Op'), **kwargs)

        # Record def.
        op_tape.add_op_def(op_def)
        grad_tape.add_op_def(op_def) if enable_grad else None

        # Set tape for outputs.
        for output in outputs:
            output._tape = op_tape
            output._requires_grad = enable_grad

        # Add spec to outputs.
        add_output_spec = OpSchema.get_spec(op_type)
        if add_output_spec is None:
            add_output_spec = OpSchema.get_spec('Unchanged')
        outputs = add_output_spec(kwargs, inputs, outputs)

        # Return single or repeated outputs.
        return outputs[0] if num_outputs == 1 else outputs

    @staticmethod
    def execute(op_type, inputs, **kwargs):
        """Execute an operator."""
        cache = ExecutionCache.get_cache(op_type)
        run_config = cache.get_config(**kwargs)
        return OpLib.run(inputs, run_config, **kwargs)

    @staticmethod
    def run(inputs, run_config, **kwargs):
        """Run operator once."""
        grad_tape = tape.get_tape()
        execute_ws = workspace.get_workspace()

        # Add inputs.
        input_names = []
        enable_grad = False
        for input in inputs:
            input_names.append(input.id)
            if grad_tape and (input.requires_grad or
                              grad_tape.is_target(id(input))):
                enable_grad = True

        # Compute gradient flags.
        no_grad = run_config['no_grad']
        enable_grad = enable_grad and not no_grad
        if isinstance(grad_tape, tape.GraphTape):
            no_grad, enable_grad = False, True

        # Add outputs.
        outputs, output_names = [], []
        output_specs = list(kwargs.get('outputs', [None]))
        for i, spec in enumerate(output_specs):
            if spec is None:
                outputs.append(Tensor(
                    device=run_config['device'].copy(),
                    impl=execute_ws.create_tensor(
                        scope=context.get_variable_scope(enable_grad)),
                    deleter=execute_ws._handle_pool))
                output_names.append(outputs[i].id)
            else:
                assert isinstance(spec, Tensor)
                outputs.append(spec)
                output_names.append(spec.id)
                if enable_grad and output_names[-1] not in input_names:
                    raise RuntimeError('Output that requires gradient is not in inputs.')

        # Specialize def for given inputs and outputs.
        op_handle = ''  # Optional handle
        op_def = run_config['def'].DeriveTo(input_names, output_names)

        # Record def if grad is enabled.
        if len(inputs) > 0 and not no_grad:
            if enable_grad:
                op_handle = execute_ws._handle_pool.create(op_def.type)
                op_def.name = op_handle
                grad_tape.add_op_def(op_def)
                for input in inputs:
                    grad_tape.add_source(input)
                for output in outputs:
                    output._requires_grad = True
            else:
                for output in outputs:
                    output._requires_grad = False

        # Ensure handle created for the graph.
        if isinstance(grad_tape, tape.GraphTape) and not op_handle:
            op_handle = execute_ws._handle_pool.create(op_def.type)
            op_def.name = op_handle

        # Emit to dispatch this execution.
        for feed_key, value_type in run_config['feed_dict'].items():
            dest = execute_ws.create_tensor(op_handle + '/' + feed_key)
            dest.FromNumpy(numpy.array(kwargs[feed_key], value_type), True)
        execute_ws.run_operator(op_def)

        # Return single or repeated outputs.
        return outputs[0] if len(outputs) == 1 else outputs
