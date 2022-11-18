
# WARNING: THIS FILE IS AUTO-GENERATED. DO NOT MODIFY.

# This file was generated from ShapeTypeExtended.idl
# using RTI Code Generator (rtiddsgen) version 4.0.0.
# The rtiddsgen tool is part of the RTI Connext DDS distribution.
# For more information, type 'rtiddsgen -help' at a command shell
# or consult the Code Generator User's Manual.

from dataclasses import field
from typing import Union, Sequence, Optional
import rti.idl as idl
from enum import IntEnum


@idl.struct(
    member_annotations = {
        'color': [idl.key, idl.bound(128)],
    }
)
class ShapeType:
    color: str = ""
    x: idl.int32 = 0
    y: idl.int32 = 0
    shapesize: idl.int32 = 0

@idl.enum
class ShapeFillKind(IntEnum):
    SOLID_FILL = 0
    TRANSPARENT_FILL = 1
    HORIZONTAL_HATCH_FILL = 2
    VERTICAL_HATCH_FILL = 3

@idl.struct
class ShapeTypeExtended(ShapeType):
    fillKind: ShapeFillKind = ShapeFillKind.SOLID_FILL
    angle: idl.float32 = 0.0
