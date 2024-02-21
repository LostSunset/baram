#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

import psutil
import asyncio
import os
import platform
import subprocess

from PySide6.QtCore import QObject, Signal


class ProcessError(Exception):
    def __init__(self, returncode):
        self._returncode = returncode

    @property
    def returncode(self):
        return self._returncode


def isRunning(pid, startTime):
    if pid and startTime:
        try:
            ps = psutil.Process(pid)
            if ps.create_time() == startTime:
                return True
        except psutil.NoSuchProcess:
            return False

    return False


async def runExternalScript(program: str, *args, cwd=None, useVenv=True, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL):
    ENV = os.environ.copy()
    if not useVenv:
        excluding = [os.path.join('venv', 'bin'), os.path.join('venv', 'Lib'), os.path.join('venv', 'Scripts')]
        ENV['PATH'] = os.pathsep.join([path for path in ENV['PATH'].split(os.pathsep) if not any([pattern in path for pattern in excluding])])

    creationflags = 0
    startupinfo = None

    if platform.system() == 'Windows':
        creationflags = subprocess.CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO(
            dwFlags=subprocess.STARTF_USESHOWWINDOW,
            wShowWindow=subprocess.SW_HIDE
        )

    proc = await asyncio.create_subprocess_exec(program, *args,
                                                env=ENV, cwd=cwd,
                                                creationflags=creationflags,
                                                startupinfo=startupinfo,
                                                stdout=stdout,
                                                stderr=stderr)
    return proc


def stopProcess(pid, startTime=None):
    try:
        ps = psutil.Process(pid)
        with ps.oneshot():
            if ps.is_running() and (ps.create_time() == startTime or startTime is None):
                ps.terminate()
    except psutil.NoSuchProcess:
        pass


class RunExternalScript(QObject):
    output = Signal(str)
    errorOutput = Signal(str)

    def __init__(self, program: str, *args, cwd: Path = None, useVenv=True):
        super().__init__()

        self._program = program
        self._args = args
        self._cwd = cwd
        self._useVenv = useVenv

        self._proc = None
        self._canceled = False

    async def start(self):
        ENV = os.environ.copy()
        if not self._useVenv:
            excluding = [os.path.join('venv', 'bin'), os.path.join('venv', 'Lib'), os.path.join('venv', 'Scripts')]
            ENV['PATH'] = os.pathsep.join([path for path in ENV['PATH'].split(os.pathsep) if not any([pattern in path for pattern in excluding])])

        creationflags = 0
        startupinfo = None

        if platform.system() == 'Windows':
            creationflags = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO(
                dwFlags=subprocess.STARTF_USESHOWWINDOW,
                wShowWindow=subprocess.SW_HIDE
            )

        self._proc = await asyncio.create_subprocess_exec(self._program, *self._args,
                                                          env=ENV, cwd=str(self._cwd),
                                                          creationflags=creationflags,
                                                          startupinfo=startupinfo,
                                                          stdout=asyncio.subprocess.PIPE,
                                                          stderr=asyncio.subprocess.PIPE)

    def cancel(self):
        try:
            if self._proc is not None:
                self._proc.terminate()
                self._canceled = True

        except ProcessLookupError:
            return

    def isCanceled(self):
        return self._canceled

    async def wait(self):
        self._canceled = False

        tasks = []

        stdout = self._proc.stdout
        outTask = asyncio.create_task(stdout.readline())
        tasks.append(outTask)

        stderr = self._proc.stderr
        errTask = asyncio.create_task(stderr.readline())
        tasks.append(errTask)

        while len(tasks) > 0:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

            tasks = list(pending)
            if outTask in done:
                self.output.emit(outTask.result().decode('UTF-8').rstrip())
                if not stdout.at_eof():
                    outTask = asyncio.create_task(stdout.readline())
                    tasks.append(outTask)

            if errTask in done:
                self.errorOutput.emit(errTask.result().decode('UTF-8').rstrip())
                if not stderr.at_eof():
                    errTask = asyncio.create_task(stderr.readline())
                    tasks.append(errTask)

            if len(done) < 1:
                await asyncio.sleep(1)

        returncode = await self._proc.wait()

        if returncode != 0:
            raise ProcessError(returncode)

        return returncode
