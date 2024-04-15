#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import logging

from lxml import etree

from resources import resource

logger = logging.getLogger(__name__)

_ns = 'http://www.baramcfd.org/baram'
_nsmap = {'': _ns}


def _addShowChartAndWriteIntervalV1(parent):
    if parent.find('showChart', namespaces=_nsmap) is None:
        logger.debug(f'    Adding showChart to {parent}')
        child = etree.Element(f'{{{_ns}}}showChart')
        child.text = 'false'
        parent.insert(1, child)

    if parent.find('writeInterval', namespaces=_nsmap) is None:
        logger.debug(f'    Adding writeInterval to {parent}')
        child = etree.Element(f'{{{_ns}}}writeInterval')
        child.text = '1'
        parent.insert(2, child)


def _version_1(root: etree.Element):
    logger.debug('  Upgrading to v2')
    # print(etree.tostring(root, xml_declaration=True, encoding='UTF-8'))
    root.set('version', '2')

    for p in root.findall(f'.//material/density', namespaces=_nsmap):
        if p.find('polynomial', namespaces=_nsmap) is None:
            logger.debug(f'    Adding polynomial to {p}')
            # Add "polynomial" at the end of child elements
            etree.SubElement(p, f'{{{_ns}}}polynomial').text = ''

    for p in root.findall(f'.//cellZone/actuatorDisk', namespaces=_nsmap):
        if p.find('upstreamPoint', namespaces=_nsmap) is None:
            e = etree.fromstring('''
                <upstreamPoint xmlns="http://www.baramcfd.org/baram">
                    <x>0</x>
                    <y>0</y>
                    <z>0</z>
                </upstreamPoint>
            ''')
            p.insert(4, e)

    for p in root.findall(f'.//monitors/forces/forceMonitor', namespaces=_nsmap):
        _addShowChartAndWriteIntervalV1(p)

    for p in root.findall(f'.//monitors/points/pointMonitor', namespaces=_nsmap):
        _addShowChartAndWriteIntervalV1(p)

    for p in root.findall(f'.//monitors/surfaces/surfaceMonitor', namespaces=_nsmap):
        _addShowChartAndWriteIntervalV1(p)

        e = p.find('reportType', namespaces=_nsmap)
        if e.text == 'flowRate':
            logger.debug(f'    Changing flowRate to massFlowRate in {p}')
            e.text = 'massFlowRate'

    for p in root.findall(f'.//monitor/volumes/volumeMonitor', namespaces=_nsmap):
        _addShowChartAndWriteIntervalV1(p)

    # print(etree.tostring(root, xml_declaration=True, encoding='UTF-8'))


def _version_2(root: etree.Element):
    logger.debug('  Upgrading to v3')

    # print(etree.tostring(root, xml_declaration=True, encoding='UTF-8'))

    root.set('version', '3')

    for p in root.findall(f'.//regions/region', namespaces=_nsmap):
        if p.find('secondaryMaterials', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "secondaryMaterials" to {p}')
            e = etree.Element(f'{{{_ns}}}secondaryMaterials')
            p.insert(2, e)
        if p.find('phaseInteractions', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "phaseInteractions" to {p}')
            e = etree.fromstring('''
                <phaseInteractions xmlns="http://www.baramcfd.org/baram">
                    <surfaceTensions><material1/><material2/><surfaceTension/></surfaceTensions>
                </phaseInteractions>
            ''')
            p.insert(3, e)

    for p in root.findall(f'.//cellZone/sourceTerms', namespaces=_nsmap):
        if p.find('materials', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "materials" to {p}')
            e = etree.Element(f'{{{_ns}}}materials')
            p.insert(1, e)

    for p in root.findall(f'.//boundaryConditions/boundaryCondition', namespaces=_nsmap):
        if p.find('volumeFractions', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "volumeFractions" to {p}')
            etree.SubElement(p, f'{{{_ns}}}volumeFractions')

    for p in root.findall(f'.//boundaryCondition/wall', namespaces=_nsmap):
        if p.find('wallAdhesions', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "wallAdhesions" to {p}')
            e = etree.fromstring('''
                <wallAdhesions xmlns="http://www.baramcfd.org/baram">
                    <model>none</model>
                    <limit>none</limit>
                </wallAdhesions>
            ''')
            p.append(e)

    for p in root.findall(f'.//numericalConditions/underRelaxationFactors', namespaces=_nsmap):
        if p.find('volumeFraction', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "volumeFraction" to {p}')
            etree.SubElement(p, f'{{{_ns}}}volumeFraction').text = '0.7'
            etree.SubElement(p, f'{{{_ns}}}volumeFractionFinal').text = '1'

    for p in root.findall(f'.//numericalConditions', namespaces=_nsmap):
        if p.find('multiphase', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "multiphase" to {p}')
            e = etree.fromstring('''
                <multiphase xmlns="http://www.baramcfd.org/baram">
                    <maxIterationsPerTimeStep>2</maxIterationsPerTimeStep>
                    <numberOfCorrectors>1</numberOfCorrectors>
                    <useSemiImplicitMules>true</useSemiImplicitMules>
                    <phaseInterfaceCompressionFactor>1</phaseInterfaceCompressionFactor>
                    <numberOfMulesIterations>3</numberOfMulesIterations>
                </multiphase>
            ''')
            p.insert(7, e)

    for p in root.findall(f'.//numericalConditions/convergenceCriteria', namespaces=_nsmap):
        if p.find('volumeFraction', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "volumeFraction" to {p}')
            e = etree.fromstring('''
                <volumeFraction xmlns="http://www.baramcfd.org/baram">
                    <absolute>0.001</absolute>
                    <relative>0.05</relative>
                </volumeFraction>
            ''')
            p.append(e)

    if (p := root.find('initialization/initialValues', namespaces=_nsmap)) is not None:
        ux = p.find('velocity/x', namespaces=_nsmap).text
        uy = p.find('velocity/y', namespaces=_nsmap).text
        uz = p.find('velocity/z', namespaces=_nsmap).text
        pr = p.find('pressure', namespaces=_nsmap).text
        t = p.find('temperature', namespaces=_nsmap).text
        v = p.find('scaleOfVelocity', namespaces=_nsmap).text
        i = p.find('turbulentIntensity', namespaces=_nsmap).text
        b = p.find('turbulentViscosity', namespaces=_nsmap).text

        e = root.find('initialization', namespaces=_nsmap)
        root.remove(e)

        for p in root.findall(f'regions/region', namespaces=_nsmap):
            logger.debug(f'    Adding "initialization" to {p}')
            e = etree.fromstring(f'''
                    <initialization xmlns="http://www.baramcfd.org/baram">
                        <initialValues>
                            <velocity><x>{ux}</x><y>{uy}</y><z>{uz}</z></velocity>
                            <pressure>{pr}</pressure>
                            <temperature>{t}</temperature>
                            <scaleOfVelocity>{v}</scaleOfVelocity>
                            <turbulentIntensity>{i}</turbulentIntensity>
                            <turbulentViscosity>{b}</turbulentViscosity>
                            <volumeFractions></volumeFractions>
                        </initialValues>
                        <advanced>
                            <sections></sections>
                        </advanced>
                    </initialization>
                ''')
            p.append(e)

    for p in root.findall(f'.//runConditions', namespaces=_nsmap):
        if p.find('VoFMaxCourantNumber', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "VoFMaxCourantNumber" to {p}')
            e = etree.Element(f'{{{_ns}}}VoFMaxCourantNumber')
            e.text = '1'
            p.insert(4, e)

    for p in root.findall(f'.//materials/material', namespaces=_nsmap):
        if (e := p.find('surfaceTension', namespaces=_nsmap)) is not None:
            p.remove(e)

    if (p := root.find('general/operatingConditions/gravity', namespaces=_nsmap)) is not None:
        p.set('disabled', 'false')


def _version_3(root: etree.Element):
    logger.debug('  Upgrading to v4')

    root.set('version', '4')

    if (p := root.find('runCalculation', namespaces=_nsmap)) is not None:
        if p.find('batch', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "batch" to {p}')
            e = etree.fromstring('<batch xmlns="http://www.baramcfd.org/baram"><parameters/></batch>')
            p.append(e)

    if (p := root.find('models/turbulenceModels/k-epsilon/realizable', namespaces=_nsmap)) is not None:
        if p.find('threshold', namespaces=_nsmap) is None:
            e = etree.Element(f'{{{_ns}}}threshold')
            e.text = '60'
            p.append(e)

        if p.find('blendingWidth', namespaces=_nsmap) is None:
            e = etree.Element(f'{{{_ns}}}blendingWidth')
            e.text = '10'
            p.append(e)

    for p in root.findall(f'.//regions/region/phaseInteractions/surfaceTensions', namespaces=_nsmap):
        e1 = p.find('material1', namespaces=_nsmap)
        if e1 is not None:
            logger.debug(f'    Splitting surface tensions in {p}')
            e2 = p.find('material2', namespaces=_nsmap)
            e = p.find('surfaceTension', namespaces=_nsmap)

            p.remove(e)
            p.remove(e1)
            p.remove(e2)

            if e1.text is not None:
                mids1 = e1.text.split()
                mids2 = e2.text.split()
                values = e.text.split()

                for i in range(len(values)):
                    e = etree.fromstring(f'<surfaceTension xmlns="http://www.baramcfd.org/baram">'
                                         f' <mid>{mids1[i]}</mid><mid>{mids2[i]}</mid><value>{values[i]}</value>'
                                         f'</surfaceTension>')
                    p.append(e)


def _version_4(root: etree.Element):
    logger.debug('  Upgrading to v5')

    root.set('version', '5')

    if (pp := root.find('numericalConditions', namespaces=_nsmap)) is not None:
        if (p := pp.find('discretizationSchemes', namespaces=_nsmap)) is not None:
            if p.find('pressure', namespaces=_nsmap) is None:
                logger.debug(f'    Adding "pressure" to {p}')
                e = etree.fromstring(
                    '<pressure xmlns="http://www.baramcfd.org/baram">momentumWeightedReconstruct</pressure>')
                p.append(e)

        if pp.find('densityBasedSolverParameters', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "densityBasedSolverParameters" to {p}')
            e = etree.fromstring(
                '<densityBasedSolverParameters xmlns="http://www.baramcfd.org/baram">'
                '   <formulation>implicit</formulation>'
                '   <fluxType>roeFlux</fluxType>'
                '   <entropyFixCoefficient>0.5</entropyFixCoefficient>'
                '   <cutOffMachNumber>0.729</cutOffMachNumber>'
                '</densityBasedSolverParameters>')
            pp.insert(1, e)

    for e in root.findall('monitors/*/*/field/field[.="modifiedPressure"]', namespaces=_nsmap):
        logger.debug(f'    Replacing text of {e} to "pressure"')
        e.text = 'pressure'

    for p in root.findall('.//boundaryConditions', namespaces=_nsmap):
        for e in p.findall('boundaryCondition/subsonicInflow', namespaces=_nsmap):
            e.tag = '{http://www.baramcfd.org/baram}subsonicInlet'

    if (p := root.find('numericalConditions/convergenceCriteria', namespaces=_nsmap)) is not None:
        if p.find('density', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "density" to {p}')
            e = etree.fromstring(
                '<density xmlns="http://www.baramcfd.org/baram">'
                '   <absolute>0.001</absolute><relative>0.05</relative>'
                '</density>')
            p.insert(1, e)

    for p in root.findall('.//boundaryCondition/farFieldRiemann', namespaces=_nsmap):
        if p.find('flowDirection/specificationMethod', namespaces=_nsmap) is None:
            logger.debug(f'    Updating "flowDirection" to {p}')
            e = p.find('flowDirection', namespaces=_nsmap)
            logger.debug(e)
            x = e.find('x', namespaces=_nsmap).text
            y = e.find('y', namespaces=_nsmap).text
            z = e.find('z', namespaces=_nsmap).text
            p.remove(e)

            e = etree.fromstring(
                '<flowDirection xmlns="http://www.baramcfd.org/baram">'
                '   <specificationMethod>direct</specificationMethod>'
                f'  <dragDirection><x>{x}</x><y>{y}</y><z>{z}</z></dragDirection>'
                '   <liftDirection><x>0</x><y>1</y><z>0</z></liftDirection>'
                '   <angleOfAttack>0</angleOfAttack><angleOfSideslip>0</angleOfSideslip>'
                '</flowDirection>')
            p.insert(0, e)

    for p in root.findall('monitors/forces/forceMonitor', namespaces=_nsmap):
        if p.find('forceDirection', namespaces=_nsmap) is None:
            logger.debug(f'    Changing directions to "forceDirection" in {p}')
            e = p.find('liftDirection', namespaces=_nsmap)
            liftX = e.find('x', namespaces=_nsmap).text
            liftY = e.find('y', namespaces=_nsmap).text
            liftZ = e.find('z', namespaces=_nsmap).text
            p.remove(e)

            e = p.find('dragDirection', namespaces=_nsmap)
            dragX = e.find('x', namespaces=_nsmap).text
            dragY = e.find('y', namespaces=_nsmap).text
            dragZ = e.find('z', namespaces=_nsmap).text
            p.remove(e)

            e = etree.fromstring(
                '<forceDirection xmlns="http://www.baramcfd.org/baram">'
                '   <specificationMethod>direct</specificationMethod>'
                f'  <dragDirection><x>{dragX}</x><y>{dragY}</y><z>{dragZ}</z></dragDirection>'
                f'  <liftDirection><x>{liftX}</x><y>{liftY}</y><z>{liftZ}</z></liftDirection>'
                '   <angleOfAttack>0</angleOfAttack><angleOfSideslip>0</angleOfSideslip>'
                '</forceDirection>')
            p.insert(3, e)


def _version_5(root: etree.Element):
    logger.debug('  Upgrading to v6')

    # Keep this commented until official v6 spec. is released
    # root.set('version', '6')
    for p in root.findall('models/turbulenceModels', namespaces=_nsmap):
        if p.find('les', namespaces=_nsmap) is None:
            logger.debug(f'    Adding "les" to {p}')
            e = etree.fromstring(
                '<les xmlns="http://www.baramcfd.org/baram">'
                '   <subgridScaleModel>Smagorinsky</subgridScaleModel>'
                '   <lengthScaleModel>cubeRootVol</lengthScaleModel>'
                '   <modelConstants><k>0.094</k><e>1.048</e><w>0.325</w></modelConstants>'
                '</les>')
            p.insert(3, e)

    for p in root.findall('.//boundaryCondition/turbulence', namespaces=_nsmap):
        if p.find('les', namespaces=_nsmap) is None:
            logger.debug(f'    Updating "les" to {p}')

            e = etree.fromstring(
                '<les xmlns="http://www.baramcfd.org/baram">'
                '   <specification>subgridScaleK</specification>'
                '   <subgridKineticEnergy>1</subgridKineticEnergy>'
                '   <subgridTurbulentIntensity>1</subgridTurbulentIntensity>'
                '   <turbulentViscosityRatio>10</turbulentViscosityRatio>'
                '</les>')
            p.append(e)


_fTable = [
    None,
    _version_1,
    _version_2,
    _version_3,
    _version_4,
    _version_5
]

currentVersion = int(etree.parse(resource.file('configurations/baram.cfg.xsd')).getroot().get('version'))


def migrate(root: etree.Element):
    version = int(root.get('version'))
    logger.debug(f'Migrating from v{version} to v{currentVersion}')

    if version == currentVersion:
        logger.debug('Migration not necessary')
        return root
    elif version > currentVersion:
        logger.debug(f'Invalid version {version}(Latest {currentVersion})')
        raise IndexError
    else:
        for i in range(version, currentVersion):
            if i < len(_fTable):
                _fTable[i](root)
