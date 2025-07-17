"""
Blender KeyMap Helper - Python implementation
BlenderのC実装のKeyMap選択ロジックをPythonで再現

PME keymap_helper改善のための参考実装
"""

import bpy
from typing import List, Dict, Optional, Tuple
import json


class BlenderKeymapHelper:
    """
    BlenderのC実装のKeyMap選択ロジックをPythonで再現するヘルパークラス
    """

    def __init__(self):
        """KeyMap構造体とマッピングテーブルを初期化"""
        self.keymap_structure = {
            "space_types": {
                "VIEW_3D": {
                    "spaceid": 1,
                    "regions": {
                        "WINDOW": {
                            "keymaps": [
                                {
                                    "name": "Paint Face Mask (Weight, Vertex, Texture)",
                                    "poll": "face_mask_mode_poll",
                                    "priority": 1,
                                },
                                {
                                    "name": "Paint Vertex Selection (Weight, Vertex)",
                                    "poll": "vertex_selection_mode_poll",
                                    "priority": 2,
                                },
                                {
                                    "name": "Paint Curve",
                                    "poll": "paint_curve_poll",
                                    "priority": 3,
                                },
                                {
                                    "name": "Weight Paint",
                                    "poll": "weight_paint_mode_poll",
                                    "priority": 4,
                                },
                                {
                                    "name": "Vertex Paint",
                                    "poll": "vertex_paint_mode_poll",
                                    "priority": 5,
                                },
                                {
                                    "name": "Pose",
                                    "poll": "pose_mode_poll",
                                    "priority": 6,
                                },
                                {
                                    "name": "Object Mode",
                                    "poll": "object_mode_poll",
                                    "priority": 7,
                                },
                                {
                                    "name": "Curve",
                                    "poll": "curve_edit_poll",
                                    "priority": 8,
                                },
                                {
                                    "name": "Curves",
                                    "poll": "curves_edit_poll",
                                    "priority": 9,
                                },
                                {
                                    "name": "Image Paint",
                                    "poll": "image_paint_mode_poll",
                                    "priority": 10,
                                },
                                {
                                    "name": "Sculpt",
                                    "poll": "sculpt_mode_poll",
                                    "priority": 11,
                                },
                                {
                                    "name": "Mesh",
                                    "poll": "ED_operator_editmesh",
                                    "priority": 12,
                                },
                                {
                                    "name": "Armature",
                                    "poll": "armature_edit_poll",
                                    "priority": 13,
                                },
                                {
                                    "name": "Metaball",
                                    "poll": "metaball_edit_poll",
                                    "priority": 14,
                                },
                                {
                                    "name": "Lattice",
                                    "poll": "lattice_edit_poll",
                                    "priority": 15,
                                },
                                {
                                    "name": "Particle",
                                    "poll": "particle_edit_poll",
                                    "priority": 16,
                                },
                                {
                                    "name": "Point Cloud",
                                    "poll": "pointcloud_edit_poll",
                                    "priority": 17,
                                },
                                {
                                    "name": "Sculpt Curves",
                                    "poll": "sculpt_curves_poll",
                                    "priority": 18,
                                },
                                {
                                    "name": "Grease Pencil Selection",
                                    "poll": "grease_pencil_selection_poll",
                                    "priority": 19,
                                },
                                {
                                    "name": "Grease Pencil Edit Mode",
                                    "poll": "grease_pencil_edit_poll",
                                    "priority": 20,
                                },
                                {
                                    "name": "Grease Pencil Paint Mode",
                                    "poll": "grease_pencil_paint_poll",
                                    "priority": 21,
                                },
                                {
                                    "name": "Grease Pencil Sculpt Mode",
                                    "poll": "grease_pencil_sculpt_poll",
                                    "priority": 22,
                                },
                                {
                                    "name": "Grease Pencil Weight Paint",
                                    "poll": "grease_pencil_weight_poll",
                                    "priority": 23,
                                },
                                {
                                    "name": "Grease Pencil Vertex Paint",
                                    "poll": "grease_pencil_vertex_poll",
                                    "priority": 24,
                                },
                                {
                                    "name": "Font",
                                    "poll": "font_edit_poll",
                                    "priority": 27,
                                },
                                {
                                    "name": "Object Non-modal",
                                    "poll": None,
                                    "priority": 28,
                                },
                                {"name": "Frames", "poll": None, "priority": 29},
                                {
                                    "name": "3D View Generic",
                                    "poll": None,
                                    "priority": 30,
                                },
                                {"name": "3D View", "poll": None, "priority": 31},
                            ]
                        },
                        "HEADER": {
                            "keymaps": [
                                {"name": "3D View Generic", "poll": None, "priority": 1}
                            ]
                        },
                    },
                },
                "IMAGE": {
                    "spaceid": 6,
                    "regions": {
                        "WINDOW": {
                            "keymaps": [
                                {
                                    "name": "Mask Editing",
                                    "poll": "mask_mode_poll",
                                    "priority": 1,
                                },
                                {
                                    "name": "Curve",
                                    "poll": "curve_edit_poll",
                                    "priority": 2,
                                },
                                {
                                    "name": "Paint Curve",
                                    "poll": "paint_curve_poll",
                                    "priority": 3,
                                },
                                {
                                    "name": "Image Paint",
                                    "poll": "image_paint_mode_poll",
                                    "priority": 4,
                                },
                                {
                                    "name": "UV Editor",
                                    "poll": "uv_edit_poll",
                                    "priority": 5,
                                },
                                {"name": "Image Generic", "poll": None, "priority": 6},
                                {"name": "Image", "poll": None, "priority": 7},
                            ]
                        }
                    },
                },
                "OUTLINER": {
                    "spaceid": 3,
                    "regions": {
                        "WINDOW": {
                            "keymaps": [
                                {"name": "Outliner", "poll": None, "priority": 1}
                            ]
                        }
                    },
                },
                "PROPERTIES": {
                    "spaceid": 4,
                    "regions": {
                        "WINDOW": {
                            "keymaps": [
                                {"name": "Property Editor", "poll": None, "priority": 1}
                            ]
                        }
                    },
                },
                "NODE": {
                    "spaceid": 16,
                    "regions": {
                        "WINDOW": {
                            "keymaps": [
                                {"name": "Node Generic", "poll": None, "priority": 1},
                                {"name": "Node Editor", "poll": None, "priority": 2},
                            ]
                        }
                    },
                },
            },
            "mode_mappings": {
                "EDIT_MESH": "Mesh",
                "EDIT_CURVE": "Curve",
                "EDIT_SURFACE": "Curve",
                "EDIT_TEXT": "Font",
                "EDIT_ARMATURE": "Armature",
                "EDIT_METABALL": "Metaball",
                "EDIT_LATTICE": "Lattice",
                "EDIT_CURVES": "Curves",
                "EDIT_GREASE_PENCIL": "Grease Pencil Edit Mode",
                "EDIT_POINTCLOUD": "Point Cloud",
                "POSE": "Pose",
                "SCULPT": "Sculpt",
                "PAINT_WEIGHT": "Weight Paint",
                "PAINT_VERTEX": "Vertex Paint",
                "PAINT_TEXTURE": "Image Paint",
                "PARTICLE_EDIT": "Particle",
                "OBJECT": "Object Mode",
                "PAINT_GPENCIL": "Grease Pencil Paint Mode",
                "EDIT_GPENCIL": "Grease Pencil Edit Mode",
                "SCULPT_GPENCIL": "Grease Pencil Sculpt Mode",
                "WEIGHT_GPENCIL": "Grease Pencil Weight Paint",
                "VERTEX_GPENCIL": "Grease Pencil Vertex Paint",
                "SCULPT_CURVES": "Sculpt Curves",
            },
        }

    def get_space_type_from_area(self, area) -> str:
        """エリアオブジェクトからスペースタイプ名を取得"""
        space_type_map = {
            "VIEW_3D": "VIEW_3D",
            "IMAGE_EDITOR": "IMAGE",
            "OUTLINER": "OUTLINER",
            "PROPERTIES": "PROPERTIES",
            "NODE_EDITOR": "NODE",
            "DOPESHEET_EDITOR": "ACTION",
            "GRAPH_EDITOR": "GRAPH",
            "NLA_EDITOR": "NLA",
            "TEXT_EDITOR": "TEXT",
            "CONSOLE": "CONSOLE",
            "INFO": "INFO",
            "TOPBAR": "TOPBAR",
            "STATUSBAR": "STATUSBAR",
            "FILE_BROWSER": "FILE",
            "SEQUENCE_EDITOR": "SEQ",
            "CLIP_EDITOR": "CLIP",
            "PREFERENCES": "USERPREF",
            "SPREADSHEET": "SPREADSHEET",
        }
        return space_type_map.get(area.type, area.type)

    def get_region_type_name(self, region) -> str:
        """リージョンオブジェクトからリージョンタイプ名を取得"""
        region_type_map = {
            "WINDOW": "WINDOW",
            "HEADER": "HEADER",
            "CHANNELS": "CHANNELS",
            "TEMPORARY": "TEMPORARY",
            "UI": "UI",
            "TOOLS": "TOOLS",
            "TOOL_PROPS": "TOOL_PROPS",
            "PREVIEW": "PREVIEW",
            "HUD": "HUD",
            "NAVIGATION_BAR": "NAVIGATION_BAR",
            "EXECUTE": "EXECUTE",
            "FOOTER": "FOOTER",
            "TOOL_HEADER": "TOOL_HEADER",
            "XR": "XR",
            "ASSET_SHELF": "ASSET_SHELF",
            "ASSET_SHELF_HEADER": "ASSET_SHELF_HEADER",
        }
        return region_type_map.get(region.type, region.type)

    def get_current_mode(self, context) -> str:
        """現在のモードを取得（bpy.context.mode形式）"""
        if not context:
            return "OBJECT"

        mode = getattr(context, "mode", "OBJECT")
        return mode

    def simulate_poll_function(self, poll_name: str, context) -> bool:
        """Poll関数をシミュレートして、現在のコンテキストで有効かを判定"""
        if not poll_name:
            return True

        current_mode = self.get_current_mode(context)
        active_object = context.active_object

        # 主要なpoll関数のシミュレーション
        poll_logic = {
            "ED_operator_editmesh": lambda: current_mode == "EDIT_MESH",
            "curve_edit_poll": lambda: current_mode in ["EDIT_CURVE", "EDIT_SURFACE"],
            "armature_edit_poll": lambda: current_mode == "EDIT_ARMATURE",
            "pose_mode_poll": lambda: current_mode == "POSE",
            "sculpt_mode_poll": lambda: current_mode == "SCULPT",
            "weight_paint_mode_poll": lambda: current_mode == "PAINT_WEIGHT",
            "vertex_paint_mode_poll": lambda: current_mode == "PAINT_VERTEX",
            "image_paint_mode_poll": lambda: current_mode == "PAINT_TEXTURE",
            "object_mode_poll": lambda: current_mode == "OBJECT",
            "font_edit_poll": lambda: current_mode == "EDIT_TEXT",
            "metaball_edit_poll": lambda: current_mode == "EDIT_METABALL",
            "lattice_edit_poll": lambda: current_mode == "EDIT_LATTICE",
            "particle_edit_poll": lambda: current_mode == "PARTICLE_EDIT",
            "grease_pencil_edit_poll": lambda: current_mode == "EDIT_GPENCIL",
            "grease_pencil_paint_poll": lambda: current_mode == "PAINT_GPENCIL",
            "grease_pencil_sculpt_poll": lambda: current_mode == "SCULPT_GPENCIL",
            "grease_pencil_weight_poll": lambda: current_mode == "WEIGHT_GPENCIL",
            "grease_pencil_vertex_poll": lambda: current_mode == "VERTEX_GPENCIL",
            "curves_edit_poll": lambda: current_mode == "EDIT_CURVES",
            "sculpt_curves_poll": lambda: current_mode == "SCULPT_CURVES",
            "pointcloud_edit_poll": lambda: current_mode == "EDIT_POINTCLOUD",
            "uv_edit_poll": lambda: current_mode == "EDIT_MESH"
            and hasattr(context, "space_data")
            and context.space_data.type == "IMAGE_EDITOR",
            "face_mask_mode_poll": lambda: current_mode
            in ["PAINT_WEIGHT", "PAINT_VERTEX", "PAINT_TEXTURE"]
            and active_object
            and active_object.data.use_paint_mask,
            "vertex_selection_mode_poll": lambda: current_mode
            in ["PAINT_WEIGHT", "PAINT_VERTEX"]
            and active_object
            and active_object.data.use_paint_mask_vertex,
        }

        poll_func = poll_logic.get(poll_name)
        if poll_func:
            try:
                return poll_func()
            except:
                return False

        # 不明なpoll関数は常にFalseを返す
        return False

    def get_active_keymaps_for_context(self, context=None) -> List[Dict]:
        """
        現在のコンテキストでアクティブなKeyMapリストを取得

        Returns:
            List[Dict]: アクティブなKeyMapの情報
                [{"name": "Mesh", "priority": 12, "poll": "ED_operator_editmesh"}, ...]
        """
        if not context:
            context = bpy.context

        # 現在のarea、region、modeを取得
        area = context.area
        region = context.region

        if not area or not region:
            return []

        space_type = self.get_space_type_from_area(area)
        region_type = self.get_region_type_name(region)

        # 該当するスペースタイプの情報を取得
        space_info = self.keymap_structure["space_types"].get(space_type)
        if not space_info:
            return []

        # 該当するリージョンタイプの情報を取得
        region_info = space_info["regions"].get(region_type)
        if not region_info:
            return []

        # 優先度順にKeyMapをチェックして、アクティブなもののみを返す
        active_keymaps = []
        for keymap_info in region_info["keymaps"]:
            if self.simulate_poll_function(keymap_info["poll"], context):
                active_keymaps.append(keymap_info)

        return active_keymaps

    def get_primary_keymap_for_context(self, context=None) -> Optional[str]:
        """
        現在のコンテキストでの主要（最優先）KeyMap名を取得

        Returns:
            Optional[str]: 主要KeyMap名（例: "Mesh", "Object Mode", "3D View"）
        """
        active_keymaps = self.get_active_keymaps_for_context(context)
        if active_keymaps:
            # 最優先（priorityが最小）のKeyMapを返す
            return active_keymaps[0]["name"]
        return None

    def get_keymap_hierarchy_for_context(self, context=None) -> List[str]:
        """
        現在のコンテキストでのKeyMap階層を取得

        Returns:
            List[str]: 優先度順のKeyMap名リスト
        """
        active_keymaps = self.get_active_keymaps_for_context(context)
        return [km["name"] for km in active_keymaps]

    def guess_keymap_from_mode(self, mode: str) -> Optional[str]:
        """
        モード名からKeyMap名を推測

        Args:
            mode: bpy.context.mode形式のモード名

        Returns:
            Optional[str]: 推測されたKeyMap名
        """
        return self.keymap_structure["mode_mappings"].get(mode)

    def debug_current_context(self, context=None) -> Dict:
        """
        現在のコンテキストのデバッグ情報を取得

        Returns:
            Dict: コンテキスト情報
        """
        if not context:
            context = bpy.context

        area = context.area
        region = context.region
        mode = self.get_current_mode(context)

        debug_info = {
            "mode": mode,
            "area_type": area.type if area else None,
            "space_type": self.get_space_type_from_area(area) if area else None,
            "region_type": region.type if region else None,
            "region_type_name": self.get_region_type_name(region) if region else None,
            "active_keymaps": self.get_active_keymaps_for_context(context),
            "primary_keymap": self.get_primary_keymap_for_context(context),
            "keymap_hierarchy": self.get_keymap_hierarchy_for_context(context),
        }

        return debug_info


# 使用例
def example_usage():
    """使用例"""
    helper = BlenderKeymapHelper()

    # 現在のコンテキストでのアクティブKeyMapを取得
    active_keymaps = helper.get_active_keymaps_for_context()
    print("Active KeyMaps:", [km["name"] for km in active_keymaps])

    # 主要KeyMapを取得
    primary_keymap = helper.get_primary_keymap_for_context()
    print("Primary KeyMap:", primary_keymap)

    # KeyMap階層を取得
    hierarchy = helper.get_keymap_hierarchy_for_context()
    print("KeyMap Hierarchy:", hierarchy)

    # デバッグ情報を取得
    debug_info = helper.debug_current_context()
    print("Debug Info:", json.dumps(debug_info, indent=2))


if __name__ == "__main__":
    # Blender内で実行する場合
    if "bpy" in locals():
        example_usage()
