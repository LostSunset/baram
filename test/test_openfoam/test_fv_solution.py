import unittest

from coredb import coredb
from openfoam.system.fv_solution import FvSolution
from view.setup.general.general_db import GeneralDB
from view.setup.cell_zone_conditions.cell_zone_db import RegionDB
from view.setup.materials.material_db import MaterialDB
from view.solution.numerical_conditions.numerical_db import NumericalDB

region = "testRegion_1"


class TestFvSolution(unittest.TestCase):
    def setUp(self):
        self._db = coredb.CoreDB()
        self._db.addRegion(region)
        self._air = self._db.getAttribute(f'{MaterialDB.MATERIALS_XPATH}/material[name="air"]', 'mid')
        self._steel = str(self._db.addMaterial('steel'))

    def tearDown(self) -> None:
        del coredb.CoreDB._instance

    def testCompressible(self):
        self._db.setValue(GeneralDB.FLOW_TYPE_XPATH, "compressible")
        content = FvSolution(region).build().asDict()
        self.assertEqual('PBiCGStab', content['solvers']['p']['solver'])

    def testIncompressible(self):
        self._db.setValue(GeneralDB.FLOW_TYPE_XPATH, "incompressible")
        content = FvSolution(region).build().asDict()
        self.assertEqual('PCG', content['solvers']['p']['solver'])

    def testSolid(self):
        self._db.setValue(RegionDB.getXPath(region) + '/material', self._steel)
        content = FvSolution(region).build().asDict()
        self.assertEqual('DIC', content['solvers']['h']['preconditioner']['smoother'])

    def testFluid(self):
        self._db.setValue(RegionDB.getXPath(region) + '/material', self._air)
        content = FvSolution(region).build().asDict()
        self.assertEqual('DILU', content['solvers']['h']['preconditioner']['smoother'])

    def testSimpleSolid(self):
        self._db.setValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/pressureVelocityCouplingScheme', 'SIMPLE')
        self._db.setValue(RegionDB.getXPath(region) + '/material', self._steel)
        content = FvSolution(region).build().asDict()
        self.assertEqual('no', content['SIMPLE']['consistent'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p_rgh'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/momentum/absolute'),
                         content['SIMPLE']['residualControl']['U'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/energy/absolute'),
                         content['SIMPLE']['residualControl']['h'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/turbulence/absolute'),
                         content['SIMPLE']['residualControl']['"(k|epsilon|omega|nuTilda)"'])
        self.assertEqual('no', content['PIMPLE']['consistent'])

    def testSimpleFluid(self):
        self._db.setValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/pressureVelocityCouplingScheme', 'SIMPLE')
        self._db.setValue(RegionDB.getXPath(region) + '/material', self._air)
        content = FvSolution(region).build().asDict()
        self.assertEqual('no', content['SIMPLE']['consistent'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p_rgh'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/momentum/absolute'),
                         content['SIMPLE']['residualControl']['U'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/energy/absolute'),
                         content['SIMPLE']['residualControl']['h'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/turbulence/absolute'),
                         content['SIMPLE']['residualControl']['"(k|epsilon|omega|nuTilda)"'])
        self.assertEqual('no', content['PIMPLE']['consistent'])
        self.assertEqual(self._db.getValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/numberOfCorrectors'),
                         content['PIMPLE']['nCorrectors'])

    def testSimplecSolid(self):
        self._db.setValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/pressureVelocityCouplingScheme', 'SIMPLEC')
        self._db.setValue(RegionDB.getXPath(region) + '/material', self._steel)
        content = FvSolution(region).build().asDict()
        self.assertEqual('no', content['SIMPLE']['consistent'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p_rgh'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/momentum/absolute'),
                         content['SIMPLE']['residualControl']['U'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/energy/absolute'),
                         content['SIMPLE']['residualControl']['h'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/turbulence/absolute'),
                         content['SIMPLE']['residualControl']['"(k|epsilon|omega|nuTilda)"'])
        self.assertEqual('no', content['PIMPLE']['consistent'])

    def testSimplecFluid(self):
        self._db.setValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/pressureVelocityCouplingScheme', 'SIMPLEC')
        self._db.setValue(RegionDB.getXPath(region) + '/material', self._air)
        content = FvSolution(region).build().asDict()
        self.assertEqual('yes', content['SIMPLE']['consistent'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['SIMPLE']['residualControl']['p_rgh'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/momentum/absolute'),
                         content['SIMPLE']['residualControl']['U'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/energy/absolute'),
                         content['SIMPLE']['residualControl']['h'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/turbulence/absolute'),
                         content['SIMPLE']['residualControl']['"(k|epsilon|omega|nuTilda)"'])
        self.assertEqual('yes', content['PIMPLE']['consistent'])
        self.assertEqual(self._db.getValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/numberOfCorrectors'),
                         content['PIMPLE']['nCorrectors'])

    def testRegion(self):
        content = FvSolution(region).build().asDict()
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['PIMPLE']['residualControl']['p']['tolerance'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/relative'),
                         content['PIMPLE']['residualControl']['p']['relTol'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/absolute'),
                         content['PIMPLE']['residualControl']['p_rgh']['tolerance'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/pressure/relative'),
                         content['PIMPLE']['residualControl']['p_rgh']['relTol'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/momentum/absolute'),
                         content['PIMPLE']['residualControl']['U']['tolerance'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/momentum/relative'),
                         content['PIMPLE']['residualControl']['U']['relTol'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/energy/absolute'),
                         content['PIMPLE']['residualControl']['h']['tolerance'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/energy/relative'),
                         content['PIMPLE']['residualControl']['h']['relTol'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/turbulence/absolute'),
                         content['PIMPLE']['residualControl']['"(k|epsilon|omega|nuTilda)"']['tolerance'])
        self.assertEqual(self._db.getValue('.//convergenceCriteria/turbulence/relative'),
                         content['PIMPLE']['residualControl']['"(k|epsilon|omega|nuTilda)"']['relTol'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/pressure'),
                         content['relaxationFactors']['fields']['p'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/pressureFinal'),
                         content['relaxationFactors']['fields']['pFinal'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/pressure'),
                         content['relaxationFactors']['fields']['p_rgh'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/pressureFinal'),
                         content['relaxationFactors']['fields']['p_rghFinal'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/density'),
                         content['relaxationFactors']['fields']['rho'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/densityFinal'),
                         content['relaxationFactors']['fields']['rhoFinal'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/momentum'),
                         content['relaxationFactors']['equations']['U'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/momentumFinal'),
                         content['relaxationFactors']['equations']['UFinal'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/energy'),
                         content['relaxationFactors']['equations']['h'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/energyFinal'),
                         content['relaxationFactors']['equations']['hFinal'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/turbulence'),
                         content['relaxationFactors']['equations']['(k|epsilon|omega|nuTilda)'])
        self.assertEqual(self._db.getValue('.//underRelaxationFactors/turbulenceFinal'),
                         content['relaxationFactors']['equations']['(k|epsilon|omega|nuTilda)Final'])

    def testNoRegion(self):
        content = FvSolution().build().asDict()
        self.assertEqual(self._db.getValue(NumericalDB.NUMERICAL_CONDITIONS_XPATH + '/maxIterationsPerTimeStep'),
                         content['PIMPLE']['nOuterCorrectors'])


if __name__ == '__main__':
    unittest.main()