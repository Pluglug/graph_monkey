from dataclasses import dataclass, field
from typing import Dict, List

import bpy
from rna_keymap_ui import draw_kmi

from ..constants import RegionType, SpaceType
from ..utils.logging import get_logger
from ..utils.ui_utils import ic

log = get_logger(__name__)


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
    active: bool = True  # キーマップの有効/無効状態

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
            "active": self.active,
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

                # キーマップが無効な場合は無効化
                if not keymap_def.active:
                    kmi.active = False

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

    def get_hotkey_entry_item(self, km, kmi_name, kmi_value, handled_kmi):
        """指定されたオペレータに対応するkmiを取得"""
        for km_item in km.keymap_items:
            if km_item in handled_kmi:
                continue
            if km_item.idname == kmi_name:
                if kmi_value is None:
                    return km_item
                elif (
                    hasattr(km_item.properties, "name")
                    and km_item.properties.name == kmi_value
                ):
                    return km_item
        return None

    def get_kmi_collision(self, kc, km, kmi):
        """キーマップアイテムの衝突を検出"""
        if kmi.active:
            for it_kmi in km.keymap_items:
                if it_kmi.active and it_kmi != kmi:
                    b_has_collision = it_kmi.compare(kmi)
                    if b_has_collision:
                        return it_kmi
        return None

    def draw_keymap_settings(self, context, layout):
        """キーマップ設定UIを描画"""
        if not self._keymaps:
            layout.label(text="No keymaps registered")
            return

        wm = context.window_manager
        kc = wm.keyconfigs.user

        if not wm or not kc:
            layout.label(text="User keyconfig is not available")
            return

        # # 統計情報を表示
        # total_groups = len(self._keymaps)
        # total_keymaps = sum(len(keymaps) for keymaps in self._keymaps.values())

        # stats_box = layout.box()
        # stats_box.label(
        #     text=f"Registered groups: {total_groups}, Total keymaps: {total_keymaps}",
        #     icon=ic("INFO"),
        # )

        # KeymapDefinitionからkm_treeを構築
        from collections import defaultdict

        km_tree = defaultdict(list)

        for group_name, keymap_defs in self._keymaps.items():
            for keymap_def in keymap_defs:
                km_tree[keymap_def.name].append(
                    (
                        keymap_def.operator_id,
                        (
                            getattr(keymap_def.properties, "name", None)
                            if keymap_def.properties and "name" in keymap_def.properties
                            else None
                        ),
                    )
                )

        # 衝突検出
        t_collisions = defaultdict(list)
        handled_kmi = set()

        for km_name, kmi_items in km_tree.items():
            km = kc.keymaps.get(km_name)
            if km:
                for kmi_node in kmi_items:
                    kmi = self.get_hotkey_entry_item(
                        km, kmi_node[0], kmi_node[1], handled_kmi
                    )
                    if kmi:
                        handled_kmi.add(kmi)
                        p_collision_kmi = self.get_kmi_collision(kc, km, kmi)
                        if p_collision_kmi:
                            t_collisions[km_name].append(
                                (
                                    kmi.to_string(),
                                    f" - {p_collision_kmi.name}({p_collision_kmi.idname})",
                                    kmi,
                                )
                            )

        # 衝突がある場合は警告表示
        if t_collisions:
            collision_box = layout.box()
            row = collision_box.row(align=True)
            row.separator()
            row.label(text="Keymap collision:", icon=ic("MOD_PHYSICS"))

            col_box = collision_box.column(align=True)
            for km_name, collision_items in t_collisions.items():
                subbox = col_box.box()
                col = subbox.column(align=True)
                col.label(text=f"{km_name}:")
                for col_item in collision_items:
                    s_keymap, s_label, p_kmi = col_item
                    row = col.row(align=True)
                    r1 = row.row(align=True)
                    r1.alignment = "LEFT"
                    r1.label(text=s_keymap, icon=ic("DOT"))
                    r2 = row.row(align=True)
                    r2.label(text=s_label)

        # 各グループのキーマップを表示
        for group_name, keymap_defs in self._keymaps.items():
            # グループ名で区切り
            group_box = layout.box()
            group_box.label(text=f"{group_name}:", icon=ic("DOT"))

            # このグループで使用されるkm名を取得
            km_names = list({kd.name for kd in keymap_defs})

            for km_name in km_names:
                km = kc.keymaps.get(km_name)
                if not km:
                    row = group_box.row()
                    row.label(
                        text=f"Keymap '{km_name}' not found", icon=ic("ERROR")
                    )
                    continue

                # キーマップボックス
                keymap_box = group_box.box()

                # キーマップヘッダー
                header_row = keymap_box.row(align=True)
                header_row.label(text=f"{km_name}:")

                # 修復状態をチェック
                b_modified = km.is_user_modified
                b_has_deleted = False

                # このkmに関連するKeymapDefinitionを取得
                related_keymaps = [kd for kd in keymap_defs if kd.name == km_name]

                # 削除されたアイテムをチェック
                for keymap_def in related_keymaps:
                    kmi = self.get_hotkey_entry_item(
                        km,
                        keymap_def.operator_id,
                        (
                            getattr(keymap_def.properties, "name", None)
                            if keymap_def.properties and "name" in keymap_def.properties
                            else None
                        ),
                        set(),
                    )
                    if not kmi:
                        b_has_deleted = True
                        break

                # # 復元ボタン (まずアドオン内のkmiを復元。次に警告を出したうえでユーザーのkmを復元)
                # if b_modified or b_has_deleted:
                #     subrow = header_row.row()
                #     subrow.alignment = "RIGHT"
                #     s_restore_caption = "キーマップを復元" if b_has_deleted else "復元"
                #     s_icon = ic("FILE_REFRESH") if b_has_deleted else ic("BACK")
                #     # 実際の復元機能は今回は省略（オペレータが必要）
                #     subrow.label(text=s_restore_caption, icon=s_icon)

                keymap_box.context_pointer_set("keymap", km)

                # km内の全kmiを表示
                handled_kmi_for_display = set()

                # まず、このグループに関連するkmiを表示
                for keymap_def in related_keymaps:
                    kmi = self.get_hotkey_entry_item(
                        km,
                        keymap_def.operator_id,
                        (
                            getattr(keymap_def.properties, "name", None)
                            if keymap_def.properties and "name" in keymap_def.properties
                            else None
                        ),
                        handled_kmi_for_display,
                    )
                    if kmi:
                        handled_kmi_for_display.add(kmi)

                        # 衝突チェック
                        p_collision_kmi = self.get_kmi_collision(kc, km, kmi)
                        subcol = keymap_box
                        if p_collision_kmi:
                            collision_row = subcol.row(align=True)
                            collision_row.separator(factor=2)
                            r1 = collision_row.row(align=True)
                            r1.alignment = "LEFT"
                            r1.label(text="Collision:", icon=ic("MOD_PHYSICS"))
                            r2 = collision_row.row(align=True)
                            r2.alignment = "RIGHT"
                            r2.label(
                                text=f"{p_collision_kmi.name}({p_collision_kmi.idname})"
                            )

                            subcol = keymap_box.column(align=True)
                            subcol.active = False

                        # draw_kmiで標準UI表示
                        draw_kmi([], kc, km, kmi, subcol, 0)

                        # # 説明文を表示
                        # if keymap_def.description:
                        #     desc_row = subcol.row()
                        #     desc_row.label(text=f"説明: {keymap_def.description}")
                    else:
                        # kmiが見つからない場合
                        error_row = keymap_box.row(align=True)
                        error_row.separator(factor=2.0)
                        error_row.label(
                            text=f"Keymap item '{keymap_def.operator_id}' not found",
                            icon=ic("ERROR"),
                        )

                # # その他のkmiも表示（このグループ以外で追加されたもの）
                # other_kmis = [
                #     kmi for kmi in km.keymap_items if kmi not in handled_kmi_for_display
                # ]
                # if other_kmis:
                #     other_box = keymap_box.box()
                #     other_box.label(text="その他のキーマップアイテム:", icon=ic("DOT"))
                #     for kmi in other_kmis:
                #         draw_kmi([], kc, km, kmi, other_box, 0)


keymap_registry = KeymapRegistry()

# Dopesheet; Frames; Graph Editor; Object Mode; Pose
