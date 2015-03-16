# -*- coding: utf-8 -*-
"""
Created on Mon Mar 16 16:27:27 2015

@author: lukas
"""

"""Correct for inhomogeneous illumination

The intensity cross section of a laser beam is usually not flat, but a
Gaussian curve or worse. That means that flourophores closer to the edges of
the image will appear dimmer simply because they do not receive so much
exciting laser light.

This module helps correcting for that using images of a homogeneous surface.

Attributes:
    pos_colums (list of str): Names of the columns describing the x and the y
        coordinate of the features in pandas.DataFrames. Defaults to
        ["x", "y"].
    mass_name (str): Name of the column describing the integrated intensities
        ("masses") of the features. Defaults to "mass".

"""
import pandas as pd
import numpy as np

from . import gaussian_fit as gfit


pd.options.mode.chained_assignment = None #Get rid of the warning


pos_columns = ["x", "y"]
mass_name = "mass"


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
    Now, the integrated intesity of a feature at position x, y is devided by
    the value of the Gaussian at the positon x, y (or the pixel intensity of
    the image) to yield a corrected value.

    Attributes:
        pos_columns (list of str): Names of the columns describing the x and
            the y coordinate of the features.
        mass_name (str): Name of the column describing the integrated intensities
            ("masses") of the features.
        avg_img (numpy.array): Averaged image pixel data
    """

    def __init__(self, images, gaussian_fit=False, pos_columns=pos_columns,
                 mass_name=mass_name):
        """Constructor

        Args:
            images (list of numpy.arrays): List of images of a homogeneous
                surface gaussian_fit (bool): Whether to fit a Gaussian to the
                averaged image. Default: False
            pos_columns (list of str): Sets the `pos_columns` attribute.
                Defaults to the `pos_columns` attribute of the module.
            mass_name (str): Sets the `mass_name` attribute.Defaults to the
                `mass_name` attribute of the module.
        """
        self.pos_columns = pos_columns
        self.mass_name = mass_name

        self.avg_img = np.zeros(images[0].shape, dtype=np.float)
        for img in images:
            self.avg_img += img

        self.avg_img /= self.avg_img.max()

        if gaussian_fit:
            g_parm = gfit.FitGauss2D(self.avg_img)
            self._gauss_norm = 1./(g_parm[0][0]+g_parm[0][6])
            self._gauss_func = gfit.Gaussian2D(*g_parm[0])
            self.get_factor = self._get_factor_gauss
        else:
            self.get_factor = self._get_factor_img

    def __call__(self, features):
        """Do brightness correction on `features` intensities

        This modifies the coordinates in place.

        Args:
            features (pandas.DataFrame): The features to be corrected.
        """
        x = self.pos_columns[0]
        y = self.pos_columns[1]
        for idx in features.index:
            features.loc[idx, self.mass_name] *= self.get_factor(
                features.loc[idx, x], features.loc[idx, y])

    def _get_factor_gauss(self, x, y):
        """Get correction factor at position x, y from Gaussian fit"""
        return 1./(self._gauss_norm*self._gauss_func(y, x))

    def _get_factor_img(self, x, y):
        """Get correction factor at position x, y from image"""
        return 1./self.avg_img[np.round(y), np.round(x)]