#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from threading import Lock
from typing import Optional

from PySide6.QtCore import QObject, Signal
from vtkmodules.vtkIOParallel import vtkPOpenFOAMReader
from vtkmodules.vtkCommonCore import vtkCommand

from baramFlow.openfoam.file_system import FileSystem

from libbaram.vtk_threads import vtk_run_in_thread

logger = logging.getLogger(__name__)


_mutex = Lock()


class OpenFOAMReader(QObject):
    _vtkReaderProgress = Signal(str)

    def __new__(cls, *args, **kwargs):
        with _mutex:
            if not hasattr(cls, '_instance'):
                cls._instance = super(OpenFOAMReader, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def __init__(self):
        with _mutex:
            if hasattr(self, '_initialized'):
                return
            else:
                self._initialized = True

        super().__init__()

        self._acquired = False

        self._reader: Optional[vtkPOpenFOAMReader] = None

    async def __aenter__(self):
        _mutex.acquire()

        self._acquired = True

        if self._reader is None:
            await self._setupReader()

        return self

    async def __aexit__(self, eType, eValue, eTraceback):
        _mutex.release()

        self._acquired = False

        logger.debug('exit without error')
        return None

    def getOutput(self):
        if not self._acquired:
            raise AssertionError

        return self._reader.GetOutput()

    async def _setupReader(self):
        if not self._acquired:
            raise AssertionError

        caseRoot = FileSystem.caseRoot()
        if caseRoot is None:
            return

        print(f'root {caseRoot}')
        self._reader = vtkPOpenFOAMReader()

        self._reader.EnableAllCellArrays()
        self._reader.EnableAllPointArrays()
        self._reader.EnableAllPatchArrays()
        self._reader.EnableAllLagrangianArrays()
        self._reader.CreateCellToPointOn()
        self._reader.SkipZeroTimeOff()
        self._reader.CacheMeshOn()
        self._reader.ReadZonesOn()

        self._reader.AddObserver(vtkCommand.ProgressEvent, self._readerProgressEvent)

        if len(list(caseRoot.glob('processor0'))) > 0:
            self._reader.SetCaseType(vtkPOpenFOAMReader.DECOMPOSED_CASE)
        else:
            self._reader.SetCaseType(vtkPOpenFOAMReader.RECONSTRUCTED_CASE)

        self._reader.SetFileName(str(FileSystem.foamFilePath()))

        await vtk_run_in_thread(self._reader.Update)

        for i in range(self._reader.GetNumberOfCellArrays()):
            name = self._reader.GetCellArrayName(i)
            self._reader.SetCellArrayStatus(name, 1)

        for i in range(self._reader.GetNumberOfPointArrays()):
            name = self._reader.GetPointArrayName(i)
            self._reader.SetPointArrayStatus(name, 1)

        for i in range(self._reader.GetNumberOfPatchArrays()):
            name = self._reader.GetPatchArrayName(i)
            self._reader.SetPatchArrayStatus(name, 1)

        await vtk_run_in_thread(self._reader.Update)

    def _readerProgressEvent(self, caller: vtkPOpenFOAMReader, ev):
        self._vtkReaderProgress.emit(self.tr('Loading Mesh : ') + f'{int(float(caller.GetProgress()) * 100)}%')

    def setTimeValue(self, value: float):
        if not self._acquired:
            raise AssertionError

        time = self._reader.GetTimeValue()
        print(f'read {time} set {value}')
        if time == value:
            return

        self._reader.SetTimeValue(value)
        self._reader.Modified()

    def getTimeValue(self):
        if not self._acquired:
            raise AssertionError

        return self._reader.GetTimeValue()

    async def Update(self):
        await vtk_run_in_thread(self._reader.Update)

    def refresh(self):
        if not self._acquired:
            raise AssertionError

        self._reader.SetRefresh()
        self._reader.UpdateInformation()

        self._reader.GetTimeValues()
