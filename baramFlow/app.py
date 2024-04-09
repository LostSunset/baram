#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, QTranslator, QCoreApplication, QLocale
from PySide6.QtWidgets import QApplication

from resources import resource
from baramFlow.coredb.app_settings import AppSettings
from baramFlow.coredb.project import ProjectOpenType


class App(QObject):
    projectCreated = Signal(Path, ProjectOpenType)
    meshUpdated = Signal()
    restarted = Signal()

    def __init__(self):
        super().__init__()

        self._window = None
        self._vtkMesh = None
        self._cellZoneActors = None
        self._internalMeshActors = None
        self._translator = None

        self._properties = None
        self._plug = None

        self._qApplication: Optional[QApplication] = None

    def setupApplication(self, properties):
        self._properties = properties
        AppSettings.setup(properties.name)

    @property
    def properties(self):
        return self._properties

    @property
    def window(self):
        return self._window

    @property
    def renderingView(self):
        return self._window.renderingView()

    @property
    def plug(self):
        return self._plug

    def setPlug(self, plug):
        self._plug = plug

    @property
    def qApplication(self):
        return self._qApplication

    @qApplication.setter
    def qApplication(self, application):
        self._qApplication = application

    def vtkMesh(self):
        return self._vtkMesh

    def cellZoneActor(self, czid):
        return self._cellZoneActors[czid].face

    def internalMeshActor(self, rname):
        return self._internalMeshActors[rname]

    def openMainWindow(self):
        self._window = self._plug.createMainWindow()
        self._window.load()
        self._window.show()

    def updateVtk(self, mesh, cellZoneActors, internalMeshActors):
        if self._vtkMesh:
            self._vtkMesh.deactivate()

        self._vtkMesh = mesh
        self._cellZoneActors = cellZoneActors
        self._internalMeshActors = internalMeshActors
        self.showMesh()

    def updateMesh(self):
        self._window.meshUpdated()

    def showMesh(self):
        if self._vtkMesh:
            self._vtkMesh.activate()

    def hideMesh(self):
        if self._vtkMesh:
            self._vtkMesh.deactivate()

    def quit(self):
        self._window = None
        QApplication.quit()

    def restart(self):
        self.restarted.emit()

    def setLanguage(self, language):
        QCoreApplication.removeTranslator(self._translator)
        self._translator = QTranslator()
        self._translator.load(QLocale(QLocale.languageToCode(QLocale(language).language())),
                              'baram', '_', str(resource.file('locale')))
        QCoreApplication.installTranslator(self._translator)


app = App()
