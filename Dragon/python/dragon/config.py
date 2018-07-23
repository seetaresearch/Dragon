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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import logging
logger = logging.getLogger('dragon')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

from dragon.import_c_apis import *

option = {}

REGISTERED_OPERATORS = set(s for s in RegisteredOperatorsCC())
NO_GRADIENT_OPERATORS = set(s for s in NoGradientOperatorsCC())

# The current device, 'CPU' or 'CUDA'
option['device'] = 'CPU'

# The device id
option['gpu_id'] = 0

# Whether to use cuDNN if possible
option['use_cudnn'] = False

# The global random seed
option['random_seed'] = 3

# Disable the memonger if true
option['debug_mode'] = False

# Whether to share grads
option['share_grads'] = True

# Whether to log the meta graphs
option['log_meta_graph'] = False

# The prefix of exporting directory
# An empty string leads to invalid exporting
option['export_meta_graph'] = ''

# Whether to log the optimized graphs
option['log_optimized_graph'] = False


def EnableCPU():
    """Enable CPU mode globally.

    Returns
    -------
    None

    """
    global option
    option['device'] = 'CPU'


def IsCUDADriverSufficient():
    """Is CUDADriver sufficient?

    Returns
    -------
    boolean
        ``True`` if your device(s) support CUDA otherwise ``False``.

    References
    ----------
    The wrapper of ``IsCUDADriverSufficientCC``.

    """
    return IsCUDADriverSufficientCC()


def EnableCUDA(gpu_id=0, use_cudnn=True):
    """Enable CUDA mode globally.

    Parameters
    ----------
    gpu_id : int
        The id of GPU to use.
    use_cudnn : boolean
        Whether to use cuDNN if available.

    Returns
    -------
    None

    """
    global option
    option['device'] = 'CUDA'
    option['gpu_id'] = gpu_id
    option['use_cudnn'] = use_cudnn

# TODO(PhyscalX): please not use @setter
# TODO(PhyscalX): seems that it can't change the global value


def SetRandomSeed(seed):
    """Set the global random seed.

    Parameters
    ----------
    seed : int
        The seed to use.

    Returns
    -------
    None

    """
    global option
    option['random_seed'] = seed


def GetRandomSeed():
    """Get the global random seed.

    Returns
    -------
    int
        The global random seed.

    """
    global option
    return option['random_seed']


def SetGPU(id):
    """Set the global id GPU.

    Parameters
    ----------
    id : int
        The id of GPU to use.

    Returns
    -------
    None

    """
    global option
    option['gpu_id'] = id


def GetGPU():
    """Get the global id of GPU.

    Returns
    -------
    int
        The global id of GPU.

    """
    global option
    return option['gpu_id']


def SetDebugMode(enabled=True):
    """Enable Debug mode globally.

    It will disable all memory sharing optimizations.

    Parameters
    ----------
    enabled : boolean
        Whether to enable debug mode.

    Returns
    -------
    None

    """
    global option
    option['debug_mode'] = enabled


def LogMetaGraph(enabled=True):
    """Enable to log meta graph globally.

    The meta graph is a describer generated by the VM frontend.

    Parameters
    ----------
    enabled : boolean
        Whether to enable logging.

    Returns
    -------
    None

    """
    global option
    option['log_meta_graph'] = enabled


def LogOptimizedGraph(enabled=True):
    """Enable to log optimized graph globally.

    The optimized graph is a describer optimized by the VM backend.

    Parameters
    ----------
    enabled : boolean
        Whether to enable logging.

    Returns
    -------
    None

    """
    global option
    option['log_optimized_graph'] = enabled


def ExportMetaGraph(prefix=''):
    """Enable to export all runnable meta graphs into text files.

    These text files will be saved as the following format:

    ``prefix/Graph_xxx.metatxt``

    Note that an empty prefix will leads to invalid exporting.

    Parameters
    ----------
    prefix : str
        The prefix of the exporting.

    Returns
    -------
    None

    """
    global option
    option['export_meta_graph'] = prefix


def SetLoggingLevel(level):
    """Set the minimum level of Logging.

    Parameters
    ----------
    level : str
        The level, ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR`` or ``FATAL``.

    Notes
    -----
    The default level is ``INFO``.

    """
    SetLogLevelCC(level)
    global logger
    logger.setLevel({
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'FATAL': logging.CRITICAL
    }[level])


def SetLoggingFile(log_file):
    """Redirect the logging into the specific file.

    Parameters
    ----------
    log_file : str
        The file for logging.

    Notes
    -----
    The function will disable all possible logging at the terminal.

    """
    global logger
    new_logger = logging.getLogger('dragon_filehandler')
    new_logger.setLevel(logger.level)
    file_handler = logging.FileHandler(log_file, mode="w", encoding="UTF-8")
    new_logger.addHandler(file_handler)
    logger = new_logger