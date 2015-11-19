# -*- coding: utf-8 -*-
"""Correct for inhomogeneous illumination

The intensity cross section of a laser beam is usually not flat, but a
Gaussian curve or worse. That means that flourophores closer to the edges of
the image will appear dimmer simply because they do not receive so much
exciting laser light.

This module helps correcting for that using images of a homogeneous surface.

Attributes
----------
pos_colums : list of str
    Names of the columns describing the x and the y coordinate of the features
    in pandas.DataFrames. Defaults to ["x", "y"].
mass_column : str
    Name of the column describing the integrated intensities ("masses") of the
    features. Defaults to "mass".
"""
import pandas as pd
import numpy as np

import pims

from . import gaussian_fit as gfit


pd.options.mode.chained_assignment = None #Get rid of the warning


pos_columns = ["x", "y"]
mass_column = "mass"


class Corrector(object):
    """Correct for inhomogeneous illumination

    This works by multiplying features' integrated intensities ("mass") by
    a position-dependent correction factor calculated from a series of
    images of a homogeneous surface.

    The factor is calculated by
    - Taking the averages of the pixel intensities of the images
    - If requested, doing a 2D Gaussian fit
    - Normalizing, so that the maximum of the Gaussian or of the average image
      (if on Gaussian fit was performed) equals 1.0
    Now, the integrated intesity of a feature at position x, y is divided by
    the value of the Gaussian at the positon x, y (or the pixel intensity of
    the image) to yield a corrected value.

    Attributes
    ----------
    pos_columns : list of str
        Names of the columns describing the x and the y coordinate of the
        features.
    mass_column : str
        Name of the column describing the integrated intensities ("masses") of
        the features.
    avg_img : numpy.ndarray
        Averaged image pixel data
    """

    def __init__(self, *images, gaussian_fit=True, pos_columns=pos_columns,
                 mass_column=mass_column):
        """Constructor

        Parameters
        ----------
        images : lists of numpy.ndarrays
            List of images of a homogeneous surface
        gaussian_fit : bool, optional
            Whether to fit a Gaussian to the averaged image. Default: True
        pos_columns : list of str, optional
            Sets the `pos_columns` attribute. Defaults to the `pos_columns`
            attribute of the module.
        mass_column : str
            Sets the `mass_column` attribute. Defaults to the `mass_column`
            attribute of the module.
        """
        self.pos_columns = pos_columns
        self.mass_column = mass_column

        self.avg_img = np.zeros(images[0][0].shape, dtype=np.float)
        for stack in images:
            for img in stack:
                # divide by max so that intensity fluctuations don't affect
                # the results
                self.avg_img += img/img.max()
        self.avg_img /= self.avg_img.max()

        self._do_fit = gaussian_fit
        if gaussian_fit:
            self._gauss_parm, success = gfit.FitGauss2D(self.avg_img)
            if success > 2:
                raise RuntimeError("Gaussian fit did not converge")
            # normalization factor so that the maximum of the Gaussian is 1.
            self._gauss_norm = 1./(self._gauss_parm[0]+self._gauss_parm[6])
            # Gaussian function
            self._gauss_func = gfit.Gaussian2D(*self._gauss_parm)

    def __call__(self, data, inplace=False):
        """Do brightness correction on `features` intensities

        Parameters
        ----------
        data : pandas.DataFrame or pims.FramesSequence or array-like
            data to be processed. If a pandas.Dataframe, correct the "mass"
            column according to the particle position in the laser beam.
            Otherwise, `pims.pipeline` is used to correct raw image data. This
            requires pims version > 0.2.2.
        inplace : bool, optional
            Only has an effect if `data` is a DataFrame. If True, the
            feature intensities will be corrected in place. Defaults to False.

        Returns
        -------
        pandas.DataFrame or pims.SliceableIterable or numpy.array
            If `data` is a DataFrame and `inplace` is False, return the
            corrected frame. If `data` is raw image data, return corrected
            images
        """
        if isinstance(data, pd.DataFrame):
            x = self.pos_columns[0]
            y = self.pos_columns[1]
            if not inplace:
                data = data.copy()
            data[self.mass_column] *= self.get_factors(data[x], data[y])
            if not inplace:
                # copied previously, now return
                return data
        else:
            @pims.pipeline
            def corr(img):
                if self._do_fit:
                    return img/(self._gauss_func(*np.indices(img.shape)) *
                                self._gauss_norm)
                else:
                    return img/self.avg_img
            return corr(data)

    def get_factors(self, x, y):
        """Get correction factors at positions x, y

        Depending on whether gaussian_fit was set to True or False in the
        constructor, the correction factors for each feature that described by
        an x and a y coordinate is calculated either from the Gaussian fit
        or the average image itself.

        Parameters
        ----------
        x, y : list of float
            x and y coordinates of features

        Returns
        -------
        numpy.ndarray
            A list of correction factors corresponding to the features
        """
        if self._do_fit:
            return 1./(self._gauss_norm*self._gauss_func(y, x))
        else:
            return 1./self.avg_img[np.round(y), np.round(x)]
