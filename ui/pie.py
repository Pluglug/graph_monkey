# pyright: reportInvalidTypeForm=false
# pyright: reportArgumentType=false
import bpy
from bpy.types import Menu, PropertyGroup, Scene

from ..utils.config_props import BlenderConfigProperty
from ..utils.logging import get_logger
from ..utils.ui_utils import ic

log = get_logger(__name__)


def validate_graph_editor_context():
    context = bpy.context
    if not context.space_data:
        raise ValueError("有効なスペースデータがありません")
    if context.space_data.type != "GRAPH_EDITOR":
        raise ValueError("グラフエディターではありません")
    return context.space_data


def is_pivot_point_center():
    space = validate_graph_editor_context()
    return space.pivot_point == "BOUNDING_BOX_CENTER"


def set_pivot_point_center(_value: bool):
    space = validate_graph_editor_context()
    space.pivot_point = "BOUNDING_BOX_CENTER"


def is_pivot_point_cursor():
    space = validate_graph_editor_context()
    return space.pivot_point == "CURSOR"


def set_pivot_point_cursor(_value: bool):
    space = validate_graph_editor_context()
    space.pivot_point = "CURSOR"


def is_pivot_point_individual_origins():
    space = validate_graph_editor_context()
    return space.pivot_point == "INDIVIDUAL_ORIGINS"


def set_pivot_point_individual_origins(_value: bool):
    space = validate_graph_editor_context()
    space.pivot_point = "INDIVIDUAL_ORIGINS"


def is_proportional_fcurve():
    context = bpy.context
    return context.scene.tool_settings.use_proportional_fcurve


def set_proportional_fcurve(_value: bool):
    context = bpy.context
    context.scene.tool_settings.use_proportional_fcurve = _value


CENTER_PIVOT_CONFIG = BlenderConfigProperty(
    name="センターピボット",
    description="センターピボットを設定",
    get_func=is_pivot_point_center,
    set_func=set_pivot_point_center,
    cache_enabled=True,
    async_update=False,
)

CURSOR_PIVOT_CONFIG = BlenderConfigProperty(
    name="カーソルピボット",
    description="カーソルピボットを設定",
    get_func=is_pivot_point_cursor,
    set_func=set_pivot_point_cursor,
    cache_enabled=True,
    async_update=False,
)

INDIVIDUAL_ORIGINS_PIVOT_CONFIG = BlenderConfigProperty(
    name="個別オリジンピボット",
    description="個別オリジンピボットを設定",
    get_func=is_pivot_point_individual_origins,
    set_func=set_pivot_point_individual_origins,
    cache_enabled=True,
    async_update=False,
)

PROPORTIONAL_FCURVE_CONFIG = BlenderConfigProperty(
    name="比例フィードバック",
    description="比例フィードバックを設定",
    get_func=is_proportional_fcurve,
    set_func=set_proportional_fcurve,
    cache_enabled=True,
    async_update=False,
)


class GraphEditorConfigSettings(PropertyGroup):
    center_pivot: CENTER_PIVOT_CONFIG.create_property()
    cursor_pivot: CURSOR_PIVOT_CONFIG.create_property()
    individual_origins_pivot: INDIVIDUAL_ORIGINS_PIVOT_CONFIG.create_property()
    proportional_fcurve: PROPORTIONAL_FCURVE_CONFIG.create_property()


class MONKEY_MT_GraphEditorConfigPie(Menu):
    bl_idname = "MONKEY_MT_graph_editor_config_pie"
    bl_label = "Graph Editor Config"

    @classmethod
    def poll(cls, context):
        return context.space_data and context.space_data.type == "GRAPH_EDITOR"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        settings = getattr(context.scene, "monkey_graph_editor_config", None)
        if not settings:
            pie.label(text="設定が利用できません")
            return

        pie.prop(settings, "center_pivot", icon=ic("PIVOT_BOUNDBOX"))
        pie.prop(settings, "cursor_pivot", icon=ic("PIVOT_CURSOR"))
        p_icon = "PROP_ON" if is_proportional_fcurve() else "PROP_OFF"
        pie.prop(settings, "proportional_fcurve", icon=ic(p_icon))
        pie.prop(settings, "individual_origins_pivot", icon=ic("PIVOT_INDIVIDUAL"))

        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()
        pie.separator()

        col = pie.column()
        gap = col.column()
        gap.separator()
        gap.scale_y = 10

        item_col = col.column()
        item_col.scale_y = 1.5
        item_row = item_col.row(align=True)
        item_row.scale_x = 1.5
        tool_settings = context.scene.tool_settings
        item_row.prop(tool_settings, "proportional_edit_falloff", expand=True, text="")


from ..keymap_manager import keymap_registry, KeymapDefinition

keymap_registry.register_keymap_group(
    group_name="Graph Pie",
    keymaps=[
        KeymapDefinition(
            operator_id="wm.call_menu_pie",
            key="C",
            value="PRESS",
            shift=1,
            properties={"name": "MONKEY_MT_graph_editor_config_pie"},
            name="Graph Editor",
            space_type="GRAPH_EDITOR",
            region_type="WINDOW",
        ),
    ],
)


def register():
    Scene.monkey_graph_editor_config = bpy.props.PointerProperty(  # type: ignore
        type=GraphEditorConfigSettings
    )


def unregister():
    if hasattr(bpy.types.Scene, "monkey_graph_editor_config"):
        del bpy.types.Scene.monkey_graph_editor_config  # type: ignore
