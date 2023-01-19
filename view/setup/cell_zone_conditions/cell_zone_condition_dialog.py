#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QMessageBox

from coredb import coredb
from coredb.coredb_writer import CoreDBWriter
from coredb.models_db import TurbulenceModelHelper, ModelsDB
from coredb.cell_zone_db import CellZoneDB, ZoneType
from coredb.general_db import GeneralDB
from coredb.region_db import DEFAULT_REGION_NAME
from .cell_zone_condition_dialog_ui import Ui_CellZoneConditionDialog
from .MRF_widget import MRFWidget
from .porous_zone_widget import PorousZoneWidget
from .sliding_mesh_widget import SlidingMeshWidget
from .actuator_disk_widget import ActuatorDiskWidget
from .variable_source_widget import VariableSourceWidget
from .constant_source_widget import ConstantSourceWidget
from .fixed_value_widget import FixedValueWidget
from .materials_widget import MaterialsWidget


class CellZoneConditionDialog(QDialog):
    def __init__(self, parent, czid, rname=None):
        super().__init__(parent)
        self._ui = Ui_CellZoneConditionDialog()
        self._ui.setupUi(self)

        self._zoneTypeRadios = {
            self._ui.zoneTypeRadioGroup.id(self._ui.none): ZoneType.NONE.value,
            self._ui.zoneTypeRadioGroup.id(self._ui.MRF): ZoneType.MRF.value,
            self._ui.zoneTypeRadioGroup.id(self._ui.porousZone): ZoneType.POROUS.value,
            self._ui.zoneTypeRadioGroup.id(self._ui.slidingMesh): ZoneType.SLIDING_MESH.value,
            self._ui.zoneTypeRadioGroup.id(self._ui.actuatorDisk): ZoneType.ACTUATOR_DISK.value,
        }

        self._czid = czid
        self._rname = rname
        self._db = coredb.CoreDB()
        self._xpath = CellZoneDB.getXPath(self._czid)
        self._name = self._db.getValue(self._xpath + '/name')

        self._materialsWidget = None
        # Zone Type Widgets
        self._MRFZone = None
        self._porousZone = None
        self._slidingMeshZone = None
        self._actuatorDiskZone = None

        layout = self._ui.setting.layout()
        if CellZoneDB.isRegion(self._name):
            self.setWindowTitle(self.tr('Region Condition'))
            self._ui.zoneType.setVisible(False)

            self._ui.singleMaterial.setVisible(False)
            self._materialsWidget = MaterialsWidget(self._rname, ModelsDB.isMultiphaseModelOn())
            layout.addWidget(self._materialsWidget)

            if self._rname:
                self._ui.zoneName.setText(self._rname)
            else:
                self._ui.zoneName.setText(DEFAULT_REGION_NAME)
        else:
            self._ui.zoneName.setText(self._name)

            self._MRFZone = MRFWidget(self._xpath)
            layout.addWidget(self._MRFZone)

            self._porousZone = PorousZoneWidget(self._xpath)
            layout.addWidget(self._porousZone)

            if GeneralDB.isTimeTransient():
                self._slidingMeshZone = SlidingMeshWidget(self._xpath)
                layout.addWidget(self._slidingMeshZone)
            else:
                self._ui.slidingMesh.setEnabled(False)

            self._actuatorDiskZone = ActuatorDiskWidget(self._xpath)
            layout.addWidget(self._actuatorDiskZone)

            self._ui.zoneTypeRadioGroup.idToggled.connect(self._zoneTypeChanged)
        layout.addStretch()

        # Source Terms Widgets
        self._massSourceTerm = VariableSourceWidget(self.tr("Mass"), self._xpath + '/sourceTerms/mass')
        self._energySourceTerm = None
        self._turbulenceSourceTerms = {}
        self._materialSourceTerms = {}

        self._ui.sourceTerms.layout().addWidget(self._massSourceTerm)

        # Fixed Value Widgets
        self._turbulenceFixedValues = {}
        self._temperature = None

        if ModelsDB.isEnergyModelOn():
            self._energySourceTerm = VariableSourceWidget(self.tr("Energy"), self._xpath + '/sourceTerms/energy')
            self._ui.sourceTerms.layout().addWidget(self._energySourceTerm)

            self._temperature = FixedValueWidget(
                self.tr("Temperature"), self.tr("Value (K)"), self._xpath + '/fixedValues/temperature')
            self._ui.fixedValues.layout().addWidget(self._temperature)

        self._setupTurbulenceWidgets()
        self._setupMaterialWidgets(["O2"])

        self._ui.sourceTerms.layout().addStretch()
        self._ui.fixedValues.layout().addStretch()

        self._load()

    def accept(self):
        writer = CoreDBWriter()

        if CellZoneDB.isRegion(self._name):
            if self._materialsWidget:
                self._materialsWidget.appendToWriter(writer)
            else:
                writer.append(self._xpath + '/material', self._ui.singleMaterial.currentData(), None)
        else:
            zoneType = self._getZoneTypeRadioValue()
            writer.append(self._xpath + '/zoneType', zoneType, None)
            if zoneType == ZoneType.MRF.value:
                self._MRFZone.appendToWriter(writer)
            elif zoneType == ZoneType.POROUS.value:
                self._porousZone.appendToWriter(writer)
            elif zoneType == ZoneType.SLIDING_MESH.value:
                self._slidingMeshZone.appendToWriter(writer)
            elif zoneType == ZoneType.ACTUATOR_DISK.value:
                self._actuatorDiskZone.appendToWriter(writer)

        if not self._massSourceTerm.appendToWriter(writer):
            return
        if self._energySourceTerm and not self._energySourceTerm.appendToWriter(writer):
            return
        for field, widget in self._turbulenceSourceTerms.items():
            widget.appendToWriter(writer)

        if self._ui.velocityGroup.isChecked():
            writer.setAttribute(self._xpath + 'fixedValues/velocity', 'disabled', 'false')
            writer.append(self._xpath + '/fixedValues/velocity/velocity/x',
                          self._ui.xVelocity.text(), self.tr("X-Velocity"))
            writer.append(self._xpath + '/fixedValues/velocity/velocity/y',
                          self._ui.yVelocity.text(), self.tr("Y-Velocity"))
            writer.append(self._xpath + '/fixedValues/velocity/velocity/z',
                          self._ui.zVelocity.text(), self.tr("Z-Velocity"))
            writer.append(self._xpath + '/fixedValues/velocity/relaxation',
                          self._ui.relaxation.text(), self.tr("relaxation"))
        else:
            writer.setAttribute(self._xpath + 'fixedValues/velocity', 'disabled', 'true')

        if self._temperature:
            self._temperature.appendToWriter(writer)
        for field, widget in self._turbulenceFixedValues.items():
            widget.appendToWriter(writer)

        errorCount = writer.write()
        if errorCount > 0:
            QMessageBox.critical(self, self.tr("Input Error"), writer.firstError().toMessage())
        else:
            super().accept()

    def _load(self):
        self._getZoneTypeRadio(self._db.getValue(self._xpath + '/zoneType')).setChecked(True)

        if CellZoneDB.isRegion(self._name):
            if self._materialsWidget:
                self._materialsWidget.load()
            else:
                pass
        else:
            self._MRFZone.load()
            self._porousZone.load()
            if self._slidingMeshZone:
                self._slidingMeshZone.load()
            self._actuatorDiskZone.load()

        self._massSourceTerm.load()
        for field, widget in self._turbulenceSourceTerms.items():
            widget.load()

        self._ui.velocityGroup.setChecked(
            self._db.getAttribute(self._xpath + '/fixedValues/velocity', 'disabled') == 'false')
        self._ui.xVelocity.setText(self._db.getValue(self._xpath + '/fixedValues/velocity/velocity/x'))
        self._ui.yVelocity.setText(self._db.getValue(self._xpath + '/fixedValues/velocity/velocity/y'))
        self._ui.zVelocity.setText(self._db.getValue(self._xpath + '/fixedValues/velocity/velocity/z'))
        self._ui.relaxation.setText(self._db.getValue(self._xpath + '/fixedValues/velocity/relaxation'))

        if ModelsDB.isEnergyModelOn():
            self._energySourceTerm.load()
            self._temperature.load()

        for field, widget in self._turbulenceFixedValues.items():
            widget.load()

    def _setupTurbulenceWidgets(self):
        sourceTermsLayout = self._ui.sourceTerms.layout()
        fixedValuesLayout = self._ui.fixedValues.layout()
        for field in TurbulenceModelHelper.getFields():
            self._turbulenceSourceTerms[field] = ConstantSourceWidget(
                field.getTitleText(), field.getLabelText(), self._xpath + '/sourceTerms/' + field.xpathName)
            sourceTermsLayout.addWidget(self._turbulenceSourceTerms[field])
            self._turbulenceFixedValues[field] = FixedValueWidget(
                field.getTitleText(), field.getLabelText(), self._xpath + '/fixedValues/' + field.xpathName)
            fixedValuesLayout.addWidget(self._turbulenceFixedValues[field])

    def _setupMaterialWidgets(self, materials):
        layout = self._ui.sourceTerms.layout()
        # for material in materials:
        #     self._materialSourceTerms[material] = VariableSourceWidget(material)
        #     layout.addWidget(self._materialSourceTerms[material])

    def _zoneTypeChanged(self, id_, checked):
        if checked:
            self._MRFZone.setVisible(self._ui.MRF.isChecked())
            self._porousZone.setVisible(self._ui.porousZone.isChecked())
            if self._slidingMeshZone:
                self._slidingMeshZone.setVisible(self._ui.slidingMesh.isChecked())
            self._actuatorDiskZone.setVisible(self._ui.actuatorDisk.isChecked())

    def _getZoneTypeRadio(self, value):
        return self._ui.zoneTypeRadioGroup.button(
            list(self._zoneTypeRadios.keys())[list(self._zoneTypeRadios.values()).index(value)])

    def _getZoneTypeRadioValue(self):
        return self._zoneTypeRadios[self._ui.zoneTypeRadioGroup.id(self._ui.zoneTypeRadioGroup.checkedButton())]
