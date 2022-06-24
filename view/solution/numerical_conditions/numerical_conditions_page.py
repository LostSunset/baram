#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QWidget, QMessageBox

from coredb import coredb
from coredb.coredb_writer import CoreDBWriter
from view.setup.general.general_db import GeneralDB
from .numerical_conditions_page_ui import Ui_NumericalConditionsPage
from .advanced_dialog import AdvancedDialog
from .numerical_db import PressureVelocityCouplingScheme, ImplicitDiscretizationScheme, UpwindDiscretizationScheme
from .numerical_db import NumericalDB


class NumericalConditionsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._ui = Ui_NumericalConditionsPage()
        self._ui.setupUi(self)

        self._pressureVelocityCouplingSchemes = {
            PressureVelocityCouplingScheme.SIMPLE.value: self.tr("SIMPLE"),
            PressureVelocityCouplingScheme.SIMPLEC.value: self.tr("SIMPLEC"),
        }

        self._implicitDiscretizationSchemes = {
            ImplicitDiscretizationScheme.FIRST_ORDER_IMPLICIT.value: self.tr("First Order Implicit"),
            ImplicitDiscretizationScheme.SECOND_ORDER_IMPLICIT.value: self.tr("Second Order Implicit"),
        }

        self._upwindDiscretizationSchemes = {
            UpwindDiscretizationScheme.FIRST_ORDER_UPWIND.value: self.tr("First Order Upwind"),
            UpwindDiscretizationScheme.SECOND_ORDER_UPWIND.value: self.tr("Second Order Upwind"),
        }

        self._setupCombo(self._ui.pressureVelocityCouplingScheme, self._pressureVelocityCouplingSchemes)
        self._setupCombo(self._ui.discretizationSchemeTime, self._implicitDiscretizationSchemes)
        self._setupCombo(self._ui.discretizationSchemeMomentum, self._upwindDiscretizationSchemes)
        self._setupCombo(self._ui.discretizationSchemeEnergy, self._upwindDiscretizationSchemes)
        self._setupCombo(self._ui.discretizationSchemeTurbulentKineticEnergy, self._upwindDiscretizationSchemes)

        self._db = coredb.CoreDB()
        self._xpath = NumericalDB.NUMERICAL_CONDITIONS_XPATH
        self._dialog = None

        self._connectSignalsSlots()

    def showEvent(self, ev):
        if ev.spontaneous():
            return super().hideEvent(ev)

        timeIsTransient = GeneralDB.isTimeTransient()
        self._ui.discretizationSchemeTime.setEnabled(timeIsTransient)
        self._ui.underRelaxationFactorPressureFinal.setEnabled(timeIsTransient)
        self._ui.underRelaxationFactorMomentumFinal.setEnabled(timeIsTransient)
        self._ui.underRelaxationFactorEnergyFinal.setEnabled(timeIsTransient)
        self._ui.underRelaxationFactorTurbulenceFinal.setEnabled(timeIsTransient)
        self._ui.maxIterationsPerTimeStep.setEnabled(timeIsTransient)
        self._ui.numberOfCorrectors.setEnabled(timeIsTransient)
        self._ui.relativePressure.setEnabled(timeIsTransient)
        self._ui.relativeMomentum.setEnabled(timeIsTransient)
        self._ui.relativeEnergy.setEnabled(timeIsTransient)
        self._ui.relativeTurbulence.setEnabled(timeIsTransient)

        self._ui.pressureVelocityCouplingScheme.setCurrentText(
            self._pressureVelocityCouplingSchemes[self._db.getValue(self._xpath + '/pressureVelocityCouplingScheme')])

        self._ui.discretizationSchemeTime.setCurrentText(
            self._implicitDiscretizationSchemes[self._db.getValue(self._xpath + '/discretizationSchemes/time')])
        self._ui.discretizationSchemeMomentum.setCurrentText(
            self._upwindDiscretizationSchemes[self._db.getValue(self._xpath + '/discretizationSchemes/momentum')])
        self._ui.discretizationSchemeEnergy.setCurrentText(
            self._upwindDiscretizationSchemes[self._db.getValue(self._xpath + '/discretizationSchemes/energy')])
        self._ui.discretizationSchemeTurbulentKineticEnergy.setCurrentText(
            self._upwindDiscretizationSchemes[
                self._db.getValue(self._xpath + '/discretizationSchemes/turbulentKineticEnergy')])

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

        self._ui.maxIterationsPerTimeStep.setText(self._db.getValue(self._xpath + '/maxIterationsPerTimeStep'))
        self._ui.numberOfCorrectors.setText(self._db.getValue(self._xpath + '/numberOfCorrectors'))

        self._ui.absolutePressure.setText(self._db.getValue(self._xpath + '/convergenceCriteria/pressure/absolute'))
        self._ui.relativePressure.setText(self._db.getValue(self._xpath + '/convergenceCriteria/pressure/relative'))
        self._ui.absoluteMomentum.setText(self._db.getValue(self._xpath + '/convergenceCriteria/momentum/absolute'))
        self._ui.relativeMomentum.setText(self._db.getValue(self._xpath + '/convergenceCriteria/momentum/relative'))
        self._ui.absoluteEnergy.setText(self._db.getValue(self._xpath + '/convergenceCriteria/energy/absolute'))
        self._ui.relativeEnergy.setText(self._db.getValue(self._xpath + '/convergenceCriteria/energy/relative'))
        self._ui.absoluteTurbulence.setText(self._db.getValue(self._xpath + '/convergenceCriteria/turbulence/absolute'))
        self._ui.relativeTurbulence.setText(self._db.getValue(self._xpath + '/convergenceCriteria/turbulence/relative'))

        return super().showEvent(ev)

    def hideEvent(self, ev):
        if ev.spontaneous():
            return super().hideEvent(ev)

        writer = CoreDBWriter()
        writer.append(self._xpath + '/pressureVelocityCouplingScheme',
                      self._ui.pressureVelocityCouplingScheme.currentData(), None)

        writer.append(self._xpath + '/discretizationSchemes/time',
                      self._ui.discretizationSchemeTime.currentData(), None)
        writer.append(self._xpath + '/discretizationSchemes/momentum',
                      self._ui.discretizationSchemeMomentum.currentData(), None)
        writer.append(self._xpath + '/discretizationSchemes/energy',
                      self._ui.discretizationSchemeEnergy.currentData(), None)
        writer.append(self._xpath + '/discretizationSchemes/turbulentKineticEnergy',
                      self._ui.discretizationSchemeTurbulentKineticEnergy.currentData(), None)

        writer.append(self._xpath + '/underRelaxationFactors/pressure',
                      self._ui.underRelaxationFactorPressure.text(), self.tr("Under-Relaxation Factor Pressure"))
        writer.append(self._xpath + '/underRelaxationFactors/pressureFinal',
                      self._ui.underRelaxationFactorPressureFinal.text(),
                      self.tr("Under-Relaxation Factor Pressure Final"))
        writer.append(self._xpath + '/underRelaxationFactors/momentum',
                      self._ui.underRelaxationFactorMomentum.text(), self.tr("Under-Relaxation Factor Momentum"))
        writer.append(self._xpath + '/underRelaxationFactors/momentumFinal',
                      self._ui.underRelaxationFactorMomentumFinal.text(),
                      self.tr("Under-Relaxation Factor Momentum Final"))
        writer.append(self._xpath + '/underRelaxationFactors/energy',
                      self._ui.underRelaxationFactorEnergy.text(), self.tr("Under-Relaxation Factor Energy"))
        writer.append(self._xpath + '/underRelaxationFactors/energyFinal',
                      self._ui.underRelaxationFactorEnergyFinal.text(), self.tr("Under-Relaxation Factor Energy Final"))
        writer.append(self._xpath + '/underRelaxationFactors/turbulence',
                      self._ui.underRelaxationFactorTurbulence.text(), self.tr("Under-Relaxation Factor Turbulence"))
        writer.append(self._xpath + '/underRelaxationFactors/turbulenceFinal',
                      self._ui.underRelaxationFactorTurbulenceFinal.text(),
                      self.tr("Under-Relaxation Factor Turbulence Final"))

        writer.append(self._xpath + '/maxIterationsPerTimeStep',
                      self._ui.maxIterationsPerTimeStep.text(), self.tr("Max Iterations per Time Step"))
        writer.append(self._xpath + '/numberOfCorrectors',
                      self._ui.numberOfCorrectors.text(), self.tr("Number of Correctors"))

        writer.append(self._xpath + '/convergenceCriteria/pressure/absolute',
                      self._ui.absolutePressure.text(), self.tr("Convergence Criteria Absulute Pressure"))
        writer.append(self._xpath + '/convergenceCriteria/pressure/relative',
                      self._ui.relativePressure.text(), self.tr("Convergence Criteria Relative Pressure"))
        writer.append(self._xpath + '/convergenceCriteria/momentum/absolute',
                      self._ui.absoluteMomentum.text(), self.tr("Convergence Criteria Absolute Moment"))
        writer.append(self._xpath + '/convergenceCriteria/momentum/relative',
                      self._ui.relativeMomentum.text(), self.tr("Convergence Criteria Relative Moment"))
        writer.append(self._xpath + '/convergenceCriteria/energy/absolute',
                      self._ui.absoluteEnergy.text(), self.tr("Convergence Criteria Absolute Energy"))
        writer.append(self._xpath + '/convergenceCriteria/energy/relative',
                      self._ui.relativeEnergy.text(), self.tr("Convergence Criteria Relative Energy"))
        writer.append(self._xpath + '/convergenceCriteria/turbulence/absolute',
                      self._ui.absoluteTurbulence.text(), self.tr("Convergence Criteria Absolute Turbulence"))
        writer.append(self._xpath + '/convergenceCriteria/turbulence/relative',
                      self._ui.relativeTurbulence.text(), self.tr("Convergence Criteria Relative Turbulence"))

        errorCount = writer.write()
        if errorCount > 0:
            QMessageBox.critical(self, self.tr("Input Error"), writer.firstError().toMessage())

        return super().hideEvent(ev)

    def _connectSignalsSlots(self):
        self._ui.advanced.clicked.connect(self._advancedSetup)

    def _advancedSetup(self):
        dialog = AdvancedDialog()
        dialog.exec()

    def _setupCombo(self, combo, items):
        for value, text in items.items():
            combo.addItem(text, value)