"""
数値入力パネルのオペレータ定義

元のkeypad.pyの機能を改良し、安全性とユーザビリティを向上させます。
"""

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from ...addon import get_prefs
from ...utils.logging import get_logger
from ...utils.ui_utils import ic
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
        """電卓UIを描画"""
        calculator = CalculatorState.get_instance()
        if not calculator.current_property:
            return

        prefs = calculator.get_preferences()
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        # === プロパティ情報パネル ===
        if calculator.current_property and prefs and prefs.show_property_path:
            # プロパティ名をヘッダーに表示
            prop_name = calculator.current_property.prop.identifier
            header, body = layout.panel("calc_property_info", default_closed=True)
            header.label(text=f"プロパティ: {prop_name}", icon=ic("RNA"))

            if body:
                # プロパティパス
                path_row = body.row()
                path_row.scale_y = 0.8
                path_row.label(text=calculator.current_property.get_display_path())

                # プロパティ詳細情報
                if (
                    prefs.respect_property_limits
                    or calculator.current_property.get_current_value() is not None
                ):
                    info_col = body.column(align=True)
                    info_col.scale_y = 0.75

                    # 現在値と範囲を横並びで表示
                    info_row = info_col.row(align=True)

                    # 現在値
                    current_value = calculator.current_property.get_current_value()
                    if current_value is not None:
                        current_str = (
                            prefs.format_result(current_value)
                            if prefs
                            else str(current_value)
                        )
                        value_sub = info_row.row(align=True)
                        value_sub.label(text="値:", icon=ic("DOT"))
                        value_sub.label(text=current_str)

                    # プロパティ制限
                    if prefs.respect_property_limits:
                        hard_min, hard_max = (
                            calculator.current_property.get_property_limits()
                        )
                        if hard_min is not None or hard_max is not None:
                            limit_sub = info_row.row(align=True)
                            limit_sub.label(text="範囲:", icon=ic("DRIVER_DISTANCE"))

                            min_str = str(hard_min) if hard_min is not None else "∞"
                            max_str = str(hard_max) if hard_max is not None else "∞"
                            limit_sub.label(text=f"[{min_str} ~ {max_str}]")

        # === 入力エリア ===
        input_box = layout.box()
        input_col = input_box.column()

        # 入力フィールド（大きめ）
        expr_row = input_col.row()
        expr_row.scale_y = 1.4
        expr_row.prop(self, "expr", text="", icon=ic("CONSOLE"))

        # 角度変換の注意書き
        if (
            calculator.current_property
            and calculator.current_property.is_angle_property()
            and prefs
            and prefs.auto_angle_conversion
        ):
            angle_row = input_col.row()
            angle_row.scale_y = 0.7
            angle_row.alignment = "CENTER"
            angle_row.label(text="🔄 度数入力は自動でラジアンに変換", icon=ic("INFO"))

        # === 関数パレット ===
        if prefs and prefs.show_functions:
            self._draw_function_buttons(layout)

        # === 数値キーパッド ===
        self._draw_numpad(layout)

        # === 履歴パネル ===
        if prefs and prefs.show_history and calculator.expression_history:
            self._draw_history_panel(layout, calculator.expression_history)

    def _draw_function_buttons(self, layout):
        """関数ボタンを描画"""
        header, body = layout.panel("calc_functions", default_closed=True)
        header.label(text="数学関数", icon=ic("SCRIPTPLUGINS"))

        if body:
            # 関数ボタンをカテゴリ分け
            func_col = body.column(align=True)
            func_col.scale_y = 0.9

            # 三角関数
            trig_row = func_col.row(align=True)
            for func, display in [
                ("sin", "sin"),
                ("cos", "cos"),
                ("tan", "tan"),
                ("pi", "π"),
            ]:
                op = trig_row.operator("wm.numeric_input_key", text=display)
                op.operation = "FUNCTION"
                op.value = func

            # その他の関数
            other_row = func_col.row(align=True)
            for func, display in [
                ("sqrt", "√"),
                ("log", "log"),
                ("exp", "exp"),
                ("abs", "abs"),
            ]:
                op = other_row.operator("wm.numeric_input_key", text=display)
                op.operation = "FUNCTION"
                op.value = func

    def _draw_numpad(self, layout):
        """テンキーレイアウトを描画"""
        calculator = CalculatorState.get_instance()
        prefs = calculator.get_preferences()

        num_box = layout.box()

        # ヘッダー
        header_row = num_box.row()
        header_row.scale_y = 0.8
        header_row.label(text="数値キーパッド", icon=ic("KEYINGSET"))

        # クリアボタン（最上段）
        clear_row = num_box.row(align=True)
        clear_row.scale_y = 1.1
        clear_op = clear_row.operator(
            "wm.numeric_input_key", text="Clear", icon=ic("CANCEL")
        )
        clear_op.operation = "CLEAR"

        # メインキーパッドレイアウト
        main_row = num_box.row(align=False)

        # 左側：数字キーパッド（3x3グリッド）
        numbers_col = main_row.column(align=True)
        numbers_col.scale_y = 1.1
        numbers_col.scale_x = 0.8

        # 電話風か電卓風かでレイアウトを切り替え
        phone_layout = prefs.phone_keypad_layout if prefs else False

        if phone_layout:
            # 電話風レイアウト（1-2-3が上）
            number_rows = [
                ["1", "2", "3"],
                ["4", "5", "6"],
                ["7", "8", "9"],
            ]
        else:
            # 電卓風レイアウト（7-8-9が上）
            number_rows = [
                ["7", "8", "9"],
                ["4", "5", "6"],
                ["1", "2", "3"],
            ]

        for row_numbers in number_rows:
            row = numbers_col.row(align=True)
            for num in row_numbers:
                op = row.operator("wm.numeric_input_key", text=num)
                op.operation = "INPUT"
                op.value = num

        # 最下段：0、ドット、バックスペース
        bottom_row = numbers_col.row(align=True)

        # 0とドットの順序を電話/電卓配列に応じて決定
        keys = [".", "0"] if phone_layout else ["0", "."]
        for key in keys:
            op = bottom_row.operator("wm.numeric_input_key", text=key)
            op.operation = "INPUT"
            op.value = key

        back_op = bottom_row.operator("wm.numeric_input_key", text="⌫")
        back_op.operation = "BACKSPACE"

        # 右側：四則演算（縦一列）
        operators_col = main_row.column(align=True)
        operators_col.scale_y = 1.1
        operators_col.scale_x = 0.8

        arithmetic_ops = [
            ("÷", "/"),
            ("×", "*"),
            ("−", "-"),
            ("+", "+"),
        ]

        for display, value in arithmetic_ops:
            op = operators_col.operator("wm.numeric_input_key", text=display)
            op.operation = "INPUT"
            op.value = value

        # 特殊操作行
        special_row = num_box.row(align=True)
        special_row.scale_y = 1.0

        # 括弧と累乗、符号反転
        paren_open_op = special_row.operator("wm.numeric_input_key", text="(")
        paren_open_op.operation = "INPUT"
        paren_open_op.value = "("

        paren_close_op = special_row.operator("wm.numeric_input_key", text=")")
        paren_close_op.operation = "INPUT"
        paren_close_op.value = ")"

        power_op = special_row.operator("wm.numeric_input_key", text="^")
        power_op.operation = "INPUT"
        power_op.value = "**"

        negate_op = special_row.operator("wm.numeric_input_key", text="±")
        negate_op.operation = "NEGATE"

    def _draw_history_panel(self, layout, history):
        """履歴パネルを描画"""
        header, body = layout.panel("calc_history", default_closed=True)
        header.label(text="履歴", icon=ic("TIME"))

        if body:
            # 最新5件を表示
            recent_history = history[-5:]
            if recent_history:
                history_col = body.column(align=True)
                history_col.scale_y = 0.9

                for expr in recent_history:
                    row = history_col.row()
                    op = row.operator("wm.numeric_input_key", text=f"📝 {expr}")
                    op.operation = "HISTORY"
                    op.value = expr
            else:
                empty_row = body.row()
                empty_row.scale_y = 0.7
                empty_row.label(text="履歴なし", icon=ic("INFO"))

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
