#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from enum import Enum
from pathlib import Path

from PySide6.QtCore import QLocale, QRect

import yaml
from filelock import FileLock


FORMAT_VERSION = 1
RECENT_PROJECTS_NUMBER = 100


class SettingKey(Enum):
    FORMAT_VERSION = 'format_version'
    UI_SCALING = 'ui_scaling'
    LOCALE = 'default_language'
    RECENT_DIRECTORY = 'recent_directory'
    RECENT_CASES = 'recent_cases'
    RECENT_MESH_DIRECTORY = 'recent_mesh_directory'
    LAST_START_WINDOW_GEOMETRY = 'last_start_window_position'
    LAST_MAIN_WINDOW_GEOMETRY = 'last_main_window_position'
    PARAVIEW_INSTALLED_PATH = 'paraview_installed_path'


class AppSettings:
    _settingsPath = None
    _casesPath = None
    _settingsFile = None
    _applicationLockFile = None

    @classmethod
    def setup(cls, name):
        cls._settingsPath = Path.home() / f'.{name}'
        cls._casesPath = cls._settingsPath / 'cases'
        cls._settingsFile = cls._settingsPath / 'baram.cfg.yaml'
        cls._applicationLockFile = cls._settingsPath / 'baram.lock'

        cls._settingsPath.mkdir(exist_ok=True)
        cls._casesPath.mkdir(exist_ok=True)

    @classmethod
    def casesPath(cls):
        return cls._casesPath

    @classmethod
    def acquireLock(cls, timeout):
        lock = FileLock(cls._applicationLockFile)
        lock.acquire(timeout=timeout)
        return lock

    @classmethod
    def getRecentLocation(cls):
        return cls._get(SettingKey.RECENT_DIRECTORY, str(Path.home()))

    @classmethod
    def getRecentProjects(cls, count):
        projects = cls._get(SettingKey.RECENT_CASES, [])
        return projects[:count]

    @classmethod
    def updateRecents(cls, project, new):
        settings = cls._load()
        if new:
            settings[SettingKey.RECENT_DIRECTORY.value] = str(project.path.parent)

        recentCases\
            = settings[SettingKey.RECENT_CASES.value] if SettingKey.RECENT_CASES.value in settings else []
        if project.uuid in recentCases:
            recentCases.remove(project.uuid)
        recentCases.insert(0, project.uuid)
        settings[SettingKey.RECENT_CASES.value] = recentCases[:RECENT_PROJECTS_NUMBER]
        cls._save(settings)

    @classmethod
    def getRecentMeshDirectory(cls):
        return cls._get(SettingKey.RECENT_MESH_DIRECTORY, os.path.expanduser('~'))

    @classmethod
    def updateRecentMeshDirectory(cls, path):
        settings = cls._load()
        settings[SettingKey.RECENT_MESH_DIRECTORY.value] = path
        cls._save(settings)

    @classmethod
    def getLastStartWindowGeometry(cls) -> QRect:
        x, y, width, height = cls._get(SettingKey.LAST_START_WINDOW_GEOMETRY, [200, 100, 400, 300])
        return QRect(x, y, width, height)

    @classmethod
    def updateLastStartWindowGeometry(cls, geometry: QRect):
        settings = cls._load()
        settings[SettingKey.LAST_START_WINDOW_GEOMETRY.value] = [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
        cls._save(settings)

    @classmethod
    def getLastMainWindowGeometry(cls) -> QRect:
        x, y, width, height = cls._get(SettingKey.LAST_MAIN_WINDOW_GEOMETRY, [200, 100, 1280, 770])
        return QRect(x, y, width, height)

    @classmethod
    def updateLastMainWindowGeometry(cls, geometry: QRect):
        settings = cls._load()
        settings[SettingKey.LAST_MAIN_WINDOW_GEOMETRY.value] = [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
        cls._save(settings)

    @classmethod
    def getUiScaling(cls):
        return cls._get(SettingKey.UI_SCALING, '1.0')

    @classmethod
    def updateUiScaling(cls, scaling):
        settings = cls._load()
        settings[SettingKey.UI_SCALING.value] = scaling
        cls._save(settings)

    # Territory is not considered for now
    @classmethod
    def getLocale(cls) -> QLocale:
        return QLocale(QLocale.languageToCode(QLocale(cls.getLanguage()).language()))

    @classmethod
    def getLanguage(cls):
        return cls._get(SettingKey.LOCALE, 'en')

    @classmethod
    def setLanguage(cls, language):
        settings = cls._load()
        settings[SettingKey.LOCALE.value] = language
        cls._save(settings)

    @classmethod
    def getParaviewInstalledPath(cls):
        return cls._get(SettingKey.PARAVIEW_INSTALLED_PATH, '')

    @classmethod
    def updateParaviewInstalledPath(cls, path):
        settings = cls._load()
        settings[SettingKey.PARAVIEW_INSTALLED_PATH.value] = str(path)
        cls._save(settings)

    @classmethod
    def _load(cls):
        if cls._settingsFile.is_file():
            with open(cls._settingsFile) as file:
                return yaml.load(file, Loader=yaml.FullLoader)
        else:
            return {}

    @classmethod
    def _save(cls, settings):
        settings[SettingKey.FORMAT_VERSION.value] = FORMAT_VERSION

        with open(cls._settingsFile, 'w') as file:
            yaml.dump(settings, file)

    @classmethod
    def _get(cls, key, default=None):
        settings = cls._load()
        return settings[key.value] if key.value in settings else default

    @classmethod
    def removeProject(cls, num):
        project = AppSettings.getRecentProjects(RECENT_PROJECTS_NUMBER)

        settings = cls._load()
        recentCases \
            = settings[SettingKey.RECENT_CASES.value] if SettingKey.RECENT_CASES.value in settings else []
        if project[num] in recentCases:
            recentCases.remove(project[num])
        cls._save(settings)
