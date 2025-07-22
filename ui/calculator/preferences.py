# pyright: reportInvalidTypeForm=false
"""
電卓機能のプリファレンス設定

アドオンプリファレンスで電卓の動作をカスタマイズできます。
"""

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy.types import PropertyGroup

from ...utils.logging import get_logger

log = get_logger(__name__)


class CalculatorPreferences(PropertyGroup):
    """電卓のプリファレンス設定"""

    # UI表示オプション
    show_current_value: BoolProperty(
        name="Show Current Value",
        description="Display the current property value in the input field when opening calculator",
        default=True,
    )

    show_property_path: BoolProperty(
        name="Show Property Path",
        description="Display the full property path in the calculator dialog",
        default=True,
    )

    show_history: BoolProperty(
        name="Show History",
        description="Display calculation history in the calculator dialog",
        default=True,
    )

    show_functions: BoolProperty(
        name="Show Function Buttons",
        description="Display mathematical function buttons",
        default=True,
    )

    phone_keypad_layout: BoolProperty(
        name="Phone Keypad Layout",
        description="Use phone-style keypad layout (1-2-3 at top) instead of calculator-style (7-8-9 at top)",
        default=False,
    )

    # 計算オプション
    respect_property_limits: BoolProperty(
        name="Respect Property Limits",
        description="Automatically clamp values to property min/max limits",
        default=True,
    )

    auto_angle_conversion: BoolProperty(
        name="Auto Angle Conversion",
        description="Automatically convert degrees to radians for angle properties",
        default=True,
    )

    # 履歴設定
    history_size: IntProperty(
        name="History Size",
        description="Number of expressions to keep in history",
        default=20,
        min=5,
        max=100,
    )

    # UI設定
    dialog_width: IntProperty(
        name="Dialog Width",
        description="Width of the calculator dialog",
        default=300,
        min=200,
        max=600,
    )

    decimal_places: IntProperty(
        name="Decimal Places",
        description="Number of decimal places to display in results",
        default=3,
        min=0,
        max=10,
    )

    def draw(self, context, layout):
        """プリファレンスUIを描画"""
        # UI表示オプション
        ui_box = layout.box()
        ui_box.label(text="UI Options", icon="PREFERENCES")

        col = ui_box.column()
        col.prop(self, "show_current_value")
        col.prop(self, "show_property_path")
        col.prop(self, "show_history")
        col.prop(self, "show_functions")
        col.prop(self, "phone_keypad_layout")

        # サイズ設定
        row = col.row(align=True)
        row.prop(self, "dialog_width")
        row.prop(self, "decimal_places")

        # 計算オプション
        calc_box = layout.box()
        calc_box.label(text="Calculation Options", icon="TOPBAR")

        col = calc_box.column()
        col.prop(self, "respect_property_limits")
        col.prop(self, "auto_angle_conversion")
        col.prop(self, "history_size")

        # 統計情報
        stats_box = layout.box()
        stats_box.label(text="Statistics", icon="INFO")

        # 電卓の使用統計を表示（将来的な拡張）
        stats_col = stats_box.column()
        stats_col.label(text="Feature available in future version")

    def get_effective_history_size(self) -> int:
        """有効な履歴サイズを取得"""
        return max(5, min(100, self.history_size))

    def should_show_current_value(self) -> bool:
        """現在値を表示すべきかチェック"""
        return self.show_current_value

    def should_respect_limits(self) -> bool:
        """プロパティ制限を尊重すべきかチェック"""
        return self.respect_property_limits

    def should_convert_angles(self) -> bool:
        """角度変換を行うべきかチェック"""
        return self.auto_angle_conversion

    def format_result(self, value) -> str:
        """結果を設定された小数点以下桁数でフォーマット"""
        # None値やVector型の場合は文字列として返す
        if value is None:
            return "N/A"

        # Vector型やその他の非数値型の場合
        if not isinstance(value, (int, float)):
            return str(value)

        # 数値の場合は小数点以下桁数でフォーマット
        if self.decimal_places == 0:
            return str(int(round(value)))
        else:
            return f"{value:.{self.decimal_places}f}"
