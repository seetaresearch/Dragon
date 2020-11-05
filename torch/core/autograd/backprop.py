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
"""Do back-propagation along the executed functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from dragon.core.util import tls
from dragon.vm.torch.core.autograd import execute


def backward(tensors, grad_tensors=None, retain_graph=False):
    """Compute the derivatives of tensors w.r.t. graph leaves.

    Parameters
    ----------
    tensors : Sequence[dragon.vm.torch.Tensor]
        The derivative targets.
    grad_tensors : Sequence[dragon.vm.torch.Tensor], optional
        The optional gradient of ``tensors``.
    retain_graph : bool, optional, default=False
        **False** to free the graph used to compute grad.

    """
    return execute.run_backward(
        tensors=tensors,
        grad_tensors=grad_tensors,
        retain_graph=retain_graph,
    )


def _new_incrementer():
    """Return a incrementer from 1."""
    i = 0  # Python returns BigInteger.
    while True:
        i += 1
        yield i


class Tape(object):
    """Record the executed functions."""

    UID_GENERATOR = _new_incrementer()

    def __init__(self, retain_graph=False, retain_op_handles=False):
        """
        Initialize the graph.

        Args:
            self: (todo): write your description
            retain_graph: (todo): write your description
            retain_op_handles: (todo): write your description
        """
        self._defs = []
        self._operations = dict()
        self._sources = set()
        self._empty_grads = set()
        self._retain_graph = retain_graph
        self._retain_op_handles = retain_op_handles

    @property
    def defs(self):
        """Return the recorded defs."""
        return self._defs

    @property
    def empty_grads(self):
        """Return the recorded empty grads."""
        return list(self._empty_grads)

    @property
    def operations(self):
        """Return the recorded operations."""
        return self._operations

    @property
    def retain_graph(self):
        """Return whether to retain the graph."""
        return self._retain_graph

    @property
    def retain_op_handles(self):
        """Return whether to retain the op handles."""
        return self._retain_op_handles

    @property
    def sources(self):
        """Return the recorded empty grads."""
        return list(self._sources)

    def add_def(self, op_def):
        """Add a new def."""
        self._defs.append(op_def)

    def add_empty_grad(self, tensor_id):
        """Add an empty grad for optimization."""
        self._empty_grads.add(tensor_id)

    def add_operation(self, op_def):
        """Add a new operation."""
        uid = next(self.UID_GENERATOR)
        self._operations[uid] = op_def

    def add_source(self, tensor_id):
        """Add a source for optimization."""
        self._sources.add(tensor_id)

    def merge_from(self, other):
        """Merge operations from the other."""
        if other is not None:
            self._operations = {**self._operations, **other._operations}
            self._sources = self._sources.union(other._sources)
            self._empty_grads = self._empty_grads.union(other._empty_grads)

    def __enter__(self):
        """Enter the tape into the stack."""
        _GLOBAL_TAPE_STACK.push(self)
        return self

    def __exit__(self, typ, value, traceback):
        """Exit the tape from the stack."""
        _GLOBAL_TAPE_STACK.pop()


def get_default_tape():
    """Return the current default tape."""
    return _GLOBAL_TAPE_STACK.get_default()


# Define a global stack to store the tapes of current thread
_GLOBAL_TAPE_STACK = tls.Stack()
