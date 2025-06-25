import bpy
from ..keymap.keymap_manager import KeymapDefinition, keymap_registry, keymap_config
from ..utils.logging import get_logger
from .dopesheet_helper import get_visible_objects

log = get_logger(__name__)

class GRAPH_OT_monkey_vertically_enhanced(bpy.types.Operator):
    """Enhanced vertical keyframe movement with dynamic keymap support"""
    bl_idname = "graph.monkey_vertically_enhanced"
    bl_label = "Move Channel Selection Vertically (Enhanced)"
    bl_options = {"UNDO"}

    direction: bpy.props.EnumProperty(
        name="Direction",
        items=[("upward", "Upward", ""), ("downward", "Downward", "")],
        default="downward",
    )
    extend: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.area.type == "GRAPH_EDITOR"

    def execute(self, context):
        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        if not visible_objects:
            self.report(
                {"ERROR"}, "There is no object that is displayed and has an action."
            )
            return {"CANCELLED"}

        log.debug("Enhanced Move Channel Selection Vertically: EXECUTE")
        # ここに既存の処理を実装
        self.report({"INFO"}, f"Moved channels {self.direction} (extend: {self.extend})")
        return {"FINISHED"}

class GRAPH_OT_monkey_horizontally_enhanced(bpy.types.Operator):
    """Enhanced horizontal keyframe movement with dynamic keymap support"""
    bl_idname = "graph.monkey_horizontally_enhanced"
    bl_label = "Move Keyframe Selection Horizontally (Enhanced)"
    bl_options = {"UNDO"}

    direction: bpy.props.EnumProperty(
        name="Direction",
        items=[("forward", "Forward", ""), ("backward", "Backward", "")],
        default="forward",
    )
    extend: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.area.type == "GRAPH_EDITOR"

    def execute(self, context):
        dopesheet = context.space_data.dopesheet
        visible_objects = get_visible_objects(dopesheet)
        if not visible_objects:
            self.report(
                {"ERROR"}, "There is no object that is displayed and has an action."
            )
            return {"CANCELLED"}

        log.debug("Enhanced Move Keyframe Selection Horizontally: EXECUTE")
        # ここに既存の処理を実装
        self.report({"INFO"}, f"Moved keyframes {self.direction} (extend: {self.extend})")
        return {"FINISHED"}

def get_keymap_definitions():
    """このモジュールのキーマップ定義を取得"""
    config = keymap_config
    
    keymaps = [
        # 垂直移動
        KeymapDefinition(
            operator_id="graph.monkey_vertically_enhanced",
            key=config.get_key_for_action("vertical_movement", "upward"),
            alt=True,
            properties={"direction": "upward", "extend": False},
            description="Move channels upward"
        ),
        KeymapDefinition(
            operator_id="graph.monkey_vertically_enhanced",
            key=config.get_key_for_action("vertical_movement", "upward"),
            alt=True,
            shift=True,
            properties={"direction": "upward", "extend": True},
            description="Move channels upward (extend)"
        ),
        KeymapDefinition(
            operator_id="graph.monkey_vertically_enhanced",
            key=config.get_key_for_action("vertical_movement", "downward"),
            alt=True,
            properties={"direction": "downward", "extend": False},
            description="Move channels downward"
        ),
        KeymapDefinition(
            operator_id="graph.monkey_vertically_enhanced",
            key=config.get_key_for_action("vertical_movement", "downward"),
            alt=True,
            shift=True,
            properties={"direction": "downward", "extend": True},
            description="Move channels downward (extend)"
        ),
        
        # 水平移動
        KeymapDefinition(
            operator_id="graph.monkey_horizontally_enhanced",
            key=config.get_key_for_action("horizontal_movement", "forward"),
            alt=True,
            properties={"direction": "forward", "extend": False},
            description="Move keyframes forward"
        ),
        KeymapDefinition(
            operator_id="graph.monkey_horizontally_enhanced",
            key=config.get_key_for_action("horizontal_movement", "forward"),
            alt=True,
            shift=True,
            properties={"direction": "forward", "extend": True},
            description="Move keyframes forward (extend)"
        ),
        KeymapDefinition(
            operator_id="graph.monkey_horizontally_enhanced",
            key=config.get_key_for_action("horizontal_movement", "backward"),
            alt=True,
            properties={"direction": "backward", "extend": False},
            description="Move keyframes backward"
        ),
        KeymapDefinition(
            operator_id="graph.monkey_horizontally_enhanced",
            key=config.get_key_for_action("horizontal_movement", "backward"),
            alt=True,
            shift=True,
            properties={"direction": "backward", "extend": True},
            description="Move keyframes backward (extend)"
        ),
    ]
    
    return keymaps

def register_keymaps():
    """このモジュールのキーマップを登録"""
    keymaps = get_keymap_definitions()
    keymap_registry.register_keymap_group("keyframe_movement", keymaps)

def unregister_keymaps():
    """このモジュールのキーマップ登録を解除"""
    # キーマップレジストリから削除
    pass

# オペレータークラスリスト（登録用）
classes = [
    GRAPH_OT_monkey_vertically_enhanced,
    GRAPH_OT_monkey_horizontally_enhanced,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()

def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls) 