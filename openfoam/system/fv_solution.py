#!/usr/bin/env python
# -*- coding: utf-8 -*-
from builtins import str

from coredb import coredb
from view.solution.numerical_conditions.numerical_db import NumericalDB, PressureVelocityCouplingScheme
from view.setup.general.general_db import GeneralDB
from view.setup.cell_zone_conditions.cell_zone_db import RegionDB
from view.setup.materials.material_db import Phase
from openfoam.dictionary_file import DictionaryFile


class FvSolution(DictionaryFile):
    def __init__(self, rname: str = None):
        super().__init__(self.systemLocation(rname), 'fvSolution')

        self._rname = rname
        self._db = coredb.CoreDB()

    def build(self):
        if self._data is not None:
            return self

        if self._rname:
            scheme = self._db.getValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/pressureVelocityCouplingScheme')
            phase = RegionDB.getPhase(self._rname)
            consistent = 'no'
            if scheme == PressureVelocityCouplingScheme.SIMPLEC.value and phase != Phase.SOLID:
                consistent = 'yes'

            self._data = {
                'solvers': {
                    'p': self._constructSolversP(),
                    'p_rgh': {
                        'solver': 'PCG',
                        'preconditioner': {
                            'preconditioner': 'GAMG',
                            'smoother': 'DIC',
                            'tolerance': '1e-5',
                            'relTol': '0.1',
                        },
                        'tolerance': '1e-16',
                        'relTol': '0.1',
                        'minIter': '1',
                        'maxIter': '5',
                    },
                    'h': self._constructSolversH(phase),
                    'rho': {
                        'solver': 'PCG',
                        'preconditioner': 'DIC',
                        'tolerance': '1e-16',
                        'relTol': '0.1',
                        'minIter': '1',
                        'maxIter': '5',
                    },
                    '"(U|k|epsilon|omega|nuTilda)"': {
                        'solver': 'PBiCGStab',
                        'preconditioner': 'DILU',
                        'tolerance': '1e-16',
                        'relTol': '0.1',
                        'minIter': '1',
                        'maxIter': '5',
                    },
                },
                'SIMPLE': {
                    'consistent': consistent,
                    'nNonOrthogonalCorrectors': '0',
                    'pRefCell': '0',        # only for fluid
                    'pRefValue': '0.0',     # only for fluid
                    'residualControl': {
                        'p': self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                        'p_rgh': self._db.getValue('//convergenceCriteria/pressure/absolute'),
                        'U': self._db.getValue('//convergenceCriteria/momentum/absolute'),
                        'h': self._db.getValue('//convergenceCriteria/energy/absolute'),
                        '"(k|epsilon|omega|nuTilda)"': self._db.getValue('//convergenceCriteria/turbulence/absolute'),
                    }
                },
                'PIMPLE': {
                    'consistent': consistent,
                    # ToDo: set momentumPredictor value. Transient일 때만, Pressure Velocity 콤보 밑에. on/off
                    'momentumPredictor': '<momentumPredictor>', # Use... checkbox. default:on
                    'turbOnFinalIterOnly': 'false',  # only for fluid
                    'nNonOrthogonalCorrectors': '0',
                    # only for fluid
                    'nCorrectors': self._db.getValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/numberOfCorrectors'),
                    # ToDo: only in single region case? 하지만 쓰기
                    'nOuterCorrectors':
                        self._db.getValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/maxIterationsPerTimeStep'),
                    'maxCo': 0, #ToDo: controlDict와 동일하게 (무조건)
                    'nonOrthogonalityThreshold': '80',
                    'skewnessThreshold': '0.95',
                    'pRefCell': '0',        # only for fluid
                    'pRefValue': '0.0',     # only for fluid
                    'rDeltaTSmoothingCoeff': '0.05',
                    'rDeltaTDampingCoeff': '0.5',
                    'residualControl': {
                        'p': {
                            'tolerance': self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                            'relTol': self._db.getValue('.//convergenceCriteria/pressure/relative'),
                        },
                        'p_rgh': {
                            'tolerance': self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                            'relTol': self._db.getValue('.//convergenceCriteria/pressure/relative'),
                        },
                        'U': {
                            'tolerance': self._db.getValue('.//convergenceCriteria/momentum/absolute'),
                            'relTol': self._db.getValue('.//convergenceCriteria/momentum/relative'),
                        },
                        'h': {
                            'tolerance': self._db.getValue('.//convergenceCriteria/energy/absolute'),
                            'relTol': self._db.getValue('.//convergenceCriteria/energy/relative'),
                        },
                        '"(k|epsilon|omega|nuTilda)"': {
                            'tolerance': self._db.getValue('.//convergenceCriteria/turbulence/absolute'),
                            'relTol': self._db.getValue('.//convergenceCriteria/turbulence/relative'),
                        },
                    }
                },
                'relaxationFactors': {
                    'fields': {
                        'p': self._db.getValue('.//underRelaxationFactors/pressure'),
                        'pFinal': self._db.getValue('.//underRelaxationFactors/pressureFinal'),
                        'p_rgh': self._db.getValue('.//underRelaxationFactors/pressure'),
                        'p_rghFinal': self._db.getValue('.//underRelaxationFactors/pressureFinal'),
                        'rho': self._db.getValue('.//underRelaxationFactors/density'),
                        'rhoFinal': self._db.getValue('.//underRelaxationFactors/densityFinal'),
                    },
                    'equations': {
                        'U': self._db.getValue('.//underRelaxationFactors/momentum'),
                        'UFinal': self._db.getValue('.//underRelaxationFactors/momentumFinal'),
                        'h': self._db.getValue('.//underRelaxationFactors/energy'),
                        'hFinal': self._db.getValue('.//underRelaxationFactors/energyFinal'),
                        '(k|epsilon|omega|nuTilda)': self._db.getValue('.//underRelaxationFactors/turbulence'),
                        '(k|epsilon|omega|nuTilda)Final': self._db.getValue('.//underRelaxationFactors/turbulenceFinal'),
                    }
                }
            }
        else:
            self._data = {
                'PIMPLE': {
                    'nOuterCorrectors':
                        self._db.getValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/maxIterationsPerTimeStep'),
                }

            }

        return self

    def _constructSolversP(self):
        if GeneralDB.isCompressible():
            return {
                'solver': 'PBiCGStab',
                'preconditioner': 'DILU',
                'tolerance': '1e-16',
                'relTol': '0.1',
                'minIter': '1',
                'maxIter': '5',
            }
        else:
            return {
                'solver': 'PCG',
                'preconditioner': {
                    'preconditioner': 'GAMG',
                    'smoother': 'DIC',
                    'tolerance': '1e-5',
                    'relTol': '0.1',
                },
                'tolerance': '1e-16',
                'relTol': '0.1',
                'minIter': '1',
                'maxIter': '5',
            }

    def _constructSolversH(self, phase):
        if phase == Phase.SOLID:
            return {
                'solver': 'PBiCGStab',
                'preconditioner': {
                    'preconditioner': 'GAMG',
                    'smoother': 'DIC',
                    'tolerance': '1e-5',
                    'relTol': '0.1',
                },
                'tolerance': '1e-16',
                'relTol': '0.1',
                'minIter': '1',
                'maxIter': '5',
            }
        else:
            return {
                'solver': 'PBiCGStab',
                'preconditioner': {
                    'preconditioner': 'GAMG',
                    'smoother': 'DILU',
                    'tolerance': '1e-5',
                    'relTol': '0.1',
                },
                'tolerance': '1e-16',
                'relTol': '0.1',
                'minIter': '1',
                'maxIter': '5',
            }