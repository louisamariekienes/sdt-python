"""Function to restrict peak localization to a ROI"""
from ..image_tools import PathROI


def restrict_roi(locate_func, buffer=0):
    """Restrict a ``locate`` or ``batch`` function to a ROI

    Create a function that takes a path describing a ROI as an additional
    parameter and applies ``locate`` or ``batch`` (or whatever takes something
    that :py:class:`sdt.image_tools.PathROI` can deal with as its first
    argument) to the ROI only.

    Parameters
    ----------
    locate_func : callable
        locate/batch function to use on the ROI
    buffer : float
        The ROI is enlarged by this many pixels before applying to the
        image data to avoid boundary artefacts. After localizing, peaks that
        are not contained in the (unbuffered) ROI are filtered out.

    Returns
    -------
    callable
        Version of ``locate_func`` that is restrictable to a ROI.
    """
    def restricted_locate(frames, roi, *args, **kwargs):
        """Process a ROI in an image or image sequence using :py:func:`{fname}`

        This chooses a region of interest in an image (or image sequence)
        before calling :py:func:`{fname}`.

        Parameters
        ----------
        frames : numpy.ndarray or iterable of numpy.ndarrays
            Iterable of array-like objects that represent image data
        roi : path
            This is used by the :py:class:`sdt.image_tools.PathROI` constructor
            to create the ROI
        reset_origin : bool, optional
            If True, the top-left corner coordinates of the path's bounding
            rectangle will be subtracted off all feature coordinates, i. e.
            the top-left corner will be the new origin. Defaults to True.
            This is a keyword-only argument.
        *args
            Positional arguments passed to :py:func:`{fname}`
        **kwargs
            Keyword arguments passed to :py:func:`{fname}`

        Returns
        -------
        pandas.DataFrame
            Result of the calls to :py:func:`{fname}` restricted to the ROI.
        """
        # slightly larger ROI to avoid boundary artefacts
        img_roi = PathROI(roi, buffer)
        feat_roi = PathROI(roi, no_image=True)

        reset_origin = kwargs.pop("reset_origin", True)

        loc = locate_func(img_roi(frames, fill_value="mean"), *args, **kwargs)

        # since we cropped the image, we have to add to the coordinates
        loc[["x", "y"]] += img_roi.bounding_rect[0]

        # now get only stuff inside the polygon
        loc = feat_roi(loc, reset_origin=reset_origin)

        return loc

    restricted_locate.__doc__ = restricted_locate.__doc__.format(
        fname=locate_func.__name__)
    return restricted_locate
