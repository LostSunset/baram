#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum


class TimeSteppingMethod(Enum):
    FIXED = "fixed"
    ADAPTIVE = "adaptive"


class DataWriteFormat(Enum):
    BINARY = "binary"
    ASCII = "ascii"


class MachineType(Enum):
    SHARED_MEMORY_ON_LOCAL_MACHINE = "true"
    DISTRIBUTED_MEMORY_ON_A_CLUSTER = "false"


class RunCalculationDB:
    RUN_CALCULATION_XPATH = './/runCalculation'
