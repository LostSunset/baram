#!/usr/bin/env python
# -*- coding: utf-8 -*-

import shutil
from pathlib import Path

import qasync

from libbaram.openfoam.constants import Directory
from libbaram.process import ProcessError
from libbaram.run import RunParallelUtility
from libbaram.utils import rmtree
from resources import resource
from widgets.new_project_dialog import NewProjectDialog
from widgets.progress_dialog import ProgressDialog

from baramMesh.app import app
from baramMesh.openfoam.file_system import FileSystem
from baramMesh.openfoam.constant.region_properties import RegionProperties
from baramMesh.openfoam.redistribution_task import RedistributionTask
from baramMesh.openfoam.system.topo_set_dict import TopoSetDict
from baramMesh.view.step_page import StepPage


class ExportPage(StepPage):
    OUTPUT_TIME = 4

    def __init__(self, ui):
        super().__init__(ui, ui.exportPage)

        self._dialog = None
        # self._fileDialog = QFileDialog(self._widget, Qt.WindowType.Widget)
        # self._fileDialog.setWindowFlags(self._fileDialog.windowFlags() & ~Qt.Dialog)
        # self._fileDialog.setFileMode(QFileDialog.FileMode.Directory)
        # self._fileDialog.setViewMode(QFileDialog.ViewMode.List)
        # self._widget.layout().addWidget(self._fileDialog)

        self._connectSignalsSlots()

    def isNextStepAvailable(self):
        return False

    def _connectSignalsSlots(self):
        self._ui.export_.clicked.connect(self._openFileDialog)

    @qasync.asyncSlot()
    async def _openFileDialog(self):
        self._dialog = NewProjectDialog(self._widget, self.tr('Export Baram Project'))
        self._dialog.accepted.connect(self._export)
        self._dialog.rejected.connect(self._ui.menubar.repaint)
        self._dialog.open()
        #
        # self._dialog = QFileDialog(self._widget, self.tr('Select Folder'))
        # self._dialog.setFileMode(QFileDialog.FileMode.Directory)
        # self._dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        # self._dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        # self._dialog.fileSelected.connect(self._export)
        # self._dialog.rejected.connect(self._ui.menubar.repaint)
        # self._dialog.open()

    @qasync.asyncSlot()
    async def _export(self):
        path = Path(self._dialog.projectLocation())

        progressDialog = ProgressDialog(self._widget, self.tr('Mesh Exporting'))
        progressDialog.setLabelText(self.tr('Preparing'))
        progressDialog.open()

        try:
            self.lock()

            self.clearResult()

            console = app.consoleView
            console.clear()

            fileSystem = app.fileSystem
            parallel = app.project.parallelEnvironment()

            if app.db.elementCount('region') > 1:
                progressDialog.setLabelText(self.tr('Splitting Mesh Regions'))

                cm = RunParallelUtility('splitMeshRegions', '-cellZonesOnly', cwd=fileSystem.caseRoot(), parallel=parallel)
                cm.output.connect(console.append)
                cm.errorOutput.connect(console.appendError)
                await cm.start()
                rc = await cm.wait()
                if rc != 0:
                    raise ProcessError(rc)
            if not fileSystem.timePathExists(self.OUTPUT_TIME, parallel.isParallelOn()):
                progressDialog.setLabelText(self.tr('Copying Files'))

                if parallel.isParallelOn():
                    for n in range(parallel.np()):
                        if not await fileSystem.copyTimeDirectory(self.OUTPUT_TIME - 1, self.OUTPUT_TIME, n):
                            await fileSystem.copyTimeDirectory(self.OUTPUT_TIME - 2, self.OUTPUT_TIME, n)
                elif not await fileSystem.copyTimeDirectory(self.OUTPUT_TIME - 1, self.OUTPUT_TIME):
                    await fileSystem.copyTimeDirectory(self.OUTPUT_TIME - 2, self.OUTPUT_TIME)

            topoSetDict = TopoSetDict().build(TopoSetDict.Mode.CREATE_CELL_ZONES)
            regions = app.db.getElements('region')
            if topoSetDict.isBuilt():
                progressDialog.setLabelText(self.tr('Processing Cell Zones'))
                if len(regions) == 1:
                    topoSetDict.write()

                    cm = RunParallelUtility('topoSet', cwd=fileSystem.caseRoot(), parallel=parallel)
                    cm.output.connect(console.append)
                    cm.errorOutput.connect(console.appendError)
                    await cm.start()
                    rc = await cm.wait()
                    if rc != 0:
                        raise ProcessError(rc)

                else:
                    for region in regions.values():
                        rname = region.value('name')
                        topoSetDict.setRegion(rname).write()

                        cm = RunParallelUtility('topoSet', '-region', rname, cwd=fileSystem.caseRoot(), parallel=parallel)
                        cm.output.connect(console.append)
                        cm.errorOutput.connect(console.appendError)
                        await cm.start()
                        rc = await cm.wait()
                        if rc != 0:
                            raise ProcessError(rc)
            path.mkdir(parents=True, exist_ok=True)
            baramSystem = FileSystem(path)
            baramSystem.createCase(resource.file('openfoam/case'))

            if len(regions) > 1:
                RegionProperties(baramSystem.caseRoot()).build().write()

            progressDialog.setLabelText(self.tr('Exporting Files'))

            if parallel.isParallelOn():
                for n in range(parallel.np()):
                    p = baramSystem.processorPath(n, False)
                    p.mkdir()
                    shutil.move(fileSystem.timePath(self.OUTPUT_TIME, n), p / Directory.CONSTANT_DIRECTORY_NAME)

                redistributionTask = RedistributionTask(baramSystem)
                redistributionTask.progress.connect(progressDialog.setLabelText)

                await redistributionTask.reconstruct()

            else:
                if len(regions) > 1:
                    for region in regions.values():
                        shutil.move(self._outputPath() / region.value('name'), baramSystem.constantPath())
                else:
                    shutil.move(self._outputPath() / Directory.POLY_MESH_DIRECTORY_NAME, baramSystem.polyMeshPath())

                rmtree(self._outputPath())

            progressDialog.finish(self.tr('Export completed'))

        except ProcessError as e:
            self.clearResult()
            progressDialog.finish(self.tr('Export failed. [') + str(e.returncode) + ']')
        finally:
            self.unlock()
