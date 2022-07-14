import unittest

from coredb import coredb
from openfoam.boundary_conditions.u import U
from view.setup.boundary_conditions.boundary_db import BoundaryDB

dimensions = '[0 1 -1 0 0 0 0]'
region = "testRegion_1"
boundary = "testBoundary_1"


class TestU(unittest.TestCase):
    def setUp(self):
        self._db = coredb.CoreDB()
        self._db.addRegion(region)
        bcid = self._db.addBoundaryCondition(region, boundary, 'wall')
        self._xpath = BoundaryDB.getXPath(bcid)
        self._initialValue = self._db.getVector('.//initialization/initialValues/velocity')

    def tearDown(self) -> None:
        del coredb.CoreDB._instance

    # Velocity Inlet
    def testVelocityInletComponentConstant(self):
        self._db.setValue(self._xpath + '/physicalType', 'velocityInlet')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/specification', 'component')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/component/profile', 'constant')
        content = U(region).build().asDict()
        self.assertEqual(dimensions, content['dimensions'])
        self.assertEqual(self._initialValue, content['internalField'][1])
        self.assertEqual('fixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(self._xpath + '/velocityInlet/velocity/component/constant'),
                         content['boundaryField'][boundary]['value'][1])

    # Velocity Inlet
    def testVelocityInletComponentSpatial(self):
        self._db.setValue(self._xpath + '/physicalType', 'velocityInlet')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/specification', 'component')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/component/profile', 'spatialDistribution')
        content = U(region).build().asDict()
        self.assertEqual('timeVaryingMappedFixedValue', content['boundaryField'][boundary]['type'])
        # ToDo: Add check according to boundary field spec

    # Velocity Inlet
    def testVelocityInletComponentTemporal(self):
        self._db.setValue(self._xpath + '/physicalType', 'velocityInlet')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/specification', 'component')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/component/profile', 'temporalDistribution')
        content = U(region).build().asDict()
        t = self._db.getValue(
            self._xpath + '/velocityInlet/velocity/component/temporalDistribution/piecewiseLinear/t').split()
        x = self._db.getValue(
            self._xpath + '/velocityInlet/velocity/component/temporalDistribution/piecewiseLinear/x').split()
        y = self._db.getValue(
            self._xpath + '/velocityInlet/velocity/component/temporalDistribution/piecewiseLinear/y').split()
        z = self._db.getValue(
            self._xpath + '/velocityInlet/velocity/component/temporalDistribution/piecewiseLinear/z').split()
        self.assertEqual('uniformFixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual([[t[i], [x[i], y[i], z[i]]] for i in range(len(t))],
                         content['boundaryField'][boundary]['uniformValue'][1])

    # Velocity Inlet
    def testVelocityInletMagnitudeConstant(self):
        self._db.setValue(self._xpath + '/physicalType', 'velocityInlet')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/specification', 'magnitudeNormal')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/magnitudeNormal/profile', 'constant')
        content = U(region).build().asDict()
        self.assertEqual('surfaceNormalFixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual(-float(self._db.getValue(self._xpath + '/velocityInlet/velocity/magnitudeNormal/constant')),
                         content['boundaryField'][boundary]['refValue'][1])

    # Velocity Inlet
    def testVelocityInletMagnitudeSpatial(self):
        self._db.setValue(self._xpath + '/physicalType', 'velocityInlet')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/specification', 'magnitudeNormal')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/magnitudeNormal/profile', 'spatialDistribution')
        content = U(region).build().asDict()
        self.assertEqual('timeVaryingMappedFixedValue', content['boundaryField'][boundary]['type'])
        # ToDo: Add check according to boundary field spec

    # Velocity Inlet
    def testVelocityInletMagnitudeTemporal(self):
        self._db.setValue(self._xpath + '/physicalType', 'velocityInlet')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/specification', 'magnitudeNormal')
        self._db.setValue(self._xpath + '/velocityInlet/velocity/magnitudeNormal/profile', 'temporalDistribution')
        content = U(region).build().asDict()
        t = self._db.getValue(
            self._xpath + '/velocityInlet/velocity/magnitudeNormal/temporalDistribution/piecewiseLinear/t').split()
        v = self._db.getValue(
            self._xpath + '/velocityInlet/velocity/magnitudeNormal/temporalDistribution/piecewiseLinear/v').split()
        self.assertEqual('uniformNormalFixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual([[t[i], -float(v[i])] for i in range(len(t))],
                         content['boundaryField'][boundary]['uniformValue'][1])

    # Flow Rate
    def testFlowRateInletVolume(self):
        self._db.setValue(self._xpath + '/physicalType', 'flowRateInlet')
        self._db.setValue(self._xpath + '/flowRateInlet/flowRate/specification', 'volumeFlowRate')
        content = U(region).build().asDict()
        self.assertEqual('flowRateInletVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getValue(self._xpath + '/flowRateInlet/flowRate/volumeFlowRate'),
                         content['boundaryField'][boundary]['volumetricFlowRate'])

    # Flow Rate
    def testFlowRateInletMass(self):
        self._db.setValue(self._xpath + '/physicalType', 'flowRateInlet')
        self._db.setValue(self._xpath + '/flowRateInlet/flowRate/specification', 'massFlowRate')
        content = U(region).build().asDict()
        self.assertEqual('flowRateInletVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getValue(self._xpath + '/flowRateInlet/flowRate/massFlowRate'),
                         content['boundaryField'][boundary]['massFlowRate'])

    def testPressureInlet(self):
        self._db.setValue(self._xpath + '/physicalType', 'pressureInlet')
        content = U(region).build().asDict()
        self.assertEqual('pressureInletOutletVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._initialValue, content['boundaryField'][boundary]['value'][1])

    def testPressureOutlet(self):
        self._db.setValue(self._xpath + '/physicalType', 'pressureOutlet')
        content = U(region).build().asDict()
        self.assertEqual('pressureInletOutletVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._initialValue, content['boundaryField'][boundary]['value'][1])

    def testAblInlet(self):
        self._db.setValue(self._xpath + '/physicalType', 'ablInlet')
        content = U(region).build().asDict()
        self.assertEqual('atmBoundaryLayerInletVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(BoundaryDB.ABL_INLET_CONDITIONS_XPATH + '/flowDirection'),
                         content['boundaryField'][boundary]['flowDir'])
        self.assertEqual(self._db.getVector(BoundaryDB.ABL_INLET_CONDITIONS_XPATH + '/groundNormalDirection'),
                         content['boundaryField'][boundary]['zDir'])
        self.assertEqual(self._db.getValue(BoundaryDB.ABL_INLET_CONDITIONS_XPATH + '/referenceFlowSpeed'),
                         content['boundaryField'][boundary]['Uref'])
        self.assertEqual(self._db.getValue(BoundaryDB.ABL_INLET_CONDITIONS_XPATH + '/referenceHeight'),
                         content['boundaryField'][boundary]['Zref'])
        self.assertEqual(self._db.getValue(BoundaryDB.ABL_INLET_CONDITIONS_XPATH + '/surfaceRoughnessLength'),
                         content['boundaryField'][boundary]['z0'])
        self.assertEqual(self._db.getValue(BoundaryDB.ABL_INLET_CONDITIONS_XPATH + '/minimumZCoordinate'),
                         content['boundaryField'][boundary]['d'])

    def testOpenChannelInlet(self):
        self._db.setValue(self._xpath + '/physicalType', 'openChannelInlet')
        content = U(region).build().asDict()
        self.assertEqual('variableHeightFlowRateInletVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getValue(self._xpath + '/openChannelInlet/volumeFlowRate'),
                         content['boundaryField'][boundary]['flowRate'])
        self.assertEqual(self._initialValue, content['boundaryField'][boundary]['value'][1])

    def testOpenChannelOutlet(self):
        self._db.setValue(self._xpath + '/physicalType', 'openChannelOutlet')
        content = U(region).build().asDict()
        self.assertEqual('outletPhaseMeanVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getValue(self._xpath + '/openChannelOutlet/meanVelocity'),
                         content['boundaryField'][boundary]['Umean'])

    def testOutflow(self):
        self._db.setValue(self._xpath + '/physicalType', 'outflow')
        content = U(region).build().asDict()
        self.assertEqual('zeroGradient', content['boundaryField'][boundary]['type'])

    def testFreeStream(self):
        self._db.setValue(self._xpath + '/physicalType', 'freeStream')
        content = U(region).build().asDict()
        self.assertEqual('freestreamVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(self._xpath + '/freeStream/streamVelocity'),
                         content['boundaryField'][boundary]['U'])

    def testFarFieldRiemann(self):
        self._db.setValue(self._xpath + '/physicalType', 'farFieldRiemann')
        content = U(region).build().asDict()
        self.assertEqual('farfieldRiemann', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(self._xpath + '/farFieldRiemann/flowDirection'),
                         content['boundaryField'][boundary]['flowDir'])
        self.assertEqual(self._db.getValue(self._xpath + '/farFieldRiemann/machNumber'),
                         content['boundaryField'][boundary]['MInf'])
        self.assertEqual(self._db.getValue(self._xpath + '/farFieldRiemann/staticPressure'),
                         content['boundaryField'][boundary]['pInf'])
        self.assertEqual(self._db.getValue(self._xpath + '/farFieldRiemann/staticTemperature'),
                         content['boundaryField'][boundary]['TInf'])

    def testSubsonicInflow(self):
        self._db.setValue(self._xpath + '/physicalType', 'subsonicInflow')
        content = U(region).build().asDict()
        self.assertEqual('subsonicInflow', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(self._xpath + '/subsonicInflow/flowDirection'),
                         content['boundaryField'][boundary]['flowDir'])
        self.assertEqual(self._db.getValue(self._xpath + '/subsonicInflow/totalPressure'),
                         content['boundaryField'][boundary]['p0'])
        self.assertEqual(self._db.getValue(self._xpath + '/subsonicInflow/totalTemperature'),
                         content['boundaryField'][boundary]['T0'])

    def testSubsonicOutflow(self):
        self._db.setValue(self._xpath + '/physicalType', 'subsonicOutflow')
        content = U(region).build().asDict()
        self.assertEqual('subsonicOutflow', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getValue(self._xpath + '/subsonicOutflow/staticPressure'),
                         content['boundaryField'][boundary]['pExit'])

    def testSupersonicInflow(self):
        self._db.setValue(self._xpath + '/physicalType', 'supersonicInflow')
        content = U(region).build().asDict()
        self.assertEqual('fixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(self._xpath + '/supersonicInflow/velocity'),
                         content['boundaryField'][boundary]['value'][1])

    def testSupersonicOutflow(self):
        self._db.setValue(self._xpath + '/physicalType', 'supersonicOutflow')
        content = U(region).build().asDict()
        self.assertEqual('zeroGradient', content['boundaryField'][boundary]['type'])

    # Wall
    def testNoSlip(self):
        self._db.setValue(self._xpath + '/physicalType', 'wall')
        self._db.setValue(self._xpath + '/wall/velocity/type', 'noSlip')
        content = U(region).build().asDict()
        self.assertEqual('fixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual('(0 0 0)', content['boundaryField'][boundary]['value'][1])

    # Wall
    def testSlip(self):
        self._db.setValue(self._xpath + '/physicalType', 'wall')
        self._db.setValue(self._xpath + '/wall/velocity/type', 'slip')
        content = U(region).build().asDict()
        self.assertEqual('slip', content['boundaryField'][boundary]['type'])

    # Wall
    def testMovingWall(self):
        self._db.setValue(self._xpath + '/physicalType', 'wall')
        self._db.setValue(self._xpath + '/wall/velocity/type', 'movingWall')
        content = U(region).build().asDict()
        self.assertEqual('movingWallVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual('uniform (0 0 0)', content['boundaryField'][boundary]['value'])

    # Wall
    def testAtmosphericWall(self):
        self._db.setValue(self._xpath + '/physicalType', 'wall')
        self._db.setValue(self._xpath + '/wall/velocity/type', 'atmosphericWall')
        content = U(region).build().asDict()
        self.assertEqual('fixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual('(0 0 0)', content['boundaryField'][boundary]['value'][1])

    # Wall
    def testTranslationalMovingWall(self):
        self._db.setValue(self._xpath + '/physicalType', 'wall')
        self._db.setValue(self._xpath + '/wall/velocity/type', 'translationalMovingWall')
        content = U(region).build().asDict()
        self.assertEqual('fixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(self._xpath + '/wall/velocity/translationalMovingWall/velocity'),
                         content['boundaryField'][boundary]['value'][1])

    # Wall
    def testWallRotationalMovingWall(self):
        self._db.setValue(self._xpath + '/physicalType', 'wall')
        self._db.setValue(self._xpath + '/wall/velocity/type', 'rotationalMovingWall')
        content = U(region).build().asDict()
        self.assertEqual('rotatingWallVelocity', content['boundaryField'][boundary]['type'])
        self.assertEqual(self._db.getVector(self._xpath + '/wall/velocity/rotationalMovingWall/rotationAxisOrigin'),
                         content['boundaryField'][boundary]['origin'])
        self.assertEqual(self._db.getVector(self._xpath + '/wall/velocity/rotationalMovingWall/rotationAxisDirection'),
                         content['boundaryField'][boundary]['axis'])
        self.assertEqual(self._db.getValue(self._xpath + '/wall/velocity/rotationalMovingWall/speed'),
                         content['boundaryField'][boundary]['omega'])

    def testThermoCoupledWall(self):
        self._db.setValue(self._xpath + '/physicalType', 'thermoCoupledWall')
        content = U(region).build().asDict()
        self.assertEqual('fixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual('(0 0 0)', content['boundaryField'][boundary]['value'][1])

    def testSymmetry(self):
        self._db.setValue(self._xpath + '/physicalType', 'symmetry')
        content = U(region).build().asDict()
        self.assertEqual('symmetry', content['boundaryField'][boundary]['type'])

    # Interface
    def testInternalInterface(self):
        self._db.setValue(self._xpath + '/physicalType', 'interface')
        self._db.setValue(self._xpath + '/interface/mode', 'internalInterface')
        content = U(region).build().asDict()
        self.assertEqual('cyclicAMI', content['boundaryField'][boundary]['type'])

    # Interface
    def testRotationalPeriodic(self):
        self._db.setValue(self._xpath + '/physicalType', 'interface')
        self._db.setValue(self._xpath + '/interface/mode', 'rotationalPeriodic')
        content = U(region).build().asDict()
        self.assertEqual('cyclicAMI', content['boundaryField'][boundary]['type'])

    # Interface
    def testTranslationalPeriodic(self):
        self._db.setValue(self._xpath + '/physicalType', 'interface')
        self._db.setValue(self._xpath + '/interface/mode', 'translationalPeriodic')
        content = U(region).build().asDict()
        self.assertEqual('cyclicAMI', content['boundaryField'][boundary]['type'])

    # Interface
    def testRegionInterface(self):
        self._db.setValue(self._xpath + '/physicalType', 'interface')
        self._db.setValue(self._xpath + '/interface/mode', 'regionInterface')
        content = U(region).build().asDict()
        self.assertEqual('fixedValue', content['boundaryField'][boundary]['type'])
        self.assertEqual('(0 0 0)', content['boundaryField'][boundary]['value'][1])

    def testPorousJump(self):
        self._db.setValue(self._xpath + '/physicalType', 'porousJump')
        content = U(region).build().asDict()
        self.assertEqual('cyclic', content['boundaryField'][boundary]['type'])

    def testFan(self):
        self._db.setValue(self._xpath + '/physicalType', 'fan')
        content = U(region).build().asDict()
        self.assertEqual('cyclic', content['boundaryField'][boundary]['type'])

    def testEmpty(self):
        self._db.setValue(self._xpath + '/physicalType', 'empty')
        content = U(region).build().asDict()
        self.assertEqual('empty', content['boundaryField'][boundary]['type'])

    def testCyclic(self):
        self._db.setValue(self._xpath + '/physicalType', 'cyclic')
        content = U(region).build().asDict()
        self.assertEqual('cyclic', content['boundaryField'][boundary]['type'])

    def testWedge(self):
        self._db.setValue(self._xpath + '/physicalType', 'wedge')
        content = U(region).build().asDict()
        self.assertEqual('wedge', content['boundaryField'][boundary]['type'])


if __name__ == '__main__':
    unittest.main()