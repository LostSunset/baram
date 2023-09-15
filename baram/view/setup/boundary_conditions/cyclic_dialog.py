#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QMessageBox

from baram.coredb import coredb
from baram.coredb.coredb_writer import CoreDBWriter
from baram.coredb.boundary_db import BoundaryDB, BoundaryType
from baram.view.widgets.selector_dialog import SelectorDialog
from .cyclic_dialog_ui import Ui_CyclicDialog
from .coupled_boundary_condition_dialog import CoupledBoundaryConditionDialog


class CyclicDialog(CoupledBoundaryConditionDialog):
    BOUNDARY_TYPE = BoundaryType.CYCLIC
    RELATIVE_XPATH = '/cyclic'

    def __init__(self, parent, bcid):
        super().__init__(parent, bcid)
        self._ui = Ui_CyclicDialog()
        self._ui.setupUi(self)

        self._db = coredb.CoreDB()
        self._xpath = BoundaryDB.getXPath(bcid)
        self._coupledBoundary = None
        self._dialog = None

        self._connectSignalsSlots()
        self._load()

    def accept(self):
        if not self._coupledBoundary:
            QMessageBox.critical(self, self.tr('Input Error'), self.tr('Select Coupled Boundary'))
            return

        writer = CoreDBWriter()
        coupleTypeChanged = self._changeCoupledBoundary(writer, self._coupledBoundary, self.BOUNDARY_TYPE)

        errorCount = writer.write()
        if errorCount == 0:
            if coupleTypeChanged:
                self.boundaryTypeChanged.emit(int(self._coupledBoundary))

            super().accept()
        else:
            QMessageBox.critical(self, self.tr('Input Error'), writer.firstError().toMessage())

    def _connectSignalsSlots(self):
        self._ui.select.clicked.connect(self._selectCoupledBoundary)

    def _load(self):
        self._setCoupledBoundary(self._db.getValue(self._xpath + '/coupledBoundary'))

    def _selectCoupledBoundary(self):
        if not self._dialog:
            self._dialog = SelectorDialog(self, self.tr("Select Boundary"), self.tr("Select Boundary"),
                                          BoundaryDB.getCyclicAMIBoundarySelectorItems(self, self._bcid))
            self._dialog.accepted.connect(self._coupledBoundaryAccepted)

        self._dialog.open()

    def _coupledBoundaryAccepted(self):
        self._setCoupledBoundary(self._dialog.selectedItem())

    def _setCoupledBoundary(self, bcid):
        if bcid != '0':
            self._coupledBoundary = str(bcid)
            self._ui.coupledBoundary.setText(BoundaryDB.getBoundaryText(bcid))
        else:
            self._coupledBoundary = 0
            self._ui.coupledBoundary.setText('')
