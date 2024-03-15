#!/usr/bin/env python
# -*- coding: utf-8 -*-
import qasync
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QEvent, QTimer
from vtkmodules.vtkCommonColor import vtkNamedColors

from widgets.async_message_box import AsyncMessageBox
from widgets.radio_group import RadioGroup

from baramMesh.app import app
from baramMesh.db.simple_schema import DBError
from baramMesh.db.configurations_schema import Shape, GeometryType, CFDType
from baramMesh.rendering.vtk_loader import hexPolyData, cylinderPolyData, spherePolyData, polyDataToActor
from .geometry import RESERVED_NAMES
from .volume_dialog_ui import Ui_VolumeDialog

def showStackPage(stack, page):
    for i in range(stack.count()):
        widget = stack.widget(i)
        if widget.objectName() == page:
            widget.show()
            stack.setCurrentIndex(i)
        else:
            widget.hide()

    stack.adjustSize()


class VolumeDialog(QDialog):
    _cfdTypes = {
        'none': CFDType.NONE.value,
        'cellZone': CFDType.CELL_ZONE.value
    }

    _baseNames = {
        Shape.HEX.value: 'Hex_',
        Shape.CYLINDER.value: 'Cylinder_',
        Shape.SPHERE.value: 'Sphere_',
        Shape.HEX6.value: 'Hex6_'
    }

    def __init__(self, parent, renderingView):
        super().__init__(parent)
        self._ui = Ui_VolumeDialog()
        self._ui.setupUi(self)

        self._renderingView = renderingView
        self._typeRadios = None

        self._gId = None
        self._shape = None

        self._dbElement = None
        self._creationMode = True

        self._actor = None
        self._existingActors = None

        self._connectSignalsSlots()

    def gId(self):
        return self._gId

    def isForCreation(self):
        return self._creationMode

    def setupForAdding(self, shape):
        self.setWindowTitle(self.tr('Add Volume'))

        self._creationMode = True
        self._gId = None
        self._dbElement = app.db.newElement('geometry')
        self._shape = shape

        self._dbElement.setValue('shape', shape)

        self._load()
        self.adjustSize()

    def setupForEdit(self, gId):
        self.setWindowTitle(self.tr('Edit Volume'))

        self._creationMode = False
        self._gId = gId
        self._dbElement = app.db.checkout(f'geometry/{gId}')
        self._shape = self._dbElement.getValue('shape')

        self._load()
        self.adjustSize()

    @qasync.asyncSlot()
    async def accept(self):
        try:
            if not await self._updateElement():
                return

            if self._creationMode:
                db = app.db.checkout()
                self._gId = db.addElement('geometry', self._dbElement)

                name = self._ui.name.text()
                if self._shape == Shape.HEX6.value:
                    for plate in Shape.PLATES.value:
                        element = app.db.newElement('geometry')
                        element.setValue('gType', GeometryType.SURFACE.value)
                        element.setValue('volume', self._gId)
                        element.setValue('name', db.getUniqueValue('geometry', 'name', f'{name}_{plate}'))
                        element.setValue('shape', plate)
                        element.setValue('cfdType', CFDType.BOUNDARY.value)
                        db.addElement('geometry', element)
                else:
                    element = app.db.newElement('geometry')
                    element.setValue('gType', GeometryType.SURFACE.value)
                    element.setValue('volume', self._gId)
                    element.setValue('name', db.getUniqueValue('geometry', 'name', f'{name}_surface'))
                    element.setValue('shape', self._shape)
                    element.setValue('cfdType', CFDType.BOUNDARY.value)
                    db.addElement('geometry', element)

                app.db.commit(db)
            else:
                app.db.commit(self._dbElement)

            super().accept()
        except DBError as e:
            QMessageBox.information(self, self.tr("Input Error"), e.toMessage())

    def event(self, ev):
        if ev.type() == QEvent.Type.LayoutRequest:
            QTimer.singleShot(0, self.adjustSize)

        return super().event(ev)

    def done(self, result):
        if self._actor:
            self._renderingView.removeActor(self._actor)
            self._renderingView.refresh()

        super().done(result)

    def _connectSignalsSlots(self):
        self._ui.preview.clicked.connect(self._preview)

    def _load(self):
        name = self._dbElement.getValue('name')
        if not name:
            baseName = self._baseNames[self._shape]
            name = f"{baseName}{app.db.getUniqueSeq('geometry', 'name', baseName, 1)}"

        self._ui.name.setText(name)

        self._typeRadios = RadioGroup(self._ui.typeRadios)
        self._typeRadios.setObjectMap(self._cfdTypes, self._dbElement.getValue('cfdType'))

        if self._shape == Shape.HEX.value or self._shape == Shape.HEX6.value:
            self._loadHexPage()
        elif self._shape == Shape.SPHERE.value:
            self._loadSpherePage()
        elif self._shape == Shape.CYLINDER.value:
            self._loadCylinderpage()
        else:
            showStackPage(self._ui.geometryStack, None)     # triSurfaceMesh

        self._preview()

    def _loadHexPage(self):
        showStackPage(self._ui.geometryStack, 'hex')

        x1, y1, z1 = self._dbElement.getVector('point1')
        x2, y2, z2 = self._dbElement.getVector('point2')
        self._ui.minX.setText(x1)
        self._ui.minY.setText(y1)
        self._ui.minZ.setText(z1)
        self._ui.maxX.setText(x2)
        self._ui.maxY.setText(y2)
        self._ui.maxZ.setText(z2)

    def _loadSpherePage(self):
        showStackPage(self._ui.geometryStack, 'sphere')

        x, y, z = self._dbElement.getVector('point1')
        self._ui.centerX.setText(x)
        self._ui.centerY.setText(y)
        self._ui.centerZ.setText(z)

        self._ui.sphereRadius.setText(self._dbElement.getValue('radius'))

    def _loadCylinderpage(self):
        showStackPage(self._ui.geometryStack, 'cylinder')

        x1, y1, z1 = self._dbElement.getVector('point1')
        x2, y2, z2 = self._dbElement.getVector('point2')
        self._ui.axis1X.setText(x1)
        self._ui.axis1Y.setText(y1)
        self._ui.axis1Z.setText(z1)
        self._ui.axis2X.setText(x2)
        self._ui.axis2Y.setText(y2)
        self._ui.axis2Z.setText(z2)

        self._ui.cylinderRadius.setText(self._dbElement.getValue('radius'))

        self._ui.annulusRadius.hide()

    async def _updateElement(self):
        name = self._ui.name.text()

        if name in RESERVED_NAMES:
            await AsyncMessageBox().information(
                self, self.tr('Input Error'), self.tr('"{0}" is an invalid geometry name.').format(name))
            return

        if name.find(' ') > -1:
            await AsyncMessageBox().information(
                self, self.tr('Input Error'), self.tr('Geometry name cannot contain spaces'))
            return

        if app.db.getKeys('geometry', lambda i, e: e['name'] == name and i != self._gId):
            await AsyncMessageBox().information(self, self.tr('Input Error'),
                                    self.tr('geometry "{0}" already exists.').format(name))
            return False

        self._dbElement.setValue('gType', GeometryType.VOLUME.value)
        self._dbElement.setValue('name', name)
        self._dbElement.setValue('cfdType', self._typeRadios.value())

        if self._shape == Shape.HEX.value or self._shape == Shape.HEX6.value:
            return self._updateHexData()
        elif self._shape == Shape.SPHERE.value:
            return self._updateSphereData()
        elif self._shape == Shape.CYLINDER.value:
            return self._updateCylinderData()
        else:
            return True     # triSurfaceMesh

    def _updateHexData(self):
        if not self._validateHex():
            QMessageBox.information(self, self.tr('Add Geometry Failed'), self.tr('Invalid coordinates'))
            return False

        self._dbElement.setValue('point1/x', self._ui.minX.text(), self.tr('Minimum X'))
        self._dbElement.setValue('point1/y', self._ui.minY.text(), self.tr('Minimum Y'))
        self._dbElement.setValue('point1/z', self._ui.minZ.text(), self.tr('Minimum Z'))
        self._dbElement.setValue('point2/x', self._ui.maxX.text(), self.tr('Maximum X'))
        self._dbElement.setValue('point2/y', self._ui.maxY.text(), self.tr('Maximum Y'))
        self._dbElement.setValue('point2/z', self._ui.maxZ.text(), self.tr('Maximum Z'))

        return True

    def _updateCylinderData(self):
        self._dbElement.setValue('point1/x', self._ui.axis1X.text(), self.tr('Axis Point1 X'))
        self._dbElement.setValue('point1/y', self._ui.axis1Y.text(), self.tr('Axis Point1 Y'))
        self._dbElement.setValue('point1/z', self._ui.axis1Z.text(), self.tr('Axis Point1 Z'))
        self._dbElement.setValue('point2/x', self._ui.axis2X.text(), self.tr('Axis Point2 X'))
        self._dbElement.setValue('point2/y', self._ui.axis2Y.text(), self.tr('Axis Point2 Y'))
        self._dbElement.setValue('point2/z', self._ui.axis2Z.text(), self.tr('Axis Point2 Z'))
        self._dbElement.setValue('radius', self._ui.cylinderRadius.text(), self.tr('radius'))

        return True

    def _updateSphereData(self):
        self._dbElement.setValue('point1/x', self._ui.centerX.text(), self.tr('Center X'))
        self._dbElement.setValue('point1/y', self._ui.centerY.text(), self.tr('Center Y'))
        self._dbElement.setValue('point1/z', self._ui.centerZ.text(), self.tr('Center Z'))
        self._dbElement.setValue('radius', self._ui.sphereRadius.text(), self.tr('radius'))

        return True

    def _preview(self):
        if self._actor:
            self._renderingView.removeActor(self._actor)

        polyData = None
        try:
            if self._shape == Shape.HEX.value or self._shape == Shape.HEX6.value:
                if points := self._validateHex():
                    polyData = hexPolyData(*points)
            elif self._shape == Shape.CYLINDER.value:
                polyData = cylinderPolyData(
                    (float(self._ui.axis1X.text()), float(self._ui.axis1Y.text()), float(self._ui.axis1Z.text())),
                    (float(self._ui.axis2X.text()), float(self._ui.axis2Y.text()), float(self._ui.axis2Z.text())),
                    float(self._ui.cylinderRadius.text()))
            elif self._shape == Shape.SPHERE.value:
                polyData = spherePolyData(
                    (float(self._ui.centerX.text()), float(self._ui.centerY.text()), float(self._ui.centerZ.text())),
                    float(self._ui.sphereRadius.text()))
        except ValueError:
            pass

        if polyData:
            self._actor = polyDataToActor(polyData)
            self._actor.GetProperty().SetRepresentationToSurface()
            self._actor.GetProperty().EdgeVisibilityOn()
            self._actor.GetProperty().SetLineWidth(1.0)
            self._actor.GetProperty().SetDiffuse(0.6)
            self._actor.GetProperty().SetEdgeColor(vtkNamedColors().GetColor3d('burlywood'))
            self._actor.GetProperty().SetLineWidth(2)
            self._renderingView.addActor(self._actor)
            self._renderingView.refresh()
        else:
            self._renderingView.refresh()
            QMessageBox.information(self, self.tr('Add Geometry Failed'), self.tr('Invalid coordinates'))
            return False

    def _validateHex(self):
        try:
            point1 = (float(self._ui.minX.text()), float(self._ui.minY.text()), float(self._ui.minZ.text()))
            point2 = (float(self._ui.maxX.text()), float(self._ui.maxY.text()), float(self._ui.maxZ.text()))
        except ValueError:
            return None

        if point1 is None or point2 is None:
            return None

        minX, minY, minZ = point1
        maxX, maxY, maxZ = point2
        if not (minX < maxX and minY < maxY and minZ < maxZ):
            return None

        return point1, point2
