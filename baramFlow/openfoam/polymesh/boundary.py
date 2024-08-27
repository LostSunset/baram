#!/usr/bin/env python
# -*- coding: utf-8 -*-

from libbaram.openfoam.dictionary.dictionary_file import DictionaryFile

from baramFlow.coredb.boundary_db import BoundaryType, BoundaryDB, InterfaceMode, GeometricalType
from baramFlow.coredb.coredb_reader import CoreDBReader
from baramFlow.openfoam.file_system import FileSystem
from .polymesh_loader import PolyMeshLoader


TYPE_MAP = {
    BoundaryType.VELOCITY_INLET.value       : GeometricalType.PATCH,
    BoundaryType.FLOW_RATE_INLET.value      : GeometricalType.PATCH,
    BoundaryType.PRESSURE_INLET.value       : GeometricalType.PATCH,
    BoundaryType.ABL_INLET.value            : GeometricalType.PATCH,
    BoundaryType.OPEN_CHANNEL_INLET.value   : GeometricalType.PATCH,
    BoundaryType.FREE_STREAM.value          : GeometricalType.PATCH,
    BoundaryType.FAR_FIELD_RIEMANN.value    : GeometricalType.PATCH,
    BoundaryType.SUBSONIC_INLET.value       : GeometricalType.PATCH,
    BoundaryType.SUPERSONIC_INFLOW.value    : GeometricalType.PATCH,
    BoundaryType.PRESSURE_OUTLET.value      : GeometricalType.PATCH,
    BoundaryType.OPEN_CHANNEL_OUTLET.value  : GeometricalType.PATCH,
    BoundaryType.OUTFLOW.value              : GeometricalType.PATCH,
    BoundaryType.SUBSONIC_OUTFLOW.value     : GeometricalType.PATCH,
    BoundaryType.SUPERSONIC_OUTFLOW.value   : GeometricalType.PATCH,
    BoundaryType.WALL.value                 : GeometricalType.WALL,
    BoundaryType.THERMO_COUPLED_WALL.value  : GeometricalType.MAPPED_WALL,
    BoundaryType.POROUS_JUMP.value          : GeometricalType.CYCLIC,
    BoundaryType.FAN.value                  : GeometricalType.CYCLIC,
    BoundaryType.SYMMETRY.value             : GeometricalType.SYMMETRY,
    BoundaryType.INTERFACE.value            : GeometricalType.CYCLIC_AMI,
    BoundaryType.EMPTY.value                : GeometricalType.EMPTY,
    BoundaryType.CYCLIC.value               : GeometricalType.CYCLIC,
    BoundaryType.WEDGE.value                : GeometricalType.WEDGE,
}


class Boundary(DictionaryFile):
    def __init__(self, rname: str, processorNo=None):
        super().__init__(FileSystem.caseRoot(), self.polyMeshLocation(rname), 'boundary')
        self._rname = rname
        self._boundaryDict = None
        self._processorNo = processorNo

        self._db = None

    def build(self):
        if self._boundaryDict is not None:
            return self

        self._db = CoreDBReader()

        fullPath = self.fullPath(self._processorNo)

        self._boundaryDict = PolyMeshLoader.loadBoundaryDict(fullPath, longListOutputThreshold=1)
        for bcname in list(self._boundaryDict.content.keys()):
            if self._boundaryDict.content[bcname]['nFaces'] == 0:
                del self._boundaryDict.content[bcname]
                continue

            xpath = BoundaryDB.getXPathByName(self._rname, bcname)
            if self._db.exists(xpath):
                bctype = self._db.getValue(xpath + '/physicalType')

                self._boundaryDict.content[bcname]['type'] = TYPE_MAP[bctype].value

                if BoundaryDB.needsCoupledBoundary(bctype):
                    couple = self._db.getValue(xpath + '/coupledBoundary')
                    if bctype == BoundaryType.THERMO_COUPLED_WALL.value:
                        self._generateMappedWall(bcname, xpath, couple)
                    elif bctype == BoundaryType.INTERFACE.value:
                        spec = self._db.getValue(xpath + '/interface/mode')
                        if spec == InterfaceMode.INTERNAL_INTERFACE.value:
                            self._generateCyclicAmiNoOrdering(bcname, xpath, couple)
                        elif spec == InterfaceMode.ROTATIONAL_PERIODIC.value:
                            self._generateCyclicAmiRotational(bcname, xpath, couple)
                        elif spec == InterfaceMode.TRANSLATIONAL_PERIODIC.value:
                            self._generateCyclicAmiTranslational(bcname, xpath, couple)
                        elif spec == InterfaceMode.REGION_INTERFACE.value:
                            self._generateMappedWall(bcname, xpath, couple)
                    else:
                        self._generateCyclic(bcname, xpath, couple)
                else:
                    self._removeEntry(bcname, 'sampleMode')
                    self._removeEntry(bcname, 'sampleRegion')
                    self._removeEntry(bcname, 'samplePatch')
                    self._removeEntry(bcname, 'transform')
                    self._removeEntry(bcname, 'neighbourPatch')
                    self._removeEntry(bcname, 'rotationAxis')
                    self._removeEntry(bcname, 'rotationCentre')
                    self._removeEntry(bcname, 'separationVector')

        return self

    def write(self):
        self._boundaryDict.writeFile()

    def _generateMappedWall(self, bcname, xpath, cpid):
        self._removeEntry(bcname, 'transform')
        self._removeEntry(bcname, 'neighbourPatch')
        self._removeEntry(bcname, 'rotationAxis')
        self._removeEntry(bcname, 'rotationCentre')
        self._removeEntry(bcname, 'separationVector')

        self._boundaryDict.content[bcname]['type'] = GeometricalType.MAPPED_WALL.value
        self._boundaryDict.content[bcname]['sampleMode'] = 'nearestPatchFaceAMI'
        if self._rname:
            self._boundaryDict.content[bcname]['sampleRegion'] = BoundaryDB.getBoundaryRegion(cpid)
        else:
            self._removeEntry(bcname, 'sampleRegion')
        self._boundaryDict.content[bcname]['samplePatch'] = BoundaryDB.getBoundaryName(cpid)

    def _generateCyclicAmiNoOrdering(self, bcname, xpath, cpid):
        self._removeEntry(bcname, 'sampleMode')
        self._removeEntry(bcname, 'sampleRegion')
        self._removeEntry(bcname, 'samplePatch')
        self._removeEntry(bcname, 'rotationAxis')
        self._removeEntry(bcname, 'rotationCentre')
        self._removeEntry(bcname, 'separationVector')

        self._boundaryDict.content[bcname]['type'] = GeometricalType.CYCLIC_AMI.value
        self._boundaryDict.content[bcname]['transform'] = 'noOrdering'
        self._boundaryDict.content[bcname]['neighbourPatch'] = BoundaryDB.getBoundaryName(cpid)

    def _generateCyclicAmiRotational(self, bcname, xpath, cpid):
        self._removeEntry(bcname, 'sampleMode')
        self._removeEntry(bcname, 'sampleRegion')
        self._removeEntry(bcname, 'samplePatch')
        self._removeEntry(bcname, 'separationVector')

        self._boundaryDict.content[bcname]['type'] = GeometricalType.CYCLIC_AMI.value
        self._boundaryDict.content[bcname]['transform'] = 'rotational'
        self._boundaryDict.content[bcname]['neighbourPatch'] = BoundaryDB.getBoundaryName(cpid)
        self._boundaryDict.content[bcname]['rotationAxis'] = self._db.getVector(xpath + '/interface/rotationAxisDirection')
        self._boundaryDict.content[bcname]['rotationCentre'] = self._db.getVector(xpath + '/interface/rotationAxisOrigin')

    def _generateCyclicAmiTranslational(self, bcname, xpath, cpid):
        self._removeEntry(bcname, 'sampleMode')
        self._removeEntry(bcname, 'sampleRegion')
        self._removeEntry(bcname, 'samplePatch')
        self._removeEntry(bcname, 'rotationAxis')
        self._removeEntry(bcname, 'rotationCentre')

        self._boundaryDict.content[bcname]['type'] = GeometricalType.CYCLIC_AMI.value
        self._boundaryDict.content[bcname]['transform'] = 'translational'
        self._boundaryDict.content[bcname]['neighbourPatch'] = BoundaryDB.getBoundaryName(cpid)
        self._boundaryDict.content[bcname]['separationVector'] = self._db.getVector(xpath + '/interface/translationVector')

    def _generateCyclic(self, bcname, xpath, cpid):
        self._removeEntry(bcname, 'sampleMode')
        self._removeEntry(bcname, 'sampleRegion')
        self._removeEntry(bcname, 'samplePatch')
        self._removeEntry(bcname, 'rotationAxis')
        self._removeEntry(bcname, 'rotationCentre')
        self._removeEntry(bcname, 'separationVector')
        self._removeEntry(bcname, 'transform')

        self._boundaryDict.content[bcname]['type'] = GeometricalType.CYCLIC.value
        self._boundaryDict.content[bcname]['neighbourPatch'] = BoundaryDB.getBoundaryName(cpid)

    def _removeEntry(self, bcname, keyword):
        if keyword in self._boundaryDict.content[bcname]:
            del self._boundaryDict.content[bcname][keyword]

