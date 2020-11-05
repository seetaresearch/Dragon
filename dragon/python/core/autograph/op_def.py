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
"""Helper for creating symbolic operators."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dragon.core.autograph.tensor import TensorRef
from dragon.core.autograph import op_spec
from dragon.core.framework import context
from dragon.core.framework import proto_util
from dragon.core.framework import workspace
from dragon.core.util import nest


class OpInfo(object):
    """A class to store the op states."""

    def __init__(self):
        """
        Initialize the object.

        Args:
            self: (todo): write your description
        """
        self._defs = dict()
        self._targets = set()

    def add_def(self, index, op_def):
        """Add a operator definition."""
        self._defs[index] = op_def

    def add_target(self, target):
        """Add an extra target relied by inputs."""
        self._targets.add(target)

    def merge_from(self, other):
        """
        Merge two set objects.

        Args:
            self: (todo): write your description
            other: (todo): write your description
        """
        if hasattr(other, '_op') and other._op is not None:
            self._defs = {**self._defs, **other._op._defs}
            self._targets = self._targets.union(other._op._targets)


class OpDef(object):
    """A helper to create op def."""

    @staticmethod
    def apply(
        op_type,
        inputs=(),
        outputs=None,
        num_outputs=1,
        extra_inputs=None,
        name=None,
        **kwargs
    ):
        """Create operator def for outputs."""
        op_info = OpInfo()

        # Collect inputs.
        inputs = nest.flatten(inputs)
        for input in inputs:
            op_info.merge_from(input)

        if extra_inputs is not None:
            extra_inputs = nest.flatten(extra_inputs)
            for input in extra_inputs:
                op_info.merge_from(input)
                op_info.add_target(input.id)

        # Create outputs.
        if outputs is None:
            outputs = []
            current_ws = workspace.get_workspace()
            name_scope = context.get_name_scope()
            for i in range(num_outputs):
                outputs.append(TensorRef(
                    current_ws.unique_name(
                        name_scope + (name if name else op_type),
                        suffix=':{}'.format(i),
                        namespace='Tensor')))
        else:
            outputs = nest.flatten(outputs)
            num_outputs = len(outputs)

        # Construct Def.
        op_index, op_name = OpDef.get_index_and_name()
        op_info.add_def(
            op_index, proto_util.make_operator_def(
                name=op_name,
                op_type=op_type,
                inputs=[input.id for input in inputs],
                outputs=[output.id for output in outputs],
                device_option=proto_util.get_default_device_option(),
                **kwargs
            ))

        # Blend the op for outputs.
        for output in outputs:
            output._op = op_info

        # Infer the spec for outputs.
        outputs = OpDef.add_spec(
            op_type=op_type,
            arguments=kwargs,
            inputs=inputs,
            outputs=outputs,
        )

        # Return the outputs.
        return outputs[0] if num_outputs == 1 else outputs

    @staticmethod
    def add_spec(op_type, arguments, inputs, outputs):
        """Add the predefined spec for outputs."""
        spec_func = op_spec.get(op_type)
        if spec_func is None:
            spec_func = op_spec.get('Unchanged')
        return spec_func(arguments, inputs, outputs)

    @staticmethod
    def get_index_and_name():
        """Return an unique op name and index."""
        name = workspace.get_workspace().unique_name(
            'Op', namespace='Op', zero_based=False)
        return int(name.split('_')[-1]), name

    @staticmethod
    def get_name():
        """Return an unique op name."""
        return OpDef.get_index_and_name()[1]
