#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QMessageBox

from coredb import coredb
from coredb.coredb_writer import CoreDBWriter
from view.widgets.resizable_dialog import ResizableDialog
from .subsonic_inflow_dialog_ui import Ui_SubsonicInflowDialog
from .turbulence_model_helper import TurbulenceModelHelper
from .boundary_db import BoundaryDB


class SubsonicInflowDialog(ResizableDialog):
    RELATIVE_PATH = '/subsonicInflow'

    def __init__(self, parent, bcid):
        super().__init__(parent)
        self._ui = Ui_SubsonicInflowDialog()
        self._ui.setupUi(self)

        self._db = coredb.CoreDB()
        self._xpath = BoundaryDB.getXPath(bcid)
        self._turbulenceWidget = TurbulenceModelHelper.createWidget(self._xpath)

        if self._turbulenceWidget is not None:
            self._ui.dialogContents.layout().addWidget(self._turbulenceWidget)

        self._load()

    def accept(self):
        path = self._xpath + self.RELATIVE_PATH

        writer = CoreDBWriter()
        writer.append(path + '/flowDirection/x', self._ui.xComponent.text(), self.tr("X-Component"))
        writer.append(path + '/flowDirection/y', self._ui.yComponent.text(), self.tr("Y-Component"))
        writer.append(path + '/flowDirection/z', self._ui.zComponent.text(), self.tr("Z-Component"))
        writer.append(path + '/totalPressure', self._ui.totalPressure.text(), self.tr("Pressure"))
        writer.append(path + '/totalTemperature', self._ui.totalTemperature.text(), self.tr("Pressure"))

        if self._turbulenceWidget is not None:
            self._turbulenceWidget.appendToWriter(writer)

        errorCount = writer.write()
        if errorCount > 0:
            QMessageBox.critical(self, self.tr("Input Error"), writer.firstError().toMessage())
        else:
            super().accept()

    def _load(self):
        path = self._xpath + self.RELATIVE_PATH

        self._ui.xComponent.setText(self._db.getValue(path + '/flowDirection/x'))
        self._ui.yComponent.setText(self._db.getValue(path + '/flowDirection/y'))
        self._ui.zComponent.setText(self._db.getValue(path + '/flowDirection/z'))
        self._ui.totalPressure.setText(self._db.getValue(path + '/totalPressure'))
        self._ui.totalTemperature.setText(self._db.getValue(path + '/totalTemperature'))

        if self._turbulenceWidget is not None:
            self._turbulenceWidget.load()