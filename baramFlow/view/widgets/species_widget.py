#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QGroupBox, QFormLayout, QLineEdit

from baramFlow.coredb import coredb
from baramFlow.coredb.coredb_writer import boolToDBText
from baramFlow.coredb.material_db import MaterialDB, MaterialType


class SpeciesWidget(QGroupBox):
    def __init__(self, mid, species=None, optional=False):
        super().__init__()

        self._db = coredb.CoreDB()
        self._mid = mid

        self._on = False
        self._layout = None
        self._species = {}
        self._optional = optional

        self.setTitle(MaterialDB.getName(self._mid))
        self.setCheckable(self._optional)
        self.setChecked(False)

        if MaterialDB.getType(self._mid) == MaterialType.MIXTURE:
            self._on = True
            self._layout = QFormLayout(self)
            for mid, name in species or self._db.getSpecies(mid):
                editor = QLineEdit()
                self._layout.addRow(name, editor)
                self._species[mid] = (name, editor)

    def mid(self):
        return self._mid

    def species(self):
        return self._species.keys()

    def on(self):
        return self._on

    def load(self, speciesXPath):
        if self._on:
            xpath = f'{speciesXPath}/mixture[mid="{self._mid}"]'
            if self._db.exists(xpath):
                if self._optional:
                    self.setChecked(self._db.getAttribute(xpath, 'disabled') == 'false')

                for mid in self._species:
                    _, editor = self._species[mid]
                    editor.setText(self._db.getValue(f'{xpath}/specie[mid="{mid}"]/value'))
            else:
                self.setChecked(False)
                for mid in self._species:
                    _, editor = self._species[mid]
                    editor.setText('0')

    def appendToWriter(self, writer, speciesXPath):
        if self._on:
            xpath = f'{speciesXPath}/mixture[mid="{self._mid}"]'
            if self._optional:
                writer.setAttribute(xpath, 'disabled', boolToDBText(not self.isChecked()))
                if not self.isChecked():
                    return True

            for mid, row in self._species.items():
                fieldName, editor = row
                writer.append(f'{xpath}/specie[mid="{mid}"]/value',
                              editor.text(), fieldName)

        return True
