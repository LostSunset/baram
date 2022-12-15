#!/usr/bin/env python
# -*- coding: utf-8 -*-

from coredb.boundary_db import BoundaryDB, BoundaryType, WallVelocityCondition, InterfaceMode
from coredb.models_db import ModelsDB, TurbulenceModel
from openfoam.boundary_conditions.boundary_condition import BoundaryCondition


class Nut(BoundaryCondition):
    DIMENSIONS = '[0 2 -1 0 0 0 0]'

    def __init__(self, region, time, processorNo):
        super().__init__(region, time, processorNo, 'nut')

        self._initialValue = region.initialNut
        self._model = ModelsDB.getTurbulenceModel()

    def build0(self):
        self._data = None

        if self._region.isFluid():
            self._data = {
                'dimensions': self.DIMENSIONS,
                'internalField': ('uniform', self._initialValue),
                'boundaryField': self._constructBoundaryField()
            }

        return self

    def _constructBoundaryField(self):
        field = {}

        for bcid, name, type_ in self._region.boundaries:
            xpath = BoundaryDB.getXPath(bcid)

            field[name] = {
                BoundaryType.VELOCITY_INLET.value:      (lambda: self._constructCalculated()),
                BoundaryType.FLOW_RATE_INLET.value:     (lambda: self._constructCalculated()),
                BoundaryType.PRESSURE_INLET.value:      (lambda: self._constructCalculated()),
                BoundaryType.PRESSURE_OUTLET.value:     (lambda: self._constructPressureOutletNut(xpath)),
                BoundaryType.ABL_INLET.value:           (lambda: self._constructCalculated()),
                BoundaryType.OPEN_CHANNEL_INLET.value:  (lambda: self._constructCalculated()),
                BoundaryType.OPEN_CHANNEL_OUTLET.value: (lambda: self._constructCalculated()),
                BoundaryType.OUTFLOW.value:             (lambda: self._constructZeroGradient()),
                BoundaryType.FREE_STREAM.value:         (lambda: self._constructCalculated()),
                BoundaryType.FAR_FIELD_RIEMANN.value:   (lambda: self._constructCalculated()),
                BoundaryType.SUBSONIC_INFLOW.value:     (lambda: self._constructCalculated()),
                BoundaryType.SUBSONIC_OUTFLOW.value:    (lambda: self._constructCalculated()),
                BoundaryType.SUPERSONIC_INFLOW.value:   (lambda: self._constructCalculated()),
                BoundaryType.SUPERSONIC_OUTFLOW.value:  (lambda: self._constructCalculated()),
                BoundaryType.WALL.value:                (lambda: self._constructWallNut(xpath)),
                BoundaryType.THERMO_COUPLED_WALL.value: (lambda: self._constructWallFunctionByModel()),
                BoundaryType.SYMMETRY.value:            (lambda: self._constructSymmetry()),
                BoundaryType.INTERFACE.value:           (lambda: self._constructInterfaceNut(xpath)),
                BoundaryType.POROUS_JUMP.value:         (lambda: self._constructCyclic()),
                BoundaryType.FAN.value:                 (lambda: self._constructCyclic()),
                BoundaryType.EMPTY.value:               (lambda: self._constructEmpty()),
                BoundaryType.CYCLIC.value:              (lambda: self._constructCyclic()),
                BoundaryType.WEDGE.value:               (lambda: self._constructWedge()),
            }.get(type_)()

        return field

    def _constructWallFunctionByModel(self):
        if self._model == TurbulenceModel.K_EPSILON:
            return self._constructNEXTNutkWallFunction()
        else:
            return self._constructNEXTNutSpaldingWallFunction()

    def _constructNEXTNutkWallFunction(self):
        return {
            'type': 'nutkWallFunction',
            'value': self._initialValueByTime()
        }

    def _constructNEXTNutSpaldingWallFunction(self):
        return {
            # 'type': 'nutSpaldingWallFunction',  # This type has not ported to OpenFOAM N yet
            'type': 'nutUSpaldingWallFunction',
            'value': self._initialValueByTime()
        }

    def _constructAtmNutkWallFunction(self):
        return {
            'type': 'atmNutkWallFunction',
            'z0': self._db.getValue(BoundaryDB.ABL_INLET_CONDITIONS_XPATH + '/surfaceRoughnessLength'),
            'value': self._initialValueByTime()
        }

    def _constructPressureOutletNut(self, xpath):
        if self._db.getValue(xpath + '/pressureOutlet/calculatedBackflow') == 'true':
            return self._constructCalculated()
        else:
            return self._constructZeroGradient()

    def _constructWallNut(self, xpath):
        spec = self._db.getValue(xpath + '/wall/velocity/type')
        if spec == WallVelocityCondition.ATMOSPHERIC_WALL.value:
            return self._constructAtmNutkWallFunction()
        else:
            return self._constructWallFunctionByModel()

    def _constructInterfaceNut(self, xpath):
        spec = self._db.getValue(xpath + '/interface/mode')
        if spec == InterfaceMode.REGION_INTERFACE.value:
            return self._constructWallFunctionByModel()
        else:
            return self._constructCyclicAMI()
