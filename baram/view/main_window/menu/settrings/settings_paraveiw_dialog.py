#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import platform

from PySide6.QtWidgets import QDialog, QFileDialog, QDialogButtonBox

from baram.coredb.app_settings import AppSettings
from .settings_paraview_dialog_ui import Ui_ParaViewSettingDialog


class SettingsParaViewDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self._ui = Ui_ParaViewSettingDialog()
        self._ui.setupUi(self)

        if path := AppSettings.findParaviewInstalledPath():
            self._ui.filePath.setText(path)
        else:
            self._ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self._connectSignalsSlots()

    def accept(self):
        AppSettings.updateParaviewInstalledPath(self._ui.filePath.text())

        super().accept()

    def _connectSignalsSlots(self):
        self._ui.select.clicked.connect(self._openFileDialog)

    def _openFileDialog(self):
        path = os.environ.get('PROGRAMFILES') if platform.system() == 'Windows' else None
        self._dialog = QFileDialog(self, self.tr('Select ParaView Executable'), path, 'exe (*.exe)')
        self._dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        self._dialog.fileSelected.connect(self._fileSelected)
        self._dialog.open()

    def _fileSelected(self, path):
        self._ui.filePath.setText(path)
        self._ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)