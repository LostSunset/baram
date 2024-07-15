#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum

from PySide6.QtCore import QCoreApplication, QObject, Signal

from baramFlow.coredb import coredb
from baramFlow.coredb.models_db import ModelsDB, TurbulenceModel, UserDefinedScalarsDB
from baramFlow.coredb.material_db import MaterialDB, Phase, MaterialType, MaterialObserver
from baramFlow.openfoam.solver import findSolver, getSolverCapability


class Field(Enum):
    PRESSURE = 'pressure'
    SPEED = 'speed'
    X_VELOCITY = 'xVelocity'
    Y_VELOCITY = 'yVelocity'
    Z_VELOCITY = 'zVelocity'
    TURBULENT_KINETIC_ENERGY = 'turbulentKineticEnergy'
    TURBULENT_DISSIPATION_RATE = 'turbulentDissipationRate'
    SPECIFIC_DISSIPATION_RATE = 'specificDissipationRate'
    MODIFIED_TURBULENT_VISCOSITY = 'modifiedTurbulentViscosity'
    TEMPERATURE = 'temperature'
    DENSITY = 'density'
    MATERIAL = 'material'
    SCALAR = 'scalar'


class SurfaceReportType(Enum):
    AREA_WEIGHTED_AVERAGE = 'areaWeightedAverage'
    MASS_WEIGHTED_AVERAGE = 'massWeightedAverage'
    INTEGRAL = 'Integral'
    MASS_FLOW_RATE = 'massFlowRate'
    VOLUME_FLOW_RATE = 'volumeFlowRate'
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'
    COEFFICIENT_OF_VARIATION = 'cov'


class VolumeReportType(Enum):
    VOLUME_AVERAGE = 'volumeAverage'
    VOLUME_INTEGRAL = 'volumeIntegral'
    MINIMUM = 'minimum'
    MAXIMUM = 'maximum'
    COEFFICIENT_OF_VARIATION = 'cov'


class DirectionSpecificationMethod(Enum):
    DIRECT = 'direct'
    AOA_AOS = 'AoA_AoS'


class MonitorDBSignals(QObject):
    monitorChanged = Signal()


class MonitorDB:
    FORCE_MONITORS_XPATH = './/monitors/forces'
    POINT_MONITORS_XPATH = './/monitors/points'
    SURFACE_MONITORS_XPATH = './/monitors/surfaces'
    VOLUME_MONITORS_XPATH = './/monitors/volumes'

    signals = MonitorDBSignals()

    @classmethod
    def getForceMonitorXPath(cls, name):
        return f'{cls.FORCE_MONITORS_XPATH}/forceMonitor[name="{name}"]'

    @classmethod
    def getPointMonitorXPath(cls, name):
        return f'{cls.POINT_MONITORS_XPATH}/pointMonitor[name="{name}"]'

    @classmethod
    def getSurfaceMonitorXPath(cls, name):
        return f'{cls.SURFACE_MONITORS_XPATH}/surfaceMonitor[name="{name}"]'

    @classmethod
    def getVolumeMonitorXPath(cls, name):
        return f'{cls.VOLUME_MONITORS_XPATH}/volumeMonitor[name="{name}"]'

    @classmethod
    def surfaceReportTypeToText(cls, reportType):
        return {
            SurfaceReportType.AREA_WEIGHTED_AVERAGE: QCoreApplication.translate('MonitorDB', 'Area-Weighted Average'),
            SurfaceReportType.MASS_WEIGHTED_AVERAGE: QCoreApplication.translate('MonitorDB', 'Mass-Weighted Average'),
            SurfaceReportType.INTEGRAL: QCoreApplication.translate('MonitorDB', 'Integral'),
            SurfaceReportType.MASS_FLOW_RATE: QCoreApplication.translate('MonitorDB', 'Mass Flow Rate'),
            SurfaceReportType.VOLUME_FLOW_RATE: QCoreApplication.translate('MonitorDB', 'Volume Flow Rate'),
            SurfaceReportType.MINIMUM: QCoreApplication.translate('MonitorDB', 'Minimum'),
            SurfaceReportType.MAXIMUM: QCoreApplication.translate('MonitorDB', 'Maximum'),
            SurfaceReportType.COEFFICIENT_OF_VARIATION:
                QCoreApplication.translate('MonitorDB', 'Coefficient of Variation, CoV'),
        }.get(reportType)

    @classmethod
    def volumeReportTypeToText(cls, reportType):
        return {
            VolumeReportType.VOLUME_AVERAGE: QCoreApplication.translate('MonitorDB', 'Volume Average'),
            VolumeReportType.VOLUME_INTEGRAL: QCoreApplication.translate('MonitorDB', 'Volume Integral'),
            VolumeReportType.MINIMUM: QCoreApplication.translate('MonitorDB', 'Minimum'),
            VolumeReportType.MAXIMUM: QCoreApplication.translate('MonitorDB', 'Maximum'),
            VolumeReportType.COEFFICIENT_OF_VARIATION:
                QCoreApplication.translate('MonitorDB', 'Coefficient of Variation, CoV'),
        }.get(reportType)


class FieldHelper:
    FIELD_TEXTS = {
        Field.PRESSURE: QCoreApplication.translate('MonitorField', 'Pressure'),
        Field.SPEED: QCoreApplication.translate('MonitorField', 'Speed'),
        Field.X_VELOCITY: QCoreApplication.translate('MonitorField', 'X-Velocity'),
        Field.Y_VELOCITY: QCoreApplication.translate('MonitorField', 'Y-Velocity'),
        Field.Z_VELOCITY: QCoreApplication.translate('MonitorField', 'Z-Velocity'),
        Field.TURBULENT_KINETIC_ENERGY: QCoreApplication.translate('MonitorField', 'Turbulent Kinetic Energy'),
        Field.TURBULENT_DISSIPATION_RATE: QCoreApplication.translate('MonitorField', 'Turbulent Dissipation Rate'),
        Field.SPECIFIC_DISSIPATION_RATE: QCoreApplication.translate('MonitorField', 'Specific Dissipation Rate'),
        Field.MODIFIED_TURBULENT_VISCOSITY: QCoreApplication.translate('MonitorField', 'Modified Turbulent Viscosity'),
        Field.TEMPERATURE: QCoreApplication.translate('MonitorField', 'Temperature'),
        Field.DENSITY: QCoreApplication.translate('MonitorField', 'Density'),
        Field.MATERIAL: QCoreApplication.translate('MonitorField', 'material'),
    }

    FIELDS = {
        Field.PRESSURE: 'p',
        Field.SPEED: 'mag(U)',
        Field.X_VELOCITY: 'Ux',
        Field.Y_VELOCITY: 'Uy',
        Field.Z_VELOCITY: 'Uz',
        Field.TURBULENT_KINETIC_ENERGY: 'k',
        Field.TURBULENT_DISSIPATION_RATE: 'epsilon',
        Field.SPECIFIC_DISSIPATION_RATE: 'omega',
        Field.MODIFIED_TURBULENT_VISCOSITY: 'nuTilda',
        Field.TEMPERATURE: 'T',
        Field.DENSITY: 'rho',
    }

    class FieldItem:
        class DBFieldKey:
            def __init__(self, field, id_='1'):
                # Values for coreDB's field element
                self._field = field
                self._id = id_

            @property
            def field(self):
                return self._field

            @property
            def id(self):
                return self._id

        def __init__(self, text, field, id_='1'):
            self._text = text
            self._key = self.DBFieldKey(field, id_)

        @property
        def text(self):
            return self._text

        @property
        def key(self):
            return self._key

    @classmethod
    def getAvailableFields(cls):
        fields = []

        def _appendField(field):
            fields.append(cls.FieldItem(cls.FIELD_TEXTS[field], field))

        def _appendMaterial(mid, name):
            fields.append(cls.FieldItem(name, Field.MATERIAL, str(mid)))

        # Always available fields
        _appendField(Field.PRESSURE)
        _appendField(Field.SPEED)
        _appendField(Field.X_VELOCITY)
        _appendField(Field.Y_VELOCITY)
        _appendField(Field.Z_VELOCITY)

        # Fields depending on the turbulence model
        turbulenceModel = ModelsDB.getTurbulenceModel()
        if turbulenceModel == TurbulenceModel.K_EPSILON:
            _appendField(Field.TURBULENT_KINETIC_ENERGY)
            _appendField(Field.TURBULENT_DISSIPATION_RATE)
        elif turbulenceModel == TurbulenceModel.K_OMEGA:
            _appendField(Field.TURBULENT_KINETIC_ENERGY)
            _appendField(Field.SPECIFIC_DISSIPATION_RATE)
        elif turbulenceModel == TurbulenceModel.SPALART_ALLMARAS:
            _appendField(Field.MODIFIED_TURBULENT_VISCOSITY)

        # Fields depending on the energy model
        energyOn = ModelsDB.isEnergyModelOn()
        if energyOn:
            _appendField(Field.TEMPERATURE)
            _appendField(Field.DENSITY)

        db = coredb.CoreDB()
        # Material fields on multiphase model
        if ModelsDB.isMultiphaseModelOn():
            for mid, name, formula, phase in db.getMaterials():
                if phase != Phase.SOLID.value:
                    _appendMaterial(mid, name)
        elif ModelsDB.isSpeciesModelOn():
            for mid, _, _, _ in db.getMaterials(MaterialType.MIXTURE.value):
                for specie, name in db.getSpecies(mid):
                    _appendMaterial(specie, name)

        for scalarID, fieldName in coredb.CoreDB().getUserDefinedScalars():
            fields.append(cls.FieldItem(fieldName, Field.SCALAR, str(scalarID)))

        return fields

    @classmethod
    def DBFieldKeyToText(cls, field, fieldID):
        if field == Field.MATERIAL:
            return MaterialDB.getName(fieldID)
        elif field == Field.SCALAR:
            return UserDefinedScalarsDB.getFieldName(fieldID)
        else:
            return cls.FIELD_TEXTS[Field(field)]

    @classmethod
    def DBFieldKeyToField(cls, field, fieldID):
        if field == Field.MATERIAL:
            if MaterialDB.getType(fieldID) == MaterialType.SPECIE:
                return MaterialDB.getName(fieldID)
            else:
                return 'alpha.' + MaterialDB.getName(fieldID)
        elif field == Field.SCALAR:
            return UserDefinedScalarsDB.getFieldName(fieldID)
        else:
            fieldName = cls.FIELDS[Field(field)]

            if fieldName == 'p':
                try:
                    cap = getSolverCapability(findSolver())
                    if cap['usePrgh']:
                        fieldName = 'p_rgh'
                except RuntimeError:
                    pass

            return fieldName


class _MaterialObserver(MaterialObserver):
    def materialRemoving(self, db, mid: int):
        removed = self._removeMonitors(db, mid)
        if MaterialDB.getType(mid) == MaterialType.MIXTURE:
            for sid in MaterialDB.getSpecies(mid):
                removed = removed or self._removeMonitors(db, sid)

        if removed:
            MonitorDB.signals.monitorChanged.emit()

    def specieRemoving(self, db, mid, primarySpecie):
        if self._removeMonitors(db, mid):
            MonitorDB.signals.monitorChanged.emit()

    def _removeMonitors(self, db, mid):
        referencingFields = db.getElements(f'monitors/*/*/field[field="material"][fieldID="{mid}"]')
        if not referencingFields:
            return False

        for field in referencingFields:
            monitor = field.getparent()
            monitor.getparent().remove(monitor)

        return True


MaterialDB.registerObserver(_MaterialObserver())
