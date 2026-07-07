from __future__ import annotations

import enum


class StructureType(str, enum.Enum):
    ELEVATED = "elevated"
    UNDERGROUND = "underground"
    AT_GRADE = "at-grade"


class Direction(str, enum.Enum):
    UP = "up"
    DOWN = "down"


class LineCode(str, enum.Enum):
    RD = "RD"
    YL = "YL"
    BL = "BL"
    BR = "BR"
    GR = "GR"
    GB = "GB"
    VL = "VL"
    PK = "PK"
    MG = "MG"
    GY = "GY"
    OR = "OR"
    RM = "RM"


class CoordinateConfidence(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
