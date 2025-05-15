# pyright: reportInvalidTypeForm=false
import datetime
import os

from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)
from bpy.types import Operator, PropertyGroup, UIList

from ..addon import ADDON_ID, get_config_dir, get_prefs
from ..utils.logging import LoggerRegistry
from ..utils.ui_utils import ic


def _update_logger_settings(self, context):
    """ロガー設定を更新"""
    # print("_update_logger_settings called for:", self)
    if not hasattr(self, "log_enable") or not self.log_enable:
        # print("Logging disabled, skipping update.")
        return

    # 自動でログファイルパスを設定
    if self.log_to_file and not self.log_file_path:
        addon_name = ADDON_ID
        log_dir = os.path.join(get_config_dir(), "logs")

        try:
            os.makedirs(log_dir, exist_ok=True)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            # ファイル名にもアドオン名を含める (取得できていれば)
            log_filename = f"{(addon_name + '_') if addon_name else ''}{today}.log"
            self.log_file_path = os.path.join(log_dir, log_filename)
            print(f"Set log file path to: {self.log_file_path}")
        except Exception as e:
            print(f"Error creating log directory or setting path: {e}")
            # エラーが発生した場合、ファイルロギングが無効になる可能性がある

    # すべてのロガーに設定を適用
    # self は MONKEY_LoggerPreferences インスタンスのはず
    try:
        # print(f"Configuring loggers with settings from: {self}")
        LoggerRegistry.configure_all(self)
    except Exception as e:
        print(f"Error configuring loggers: {e}")


# シンプルなモジュールロガー設定
class MONKEY_ModuleLoggerSettings(PropertyGroup):
    """Module-specific logger settings"""

    name: StringProperty(
        name="Module Name", description="Module name to apply logging settings"
    )

    enabled: BoolProperty(
        name="Enable", description="Enable individual module settings", default=True
    )

    log_level: EnumProperty(
        items=[
            ("DEBUG", "Debug", "Detailed debug information"),
            ("INFO", "Info", "General information"),
            ("WARNING", "Warning", "Warnings only"),
            ("ERROR", "Error", "Errors only"),
            ("CRITICAL", "Critical", "Critical errors only"),
        ],
        name="Log Level",
        description="Log level for this module",
        default="INFO",
    )


class MONKEY_LoggerPreferences(PropertyGroup):
    """Logger settings property group"""

    def update_logger_settings(self, context):
        """Update logger settings"""
        # print("update_logger_settings called for:", self)
        if not self.log_enable:
            return

        _update_logger_settings(self, context)

    log_enable: BoolProperty(
        name="Enable Logging",
        description="Enable logging system",
        default=True,
        update=_update_logger_settings,
    )

    log_level: EnumProperty(
        items=[
            ("DEBUG", "Debug", "Detailed debug information"),
            ("INFO", "Info", "General information"),
            ("WARNING", "Warning", "Warnings only"),
            ("ERROR", "Error", "Errors only"),
            ("CRITICAL", "Critical", "Critical errors only"),
        ],
        name="Log Level",
        description="Default log level",
        default="INFO",
        update=_update_logger_settings,
    )

    log_to_console: BoolProperty(
        name="Console Logging",
        description="Output logs to console",
        default=True,
        update=_update_logger_settings,
    )

    use_colors: BoolProperty(
        name="Use Colors",
        description="Use colors in console output",
        default=True,
        update=_update_logger_settings,
    )

    log_to_file: BoolProperty(
        name="File Logging",
        description="Output logs to file",
        default=False,
        update=_update_logger_settings,
    )

    log_file_path: StringProperty(
        name="Log File",
        description="Path to log file",
        subtype="FILE_PATH",
        update=_update_logger_settings,
    )

    memory_capacity: IntProperty(
        name="Memory Capacity",
        description="Maximum number of logs to keep in memory",
        default=1000,
        min=100,
        max=10000,
        update=_update_logger_settings,
    )

    # モジュール設定のコレクション
    modules: CollectionProperty(type=MONKEY_ModuleLoggerSettings)
    active_module_index: IntProperty(default=0)

    def draw(self, layout):
        box = layout.box()
        box.label(text="Logging Settings", icon=ic("CONSOLE"))
        row = box.row()
        row.prop(self, "log_enable")

        if not self.log_enable:
            return

        row = box.row()
        row.prop(self, "log_to_console")

        row = box.row()
        row.prop(self, "log_to_file")
        if self.log_to_file:
            row = box.row()
            row.prop(self, "log_file_path")

        row = box.row()
        row.prop(self, "memory_capacity")

        row.separator()

        # モジュール設定セクション
        if len(self.modules) > 0:
            box.label(text="Module Settings")
            row = box.row()
            row.template_list(
                "MONKEY_UL_modules",
                "",
                self,
                "modules",
                self,
                "active_module_index",
            )

            # ログ操作ボタン
            row = box.row()
            row.operator("monkey_logger.export_logs", text="Export Logs")
            row.operator("monkey_logger.clear_logs", text="Clear Logs")
            row = box.row()
            row.operator(
                "monkey_logger.batch_update_log_levels", text="Batch Update Log Levels"
            )

    def register_module(self, module_name, log_level="INFO"):
        """Register module settings (update if existing)"""
        # 既存のモジュールを探す
        for module in self.modules:
            if module.name == module_name:
                module.log_level = log_level
                return

        module = self.modules.add()
        if module_name.startswith(ADDON_ID):
            module.name = module_name[len(ADDON_ID) :]
        else:
            module.name = module_name
        module.enabled = True
        module.log_level = log_level

    def register_modules(self, module_config):
        """Register multiple module settings at once

        Args:
            module_config: Dict[str, str] - Module name and log level mapping
                Example: {"my_addon.core": "DEBUG", "my_addon.ui": "INFO"}
        """
        for module_name, log_level in module_config.items():
            self.register_module(module_name, log_level)

    def get_logger(self, module_name):
        """Get logger for module"""
        return LoggerRegistry.get_logger(module_name)


class MONKEY_UL_modules(UIList):
    """Module settings list display"""

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.prop(item, "name", text="", emboss=False)
            icon = "CHECKBOX_HLT" if item.enabled else "CHECKBOX_DEHLT"
            row.prop(item, "enabled", text="", icon=icon, emboss=False)
            row.prop(item, "log_level", text="")


class MONKEY_OT_update_settings(Operator):
    """Update logger settings"""

    bl_idname = "monkey_logger.update_settings"
    bl_label = "Update Logger Settings"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        # アドオン設定を取得
        pr = get_prefs(context)
        if hasattr(pr, "_update_logger_settings"):
            pr._update_logger_settings(context)
            self.report({"INFO"}, "Logger settings updated")
            return {"FINISHED"}

        self.report({"ERROR"}, "Failed to update logger settings")
        return {"CANCELLED"}


class MONKEY_OT_export_logs(Operator):
    """Export logs"""

    bl_idname = "monkey_logger.export_logs"
    bl_label = "Export Logs"
    bl_options = {"REGISTER", "INTERNAL"}

    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        if LoggerRegistry.export_all_logs(self.filepath):
            self.report({"INFO"}, f"Logs exported to {self.filepath}")
        else:
            self.report({"ERROR"}, "Failed to export logs")
        return {"FINISHED"}

    def invoke(self, context, event):
        # デフォルトパスを設定
        addon_id = getattr(context.preferences, "active_addon", None)
        if addon_id:
            addon_name = addon_id.split(".")[0]
            file_dir = os.path.join(get_config_dir(), "logs")
            os.makedirs(file_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.filepath = os.path.join(file_dir, f"logs_{timestamp}.txt")

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class MONKEY_OT_clear_logs(Operator):
    """Clear all logs"""

    bl_idname = "monkey_logger.clear_logs"
    bl_label = "Clear Logs"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        # すべてのロガーのメモリハンドラをクリア
        for module_name, logger in LoggerRegistry.get_all_loggers().items():
            logger.memory_handler.clear()

        self.report({"INFO"}, "All logs cleared")
        return {"FINISHED"}


class MONKEY_OT_batch_update_log_levels(Operator):
    """Batch update log levels for all module loggers"""

    bl_idname = "monkey_logger.batch_update_log_levels"
    bl_label = "Batch Update Log Levels"
    bl_options = {"REGISTER", "INTERNAL"}

    log_level: EnumProperty(
        items=[
            ("DEBUG", "Debug", "Detailed debug information"),
            ("INFO", "Info", "General information"),
            ("WARNING", "Warning", "Warnings only"),
            ("ERROR", "Error", "Errors only"),
            ("CRITICAL", "Critical", "Critical errors only"),
        ],
        name="Log Level",
        description="Log level to set",
        default="INFO",
    )

    def execute(self, context):
        prefs = get_prefs(context).logger_prefs
        if not hasattr(prefs, "modules"):
            self.report({"ERROR"}, "Logger preferences not found")
            return {"CANCELLED"}

        # すべてのモジュールのログレベルを更新
        for module in prefs.modules:
            if module.enabled:  # 有効なモジュールのみ更新
                module.log_level = self.log_level

        # ロガー設定を更新
        prefs.update_logger_settings(context)  # インスタンスメソッドを呼び出す
        self.report({"INFO"}, f"All module log levels set to {self.log_level}")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
