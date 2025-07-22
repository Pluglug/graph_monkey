"""
数値入力パネルのオペレータ定義

元のkeypad.pyの機能を改良し、安全性とユーザビリティを向上させます。
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ...addon import get_prefs
from ...utils.logging import get_logger
from .core import CalculatorState

log = get_logger(__name__)


class WM_OT_numeric_input(Operator):
    """数値プロパティ用の電卓インターフェース"""

    bl_idname = "wm.numeric_input"
    bl_label = "Numeric Input Calculator"
    bl_description = "Calculator interface for numeric properties"

    expr: StringProperty(default="")  # type: ignore
    initial_value_set: BoolProperty(default=False)  # type: ignore

    @classmethod
    def poll(cls, context):
        """オペレータが実行可能かチェック"""
        # 既に電卓が開いている場合は許可
        calculator = CalculatorState.get_instance()
        if calculator.current_property:
            return True

        # 通常のプロパティコンテキストをチェック
        ptr = getattr(context, "button_pointer", None)
        prop = getattr(context, "button_prop", None)
        if ptr and prop and prop.type in {"INT", "FLOAT"}:
            return True

        # ホットキー呼び出し時: copy_data_path_buttonのpollを使用
        try:
            return bpy.ops.ui.copy_data_path_button.poll()
        except Exception:
            return False

    def invoke(self, context, event):
        """電卓ダイアログを表示"""
        calculator = CalculatorState.get_instance()

        # プロパティ情報を設定
        if not calculator.set_property_info(context):
            self.report({"ERROR"}, "Failed to get property information")
            return {"CANCELLED"}

        # プロパティ型をチェック（ホットキー呼び出し時の型検証）
        if (
            not calculator.current_property
            or calculator.current_property.prop.type not in {"INT", "FLOAT"}
        ):
            self.report(
                {"ERROR"},
                "Calculator can only be used with numeric properties (INT/FLOAT)",
            )
            return {"CANCELLED"}

        # Vector型プロパティ全体の場合はエラー
        current_value = calculator.current_property.get_current_value()
        if current_value is None:
            self.report(
                {"ERROR"},
                "Calculator can only be used with individual numeric values, not vector properties",
            )
            return {"CANCELLED"}

        # 電卓の参照を設定
        calculator.set_popup(self)

        # プリファレンスを取得
        prefs = calculator.get_preferences()

        # 現在値を表示するかチェック
        if prefs and prefs.should_show_current_value():
            current_value = calculator.current_property.get_current_value()
            if current_value is not None:
                # プリファレンスの小数点以下桁数でフォーマット
                if prefs:
                    self.expr = prefs.format_result(current_value)
                else:
                    self.expr = str(current_value)
                # 初期値が設定されたことを記録
                self.initial_value_set = True
            else:
                self.expr = ""
                self.initial_value_set = False
        else:
            self.expr = ""
            self.initial_value_set = False

        log.debug(
            f"Calculator invoked for: {calculator.current_property.get_display_path()}"
        )

        # ダイアログ幅をプリファレンスから取得
        dialog_width = prefs.dialog_width if prefs else 300
        return context.window_manager.invoke_props_dialog(self, width=dialog_width)

    def draw(self, context):
        """UIを描画"""
        calculator = CalculatorState.get_instance()
        if not calculator.current_property:
            return

        prefs = calculator.get_preferences()
        layout = self.layout

        # プロパティパス表示（オプション）
        if prefs and prefs.show_property_path:
            col = layout.column()
            col.label(text=calculator.current_property.get_display_path(), icon="RNA")
            col.separator()

        # 入力フィールド
        input_col = layout.column()
        input_col.prop(self, "expr", text="", icon="OUTLINER_OB_FONT")

        # プロパティ情報表示
        if calculator.current_property:
            info_row = input_col.row()
            info_row.scale_y = 0.7

            # 現在値表示
            current_value = calculator.current_property.get_current_value()
            if current_value is not None:
                current_str = (
                    prefs.format_result(current_value) if prefs else str(current_value)
                )
                info_row.label(text=f"Current: {current_str}")

            # プロパティ制限表示
            if prefs and prefs.respect_property_limits:
                hard_min, hard_max = calculator.current_property.get_property_limits()
                if hard_min is not None or hard_max is not None:
                    limit_parts = []
                    if hard_min is not None:
                        limit_parts.append(f"min: {hard_min}")
                    if hard_max is not None:
                        limit_parts.append(f"max: {hard_max}")
                    info_row.label(text=f"Limits: {', '.join(limit_parts)}")

            # 角度プロパティの通知
            if (
                calculator.current_property.is_angle_property()
                and prefs
                and prefs.auto_angle_conversion
            ):
                angle_row = input_col.row()
                angle_row.scale_y = 0.6
                angle_row.label(
                    text="Note: Input in degrees will be auto-converted to radians",
                    icon="INFO",
                )

        # 関数ボタン（オプション）
        if prefs and prefs.show_functions:
            self._draw_function_buttons(input_col)

        # テンキー風ボタン配置
        self._draw_numpad(input_col)

        # 履歴表示（オプション）
        if prefs and prefs.show_history and calculator.expression_history:
            input_col.separator()
            history_box = input_col.box()
            history_box.label(text="History:")
            # 最新5件を表示
            recent_history = calculator.expression_history[-5:]
            for expr in recent_history:
                row = history_box.row()
                row.scale_y = 0.8
                op = row.operator("wm.numeric_input_key", text=expr)
                op.operation = "HISTORY"
                op.value = expr

    def _draw_function_buttons(self, layout):
        """関数ボタンを描画"""
        func_box = layout.box()
        func_box.label(text="Functions:")
        func_grid = func_box.grid_flow(columns=4, align=True)

        functions = [
            ("sin", "sin"),
            ("cos", "cos"),
            ("tan", "tan"),
            ("pi", "π"),
            ("sqrt", "√"),
            ("log", "log"),
            ("exp", "exp"),
            ("abs", "abs"),
        ]

        for func, display in functions:
            op = func_grid.operator("wm.numeric_input_key", text=display)
            op.operation = "FUNCTION"
            op.value = func

    def _draw_numpad(self, layout):
        """テンキーレイアウトを描画"""
        # 数値キー
        num_box = layout.box()

        # 最上段（クリア、バックスペース）
        top_row = num_box.row(align=True)
        op = top_row.operator("wm.numeric_input_key", text="Clear")
        op.operation = "CLEAR"
        op = top_row.operator("wm.numeric_input_key", text="←")
        op.operation = "BACKSPACE"

        # 数値グリッド
        grid = num_box.grid_flow(row_major=True, columns=4, align=True)

        # 数字ボタン（7-9, 4-6, 1-3, 0）
        for row_nums in [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["0", ".", "(", "+"],
        ]:
            for char in row_nums:
                op = grid.operator("wm.numeric_input_key", text=char)
                op.operation = "INPUT"
                op.value = char

        # 特殊操作
        special_row = num_box.row(align=True)
        op = special_row.operator("wm.numeric_input_key", text=")")
        op.operation = "INPUT"
        op.value = ")"

        op = special_row.operator("wm.numeric_input_key", text="^")
        op.operation = "INPUT"
        op.value = "**"

        op = special_row.operator("wm.numeric_input_key", text="±")
        op.operation = "NEGATE"

    def execute(self, context):
        """計算を実行してプロパティに適用"""
        calculator = CalculatorState.get_instance()

        if not calculator.current_property:
            self.report({"ERROR"}, "No property information available")
            return {"CANCELLED"}

        if not self.expr.strip():
            self.report({"ERROR"}, "Empty expression")
            return {"CANCELLED"}

        try:
            # 式の前処理（角度変換など）
            processed_expr = calculator.process_expression_for_property(self.expr)

            # 数式を評価
            result = calculator.evaluate_expression(processed_expr)

            # プロパティに書き込み
            if calculator.write_value_to_property(result):
                prefs = calculator.get_preferences()
                result_str = prefs.format_result(result) if prefs else str(result)
                self.report({"INFO"}, f"Set to {result_str}")
                calculator.clear_popup()
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, "Failed to write value to property")
                return {"CANCELLED"}

        except ValueError as e:
            self.report({"ERROR"}, f"Invalid expression: {e}")
            return {"CANCELLED"}
        except Exception as e:
            log.error(f"Unexpected error in calculator execution: {e}")
            self.report({"ERROR"}, "Calculation failed")
            return {"CANCELLED"}


class WM_OT_numeric_input_key(Operator):
    """電卓キー入力オペレータ"""

    bl_idname = "wm.numeric_input_key"
    bl_label = "Calculator Key"
    bl_description = "Calculator key input"

    operation: StringProperty()  # type: ignore
    value: StringProperty()  # type: ignore

    def execute(self, context):
        """キー操作を実行"""
        calculator = CalculatorState.get_instance()
        popup = calculator.get_popup()

        if not popup:
            self.report({"ERROR"}, "Calculator not running")
            return {"CANCELLED"}

        # 初期値が表示されている状態での自動クリア判定
        should_auto_clear = (
            popup.initial_value_set
            and self.operation in ("INPUT", "FUNCTION")
            and (
                self.value.isdigit()
                or self.value in [".", "("]
                or self.operation == "FUNCTION"
            )
        )

        if should_auto_clear:
            popup.expr = ""
            popup.initial_value_set = False
            log.debug("Auto-cleared initial value before new input")

        if self.operation == "INPUT":
            popup.expr += self.value
            # 四則演算子が入力された場合は初期値フラグをクリア（計算継続モードに移行）
            if self.value in ["+", "-", "*", "/", ")", "**", "%"]:
                popup.initial_value_set = False
        elif self.operation == "BACKSPACE":
            popup.expr = popup.expr[:-1]
            # バックスペースで編集開始した場合も初期値フラグをクリア
            popup.initial_value_set = False
        elif self.operation == "CLEAR":
            popup.expr = ""
            popup.initial_value_set = False
        elif self.operation == "NEGATE":
            if popup.expr:
                # 現在の式を括弧で囲んで符号反転
                popup.expr = f"-({popup.expr})"
            popup.initial_value_set = False
        elif self.operation == "FUNCTION":
            # 関数名を挿入（引数用の括弧も追加）
            if self.value in ["pi", "e", "tau"]:
                popup.expr += self.value
            else:
                popup.expr += f"{self.value}("
        elif self.operation == "HISTORY":
            popup.expr = self.value
            popup.initial_value_set = False

        log.debug(f"Key operation: {self.operation} = {self.value}, expr: {popup.expr}")
        return {"FINISHED"}
