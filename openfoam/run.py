#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import platform
import subprocess
import psutil
from pathlib import Path
import asyncio
import glob

import app

# Solver Directory Structure
#
# solvers/
#     mingw64/ : mingw64 library, only on Windows
#         bin/
#         lib/
#     openfoam/
#         bin/ : solvers reside here
#         lib/
#         lib/sys-openmpi
#         lib/dummy
#         etc/ : OpenFOAM system 'etc'
#         tlib/ : Third-Party Library, only for Linux and macOS

MPICMD = 'mpirun'

OPENFOAM = app.APP_PATH/'solvers'/'openfoam'

creationflags = 0
startupinfo = None

STDOUT_FILE_NAME = 'stdout.log'
STDERR_FILE_NAME = 'stderr.log'

if platform.system() == 'Windows':
    MPICMD = 'mpiexec'
    MINGW = app.APP_PATH/'solvers'/'mingw64'
    library = str(OPENFOAM/'lib') + os.pathsep \
              + str(OPENFOAM/'lib'/'msmpi') + os.pathsep \
              + str(MINGW/'bin') + os.pathsep \
              + str(MINGW/'lib')
    creationflags = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NO_WINDOW
            | subprocess.CREATE_NEW_PROCESS_GROUP
    )
    startupinfo = subprocess.STARTUPINFO(
        dwFlags=subprocess.STARTF_USESHOWWINDOW,
        wShowWindow=subprocess.SW_HIDE
    )
    ENV = os.environ.copy()
    ENV.update({
        'WM_PROJECT_DIR': str(OPENFOAM),
        'PATH': library + os.pathsep + os.environ['PATH']
    })
else:
    library = str(OPENFOAM/'lib') + os.pathsep \
              + str(OPENFOAM/'lib'/'sys-openmpi') + os.pathsep \
              + str(OPENFOAM/'lib'/'dummy') + os.pathsep \
              + str(OPENFOAM/'tlib')

    if platform.system() == 'Darwin':
        library = library + os.pathsep + str(OPENFOAM/'tlib'/'lib')

    if platform.system() == 'Darwin':
        LIBRARY_PATH_NAME = 'DYLD_LIBRARY_PATH'
    else:
        LIBRARY_PATH_NAME = 'LD_LIBRARY_PATH'

    if LIBRARY_PATH_NAME not in os.environ:
        os.environ[LIBRARY_PATH_NAME] = ''

    ENV = os.environ.copy()
    ENV.update({
        'WM_PROJECT_DIR': str(OPENFOAM),
        LIBRARY_PATH_NAME: library + os.pathsep + os.environ[LIBRARY_PATH_NAME]
    })

    # if platform.system() == 'Darwin':
    #     ENV['OPAL_PREFIX'] = tmpiPath
    #     ENV['OPAL_LIBDIR'] = str(Path(tmpiPath).joinpath('lib'))
    #     ENV.update({
    #         'PATH': str(Path(tmpiPath).joinpath('bin')) + os.pathsep + os.environ['PATH']
    #     })


def openSolverProcess(cmd, casePath, inParallel):
    stdout = open(casePath / STDOUT_FILE_NAME, 'w')
    stderr = open(casePath / STDERR_FILE_NAME, 'w')

    if inParallel:
        cmd.append('-parallel')

    p = subprocess.Popen(cmd,
                         env=ENV, cwd=casePath,
                         stdout=stdout, stderr=stderr,
                         creationflags=creationflags,
                         startupinfo=startupinfo)

    stdout.close()
    stderr.close()

    return p


def launchSolverOnWindow(solver: str, casePath: Path, np: int = 1) -> (int, float):
    args = [MPICMD, '-np', str(np), OPENFOAM/'bin'/solver]

    process = openSolverProcess(args, casePath, np > 1)

    ps = psutil.Process(pid=process.pid)
    return ps.pid, ps.create_time()


def launchSolverOnLinux(solver: str, casePath: Path, uuid, np: int = 1) -> (int, float):
    args = [OPENFOAM/'bin'/'baramd', '-project', uuid, '-cmdline', MPICMD, '-np', str(np), OPENFOAM/'bin'/solver]

    process = openSolverProcess(args, casePath, np > 1)
    process.wait()

    processes = [p for p in psutil.process_iter(['pid', 'cmdline', 'create_time']) if (p.info['cmdline'] is not None) and (uuid in p.info['cmdline'])]
    if processes:
        ps = max(processes, key=lambda p: p.create_time())
        return ps.pid, ps.create_time()

    return None


def launchSolver(solver: str, casePath: Path, uuid, np: int = 1) -> (int, float):
    """Launch solver

    Launch solver in case folder
    Solver runs by mpirun/mpiexec by default

    Solver standard output file
        casePath/stdout.log
    Solver standard error file
        casePath/stderr.log

    Args:
        solver: solver name
        casePath: case folder absolute path
        np: number of process

    Returns:
        pid: process id of mpirun/mpiexec
        create_time: process creation time
    """
    if not isinstance(casePath, Path) or not casePath.is_absolute():
        raise AssertionError

    if platform.system() == 'Windows':
        return launchSolverOnWindow(solver, casePath, np)
    else:
        return launchSolverOnLinux(solver, casePath, uuid, np)


async def runUtility(program: str, *args, cwd=None, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL):
    global creationflags
    global startupinfo

    if platform.system() == 'Windows':
        creationflags = subprocess.CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO(
            dwFlags=subprocess.STARTF_USESHOWWINDOW,
            wShowWindow=subprocess.SW_HIDE
        )

    proc = await asyncio.create_subprocess_exec(OPENFOAM/'bin'/program, *args,
                                                env=ENV, cwd=cwd,
                                                creationflags=creationflags,
                                                startupinfo=startupinfo,
                                                stdout=stdout,
                                                stderr=stderr)

    return proc


async def runParallelUtility(program: str, *args, np: int = 1, cwd=None, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL):
    global creationflags
    global startupinfo

    if platform.system() == 'Windows':
        creationflags = subprocess.CREATE_NO_WINDOW
        startupinfo = subprocess.STARTUPINFO(
            dwFlags=subprocess.STARTF_USESHOWWINDOW,
            wShowWindow=subprocess.SW_HIDE
        )

    if np > 1:
        args = list(args)
        args.append('-parallel')

    proc = await asyncio.create_subprocess_exec(MPICMD, '-np', str(np), OPENFOAM/'bin'/program, *args,
                                                env=ENV, cwd=cwd,
                                                creationflags=creationflags,
                                                startupinfo=startupinfo,
                                                stdout=stdout,
                                                stderr=stderr)

    return proc


def hasUtility(program: str):
    return (OPENFOAM / 'bin' / program).is_file()
