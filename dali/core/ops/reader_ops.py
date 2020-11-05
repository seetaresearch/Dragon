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
"""Reader ops."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import multiprocessing as mp
import os

try:
    from nvidia.dali import ops
    from nvidia.dali import tfrecord
except ImportError:
    from dragon.core.util import deprecation
    ops = deprecation.NotInstalled('nvidia.dali')
    tfrecord = deprecation.NotInstalled('nvidia.dali')

from dragon.core.io import reader
from dragon.core.io import kpl_record
from dragon.vm.dali.core.framework import context
from dragon.vm.dali.core.ops.builtin_ops import ExternalSource


class KPLRecordReader(object):
    """Read examples from the KPLRecord.

    Examples:

    ```python
    class MyPipeline(dali.Pipeline):

        def __init__():
            super(MyPipeline, self).__init__()
            # Assume the we have the following data:
            # /data/root.data
            # /data/root.index
            # /data/root.meta
            self.reader = dali.ops.KPLRecordReader(
                path='/data'
                features=('image', 'label'),
                pipeline=self,
                # Shuffle locally in the next ``initial_fill`` examples
                # It turns to be weak with the decreasing of ``initial_fill``
                # and disabled if ``initial_fill`` is set to **1**
                random_shuffle=True,
                initial_fill=1024,
            )

        def iter_step(self):
            self.reader.feed_inputs()

        def define_graph(self):
            inputs = self.reader()
    ```

    """

    def __init__(
        self,
        path,
        features,
        pipeline,
        shard_id=0,
        num_shards=1,
        random_shuffle=False,
        initial_fill=1024,
        **kwargs
    ):
        """Create a ``KPLRecordReader``.

        Parameters
        ----------
        path : str
            The folder of record files.
        features : Sequence[str], required
            The name of features to extract.
        pipeline : nvidia.dali.Pipeline, required
            The pipeline to connect to.
        shard_id : int, optional, default=0
            The index of partition to read.
        num_shards : int, optional, default=1
            The total number of partitions over dataset.
        random_shuffle : bool, optional, default=False
            Whether to shuffle the data.
        initial_fill : int, optional, default=1024
            The length of sampling sequence for shuffle.

        """
        self._pipe = pipeline
        self._batch_size = pipeline.batch_size
        self._prefetch_depth = pipeline._prefetch_queue_depth
        self._reader = reader.DataReader(
            dataset=kpl_record.KPLRecordDataset,
            source=path,
            part_idx=shard_id,
            num_parts=num_shards,
            shuffle=random_shuffle,
            initial_fill=initial_fill,
            **kwargs
        )
        self._buffer = self._reader.q_out = mp.Queue(
            self._prefetch_depth * self._batch_size)
        self._reader.start()

        with context.device('cpu'):
            self.features = dict((k, ExternalSource()) for k in features)

        def cleanup():
            """
            Terminate the context manager.

            Args:
            """
            self.terminate()

        import atexit
        atexit.register(cleanup)

    def example_to_data(self, example):
        """Define the translation from example to array data.

        Override this method to implement the translation.

        """
        raise NotImplementedError

    def feed_inputs(self):
        """Feed the data to edge references.

        Call this method in the ``Pipeline.iter_setup(...)``.

        """
        feed_dict = collections.defaultdict(list)
        for i in range(self._pipe.batch_size):
            data = self.example_to_data(self._buffer.get())
            for k, v in data.items():
                feed_dict[k].append(v)
        for k, v in self.features.items():
            self._pipe.feed_input(self.features[k], feed_dict[k])

    def terminate(self):
        """Terminate the reader."""
        self._reader.terminate()
        self._reader.join()

    def __call__(self, *args, **kwargs):
        """Create the edge references for features.

        Call this method in the ``Pipeline.define_graph(...)``.

        Returns
        -------
        Dict[str, _EdgeReference]
            The feature reference dict.

        """
        self.features = dict((k, v()) for k, v in self.features.items())
        return self.features


class TFRecordReader(object):
    """Read examples from the TFRecord.

    Examples:

    ```python
    # Assume the we have the following data:
    # /data/00001.data
    # /data/00001.index
    # /data/FEATURES
    database = '/data'
    input = dali.ops.TFRecordReader(
        path=database,
        # Shuffle locally in the next ``initial_fill`` examples
        # It turns to be weak with the decreasing of ``initial_fill``
        # and disabled if ``initial_fill`` is set to **1**
        random_shuffle=True,
        initial_fill=1024,
    )
    ```

    """

    def __new__(
        cls,
        path,
        shard_id=0,
        num_shards=1,
        random_shuffle=False,
        initial_fill=1024,
        **kwargs
    ):
        """Create a ``TFRecordReader``.

        Parameters
        ----------
        path : str
            The folder of record files.
        shard_id : int, optional, default=0
            The index of partition to read.
        num_shards : int, optional, default=1
            The total number of partitions over dataset.
        random_shuffle : bool, optional, default=False
            Whether to shuffle the data.
        initial_fill : int, optional, default=1024
            The length of sampling sequence for shuffle.

        Returns
        -------
        nvidia.dali.ops.TFRecordReader
            The reader instance.

        """
        path, index_path, features = cls.check_files(path)
        return ops.TFRecordReader(
            path=path,
            index_path=index_path,
            shard_id=shard_id,
            num_shards=num_shards,
            features=features,
            random_shuffle=random_shuffle,
            initial_fill=initial_fill,
            **kwargs
        )

    @staticmethod
    def check_files(path):
        """
        Check that the data files.

        Args:
            path: (str): write your description
        """
        data_files, index_files, features_file = [], [], None
        for file in os.listdir(path):
            if file.endswith('.data'):
                data_files.append(file)
            elif file.endswith('.index'):
                index_files.append(file)
            elif file == 'FEATURES':
                features_file = file
        if features_file is None:
            raise FileNotFoundError('File <FEATURES> is missing.')
        with open(os.path.join(path, features_file), 'r') as f:
            features = f.read()
            features = features.replace('tf.', 'tfrecord.')
            features = features.replace('tf.io.', 'tfrecord.')
            features = eval(features)
        data_files.sort()
        index_files.sort()
        data = [os.path.join(path, e) for e in data_files]
        index = [os.path.join(path, e) for e in index_files]
        return data, index, features
