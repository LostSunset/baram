#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum
from pathlib import Path

import yaml
from filelock import FileLock

from libbaram.mpi import ParallelEnvironment, ParallelType

FORMAT_VERSION = 1


class LocalSettingKey(Enum):
    FORMAT_VERSION = 'format_version'
    PATH = 'case_full_path'
    PARALLEL_NP = 'parallel_np'
    PARALLEL_TYPE = 'parallel_type'
    PARALLEL_HOSTS = 'parallel_hosts'


class LocalSettings:
    def __init__(self, path):
        self._settingsFile = path / 'local.cfg'

        self._settings = {}
        self._lock = None

        self._load()

        self.set(LocalSettingKey.PATH, str(path.resolve()))

    @property
    def path(self):
        if path := self.get(LocalSettingKey.PATH):
            return Path(path)

        return None

    def parallelEnvironment(self):
        return ParallelEnvironment(
            self.get(LocalSettingKey.PARALLEL_NP, 1),
            ParallelType[self.get(LocalSettingKey.PARALLEL_TYPE, ParallelType.LOCAL_MACHINE.name)],
            self.get(LocalSettingKey.PARALLEL_HOSTS, '')
        )

    def setParallelEnvironment(self, environment):
        self.set(LocalSettingKey.PARALLEL_NP, environment.np()),
        self.set(LocalSettingKey.PARALLEL_TYPE, environment.type().name),
        self.set(LocalSettingKey.PARALLEL_HOSTS, environment.hosts())

    def acquireLock(self, timeout):
        self._lock = FileLock(self.path / 'case.lock')
        self._lock.acquire(timeout=timeout)

    def releaseLock(self):
        self._lock.release()

    def get(self, key, default=None):
        if self._settings and key.value in self._settings:
            return self._settings[key.value]

        return default

    def set(self, key, value):
        if self.get(key) != value:
            self._settings[key.value] = value
            self._save()

    def _load(self):
        if self._settingsFile.is_file():
            with open(self._settingsFile) as file:
                self._settings = yaml.load(file, Loader=yaml.FullLoader)
        # ToDo: For compatibility. Remove this code block after 20251231
        # Migration from previous name of "baram.cfg"
        # Begin
        elif (oldFile := self._settingsFile.parent / 'baram.cfg').is_file():
            with open(oldFile) as file:
                self._settings = yaml.load(file, Loader=yaml.FullLoader)
                self._save()
        # End

    def _save(self):
        self._settings[LocalSettingKey.FORMAT_VERSION.value] = FORMAT_VERSION

        with open(self._settingsFile, 'w') as file:
            yaml.dump(self._settings, file)
