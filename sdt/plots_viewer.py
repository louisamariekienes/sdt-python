# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 12:04:36 2015

@author: lukas
"""
import os

from PyQt4.QtCore import Qt, pyqtSlot
from PyQt4 import uic

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

_references = set()

#load ui file from same directory
path = os.path.dirname(os.path.abspath(__file__))
pvClass, pvBase = uic.loadUiType(os.path.join(path, "plots_viewer.ui"))

class PlotsViewer(pvBase):
    def __init__(self, x, y, index, parent=None):
        super().__init__(parent)

        self._ui = pvClass()
        self._ui.setupUi(self)

        self.figure = Figure()
        self._canvas = FigureCanvas(self.figure)
        self._ui.centralLayout.insertWidget(0, self._canvas)

        self.axes = self.figure.add_subplot(111)
        self.axes.hold(False)

        self._x = x
        self._y = y
        self._index = index
        self._current = 0
        self._ui.selectorBox.setRange(0, len(index) - 1)
        self.plot()

        self._ui.selectorBox.valueChanged.connect(self._changePlotSlot)
        self._ui.checkInteresting.stateChanged.connect(self._interestingSlot)

        self.interesting = set()

    def plot(self):
        curr_ind = self._index[self._ui.selectorBox.value()]

        self.axes.plot(self._x(curr_ind), self._y(curr_ind))
        self.axes.set_title(str(curr_ind))
        self._canvas.draw()

    @pyqtSlot()
    def _changePlotSlot(self):
        if self._index[self._ui.selectorBox.value()] in self.interesting:
            self._ui.checkInteresting.setChecked(True)
        else:
            self._ui.checkInteresting.setChecked(False)

        self.plot()

    def _interestingSlot(self, state):
        if state == Qt.Unchecked:
            self.interesting.remove(self._index[self._ui.selectorBox.value()])
        else:
            self.interesting.add(self._index[self._ui.selectorBox.value()])


def ipython_run(x, y, index):
    win = PlotsViewer(x, y, index)

    win.setAttribute(Qt.WA_DeleteOnClose)
    win.show()

    return win

#Usage example:
#w = ipython_run(lambda i: [x for x in range(10)],
#                lambda i: [y**i for y in range(10)],
#                [i for i in range(5)])