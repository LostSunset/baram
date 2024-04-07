#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import qasync
from PySide6.QtWidgets import QMessageBox

from widgets.async_message_box import AsyncMessageBox

from baramFlow.coredb import coredb
from baramFlow.coredb.coredb_writer import CoreDBWriter
from baramFlow.coredb.general_db import GeneralDB, SolverType
from baramFlow.openfoam.file_system import FileSystem
from baramFlow.view.widgets.content_page import ContentPage
from .general_page_ui import Ui_GeneralPage


logger = logging.getLogger(__name__)

GRAVITY_XPATH = GeneralDB.OPERATING_CONDITIONS_XPATH + '/gravity'


class GeneralPage(ContentPage):
    def __init__(self, parent):
        super().__init__(parent)
        self._ui = Ui_GeneralPage()
        self._ui.setupUi(self)

        self._timeTransient = None

        self._load()

        if GeneralDB.getSolverType() == SolverType.DENSITY_BASED:
            self._ui.transient_.setEnabled(False)

    @qasync.asyncSlot()
    async def save(self):
        writer = CoreDBWriter()

        timeTransient = self._ui.transient_.isChecked()

        writer.append(GeneralDB.GENERAL_XPATH + '/timeTransient', 'true' if timeTransient else 'false', None)
        writer.append(GRAVITY_XPATH + '/direction/x', self._ui.gravityX.text(), self.tr('Gravity X'))
        writer.append(GRAVITY_XPATH + '/direction/y', self._ui.gravityY.text(), self.tr('Gravity Y'))
        writer.append(GRAVITY_XPATH + '/direction/z', self._ui.gravityZ.text(), self.tr('Gravity Z'))
        writer.append(GeneralDB.OPERATING_CONDITIONS_XPATH + '/pressure',
                      self._ui.operatingPressure.text(), self.tr("Operating Pressure"))

        errorCount = writer.write()
        if errorCount > 0:
            await AsyncMessageBox().critical(self, self.tr("Input Error"), writer.firstError().toMessage())
            return False

        if timeTransient and not self._timeTransient and FileSystem.hasCalculationResults():
            confirm = await AsyncMessageBox().question(
                self, self.tr("Change to Transient Mode"),
                self.tr('Use the final result for the initial value of transient calculation?'))
            if confirm == QMessageBox.StandardButton.Yes:
                FileSystem.latestTimeToZero()

        self._timeTransient = timeTransient

        return True

    def _load(self):
        db = coredb.CoreDB()

        self._timeTransient = GeneralDB.isTimeTransient()
        if self._timeTransient:
            self._ui.transient_.setChecked(True)
        else:
            self._ui.steady.setChecked(True)

        if GeneralDB.isDensityBased():
            self._ui.gravity.setEnabled(False)
            self._ui.gravityX.setText('0')
            self._ui.gravityY.setText('0')
            self._ui.gravityZ.setText('0')
            self._ui.operatingPressure.setEnabled(False)
            self._ui.operatingPressure.setText('0')
        else:
            self._ui.gravityX.setText(db.getValue(GRAVITY_XPATH + '/direction/x'))
            self._ui.gravityY.setText(db.getValue(GRAVITY_XPATH + '/direction/y'))
            self._ui.gravityZ.setText(db.getValue(GRAVITY_XPATH + '/direction/z'))
            self._ui.operatingPressure.setText(db.getValue(GeneralDB.OPERATING_CONDITIONS_XPATH + '/pressure'))

