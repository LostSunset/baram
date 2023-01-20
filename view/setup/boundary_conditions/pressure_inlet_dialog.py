#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QMessageBox

from coredb import coredb
from coredb.coredb_writer import CoreDBWriter
from coredb.models_db import ModelsDB
from coredb.boundary_db import BoundaryDB
from view.widgets.resizable_dialog import ResizableDialog
from .pressure_inlet_dialog_ui import Ui_PressureInletDialog
from .turbulence_model_helper import TurbulenceModelHelper
from .temperature_widget import TemperatureWidget
from .volume_franction_widget import VolumeFractionWidget


class PressureInletDialog(ResizableDialog):
    RELATIVE_XPATH = '/pressureInlet'

    def __init__(self, parent, bcid):
        super().__init__(parent)
        self._ui = Ui_PressureInletDialog()
        self._ui.setupUi(self)

        self._db = coredb.CoreDB()
        self._xpath = BoundaryDB.getXPath(bcid)
        self._turbulenceWidget = TurbulenceModelHelper.createWidget(self._xpath)
        self._temperatureWidget = TemperatureWidget(self._xpath, bcid)

        layout = self._ui.dialogContents.layout()

        if self._turbulenceWidget:
            layout.addWidget(self._turbulenceWidget)
        if ModelsDB.isEnergyModelOn():
            layout.addWidget(self._temperatureWidget)

        self._volumeFractionWidget = VolumeFractionWidget(bcid)
        if self._volumeFractionWidget.on():
            layout.addWidget(self._volumeFractionWidget)

        self._load()

    def accept(self):
        path = self._xpath + self.RELATIVE_XPATH

        writer = CoreDBWriter()
        writer.append(path + '/pressure', self._ui.totalPressure.text(), self.tr("Total Pressure"))

        if self._turbulenceWidget:
            self._turbulenceWidget.appendToWriter(writer)

        if not self._temperatureWidget.appendToWriter(writer):
            return

        if not self._volumeFractionWidget.appendToWriter(writer):
            return

        errorCount = writer.write()
        if errorCount > 0:
            self._temperatureWidget.rollbackWriting()
            QMessageBox.critical(self, self.tr("Input Error"), writer.firstError().toMessage())
        else:
            self._temperatureWidget.completeWriting()
            super().accept()

    def _load(self):
        path = self._xpath + self.RELATIVE_XPATH

        self._ui.totalPressure.setText(self._db.getValue(path + '/pressure'))

        if self._turbulenceWidget:
            self._turbulenceWidget.load()

        self._temperatureWidget.load()
        self._temperatureWidget.freezeProfileToConstant()

        self._volumeFractionWidget.load()
