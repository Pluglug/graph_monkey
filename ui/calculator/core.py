"""
電卓機能のコアロジック

安全な数式評価とプロパティ管理を提供します。
"""

import ast
import math
import operator as op
import weakref
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union, Set

import bpy

from ...addon import get_prefs
from ...utils.logging import get_logger

log = get_logger(__name__)

# 許可する演算子
ALLOWED_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: lambda x, y: float(x) ** float(y),  # 複素数を避けるため独自実装
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

# 許可する数学関数と定数
ALLOWED_MATH = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sqrt": math.sqrt,
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "abs": abs,
    "min": min,
    "max": max,
    "radians": math.radians,
    "degrees": math.degrees,
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


@dataclass
class PropertyInfo:
    """プロパティ情報を格納するデータクラス"""

    ptr: Any  # PointerRNA
    prop: Any  # Property definition
    prop_index: int = -1  # Vector要素番号
    sub_path: str = ""  # ID からの相対パス
    id_owner: Any = None  # 最終的に書き込む ID オブジェクト

    def get_display_path(self) -> str:
        """UI表示用のパスを生成"""
        if not self.id_owner:
            return "Unknown"

        try:
            id_path = f'bpy.data.{self.id_owner.__class__.__name__.lower()}s["{self.id_owner.name}"]'
            full_path = f"{id_path}{self.sub_path}.{self.prop.identifier}"
            if self.prop_index != -1:
                full_path += f"[{self.prop_index}]"
            return full_path
        except Exception as e:
            log.warning(f"Failed to generate display path: {e}")
            return "Path generation failed"

    def get_current_value(self) -> Union[int, float, None]:
        """現在のプロパティ値を取得"""
        try:
            # ネストしたパスの場合は ptr を直接使用
            # 単純なパスの場合は sub_path を使って解決
            if self.sub_path and self.ptr == self.id_owner:
                # 単純なパス（従来の処理）
                container = self.id_owner.path_resolve(self.sub_path, False)
            else:
                # ネストしたパスまたは直接アクセス
                container = self.ptr

            prop_value = getattr(container, self.prop.identifier)

            if self.prop_index != -1:
                # ベクタープロパティの個別成分の場合
                if (
                    hasattr(prop_value, "__getitem__")
                    and len(prop_value) > self.prop_index
                ):
                    return prop_value[self.prop_index]
            else:
                # スカラープロパティまたはベクタープロパティ全体
                # Vector型の場合は電卓では処理できない
                if hasattr(prop_value, "__len__") and len(prop_value) > 1:
                    log.warning(
                        f"Vector property detected: {self.prop.identifier}. Calculator supports individual components only."
                    )
                    return None
                # スカラープロパティの場合
                return prop_value
        except Exception as e:
            log.warning(f"Failed to get current value: {e}")

        return None

    def get_property_limits(self) -> tuple[Optional[float], Optional[float]]:
        """プロパティの制限値を取得 (min, max)"""
        try:
            hard_min = getattr(self.prop, "hard_min", None)
            hard_max = getattr(self.prop, "hard_max", None)
            return hard_min, hard_max
        except Exception:
            return None, None

    def is_angle_property(self) -> bool:
        """角度プロパティかどうかチェック"""
        try:
            subtype = getattr(self.prop, "subtype", "")
            prop_name = getattr(self.prop, "identifier", "")

            # subtype が ANGLE の場合
            if subtype == "ANGLE":
                return True

            # rotation関連のプロパティ名の場合（クォータニオンは除外）
            angle_property_names = [
                "rotation",
                "rotation_euler",
                "rotation_axis_angle",
                "rotation_x",
                "rotation_y",
                "rotation_z",
            ]

            if prop_name in angle_property_names:
                return True

            # EULERサブタイプの場合（回転オイラー角）
            if subtype == "EULER":
                return True

            return False
        except Exception:
            return False


class SafeExpressionEvaluator:
    """安全な数式評価クラス"""

    def __init__(self):
        self.allowed_names = ALLOWED_MATH.copy()

    def evaluate(self, expression: str) -> Union[int, float]:
        """
        安全に数式を評価

        Args:
            expression: 評価する数式

        Returns:
            評価結果（数値）

        Raises:
            ValueError: 無効な数式や禁止された操作
            TypeError: 予期しない型
        """
        if not expression.strip():
            raise ValueError("Empty expression")

        # Blender風の「.1」→「0.1」自動補完
        import re

        original_expr = expression
        expression = re.sub(r"(^|[^0-9])\.([0-9]+)", r"\g<1>0.\2", expression)
        if expression != original_expr:
            log.debug(f"Auto-completed decimal: '{original_expr}' → '{expression}'")

        try:
            node = ast.parse(expression, mode="eval")
            return self._eval_node(node.body)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in expression: {e}")
        except Exception as e:
            raise ValueError(f"Evaluation error: {e}")

    def _eval_node(self, node: ast.AST) -> Union[int, float]:
        """ASTノードを安全に評価"""

        if isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            else:
                raise TypeError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n

        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_func = ALLOWED_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"Unsupported operation: {type(node.op).__name__}")
            result = op_func(left, right)
            # 複素数や無限大を排除
            if isinstance(result, complex):
                raise ValueError("Complex numbers are not supported")
            if not isinstance(result, (int, float)) or not (
                float("-inf") < result < float("inf")
            ):
                raise ValueError("Result must be a finite real number")
            return result

        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_func = ALLOWED_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(
                    f"Unsupported unary operation: {type(node.op).__name__}"
                )
            result = op_func(operand)
            # 型チェック
            if not isinstance(result, (int, float)) or not (
                float("-inf") < result < float("inf")
            ):
                raise ValueError("Result must be a finite real number")
            return result

        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name not in self.allowed_names:
                raise ValueError(f"Function '{func_name}' is not allowed")

            args = [self._eval_node(arg) for arg in node.args]
            func = self.allowed_names[func_name]
            result = func(*args)
            # 複素数を排除
            if isinstance(result, complex):
                raise ValueError("Complex numbers are not supported")
            # 型と有限性チェック
            if not isinstance(result, (int, float)) or not (
                float("-inf") < result < float("inf")
            ):
                raise ValueError("Result must be a finite real number")
            return result

        elif isinstance(node, ast.Name):
            if node.id in self.allowed_names:
                return self.allowed_names[node.id]
            else:
                raise ValueError(f"Name '{node.id}' is not allowed")

        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")


class CalculatorState:
    """電卓の状態管理クラス（シングルトン）"""

    _instance: Optional["CalculatorState"] = None
    _popup_ref: Optional[weakref.ref] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized") or not self._initialized:
            self.evaluator = SafeExpressionEvaluator()
            self.current_property: Optional[PropertyInfo] = None
            self.expression_history: list[str] = []
            self._initialized = True

    @classmethod
    def get_instance(cls) -> "CalculatorState":
        """シングルトンインスタンスを取得"""
        return cls()

    @classmethod
    def set_popup(cls, popup_operator):
        """ポップアップオペレータの参照を設定"""
        if popup_operator is None:
            cls._popup_ref = None
        else:
            cls._popup_ref = weakref.ref(popup_operator)
        log.debug(f"Popup reference set: {cls._popup_ref}")

    @classmethod
    def get_popup(cls):
        """ポップアップオペレータの参照を取得"""
        if cls._popup_ref is None:
            return None
        try:
            popup = cls._popup_ref()
            if popup is None:
                cls._popup_ref = None  # 無効な参照をクリア
            return popup
        except Exception:
            cls._popup_ref = None
            return None

    @classmethod
    def clear_popup(cls):
        """ポップアップ参照をクリア"""
        cls.set_popup(None)

    @classmethod
    def cleanup_on_reload(cls):
        """モジュールリロード時のクリーンアップ"""
        if cls._instance:
            cls.clear_popup()
            cls._instance = None
        log.debug("Calculator state cleaned up for reload")

    def get_preferences(self):
        """プリファレンスを取得"""
        try:
            prefs = get_prefs()
            return prefs.calculator
        except Exception as e:
            log.warning(f"Failed to get calculator preferences: {e}")
            return None

    def evaluate_expression(self, expression: str) -> Union[int, float]:
        """数式を評価して履歴に追加"""
        result = self.evaluator.evaluate(expression)

        # 履歴に追加（重複は避ける）
        if expression not in self.expression_history:
            self.expression_history.append(expression)
            # 履歴サイズ制限（プリファレンスから取得）
            prefs = self.get_preferences()
            max_history = prefs.get_effective_history_size() if prefs else 20
            if len(self.expression_history) > max_history:
                self.expression_history = self.expression_history[-max_history:]

        log.debug(f"Evaluated: {expression} = {result}")
        return result

    def set_property_info(self, context) -> bool:
        """コンテキストからプロパティ情報を設定"""
        try:
            ptr = getattr(context, "button_pointer", None)
            prop = getattr(context, "button_prop", None)
            prop_index = getattr(context, "button_prop_index", -1)

            # 通常のコンテキストが利用可能な場合
            if ptr and prop and prop.type in {"INT", "FLOAT"}:
                return self._set_property_info_from_context(ptr, prop, prop_index)

            # ホットキーからの呼び出しでコンテキストが無い場合
            log.debug("No button context available, trying copy_data_path_button")
            return self._set_property_info_from_clipboard(context)

        except Exception as e:
            log.error(f"Failed to set property info: {e}")
            return False

    def _set_property_info_from_context(self, ptr, prop, prop_index):
        """通常のコンテキストからプロパティ情報を設定"""
        try:
            # 相対パスを安全に取得
            try:
                sub_path = ptr.path_from_id() or ""
            except Exception:
                log.warning("Failed to get path_from_id, using empty path")
                sub_path = ""

            # ID オーナーを取得
            id_owner = ptr.id_data or ptr

            self.current_property = PropertyInfo(
                ptr=ptr,
                prop=prop,
                prop_index=prop_index,
                sub_path=sub_path,
                id_owner=id_owner,
            )

            log.debug(
                f"Property info set from context: {self.current_property.get_display_path()}"
            )
            return True

        except Exception as e:
            log.error(f"Failed to set property info from context: {e}")
            return False

    def _set_property_info_from_clipboard(self, context):
        """クリップボードからプロパティ情報を設定"""
        try:
            # copy_data_path_buttonを呼び出してクリップボードにパスをコピー
            result = bpy.ops.ui.copy_data_path_button(full_path=False)

            if result != {"FINISHED"}:
                log.warning("copy_data_path_button failed")
                return False

            # クリップボードからパスを取得
            clipboard_text = context.window_manager.clipboard
            if not clipboard_text:
                log.warning("No clipboard content available")
                return False

            log.debug(f"Got clipboard path: {clipboard_text}")

            # パスを解析してプロパティ情報を取得
            return self._parse_property_path(clipboard_text)

        except Exception as e:
            log.error(f"Failed to set property info from clipboard: {e}")
            return False

    def _parse_property_path(self, data_path: str):
        """データパスを解析してプロパティ情報を設定"""
        try:
            # パスの例: "location[0]", "eevee.taa_samples", "world.node_tree.nodes[0].inputs[1].default_value"
            log.debug(f"Parsing property path: {data_path}")

            # 配列インデックスを抽出
            prop_index = -1
            base_path = data_path

            if "[" in data_path and data_path.endswith("]"):
                # 配列プロパティの場合 "location[0]" -> "location", 0
                bracket_pos = data_path.rfind("[")  # 最後の[を見つける
                base_path = data_path[:bracket_pos]
                index_str = data_path[bracket_pos + 1 : -1]
                try:
                    prop_index = int(index_str)
                except ValueError:
                    log.warning(f"Invalid array index in path: {index_str}")
                    prop_index = -1

            # ネストしたパスかどうかチェック
            if "." in base_path:
                return self._resolve_nested_property_path(base_path, prop_index)
            else:
                return self._resolve_simple_property_path(base_path, prop_index)

        except Exception as e:
            log.error(f"Failed to parse property path '{data_path}': {e}")
            return False

    def _resolve_nested_property_path(self, path: str, prop_index: int):
        """ネストしたプロパティパスを解決"""
        try:
            # パスをドットで分割
            path_parts = path.split(".")
            log.debug(f"Nested path parts: {path_parts}")

            # 様々なルートオブジェクトで試行
            root_candidates = [
                ("scene", bpy.context.scene),
                ("active_object", bpy.context.active_object),
                ("view_layer", bpy.context.view_layer),
            ]

            # worldオブジェクトを安全に追加
            if bpy.context.scene and hasattr(bpy.context.scene, "world"):
                root_candidates.append(("world", bpy.context.scene.world))

            # 選択されたオブジェクトも追加
            for i, obj in enumerate(bpy.context.selected_objects[:5]):  # 最大5個まで
                root_candidates.append((f"selected_object_{i}", obj))

            for root_name, root_obj in root_candidates:
                if root_obj is None:
                    continue

                log.debug(f"Trying to resolve path on {root_name}: {root_obj}")

                if self._try_resolve_nested_path(root_obj, path_parts, prop_index):
                    log.debug(f"Successfully resolved nested path on {root_name}")
                    return True

            log.warning(f"Could not resolve nested property path: {path}")
            return False

        except Exception as e:
            log.error(f"Failed to resolve nested property path '{path}': {e}")
            return False

    def _try_resolve_nested_path(self, root_obj, path_parts: list, prop_index: int):
        """ネストしたパスでプロパティ解決を試行"""
        try:
            # パスを順次辿る
            current_obj = root_obj

            for i, part in enumerate(path_parts):
                log.debug(f"Resolving path part {i}: '{part}' on {current_obj}")

                # プロパティが存在するかチェック
                if not hasattr(current_obj, part):
                    log.debug(f"Property '{part}' not found on {current_obj}")
                    return False

                # 最後のパートの場合、プロパティ定義をチェック
                if i == len(path_parts) - 1:
                    # 最終プロパティの定義を取得
                    prop_def = None
                    if hasattr(current_obj, "bl_rna") and hasattr(
                        current_obj.bl_rna, "properties"
                    ):
                        prop_def = current_obj.bl_rna.properties.get(part)

                    if not prop_def:
                        log.debug(f"Property definition not found for '{part}'")
                        return False

                    # 数値プロパティかチェック
                    if prop_def.type not in {"INT", "FLOAT"}:
                        log.debug(f"Property '{part}' is not numeric: {prop_def.type}")
                        return False

                    # PropertyInfoを作成
                    self.current_property = PropertyInfo(
                        ptr=current_obj,  # 最終的なプロパティを持つオブジェクト
                        prop=prop_def,
                        prop_index=prop_index,
                        sub_path="",
                        id_owner=root_obj,  # ルートオブジェクトをIDオーナーに
                    )

                    log.debug(
                        f"Nested property resolved: {'.'.join(path_parts)} on {root_obj}"
                    )
                    return True
                else:
                    # 中間パス - 次のオブジェクトに進む
                    current_obj = getattr(current_obj, part)
                    if current_obj is None:
                        log.debug(f"Intermediate path '{part}' returned None")
                        return False

            return False

        except Exception as e:
            log.debug(
                f"Failed to resolve nested path {'.'.join(path_parts)} on {root_obj}: {e}"
            )
            return False

    def _resolve_simple_property_path(self, prop_name: str, prop_index: int):
        """単純なプロパティパスを解決（従来の処理）"""
        try:
            # アクティブオブジェクトから開始して解決を試みる
            target_objects = []

            # 1. アクティブオブジェクト
            if bpy.context.active_object:
                target_objects.append(bpy.context.active_object)

            # 2. 選択されたオブジェクト
            target_objects.extend(bpy.context.selected_objects)

            # 3. シーン
            target_objects.append(bpy.context.scene)

            # 各候補でプロパティを探す
            for obj in target_objects:
                if self._try_resolve_property(obj, prop_name, prop_index):
                    log.debug(f"Successfully resolved simple property on {obj}")
                    return True

            log.warning(f"Could not resolve simple property path: {prop_name}")
            return False

        except Exception as e:
            log.error(f"Failed to resolve simple property path '{prop_name}': {e}")
            return False

    def _try_resolve_property(self, obj, prop_name: str, prop_index: int):
        """オブジェクトでプロパティの解決を試行"""
        try:
            # プロパティが存在するかチェック
            if not hasattr(obj, prop_name):
                return False

            # プロパティの定義を取得
            prop_def = None
            if hasattr(obj, "bl_rna") and hasattr(obj.bl_rna, "properties"):
                prop_def = obj.bl_rna.properties.get(prop_name)

            if not prop_def:
                return False

            # 数値プロパティかチェック
            if prop_def.type not in {"INT", "FLOAT"}:
                return False

            # PropertyInfoを作成
            self.current_property = PropertyInfo(
                ptr=obj,
                prop=prop_def,
                prop_index=prop_index,
                sub_path="",  # ルートオブジェクトなので空
                id_owner=obj,
            )

            log.debug(f"Property resolved: {prop_name} on {obj}")
            return True

        except Exception as e:
            log.debug(f"Failed to resolve property {prop_name} on {obj}: {e}")
            return False

    def write_value_to_property(self, value: Union[int, float]) -> bool:
        """プロパティに値を書き込み"""
        if not self.current_property:
            log.error("No property info available")
            return False

        try:
            prefs = self.get_preferences()

            # プロパティ制限のチェック
            if prefs and prefs.should_respect_limits():
                hard_min, hard_max = self.current_property.get_property_limits()
                if hard_min is not None and value < hard_min:
                    value = hard_min
                    log.debug(f"Value clamped to hard_min: {hard_min}")
                elif hard_max is not None and value > hard_max:
                    value = hard_max
                    log.debug(f"Value clamped to hard_max: {hard_max}")

            # 型変換
            if self.current_property.prop.type == "INT":
                value = int(round(value))

            # コンテナを解決
            try:
                # ネストしたパスの場合は ptr を直接使用
                # 単純なパスの場合は sub_path を使って解決
                if (
                    self.current_property.sub_path
                    and self.current_property.ptr == self.current_property.id_owner
                ):
                    # 単純なパス（従来の処理）
                    container = self.current_property.id_owner.path_resolve(
                        self.current_property.sub_path, False
                    )
                else:
                    # ネストしたパスまたは直接アクセス
                    container = self.current_property.ptr
            except Exception:
                log.warning("Path resolution failed, using original pointer")
                container = self.current_property.ptr

            # 値を書き込み
            prop_name = self.current_property.prop.identifier
            if self.current_property.prop_index != -1:
                # ベクタープロパティの場合
                vec = list(getattr(container, prop_name))
                vec[self.current_property.prop_index] = value
                setattr(container, prop_name, vec)
            else:
                # スカラープロパティの場合
                setattr(container, prop_name, value)

            # デプスグラフ更新でUI反映
            bpy.context.evaluated_depsgraph_get().update()

            # Undo履歴にプッシュ（値の変更が成功した場合のみ）
            try:
                bpy.ops.ed.undo_push(message=f"Calculator: Set {prop_name} to {value}")
                log.debug(f"Undo pushed for property change: {prop_name} = {value}")
            except Exception as e:
                log.warning(f"Failed to push undo: {e}")

            log.debug(f"Successfully wrote value {value} to property")
            return True

        except Exception as e:
            log.error(f"Failed to write value to property: {e}")
            return False

    def process_expression_for_property(self, expression: str) -> str:
        """プロパティの特性に応じて数式を前処理"""
        if not self.current_property:
            log.debug("No current property for expression processing")
            return expression

        prefs = self.get_preferences()
        log.debug(
            f"Angle conversion setting: {prefs.should_convert_angles() if prefs else 'No prefs'}"
        )

        if not prefs or not prefs.should_convert_angles():
            log.debug("Angle conversion disabled in preferences")
            return expression

        # 角度プロパティかどうかをチェック
        is_angle = self.current_property.is_angle_property()
        log.debug(
            f"Is angle property: {is_angle} (subtype: {getattr(self.current_property.prop, 'subtype', 'N/A')})"
        )

        # 角度プロパティの場合の自動変換
        if is_angle:
            # 数式に明示的にradians()やdegrees()が含まれていない場合
            has_angle_funcs = any(
                func in expression.lower() for func in ["radians", "degrees", "pi"]
            )
            log.debug(f"Expression has angle functions: {has_angle_funcs}")

            if not has_angle_funcs:
                # 度数法として解釈してラジアンに変換
                log.debug(
                    f"Auto-converting degrees to radians for angle property: {expression}"
                )
                return f"radians({expression})"

        return expression


# モジュールリロード時のクリーンアップ
def cleanup_on_reload():
    """モジュールリロード時に呼び出される"""
    CalculatorState.cleanup_on_reload()
