#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget

from coredb import coredb
from coredb.boundary_db import KOmegaSpecification
from .turbulence_k_omega_widget_ui import Ui_turbulenceKOmegaWidget


class TurbulenceKOmegaWidget(QWidget):
    RELATIVE_XPATH = '/turbulence/k-omega'

    def __init__(self, xpath):
        super().__init__()
        self._ui = Ui_turbulenceKOmegaWidget()
        self._ui.setupUi(self)

        self._specificationMethods = {
            KOmegaSpecification.K_AND_OMEGA.value: self.tr("K and Omega"),
            KOmegaSpecification.INTENSITY_AND_VISCOSITY_RATIO.value: self.tr("Intensity and Viscosity Ratio"),
        }
        self._setupSpecificationMethodCombo()

        self._db = coredb.CoreDB()
        self._xpath = xpath

        self._connectSignalsSlots()

    def load(self):
        xpath = self._xpath + self.RELATIVE_XPATH

        self._ui.specificationMethod.setCurrentText(
            self._specificationMethods[self._db.getValue(xpath + '/specification')])
        self._ui.turbulentKineticEnergy.setText(self._db.getValue(xpath + '/turbulentKineticEnergy'))
        self._ui.specificDissipationRate.setText(self._db.getValue(xpath + '/specificDissipationRate'))
        self._ui.turbulentIntensity.setText(self._db.getValue(xpath + '/turbulentIntensity'))
        self._ui.turbulentViscosityRatio.setText(self._db.getValue(xpath + '/turbulentViscosityRatio'))
        self._specificationMethodChanged()

    def appendToWriter(self, writer):
        xpath = self._xpath + self.RELATIVE_XPATH

        specification = self._ui.specificationMethod.currentData()
        writer.append(xpath + '/specification', specification, None)
        if specification == KOmegaSpecification.K_AND_OMEGA.value:
            writer.append(xpath + '/turbulentKineticEnergy', self._ui.turbulentKineticEnergy.text(),
                          self.tr("Turbulent Kinetic Energy"))
            writer.append(xpath + '/specificDissipationRate', self._ui.specificDissipationRate.text(),
                          self.tr("Specific Dissipation Rate"))
        elif specification == KOmegaSpecification.INTENSITY_AND_VISCOSITY_RATIO.value:
            writer.append(xpath + '/turbulentIntensity', self._ui.turbulentIntensity.text(),
                          self.tr("Turbulent Intensity"))
            writer.append(xpath + '/turbulentViscosityRatio', self._ui.turbulentViscosityRatio.text(),
                          self.tr("Turbulent Viscosity Ratio"))

    def _connectSignalsSlots(self):
        self._ui.specificationMethod.currentIndexChanged.connect(self._specificationMethodChanged)

    def _setupSpecificationMethodCombo(self):
        for value, text in self._specificationMethods.items():
            self._ui.specificationMethod.addItem(text, value)

    def _specificationMethodChanged(self):
        specification = self._ui.specificationMethod.currentData()
        self._ui.kAndOmega.setVisible(specification == KOmegaSpecification.K_AND_OMEGA.value)
        self._ui.intensityAndViscocityRatio.setVisible(
            specification == KOmegaSpecification.INTENSITY_AND_VISCOSITY_RATIO.value)
