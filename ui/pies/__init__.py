# pyright: reportInvalidTypeForm=false
# pyright: reportArgumentType=false
import bpy
from bpy.types import PropertyGroup, Scene

from .graph_transform import (
    CENTER_PIVOT_CONFIG,
    CURSOR_PIVOT_CONFIG,
    INDIVIDUAL_ORIGINS_PIVOT_CONFIG,
    PROPORTIONAL_FCURVE_CONFIG,
)


class GraphEditorConfigSettings(PropertyGroup):
    center_pivot: CENTER_PIVOT_CONFIG.create_property()
    cursor_pivot: CURSOR_PIVOT_CONFIG.create_property()
    individual_origins_pivot: INDIVIDUAL_ORIGINS_PIVOT_CONFIG.create_property()
    proportional_fcurve: PROPORTIONAL_FCURVE_CONFIG.create_property()


def register():
    Scene.monkey_graph_editor_config = bpy.props.PointerProperty(  # type: ignore
        type=GraphEditorConfigSettings
    )


def unregister():
    if hasattr(bpy.types.Scene, "monkey_graph_editor_config"):
        del bpy.types.Scene.monkey_graph_editor_config  # type: ignore
