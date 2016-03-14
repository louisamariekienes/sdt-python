"""Functions to generate batch processing functions from locate

Turn locate functions (that process a single frame) into "batch" processing
functions that process a sequence of images
"""
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

import pandas as pd


num_cpus = multiprocessing.cpu_count()


def make_batch(locate_func):
    """Turn a single image ``locate`` function into a batch processing function

    This is the single-threaded version.

    Parameters
    ----------
    locate_func : callable
        Will be called on every image. The images are passed as the first
        parameter.

    Returns
    -------
    callable
        Batch version of ``locate_func``
    """
    def batch(frames, *args, **kwargs):
        """Process an image stack using :py:func:`locate`

        Apply :py:func:`locate` to each image in ``frames``. The image is
        passed as the first argument. For details on function parameters, see
        the :py:func:`locate` documentation.

        Parameters
        ----------
        frames : iterable of images
            Iterable of array-like objects that represent image data
        *args
            Positional arguments passed to :py:func:`locate`
        **kwargs
            Keyword arguments passed to :py:func:`locate`

        Returns
        -------
        pandas.DataFrame
            Concatenation of DataFrames returned by the individual
            :py:func:`locate` calls. Additionally, there is a "frame"
            column specifying the frame number.
        """
        all_features = []
        for i, img in enumerate(frames):
            features = locate_func(img, *args, **kwargs)

            if not hasattr(img, "frame_no") or img.frame_no is None:
                features["frame"] = i
                # otherwise it has been set in locate()

            all_features.append(features)

        return pd.concat(all_features, ignore_index=True)

    return batch


def make_batch_threaded(locate_func):
    """Turn a single image ``locate`` function into a batch processing function

    This is the multi-threaded version.

    Parameters
    ----------
    locate_func : callable
        Will be called on every image. The images are passed as the first
        parameter.

    Returns
    -------
    callable
        Batch version of ``locate_func``
    """
    def batch(frames, *args, **kwargs):
        """Process an image stack using :py:func:`locate`

        Apply :py:func:`locate` to each image in ``frames``. The image is
        passed as the first argument. For details on function parameters, see
        the:py:func:`{loc_fn}` documentation.

        Parameters
        ----------
        frames : iterable of images
            Iterable of array-like objects that represent image data
        *args
            Positional arguments passed to :py:func:`locate`
        **kwargs
            Keyword arguments passed to :py:func:`locate`

        Returns
        -------
        pandas.DataFrame
            Concatenation of DataFrames returned by the individual
            :py:meth:`locate` calls. Additionally, there is a "frame"
            column specifying the frame number.

        Other parameters
        ----------------
        num_threads : int
            Number of CPU threads to use. Defaults to the number of CPUs.
        """
        num_threads = kwargs.pop("num_threads", num_cpus)

        def func(frame):
            return locate_func(frame, *args, **kwargs)

        all_features = []
        with ThreadPoolExecutor(max_workers=num_threads) as e:
            all_features = list(e.map(func, frames))

        for i, df in enumerate(all_features):
            if "frame" not in df.columns:
                df["frame"] = i

        return pd.concat(all_features, ignore_index=True)

    return batch