# ------------------------------------------------------------
# Copyright (c) 2017-present, SeetaTech, Co.,Ltd.
#
# Licensed under the BSD 2-Clause License.
# You should have received a copy of the BSD 2-Clause License
# along with the software. If not, See,
#
#      <https://opensource.org/licenses/BSD-2-Clause>
#
# ------------------------------------------------------------

"""Maintaining the version here is not a good design.

You can also find the version information in the backend:

    <https://github.com/seetaresearch/Dragon/blob/master/Dragon/include/core/common.h>

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

version = '0.3.0'
full_version = '0.3.0.0'
release = False

if not release:
    version = full_version