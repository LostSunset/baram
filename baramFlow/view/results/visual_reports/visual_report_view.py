#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
from enum import Enum, auto

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QVBoxLayout, QWidget, QColorDialog

from vtkmodules.vtkRenderingCore import vtkActor

from baramFlow.coredb.app_settings import AppSettings
from baramFlow.coredb.visual_report import VisualReport
from baramFlow.openfoam.file_system import FileSystem

from widgets.overlay_frame import OverlayFrame
from widgets.rendering.rotation_center_widget import RotationCenterWidget
from widgets.rendering.ruler_widget import RulerWidget

from .display_control.display_control import DisplayControl

from .visual_report_view_ui import Ui_RenderingView


class DisplayMode(Enum):
    DISPLAY_MODE_FEATURE        = 0
    DISPLAY_MODE_POINTS         = auto()
    DISPLAY_MODE_SURFACE        = auto()
    DISPLAY_MODE_SURFACE_EDGE   = auto()
    DISPLAY_MODE_WIREFRAME      = auto()


class VisualReportView(QWidget):
    actorPicked = Signal(vtkActor, bool)
    renderingModeChanged = Signal(DisplayMode)
    viewClosed = Signal()

    def __init__(self, report: VisualReport):
        super().__init__()

        self._ui = Ui_RenderingView()
        self._ui.setupUi(self)

        self._view = self._ui.view

        self._rotationCenter = None

        self._dialog = None

        self._updateBGButtonStyle(self._ui.bg1, QColor.fromRgbF(*self._view.background1()))
        self._updateBGButtonStyle(self._ui.bg2, QColor.fromRgbF(*self._view.background2()))

        for mode in DisplayMode:
            self._ui.renderingMode.setItemData(mode.value, mode)

        self._overlayFrame = OverlayFrame(self._view)
        self._displayControl = DisplayControl(self._overlayFrame, self._view)
        layout = QVBoxLayout(self._overlayFrame)
        layout.addWidget(self._displayControl)

        self._report = report

        self._connectSignalsSlots()

    def view(self):
        return self._view

    def close(self):
        self._view.close()
        return super().close()

    def renderingMode(self):
        return self._ui.renderingMode.currentData()

    def addActor(self, actor: vtkActor):
        self._view.addActor(actor)

    def removeActor(self, actor):
        self._view.removeActor(actor)

    def refresh(self):
        self._view.refresh()

    def fitCamera(self):
        self._view.fitCamera()

    def _connectSignalsSlots(self):
        self._ui.axis.toggled.connect(self._view.setAxisVisible)
        self._ui.cubeAxis.toggled.connect(self._view.setCubeAxisVisible)
        self._ui.ruler.toggled.connect(self._setRulerVisible)
        self._ui.fit.clicked.connect(self._view.fitCamera)
        self._ui.perspective.toggled.connect(self._view.setParallelProjection)
        self._ui.alignAxis.clicked.connect(self._view.alignCamera)
        self._ui.rotate.clicked.connect(self._view.rollCamera)
        self._ui.rotationCenter.clicked.connect(self._toggleRotationCenter)
        self._ui.renderingMode.currentIndexChanged.connect(self._renderingModeChanged)
        self._ui.bg1.clicked.connect(self._pickBackground1)
        self._ui.bg2.clicked.connect(self._pickBackground2)

        self._view.actorPicked.connect(self.actorPicked)
        self._view.viewClosed.connect(self.viewClosed)

    def _setRulerVisible(self, checked):
        if checked:
            self._ruler = RulerWidget(self._view.interactor(), self._view.renderer())
            self._ruler.on()
        else:
            self._ruler.off()
            self._ruler = None

    def _paraviewFileSelected(self, file):
        casePath = FileSystem.foamFilePath()
        AppSettings.updateParaviewInstalledPath(file)
        subprocess.Popen([f'{file}', f'{casePath}'])

    def _toggleRotationCenter(self, checked):
        if checked:
            self._rotationCenter = self._rotationCenter or RotationCenterWidget(self._view)
            self._rotationCenter.on()
        else:
            self._rotationCenter.off()

    def _renderingModeChanged(self, index):
        self.renderingModeChanged.emit(DisplayMode(index))

    def _pickBackground1(self):
        self._dialog = self._newBGColorDialog()
        self._dialog.colorSelected.connect(self._setBackground1)
        self._dialog.open()

    def _pickBackground2(self):
        self._dialog = self._newBGColorDialog()
        self._dialog.colorSelected.connect(self._setBackground2)
        self._dialog.open()

    def _newBGColorDialog(self):
        dialog = QColorDialog(self)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.setCustomColor(0, QColor(56, 61, 84))
        dialog.setCustomColor(1, QColor(209, 209, 209))

        return dialog

    def _setBackground1(self, color: QColor):
        r, g, b, a = color.getRgbF()
        self._view.setBackground1(r, g, b)
        self._updateBGButtonStyle(self._ui.bg1, color)

    def _setBackground2(self, color: QColor):
        r, g, b, a = color.getRgbF()
        self._view.setBackground2(r, g, b)
        self._updateBGButtonStyle(self._ui.bg2, color)

    def _updateBGButtonStyle(self, button, color: QColor):
        r, g, b, a = color.getRgb()
        button.setStyleSheet(
            f'background: rgb({r}, {g}, {b}); border-style: solid; border-color:black; border-width: 1')
