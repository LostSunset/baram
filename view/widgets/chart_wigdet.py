#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget

import numpy as np
import pandas as pd
import matplotlib.ticker as ticker
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qtagg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

END_MARGIN = 0.05  # 5% margin between line end and right axis


class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._data = None
        self._timeMax = None
        self._timeMin = None
        self._lines = {}
        self._logScale = False
        self._initialMaxX = 10

        layout = QtWidgets.QVBoxLayout(self)

        self._canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._canvas.mpl_connect('scroll_event', self._onScroll)

        layout.addWidget(self._canvas)

        self._axes = self._canvas.figure.subplots()
        self.clear()

    def setTitle(self, title):
        self._axes.set_title(title)

    def setMaxX(self, maxX):
        self._initialMaxX = maxX

    def logScaleOn(self):
        self._logScale = True

    def setData(self, data):
        self._data = data
        self._updateChart()

    def appendData(self, data):
        if self._data is None:
            self._data = data
        else:
            self._data = pd.concat([self._data[self._data.index < data.first_valid_index()], data])

        self._updateChart()

    def clear(self):
        self._axes.cla()

        self._data = None
        self._timeMax = None
        self._timeMin = None
        self._lines = {}

        self._axes.grid(alpha=0.6, linestyle='--')
        self._axes.xaxis.set_major_formatter(ticker.FuncFormatter(lambda num, _: '{:g}'.format(num)))
        self._axes.yaxis.set_major_formatter(ticker.FuncFormatter(lambda num, _: '{:g}'.format(num)))
        if self._logScale:
            self._axes.set_yscale('log')

        self._axes.set_xlim([-(self._initialMaxX * END_MARGIN), self._initialMaxX])

        self._canvas.draw()

    def draw(self):
        if self._data is None:
            self.clear()
        else:
            self._updateChart()

    def _updateChart(self):
        d = self._data.reset_index()  # "Time" is back to a column to serve as X value in numpy transpose below

        for c in self._data.columns.values.tolist():
            if c not in self._lines:
                self._lines[c], = self._axes.plot('Time', c, '', label=c, data=d)
                self._lines[c].set_linewidth(0.8)
            else:
                self._lines[c].set_data(d[['Time', c]].to_numpy().transpose())

        timeMax = float(self._data.last_valid_index())
        timeMin = float(self._data.first_valid_index())

        minX, maxX = self._axes.get_xlim()
        chartWidth = (maxX - minX)

        if self._timeMax is None:  # new drawing
            dataWidth = chartWidth * (1 - 2 * END_MARGIN)
            if (timeMax - timeMin) > dataWidth:
                maxX = timeMax + chartWidth * END_MARGIN
                minX = maxX - chartWidth
            else:
                minX = timeMin - END_MARGIN
                maxX = minX + chartWidth
        else:
            if timeMax + chartWidth * END_MARGIN < maxX:
                pass  # keep the range as is
            else:
                maxX = timeMax + chartWidth * END_MARGIN
                minX = maxX - chartWidth

        self._timeMax = timeMax
        self._timeMin = timeMin

        self._axes.set_xlim([minX, maxX])

        self._adjustYRange()

        legend = self._axes.legend()
        for h in legend.legendHandles:
            h.set_linewidth(1.6)

        self._canvas.draw()

    def _onScroll(self, event):
        if self._timeMax is None:
            return

        minX, maxX = self._axes.get_xlim()
        width = maxX - minX

        # this margin will be kept without change
        margin = (maxX - self._timeMax) / width

        scale = np.power(1.05, -event.step)

        newWidth = width * scale

        if scale < 1:  # Zoom in
            # if self._timeMax + width * END_MARGIN >= maxX:
            if minX > self._timeMin or maxX <= self._timeMax + width * END_MARGIN:
                maxX = self._timeMax + newWidth * margin
                minX = self._timeMax - newWidth * (1 - margin)
            else:
                maxX = minX + newWidth
        else:  # Zoom out
            if minX >= self._timeMin:
                maxX = self._timeMax + newWidth * margin
                minX = self._timeMax - newWidth * (1 - margin)
            else:
                maxX = minX + newWidth

        self._axes.set_xlim([minX, maxX])

        self._adjustYRange()

        self._canvas.draw()  # force re-draw the next time the GUI refreshes

    def _adjustYRange(self):
        minY = None
        maxY = None

        minX, maxX = self._axes.get_xlim()

        d = self._data[(self._data.index >= minX) & (self._data.index <= maxX)]

        if minY is None or minY > d.min().min():
            minY = d.min().min()
        if maxY is None or maxY < d.max().max():
            maxY = d.max().max()

        if self._logScale:
            minY = minY / 10  # margin in log scale
            if maxY < 0.1:
                maxY = maxY * 10  # margin in log scale
            else:
                maxY = 1
        else:
            m = (maxY - minY) * 0.05
            if m == 0:
                m = 1
            maxY += m
            minY -= m

        self._axes.set_ylim([minY, maxY])
