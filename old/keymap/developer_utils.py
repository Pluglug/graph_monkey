"""
MonKey Keymap Developer Utilities

キーマップ開発者用のユーティリティ関数とツール
"""

import bpy
import json
import os
from typing import Dict, List, Tuple, Optional
from .keymap_manager import KeymapDefinition, keymap_registry


class KeymapAnalyzer:
    """キーマップ分析ツール"""

    @staticmethod
    def get_all_blender_keymaps() -> Dict[str, List[Dict]]:
        """Blender内の全キーマップを取得"""
        keymaps = {}
        wm = bpy.context.window_manager

        for kc_name in ["default", "addon", "user"]:
            kc = getattr(wm.keyconfigs, kc_name, None)
            if not kc:
                continue

            keymaps[kc_name] = []
            for km in kc.keymaps:
                km_info = {
                    "name": km.name,
                    "space_type": km.space_type,
                    "region_type": km.region_type,
                    "items": [],
                }

                for kmi in km.keymap_items:
                    kmi_info = {
                        "idname": kmi.idname,
                        "type": kmi.type,
                        "value": kmi.value,
                        "alt": kmi.alt,
                        "ctrl": kmi.ctrl,
                        "shift": kmi.shift,
                        "active": kmi.active,
                    }
                    km_info["items"].append(kmi_info)

                keymaps[kc_name].append(km_info)

        return keymaps

    @staticmethod
    def find_key_conflicts(key: str, modifiers: Dict[str, bool] = None) -> List[Dict]:
        """指定したキーのコンフリクトを検索"""
        if modifiers is None:
            modifiers = {"alt": False, "ctrl": False, "shift": False}

        conflicts = []
        wm = bpy.context.window_manager

        for kc_name in ["default", "addon", "user"]:
            kc = getattr(wm.keyconfigs, kc_name, None)
            if not kc:
                continue

            for km in kc.keymaps:
                for kmi in km.keymap_items:
                    if (
                        kmi.type == key
                        and kmi.alt == modifiers["alt"]
                        and kmi.ctrl == modifiers["ctrl"]
                        and kmi.shift == modifiers["shift"]
                        and kmi.active
                    ):

                        conflicts.append(
                            {
                                "keyconfig": kc_name,
                                "keymap": km.name,
                                "space_type": km.space_type,
                                "operator": kmi.idname,
                                "description": getattr(kmi, "name", ""),
                            }
                        )

        return conflicts

    @staticmethod
    def suggest_free_keys() -> List[str]:
        """使用されていないキーを提案"""
        all_keys = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
            "ZERO",
            "ONE",
            "TWO",
            "THREE",
            "FOUR",
            "FIVE",
            "SIX",
            "SEVEN",
            "EIGHT",
            "NINE",
        ]

        used_keys = set()
        wm = bpy.context.window_manager

        for kc_name in ["default", "addon", "user"]:
            kc = getattr(wm.keyconfigs, kc_name, None)
            if not kc:
                continue

            for km in kc.keymaps:
                for kmi in km.keymap_items:
                    if kmi.active and kmi.type in all_keys:
                        used_keys.add(kmi.type)

        return [key for key in all_keys if key not in used_keys]


class KeymapExporter:
    """キーマップエクスポートツール"""

    @staticmethod
    def export_monkey_keymaps(filepath: str) -> bool:
        """MonKeyキーマップをJSONファイルにエクスポート"""
        try:
            keymaps = keymap_registry.get_all_keymaps()

            export_data = {"version": "1.0", "addon": "MonKey", "keymaps": {}}

            for group_name, keymap_list in keymaps.items():
                export_data["keymaps"][group_name] = [
                    keymap_def.to_dict() for keymap_def in keymap_list
                ]

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    @staticmethod
    def import_monkey_keymaps(filepath: str) -> bool:
        """JSONファイルからMonKeyキーマップをインポート"""
        try:
            if not os.path.exists(filepath):
                return False

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "keymaps" not in data:
                return False

            for group_name, keymap_list in data["keymaps"].items():
                keymaps = []
                for kmap_dict in keymap_list:
                    keymap_def = KeymapDefinition(
                        operator_id=kmap_dict["operator_id"],
                        key=kmap_dict["key"],
                        value=kmap_dict.get("value", "PRESS"),
                        alt=kmap_dict.get("alt", False),
                        ctrl=kmap_dict.get("ctrl", False),
                        shift=kmap_dict.get("shift", False),
                        properties=kmap_dict.get("properties", {}),
                        description=kmap_dict.get("description", ""),
                        context=kmap_dict.get("context", "GRAPH_EDITOR"),
                    )
                    keymaps.append(keymap_def)

                keymap_registry.register_keymap_group(group_name, keymaps)

            return True
        except Exception as e:
            print(f"Import failed: {e}")
            return False


class KeymapValidator:
    """キーマップ検証ツール"""

    @staticmethod
    def validate_keymap_definition(keymap_def: KeymapDefinition) -> List[str]:
        """キーマップ定義を検証"""
        errors = []

        # オペレーターIDの検証
        if not keymap_def.operator_id:
            errors.append("Operator ID is required")

        # キーの検証
        valid_keys = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
            "ZERO",
            "ONE",
            "TWO",
            "THREE",
            "FOUR",
            "FIVE",
            "SIX",
            "SEVEN",
            "EIGHT",
            "NINE",
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "F9",
            "F10",
            "F11",
            "F12",
        ]

        if keymap_def.key not in valid_keys:
            errors.append(f"Invalid key: {keymap_def.key}")

        # コンテキストの検証
        valid_contexts = [
            "GRAPH_EDITOR",
            "DOPESHEET_EDITOR",
            "VIEW_3D",
            "IMAGE_EDITOR",
            "NODE_EDITOR",
            "SEQUENCE_EDITOR",
            "TEXT_EDITOR",
        ]

        if keymap_def.context not in valid_contexts:
            errors.append(f"Invalid context: {keymap_def.context}")

        return errors

    @staticmethod
    def validate_all_keymaps() -> Dict[str, List[str]]:
        """全キーマップを検証"""
        validation_results = {}
        keymaps = keymap_registry.get_all_keymaps()

        for group_name, keymap_list in keymaps.items():
            group_errors = []
            for i, keymap_def in enumerate(keymap_list):
                errors = KeymapValidator.validate_keymap_definition(keymap_def)
                if errors:
                    group_errors.extend([f"Item {i}: {error}" for error in errors])

            if group_errors:
                validation_results[group_name] = group_errors

        return validation_results


class KeymapDocumentationGenerator:
    """キーマップドキュメント生成ツール"""

    @staticmethod
    def generate_markdown_documentation() -> str:
        """Markdownフォーマットのドキュメントを生成"""
        doc = "# MonKey Keymap Documentation\n\n"
        keymaps = keymap_registry.get_all_keymaps()

        for group_name, keymap_list in keymaps.items():
            doc += f"## {group_name.replace('_', ' ').title()}\n\n"
            doc += "| Key Combination | Operator | Description |\n"
            doc += "|----------------|----------|-------------|\n"

            for keymap_def in keymap_list:
                modifiers = []
                if keymap_def.alt:
                    modifiers.append("Alt")
                if keymap_def.ctrl:
                    modifiers.append("Ctrl")
                if keymap_def.shift:
                    modifiers.append("Shift")

                key_combo = " + ".join(modifiers + [keymap_def.key])

                doc += f"| {key_combo} | {keymap_def.operator_id} | {keymap_def.description} |\n"

            doc += "\n"

        return doc

    @staticmethod
    def save_documentation(filepath: str) -> bool:
        """ドキュメントをファイルに保存"""
        try:
            doc = KeymapDocumentationGenerator.generate_markdown_documentation()
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(doc)
            return True
        except Exception as e:
            print(f"Documentation save failed: {e}")
            return False


# オペレーター定義
class MONKEY_OT_analyze_keymaps(bpy.types.Operator):
    """Analyze current keymaps"""

    bl_idname = "monkey.analyze_keymaps"
    bl_label = "Analyze Keymaps"
    bl_description = "Analyze current keymap configuration"

    def execute(self, context):
        analyzer = KeymapAnalyzer()
        conflicts = keymap_registry.check_conflicts()
        free_keys = analyzer.suggest_free_keys()

        self.report(
            {"INFO"},
            f"Found {len(conflicts)} conflicts, {len(free_keys)} free keys available",
        )

        return {"FINISHED"}


class MONKEY_OT_export_keymaps(bpy.types.Operator):
    """Export keymaps to file"""

    bl_idname = "monkey.export_keymaps"
    bl_label = "Export Keymaps"
    bl_description = "Export keymap configuration to JSON file"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to export file",
        default="monkey_keymaps.json",
        subtype="FILE_PATH",
    )

    def execute(self, context):
        success = KeymapExporter.export_monkey_keymaps(self.filepath)
        if success:
            self.report({"INFO"}, f"Keymaps exported to {self.filepath}")
        else:
            self.report({"ERROR"}, "Export failed")
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


# 登録用クラスリスト
classes = [
    MONKEY_OT_analyze_keymaps,
    MONKEY_OT_export_keymaps,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
