from dataclasses import dataclass, field
from typing import Dict, List, Literal

import bpy
from rna_keymap_ui import draw_kmi

from ..utils.logging import get_logger

log = get_logger(__name__)

# スペースタイプの型定義
SpaceType = Literal[
    "EMPTY",
    "VIEW_3D",
    "IMAGE_EDITOR",
    "NODE_EDITOR",
    "SEQUENCE_EDITOR",
    "CLIP_EDITOR",
    "MOTION_TRACKING",
    "ANIMATION",
    "DOPESHEET_EDITOR",
    "GRAPH_EDITOR",
    "NLA_EDITOR",
    "SCRIPTING",
    "TEXT_EDITOR",
    "CONSOLE",
    "INFO",
    "TOPBAR",
    "STATUSBAR",
    "OUTLINER",
    "PROPERTIES",
    "FILE_BROWSER",
    "SPREADSHEET",
    "PREFERENCES",
]

# リージョンタイプの型定義
RegionType = Literal[
    "WINDOW",
    "HEADER",
    "CHANNELS",
    "TEMPORARY",
    "UI",
    "TOOLS",
    "TOOL_PROPS",
    "ASSET_SHELF",
    "PREVIEW",
    "HUD",
    "NAVIGATION_BAR",
    "EXECUTE",
    "FOOTER",
    "TOOL_HEADER",
    "XR",
]

SPACE_TYPE_ITEMS = [
    ("EMPTY", "Empty", "Empty"),
    ("VIEW_3D", "3D Viewport", "3D Viewport"),
    ("IMAGE_EDITOR", "Image Editor", "Image Editor"),
    ("NODE_EDITOR", "Node Editor", "Node Editor"),
    ("SEQUENCE_EDITOR", "Video Sequencer", "Video Sequencer"),
    ("CLIP_EDITOR", "Movie Clip Editor", "Movie Clip Editor"),
    ("MOTION_TRACKING", "Motion Tracking", "Motion Tracking"),
    ("ANIMATION", "Animation", "Animation"),
    ("DOPESHEET_EDITOR", "Dope Sheet", "Dope Sheet"),
    ("GRAPH_EDITOR", "Graph Editor", "Graph Editor"),
    ("NLA_EDITOR", "Nonlinear Animation", "Nonlinear Animation"),
    ("SCRIPTING", "Scripting", "Scripting"),
    ("TEXT_EDITOR", "Text Editor", "Text Editor"),
    ("CONSOLE", "Console", "Console"),
    ("INFO", "Info", "Info"),
    ("TOPBAR", "Top Bar", "Top Bar"),
    ("STATUSBAR", "Status Bar", "Status Bar"),
    ("OUTLINER", "Outliner", "Outliner"),
    ("PROPERTIES", "Properties", "Properties"),
    ("FILE_BROWSER", "File Browser", "File Browser"),
    ("SPREADSHEET", "Spreadsheet", "Spreadsheet"),
    ("PREFERENCES", "Preferences", "Preferences"),
]

REGION_TYPE_ITEMS = [
    ("WINDOW", "Window", "Window"),
    ("HEADER", "Header", "Header"),
    ("CHANNELS", "Channels", "Channels"),
    ("TEMPORARY", "Temporary", "Temporary"),
    ("UI", "Sidebar", "Sidebar"),
    ("TOOLS", "Tools", "Tools"),
    ("TOOL_PROPS", "Tool Properties", "Tool Properties"),
    ("ASSET_SHELF", "Asset Shelf", "Asset Shelf"),
    ("PREVIEW", "Preview", "Preview"),
    ("HUD", "Floating Region", "Floating Region"),
    ("NAVIGATION_BAR", "Navigation Bar", "Navigation Bar"),
    ("EXECUTE", "Execute Buttons", "Execute Buttons"),
    ("FOOTER", "Footer", "Footer"),
    ("TOOL_HEADER", "Tool Header", "Tool Header"),
    ("XR", "XR", "XR"),
]

EVENT_DIRECTION_ITEMS = [
    ("ANY", "Any", "Any"),
    ("NORTH", "North", "North"),
    ("NORTH_EAST", "North-East", "North-East"),
    ("EAST", "East", "East"),
    ("SOUTH_EAST", "South-East", "South-East"),
    ("SOUTH", "South", "South"),
    ("SOUTH_WEST", "South-West", "South-West"),
    ("WEST", "West", "West"),
    ("NORTH_WEST", "North-West", "North-West"),
]

EVENT_VALUE_ITEMS = [
    ("ANY", "Any", "Any"),
    ("PRESS", "Press", "Press"),
    ("RELEASE", "Release", "Release"),
    ("CLICK", "Click", "Click"),
    ("DOUBLE_CLICK", "Double Click", "Double Click"),
    ("CLICK_DRAG", "Click Drag", "Click Drag"),
    ("NOTHING", "Nothing", "Nothing"),
]


@dataclass
class KeymapDefinition:
    """キーマップ定義クラス"""

    operator_id: str
    key: str
    value: str = "PRESS"
    any: bool = False
    shift: int = 0
    ctrl: int = 0
    alt: int = 0
    oskey: int = 0
    key_modifier: str = "NONE"
    direction: str = "ANY"
    repeat: bool = False
    head: bool = False
    properties: Dict = field(default_factory=dict)
    description: str = ""
    name: str = "3D View"  # キーマップの識別名
    space_type: SpaceType = "VIEW_3D"  # スペースタイプ
    region_type: RegionType = "WINDOW"  # リージョンタイプ

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "operator_id": self.operator_id,
            "key": self.key,
            "value": self.value,
            "any": self.any,
            "shift": self.shift,
            "ctrl": self.ctrl,
            "alt": self.alt,
            "oskey": self.oskey,
            "key_modifier": self.key_modifier,
            "direction": self.direction,
            "repeat": self.repeat,
            "head": self.head,
            "properties": self.properties,
            "description": self.description,
            "name": self.name,
            "space_type": self.space_type,
            "region_type": self.region_type,
        }


class KeymapRegistry:
    """キーマップ登録管理クラス"""

    def __init__(self):
        self._keymaps: Dict[str, List[KeymapDefinition]] = {}
        self._registered_keymaps: List = []

    def register_keymap_group(self, group_name: str, keymaps: List[KeymapDefinition]):
        """キーマップグループを登録"""
        self._keymaps[group_name] = keymaps
        log.info(f"Registered keymap group: {group_name} with {len(keymaps)} keymaps")

    def get_all_keymaps(self) -> Dict[str, List[KeymapDefinition]]:
        """全てのキーマップを取得"""
        return self._keymaps.copy()

    def apply_keymaps(self):
        """Blenderにキーマップを適用"""
        self.unregister_keymaps()

        wm = bpy.context.window_manager
        if not wm or not wm.keyconfigs.addon:
            log.error("Window manager or keyconfig not available")
            return
        kc = wm.keyconfigs.addon

        for group_name, keymaps in self._keymaps.items():
            for keymap_def in keymaps:
                km = kc.keymaps.new(
                    name=keymap_def.name,
                    space_type=keymap_def.space_type,  # type: ignore
                )

                kmi = km.keymap_items.new(
                    keymap_def.operator_id,
                    type=keymap_def.key,  # type: ignore
                    value=keymap_def.value,  # type: ignore
                    any=keymap_def.any,
                    shift=keymap_def.shift,
                    ctrl=keymap_def.ctrl,
                    alt=keymap_def.alt,
                    oskey=keymap_def.oskey,
                    key_modifier=keymap_def.key_modifier,  # type: ignore
                    direction=keymap_def.direction,  # type: ignore
                    repeat=keymap_def.repeat,
                    head=keymap_def.head,
                )

                # プロパティを設定
                for prop_name, prop_value in keymap_def.properties.items():
                    setattr(kmi.properties, prop_name, prop_value)

                self._registered_keymaps.append(km)

        log.info(f"Applied {len(self._registered_keymaps)} keymaps")

    def unregister_keymaps(self):
        """キーマップを登録解除"""
        wm = bpy.context.window_manager
        if not wm or not wm.keyconfigs.addon:
            return
        for km in self._registered_keymaps:
            try:
                wm.keyconfigs.addon.keymaps.remove(km)
            except:
                pass  # 既に削除されている場合
        self._registered_keymaps.clear()

    def draw_keymap_settings(self, context, layout):
        """キーマップ設定UIを描画"""
        if not self._keymaps:
            layout.label(text="登録されたキーマップがありません")
            return

        wm = context.window_manager
        if not wm or not wm.keyconfigs.addon:
            layout.label(text="キーコンフィグが利用できません")
            return

        kc = wm.keyconfigs.addon

        # 統計情報を表示
        total_groups = len(self._keymaps)
        total_keymaps = sum(len(keymaps) for keymaps in self._keymaps.values())

        stats_box = layout.box()
        stats_box.label(
            text=f"登録済みグループ: {total_groups}, 総キーマップ数: {total_keymaps}",
            icon="INFO",
        )

        # グループごとにキーマップを表示
        for group_name, keymap_defs in self._keymaps.items():
            # グループ名で区切り
            box = layout.box()
            box.label(text=f"グループ: {group_name}", icon="KEYINGSET")

            # このグループのキーマップを取得
            group_keymaps = {}
            for km in kc.keymaps:
                if km.name in [kd.name for kd in keymap_defs]:
                    group_keymaps[km.name] = km

            # 各キーマップ定義に対してUIを描画
            for keymap_def in keymap_defs:
                km = group_keymaps.get(keymap_def.name)
                if not km:
                    # キーマップが見つからない場合
                    row = box.row()
                    row.label(
                        text=f"キーマップ '{keymap_def.name}' が見つかりません",
                        icon="ERROR",
                    )
                    continue

                # キーマップ名を表示
                keymap_box = box.box()
                keymap_box.label(text=f"キーマップ: {keymap_def.name}", icon="KEY")

                # このキーマップのキーマップアイテムを検索
                found_kmi = None
                for kmi in km.keymap_items:
                    if (
                        kmi.idname == keymap_def.operator_id
                        and kmi.type == keymap_def.key
                        and kmi.value == keymap_def.value
                    ):
                        found_kmi = kmi
                        break

                if found_kmi:
                    # キーマップアイテムが見つかった場合、draw_kmiで描画
                    draw_kmi([], kc, km, found_kmi, keymap_box, 0)

                    # 追加情報を表示
                    info_row = keymap_box.row()
                    info_row.label(
                        text=f"キー: {keymap_def.key}, 値: {keymap_def.value}"
                    )
                    if keymap_def.description:
                        desc_row = keymap_box.row()
                        desc_row.label(text=f"説明: {keymap_def.description}")
                else:
                    # キーマップアイテムが見つからない場合
                    row = keymap_box.row()
                    row.label(
                        text=f"オペレータ '{keymap_def.operator_id}' のキーマップアイテムが見つかりません",
                        icon="ERROR",
                    )

                    # 定義情報を表示
                    info_row = keymap_box.row()
                    info_row.label(
                        text=f"期待されるキー: {keymap_def.key}, 値: {keymap_def.value}"
                    )
                    if keymap_def.description:
                        desc_row = keymap_box.row()
                        desc_row.label(text=f"説明: {keymap_def.description}")


keymap_registry = KeymapRegistry()
