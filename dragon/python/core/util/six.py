# Copyright (c) 2010-2019 Benjamin Peterson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Utilities for writing code that runs on Python 2 and 3"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import types


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3


if PY3:
    integer_types = int,
    string_types = str,
else:
    integer_types = (int, long)
    string_types = (str, unicode)


if PY3:
    import collections.abc
    collections_abc = collections.abc
else:
    import collections
    collections_abc = collections


if PY3:
    def get_unbound_function(unbound):
        """
        Get unbound unbound function.

        Args:
            unbound: (str): write your description
        """
        return unbound
else:
    def get_unbound_function(unbound):
        """
        Returns the unbound unbound function.

        Args:
            unbound: (str): write your description
        """
        return unbound.im_func


def _import_module(name):
    """Import module, returning the module after the last dot."""
    __import__(name)
    return sys.modules[name]


class _LazyDescr(object):

    def __init__(self, name):
        """
        Sets the name.

        Args:
            self: (todo): write your description
            name: (str): write your description
        """
        self.name = name

    def __get__(self, obj, tp):
        """
        Get the value of the given object.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            tp: (int): write your description
        """
        result = self._resolve()
        setattr(obj, self.name, result)  # Invokes __set__.
        try:
            # This is a bit ugly, but it avoids running this again by
            # removing this descriptor.
            delattr(obj.__class__, self.name)
        except AttributeError:
            pass
        return result


class MovedModule(_LazyDescr):
    def __init__(self, name, old, new=None):
        """
        Initialize a new module.

        Args:
            self: (todo): write your description
            name: (str): write your description
            old: (list): write your description
            new: (list): write your description
        """
        super(MovedModule, self).__init__(name)
        if PY3:
            if new is None:
                new = name
            self.mod = new
        else:
            self.mod = old

    def _resolve(self):
        """
        Resolve the module.

        Args:
            self: (todo): write your description
        """
        return _import_module(self.mod)

    def __getattr__(self, attr):
        """
        Get the value of the given attribute.

        Args:
            self: (todo): write your description
            attr: (str): write your description
        """
        _module = self._resolve()
        value = getattr(_module, attr)
        setattr(self, attr, value)
        return value


class _LazyModule(types.ModuleType):
    def __init__(self, name):
        """
        Initialize a class.

        Args:
            self: (todo): write your description
            name: (str): write your description
        """
        super(_LazyModule, self).__init__(name)
        self.__doc__ = self.__class__.__doc__

    def __dir__(self):
        """
        Returns a list of all the attributes of the given object.

        Args:
            self: (todo): write your description
        """
        attrs = ["__doc__", "__name__"]
        attrs += [attr.name for attr in self._moved_attributes]
        return attrs

    # Subclasses should override this
    _moved_attributes = []


class _MovedItems(_LazyModule):
    """Lazy loading of moved objects"""
    __path__ = []  # mark as package


class _SixMetaPathImporter(object):
    """A meta path importer to import six.moves and its submodules.
    This class implements a PEP302 finder and loader. It should be compatible
    with Python 2.5 and all existing versions of Python3
    """

    def __init__(self, six_module_name):
        """
        Initialize the module.

        Args:
            self: (todo): write your description
            six_module_name: (str): write your description
        """
        self.name = six_module_name
        self.known_modules = {}

    def _add_module(self, mod, *fullnames):
        """
        Add a module to the list.

        Args:
            self: (todo): write your description
            mod: (todo): write your description
            fullnames: (str): write your description
        """
        for fullname in fullnames:
            self.known_modules[self.name + "." + fullname] = mod

    def _get_module(self, fullname):
        """
        Returns the module object by fullname.

        Args:
            self: (todo): write your description
            fullname: (str): write your description
        """
        return self.known_modules[self.name + "." + fullname]

    def find_module(self, fullname, path=None):
        """
        Find a module by fullname.

        Args:
            self: (todo): write your description
            fullname: (str): write your description
            path: (list): write your description
        """
        if fullname in self.known_modules:
            return self
        return None

    def __get_module(self, fullname):
        """
        Returns the module by full name.

        Args:
            self: (todo): write your description
            fullname: (str): write your description
        """
        try:
            return self.known_modules[fullname]
        except KeyError:
            raise ImportError("This loader does not know module " + fullname)

    def load_module(self, fullname):
        """
        Load a module.

        Args:
            self: (todo): write your description
            fullname: (str): write your description
        """
        try:
            # in case of a reload
            return sys.modules[fullname]
        except KeyError:
            pass
        mod = self.__get_module(fullname)
        if isinstance(mod, MovedModule):
            mod = mod._resolve()
        else:
            mod.__loader__ = self
        sys.modules[fullname] = mod
        return mod

    def is_package(self, fullname):
        """
        Return true, if the named module is a package.
        We need this method to get correct spec objects with
        Python 3.4 (see PEP451)
        """
        return hasattr(self.__get_module(fullname), "__path__")

    def get_code(self, fullname):
        """Return None
        Required, if is_package is implemented"""
        self.__get_module(fullname)  # eventually raises ImportError
        return None
    get_source = get_code  # same as get_code


_importer = _SixMetaPathImporter(__name__)


_moved_attributes = [
    MovedModule('pickle', 'cPickle', 'pickle'),
]


for attr in _moved_attributes:
    setattr(_MovedItems, attr.name, attr)
    if isinstance(attr, MovedModule):
        _importer._add_module(attr, "moves." + attr.name)
del attr


_MovedItems._moved_attributes = _moved_attributes
moves = _MovedItems(__name__ + '.moves')
_importer._add_module(moves, 'moves')
