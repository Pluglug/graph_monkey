import bpy
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field

from ..utils.logging import get_logger

log = get_logger(__name__)

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
    context: str = "GRAPH_EDITOR"

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
            "context": self.context,
        }


class KeymapRegistry:
    """キーマップ登録管理クラス"""

    def __init__(self):
        self._keymaps: Dict[str, List[KeymapDefinition]] = {}
        self._registered_keymaps: List = []
        self._conflict_detector = KeymapConflictDetector()

    def register_keymap_group(self, group_name: str, keymaps: List[KeymapDefinition]):
        """キーマップグループを登録"""
        self._keymaps[group_name] = keymaps
        log.info(f"Registered keymap group: {group_name} with {len(keymaps)} keymaps")

    def get_all_keymaps(self) -> Dict[str, List[KeymapDefinition]]:
        """全てのキーマップを取得"""
        return self._keymaps.copy()

    def check_conflicts(self) -> List[Tuple[str, str]]:
        """キーコンフリクトをチェック"""
        return self._conflict_detector.detect_conflicts(self._keymaps)

    def apply_keymaps(self):
        """Blenderにキーマップを適用"""
        self.unregister_keymaps()

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon

        for group_name, keymaps in self._keymaps.items():
            for keymap_def in keymaps:
                km = kc.keymaps.new(
                    name=keymap_def.context, space_type=keymap_def.context
                )

                kmi = km.keymap_items.new(
                    keymap_def.operator_id,
                    type=keymap_def.key,
                    value=keymap_def.value,
                    any=keymap_def.any,
                    shift=keymap_def.shift,
                    ctrl=keymap_def.ctrl,
                    alt=keymap_def.alt,
                    oskey=keymap_def.oskey,
                    key_modifier=keymap_def.key_modifier,
                    direction=keymap_def.direction,
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
        for km in self._registered_keymaps:
            try:
                wm.keyconfigs.addon.keymaps.remove(km)
            except:
                pass  # 既に削除されている場合
        self._registered_keymaps.clear()


class KeymapConflictDetector:
    """キーマップコンフリクト検出クラス"""

    def detect_conflicts(
        self, keymaps: Dict[str, List[KeymapDefinition]]
    ) -> List[Tuple[str, str]]:
        """コンフリクトを検出"""
        conflicts = []
        all_keymaps = []

        # 全キーマップを収集
        for group_name, keymap_list in keymaps.items():
            for keymap_def in keymap_list:
                all_keymaps.append((group_name, keymap_def))

        # コンフリクトチェック
        for i, (group1, keymap1) in enumerate(all_keymaps):
            for j, (group2, keymap2) in enumerate(all_keymaps[i + 1 :], i + 1):
                if self._is_conflict(keymap1, keymap2):
                    conflicts.append(
                        (
                            f"{group1}: {keymap1.description}",
                            f"{group2}: {keymap2.description}",
                        )
                    )

        return conflicts

    def _is_conflict(
        self, keymap1: KeymapDefinition, keymap2: KeymapDefinition
    ) -> bool:
        """2つのキーマップがコンフリクトするかチェック"""
        return (
            keymap1.context == keymap2.context
            and keymap1.key == keymap2.key
            and keymap1.alt == keymap2.alt
            and keymap1.ctrl == keymap2.ctrl
            and keymap1.shift == keymap2.shift
        )


class KeymapConfig:
    """キーマップ設定管理クラス"""

    def __init__(self):
        self.default_configs = self._load_default_configs()
        self.user_configs = {}

    def _load_default_configs(self) -> Dict:
        """デフォルト設定を読み込み"""
        return {
            "vertical_movement": {"upward": "W", "downward": "S"},
            "horizontal_movement": {"forward": "D", "backward": "A"},
            "handle_selection": {"left": "Q", "right": "E"},
            "view_control": {"focus": "F"},
        }

    def get_key_for_action(self, category: str, action: str) -> str:
        """アクションに対応するキーを取得"""
        if category in self.user_configs and action in self.user_configs[category]:
            return self.user_configs[category][action]
        return self.default_configs.get(category, {}).get(action, "")

    def set_key_for_action(self, category: str, action: str, key: str):
        """アクションにキーを設定"""
        if category not in self.user_configs:
            self.user_configs[category] = {}
        self.user_configs[category][action] = key


# グローバルインスタンス
keymap_registry = KeymapRegistry()
keymap_config = KeymapConfig()
