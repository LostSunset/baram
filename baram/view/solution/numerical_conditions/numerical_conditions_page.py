#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QMessageBox

from baram.coredb import coredb
from baram.coredb.coredb_writer import CoreDBWriter
from baram.coredb.general_db import GeneralDB
from baram.coredb.numerical_db import PressureVelocityCouplingScheme, ImplicitDiscretizationScheme, UpwindDiscretizationScheme
from baram.coredb.numerical_db import NumericalDB
from baram.coredb.models_db import ModelsDB, TurbulenceModel
from baram.view.widgets.content_page import ContentPage
from .numerical_conditions_page_ui import Ui_NumericalConditionsPage
from .advanced_dialog import AdvancedDialog


class NumericalConditionsPage(ContentPage):
    def __init__(self):
        super().__init__()
        self._ui = Ui_NumericalConditionsPage()
        self._ui.setupUi(self)

        self._pressureVelocityCouplingSchemes = {
            PressureVelocityCouplingScheme.SIMPLE.value: self.tr('SIMPLE'),
            PressureVelocityCouplingScheme.SIMPLEC.value: self.tr('SIMPLEC'),
        }

        self._implicitDiscretizationSchemes = {
            ImplicitDiscretizationScheme.FIRST_ORDER_IMPLICIT.value: self.tr('First Order Implicit'),
            ImplicitDiscretizationScheme.SECOND_ORDER_IMPLICIT.value: self.tr('Second Order Implicit'),
        }

        self._upwindDiscretizationSchemes = {
            UpwindDiscretizationScheme.FIRST_ORDER_UPWIND.value: self.tr('First Order Upwind'),
            UpwindDiscretizationScheme.SECOND_ORDER_UPWIND.value: self.tr('Second Order Upwind'),
        }

        self._setupCombo(self._ui.pressureVelocityCouplingScheme, self._pressureVelocityCouplingSchemes)
        self._setupCombo(self._ui.discretizationSchemeTime, self._implicitDiscretizationSchemes)
        self._setupCombo(self._ui.discretizationSchemeMomentum, self._upwindDiscretizationSchemes)
        self._setupCombo(self._ui.discretizationSchemeEnergy, self._upwindDiscretizationSchemes)
        self._setupCombo(self._ui.discretizationSchemeTurbulence, self._upwindDiscretizationSchemes)
        self._setupCombo(self._ui.discretizationSchemeVolumeFraction, self._upwindDiscretizationSchemes)

        self._db = coredb.CoreDB()
        self._xpath = NumericalDB.NUMERICAL_CONDITIONS_XPATH
        self._dialog = None

        self._connectSignalsSlots()

    def _load(self):
        timeIsTransient = GeneralDB.isTimeTransient()
        energyOn = ModelsDB.isEnergyModelOn()
        turbulenceOn = ModelsDB.getTurbulenceModel() not in (TurbulenceModel.INVISCID, TurbulenceModel.LAMINAR)
        multiphaseOn = ModelsDB.isMultiphaseModelOn()

        self._ui.useMomentumPredictor.setVisible(timeIsTransient)

        self._ui.discretizationSchemeTime.setEnabled(timeIsTransient)
        self._ui.discretizationSchemeEnergy.setEnabled(energyOn)
        self._ui.discretizationSchemeTurbulence.setEnabled(turbulenceOn)
        self._ui.discretizationSchemeVolumeFraction.setEnabled(multiphaseOn)

        self._ui.underRelaxationFactorPressureFinal.setEnabled(timeIsTransient)
        self._ui.underRelaxationFactorMomentumFinal.setEnabled(timeIsTransient)
        self._ui.underRelaxationFactorEnergy.setEnabled(energyOn)
        self._ui.underRelaxationFactorEnergyFinal.setEnabled(timeIsTransient and energyOn)
        self._ui.underRelaxationFactorTurbulence.setEnabled(turbulenceOn)
        self._ui.underRelaxationFactorTurbulenceFinal.setEnabled(timeIsTransient and turbulenceOn)
        self._ui.underRelaxationFactorDensityFinal.setEnabled(timeIsTransient)
        self._ui.underRelaxationFactorVolumeFraction.setEnabled(multiphaseOn)
        self._ui.underRelaxationFactorVolumeFractionFinal.setEnabled(timeIsTransient and multiphaseOn)

        self._ui.maxIterationsPerTimeStep.setEnabled(timeIsTransient)
        self._ui.numberOfCorrectors.setEnabled(timeIsTransient)

        if multiphaseOn:
            self._ui.multiphaseMaxIterationsPerTimeStep.setEnabled(timeIsTransient)
            self._ui.multiphaseNumberOfCorrectors.setEnabled(timeIsTransient)
        else:
            self._ui.multiphase.setEnabled(False)

        self._ui.relativePressure.setEnabled(timeIsTransient)
        self._ui.relativeMomentum.setEnabled(timeIsTransient)
        self._ui.absoluteEnergy.setEnabled(energyOn)
        self._ui.relativeEnergy.setEnabled(timeIsTransient and energyOn)
        self._ui.absoluteTurbulence.setEnabled(turbulenceOn)
        self._ui.relativeTurbulence.setEnabled(timeIsTransient and turbulenceOn)
        self._ui.absoluteVolumeFraction.setEnabled(multiphaseOn)
        self._ui.relativeVolumeFraction.setEnabled(timeIsTransient and multiphaseOn)

        self._ui.pressureVelocityCouplingScheme.setCurrentText(
            self._pressureVelocityCouplingSchemes[self._db.getValue(self._xpath + '/pressureVelocityCouplingScheme')])
        self._ui.useMomentumPredictor.setChecked(self._db.getValue(self._xpath + '/useMomentumPredictor') == 'true')
        self._ui.discretizationSchemeTime.setCurrentText(
            self._implicitDiscretizationSchemes[self._db.getValue(self._xpath + '/discretizationSchemes/time')])
        self._ui.discretizationSchemeMomentum.setCurrentText(
            self._upwindDiscretizationSchemes[self._db.getValue(self._xpath + '/discretizationSchemes/momentum')])
        self._ui.discretizationSchemeEnergy.setCurrentText(
            self._upwindDiscretizationSchemes[self._db.getValue(self._xpath + '/discretizationSchemes/energy')])
        self._ui.discretizationSchemeTurbulence.setCurrentText(
            self._upwindDiscretizationSchemes[
                self._db.getValue(self._xpath + '/discretizationSchemes/turbulentKineticEnergy')])
        self._ui.discretizationSchemeVolumeFraction.setCurrentText(
            self._upwindDiscretizationSchemes[self._db.getValue(self._xpath + '/discretizationSchemes/volumeFraction')])

        self._ui.underRelaxationFactorPressure.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/pressure'))
        self._ui.underRelaxationFactorPressureFinal.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/pressureFinal'))
        self._ui.underRelaxationFactorMomentum.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/momentum'))
        self._ui.underRelaxationFactorMomentumFinal.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/momentumFinal'))
        self._ui.underRelaxationFactorEnergy.setText(self._db.getValue(self._xpath + '/underRelaxationFactors/energy'))
        self._ui.underRelaxationFactorEnergyFinal.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/energyFinal'))
        self._ui.underRelaxationFactorTurbulence.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/turbulence'))
        self._ui.underRelaxationFactorTurbulenceFinal.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/turbulenceFinal'))
        self._ui.underRelaxationFactorDensity.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/density'))
        self._ui.underRelaxationFactorDensityFinal.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/densityFinal'))
        self._ui.underRelaxationFactorVolumeFraction.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/volumeFraction'))
        self._ui.underRelaxationFactorVolumeFractionFinal.setText(
            self._db.getValue(self._xpath + '/underRelaxationFactors/volumeFractionFinal'))

        self._ui.limitingFactor.setText(self._db.getValue(self._xpath + '/highOrderTermRelaxation/relaxationFactor'))
        self._ui.improveStablitiy.setChecked(
            self._db.getAttribute(self._xpath + '/highOrderTermRelaxation', 'disabled') == 'false')

        self._ui.maxIterationsPerTimeStep.setText(self._db.getValue(self._xpath + '/maxIterationsPerTimeStep'))
        self._ui.numberOfCorrectors.setText(self._db.getValue(self._xpath + '/numberOfCorrectors'))

        self._ui.multiphaseMaxIterationsPerTimeStep.setText(
            self._db.getValue(self._xpath + '/multiphase/maxIterationsPerTimeStep'))
        self._ui.multiphaseNumberOfCorrectors.setText(
            self._db.getValue(self._xpath + '/multiphase/numberOfCorrectors'))
        if self._db.getValue(self._xpath + '/multiphase/useSemiImplicitMules') == 'true':
            self._ui.mulesSemiImplicit.setChecked(True)
        else:
            self._ui.mullesExplicit.setChecked(True)
        self._ui.phaseInterfaceCompressionFactor.setText(
            self._db.getValue(self._xpath + '/multiphase/phaseInterfaceCompressionFactor'))
        self._ui.numberOfMulesIterations.setText(
            self._db.getValue(self._xpath + '/multiphase/numberOfMulesIterations'))

        self._ui.absolutePressure.setText(self._db.getValue(self._xpath + '/convergenceCriteria/pressure/absolute'))
        self._ui.relativePressure.setText(self._db.getValue(self._xpath + '/convergenceCriteria/pressure/relative'))
        self._ui.absoluteMomentum.setText(self._db.getValue(self._xpath + '/convergenceCriteria/momentum/absolute'))
        self._ui.relativeMomentum.setText(self._db.getValue(self._xpath + '/convergenceCriteria/momentum/relative'))
        self._ui.absoluteEnergy.setText(self._db.getValue(self._xpath + '/convergenceCriteria/energy/absolute'))
        self._ui.relativeEnergy.setText(self._db.getValue(self._xpath + '/convergenceCriteria/energy/relative'))
        self._ui.absoluteTurbulence.setText(self._db.getValue(self._xpath + '/convergenceCriteria/turbulence/absolute'))
        self._ui.relativeTurbulence.setText(self._db.getValue(self._xpath + '/convergenceCriteria/turbulence/relative'))
        self._ui.absoluteVolumeFraction.setText(
            self._db.getValue(self._xpath + '/convergenceCriteria/volumeFraction/absolute'))
        self._ui.relativeVolumeFraction.setText(
            self._db.getValue(self._xpath + '/convergenceCriteria/volumeFraction/relative'))

    def save(self):
        writer = CoreDBWriter()
        writer.append(self._xpath + '/pressureVelocityCouplingScheme',
                      self._ui.pressureVelocityCouplingScheme.currentData(), None)
        writer.append(self._xpath + '/useMomentumPredictor',
                      'true' if self._ui.useMomentumPredictor.isChecked() else 'false', None)

        writer.append(self._xpath + '/discretizationSchemes/time',
                      self._ui.discretizationSchemeTime.currentData(), None)
        writer.append(self._xpath + '/discretizationSchemes/momentum',
                      self._ui.discretizationSchemeMomentum.currentData(), None)
        writer.append(self._xpath + '/discretizationSchemes/energy',
                      self._ui.discretizationSchemeEnergy.currentData(), None)
        writer.append(self._xpath + '/discretizationSchemes/turbulentKineticEnergy',
                      self._ui.discretizationSchemeTurbulence.currentData(), None)
        writer.append(self._xpath + '/discretizationSchemes/volumeFraction',
                      self._ui.discretizationSchemeVolumeFraction.currentData(), None)

        writer.append(self._xpath + '/underRelaxationFactors/pressure',
                      self._ui.underRelaxationFactorPressure.text(), self.tr('Under-Relaxation Factor Pressure'))
        writer.append(self._xpath + '/underRelaxationFactors/pressureFinal',
                      self._ui.underRelaxationFactorPressureFinal.text(),
                      self.tr('Under-Relaxation Factor Pressure Final'))
        writer.append(self._xpath + '/underRelaxationFactors/momentum',
                      self._ui.underRelaxationFactorMomentum.text(), self.tr('Under-Relaxation Factor Momentum'))
        writer.append(self._xpath + '/underRelaxationFactors/momentumFinal',
                      self._ui.underRelaxationFactorMomentumFinal.text(),
                      self.tr('Under-Relaxation Factor Momentum Final'))
        writer.append(self._xpath + '/underRelaxationFactors/energy',
                      self._ui.underRelaxationFactorEnergy.text(), self.tr('Under-Relaxation Factor Energy'))
        writer.append(self._xpath + '/underRelaxationFactors/energyFinal',
                      self._ui.underRelaxationFactorEnergyFinal.text(), self.tr('Under-Relaxation Factor Energy Final'))
        writer.append(self._xpath + '/underRelaxationFactors/turbulence',
                      self._ui.underRelaxationFactorTurbulence.text(), self.tr('Under-Relaxation Factor Turbulence'))
        writer.append(self._xpath + '/underRelaxationFactors/turbulenceFinal',
                      self._ui.underRelaxationFactorTurbulenceFinal.text(),
                      self.tr('Under-Relaxation Factor Turbulence Final'))
        writer.append(self._xpath + '/underRelaxationFactors/density',
                      self._ui.underRelaxationFactorDensity.text(), self.tr('Under-Relaxation Factor Density'))
        writer.append(self._xpath + '/underRelaxationFactors/densityFinal',
                      self._ui.underRelaxationFactorDensityFinal.text(),
                      self.tr('Under-Relaxation Factor Density Final'))
        writer.append(self._xpath + '/underRelaxationFactors/volumeFraction',
                      self._ui.underRelaxationFactorVolumeFraction.text(),
                      self.tr('Under-Relaxation Factor Volume Fraction'))
        writer.append(self._xpath + '/underRelaxationFactors/volumeFractionFinal',
                      self._ui.underRelaxationFactorVolumeFractionFinal.text(),
                      self.tr('Under-Relaxation Factor Volume Fraction Final'))

        if self._ui.improveStablitiy.isChecked():
            writer.append(self._xpath + '/highOrderTermRelaxation/relaxationFactor',
                          self._ui.limitingFactor.text(), self.tr('Limiting Factor'))
            writer.setAttribute(self._xpath + '/highOrderTermRelaxation', 'disabled', 'false')
        else:
            writer.setAttribute(self._xpath + '/highOrderTermRelaxation', 'disabled', 'true')

        writer.append(self._xpath + '/maxIterationsPerTimeStep',
                      self._ui.maxIterationsPerTimeStep.text(), self.tr('Max Iterations per Time Step'))
        writer.append(self._xpath + '/numberOfCorrectors',
                      self._ui.numberOfCorrectors.text(), self.tr('Number of Correctors'))

        writer.append(self._xpath + '/multiphase/maxIterationsPerTimeStep',
                      self._ui.multiphaseMaxIterationsPerTimeStep.text(),
                      self.tr('Multiphase Max Iterations per Time Step'))
        writer.append(self._xpath + '/multiphase/numberOfCorrectors',
                      self._ui.multiphaseNumberOfCorrectors.text(), self.tr('Multiphase Number of Correctors'))
        writer.append(self._xpath + '/multiphase/useSemiImplicitMules',
                      'true' if self._ui.mulesSemiImplicit.isChecked() else 'false', None)
        writer.append(self._xpath + '/multiphase/phaseInterfaceCompressionFactor',
                      self._ui.phaseInterfaceCompressionFactor.text(), self.tr('Phase Interface Compression Factor'))
        writer.append(self._xpath + '/multiphase/numberOfMulesIterations',
                      self._ui.numberOfMulesIterations.text(), self.tr('Number of MULES iterations over the limiter'))

        writer.append(self._xpath + '/convergenceCriteria/pressure/absolute',
                      self._ui.absolutePressure.text(), self.tr('Convergence Criteria Absolute Pressure'))
        writer.append(self._xpath + '/convergenceCriteria/pressure/relative',
                      self._ui.relativePressure.text(), self.tr('Convergence Criteria Relative Pressure'))
        writer.append(self._xpath + '/convergenceCriteria/momentum/absolute',
                      self._ui.absoluteMomentum.text(), self.tr('Convergence Criteria Absolute Moment'))
        writer.append(self._xpath + '/convergenceCriteria/momentum/relative',
                      self._ui.relativeMomentum.text(), self.tr('Convergence Criteria Relative Moment'))
        writer.append(self._xpath + '/convergenceCriteria/energy/absolute',
                      self._ui.absoluteEnergy.text(), self.tr('Convergence Criteria Absolute Energy'))
        writer.append(self._xpath + '/convergenceCriteria/energy/relative',
                      self._ui.relativeEnergy.text(), self.tr('Convergence Criteria Relative Energy'))
        writer.append(self._xpath + '/convergenceCriteria/turbulence/absolute',
                      self._ui.absoluteTurbulence.text(), self.tr('Convergence Criteria Absolute Turbulence'))
        writer.append(self._xpath + '/convergenceCriteria/turbulence/relative',
                      self._ui.relativeTurbulence.text(), self.tr('Convergence Criteria Relative Turbulence'))
        writer.append(self._xpath + '/convergenceCriteria/volumeFraction/absolute',
                      self._ui.absoluteVolumeFraction.text(), self.tr('Convergence Criteria Absolute Volume Fraction'))
        writer.append(self._xpath + '/convergenceCriteria/volumeFraction/relative',
                      self._ui.relativeVolumeFraction.text(), self.tr('Convergence Criteria Relative Volume Fraction'))

        errorCount = writer.write()
        if errorCount > 0:
            QMessageBox.critical(self, self.tr('Input Error'), writer.firstError().toMessage())
            return False

        return True

    def showEvent(self, ev):
        if not ev.spontaneous():
            self._load()

        return super().showEvent(ev)

    def _connectSignalsSlots(self):
        self._ui.advanced.clicked.connect(self._advancedSetup)

    def _advancedSetup(self):
        self._dialog = AdvancedDialog()
        self._dialog.open()

    def _setupCombo(self, combo, items):
        for value, text in items.items():
            combo.addItem(text, value)