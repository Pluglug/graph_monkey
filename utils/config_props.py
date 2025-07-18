# pyright: reportInvalidTypeForm=false
"""
Blender環境設定プロパティシステム

このモジュールは、Blenderの環境設定を管理するBoolPropertyの統一的な仕組みを提供します。

## 主な機能:
- 設定の状態取得と実行を統一管理
- エラーハンドリングとロギング
- メンテナンスしやすい設計
- 高度なパフォーマンス最適化

## パフォーマンス最適化機能:
- インテリジェントキャッシュ: 状態の重複取得を回避
- 遅延実行: UI応答性を保持しつつ設定を適用
- コンテキスト検証: 不正なスペースでの実行を防止
- バッチ処理: 複数設定の一括更新
- プロファイリング: パフォーマンス測定とレポート

## 使用方法:

### 1. 新しい設定の追加方法:

```python
# 1. 状態取得関数を定義
def get_my_setting_state():
    # 現在の設定状態を bool で返す
    return bpy.context.scene.my_setting

# 2. 設定適用関数を定義
def set_my_setting_state(enabled):
    # enabled (bool) を受け取って設定を適用
    bpy.context.scene.my_setting = enabled

# 3. BlenderConfigPropertyインスタンスを作成
MY_SETTING_CONFIG = BlenderConfigProperty(
    name="マイ設定",
    description="マイ設定の説明",
    get_func=get_my_setting_state,
    set_func=set_my_setting_state
)

# 4. BlenderConfigSettingsクラスにプロパティを追加
class BlenderConfigSettings(PropertyGroup):
    # 既存のプロパティ...
    my_setting: MY_SETTING_CONFIG.create_property()
```

### 2. 使用例:

```python
# Pythonコンソールまたはスクリプトから
settings = bpy.context.scene.monkey_blender_config

# 設定の読み取り
print(f"ソリッドビュー: {settings.solid_view}")

# 設定の変更（自動的に適用される）
settings.solid_view = True
```

### 3. UIでの使用:

```python
# パネルでの表示
def draw(self, context):
    layout = self.layout
    settings = context.scene.monkey_blender_config
    layout.prop(settings, "solid_view")

# パイメニューでの使用
bpy.ops.wm.call_menu_pie(name="MONKEY_MT_blender_config_pie")
```

### 4. テスト:

```python
# テストオペレータの実行
bpy.ops.monkey.test_blender_config()
```

## 現在実装されている設定:
- solid_view: ソリッドビュー表示
- render_view: レンダープレビュー表示
- wireframe_view: ワイヤーフレーム表示
- xray_display: X-Ray表示

## アーキテクチャ:
- BlenderConfigProperty: 設定プロパティの基底クラス
- BlenderConfigSettings: 全設定を管理するPropertyGroup
- MONKEY_MT_BlenderConfigPie: パイメニューUI
- MONKEY_OT_TestBlenderConfig: テスト用オペレータ
- PerformanceCache: インテリジェントキャッシュシステム
- ConfigProfiler: パフォーマンス測定システム
"""

from bpy.types import Menu, PropertyGroup, Operator
from bpy.props import BoolProperty
import bpy
import time
import threading
from collections import defaultdict, deque
from functools import wraps
from typing import Dict, Any, Callable, Optional, Tuple, TYPE_CHECKING

from ..utils.logging import get_logger
from ..utils.timer import timeout

if TYPE_CHECKING:
    from bpy.types import SpaceView3D

log = get_logger(__name__)


class PerformanceCache:
    """インテリジェントキャッシュシステム

    頻繁にアクセスされる設定値をキャッシュし、
    不要なBlender APIアクセスを削減します。
    """

    def __init__(self, ttl: float = 0.1, max_size: int = 100):
        """
        Args:
            ttl: キャッシュの生存時間（秒）
            max_size: 最大キャッシュサイズ
        """
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._access_order = deque()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """キャッシュからの値取得"""
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    # アクセス順序の更新（LRU）
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._access_order.append(key)
                    return value
                else:
                    # 期限切れエントリの削除
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
        return None

    def set(self, key: str, value: Any) -> None:
        """キャッシュへの値設定"""
        with self._lock:
            current_time = time.time()

            # サイズ制限のチェック
            if len(self._cache) >= self.max_size and key not in self._cache:
                # LRUに基づく古いエントリの削除
                oldest_key = self._access_order.popleft()
                if oldest_key in self._cache:
                    del self._cache[oldest_key]

            self._cache[key] = (value, current_time)

            # アクセス順序の更新
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    def invalidate(self, key: Optional[str] = None) -> None:
        """キャッシュの無効化"""
        with self._lock:
            if key is None:
                # 全キャッシュをクリア
                self._cache.clear()
                self._access_order.clear()
            elif key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)

    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計の取得"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "keys": list(self._cache.keys()),
            }


class ConfigProfiler:
    """パフォーマンス測定システム"""

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._lock = threading.RLock()

    def measure(self, operation_name: str):
        """デコレータ: 操作時間の測定"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    duration = end_time - start_time
                    with self._lock:
                        self.metrics[operation_name].append(duration)
                        if duration > 0.01:  # 10ms以上の処理を警告
                            log.warning(
                                f"遅い処理検出: {operation_name} took {duration:.3f}s"
                            )

            return wrapper

        return decorator

    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """統計情報の取得"""
        with self._lock:
            stats = {}
            for operation, times in self.metrics.items():
                if times:
                    stats[operation] = {
                        "count": len(times),
                        "avg": sum(times) / len(times),
                        "min": min(times),
                        "max": max(times),
                        "total": sum(times),
                    }
            return stats

    def reset(self):
        """統計のリセット"""
        with self._lock:
            self.metrics.clear()


# グローバルインスタンス
_performance_cache = PerformanceCache()
_profiler = ConfigProfiler()


def validate_viewport_context():
    """ビューポートコンテキストの検証"""
    context = bpy.context
    if not context.space_data:
        raise ValueError("有効なスペースデータがありません")

    space = context.space_data
    if not hasattr(space, "shading"):
        raise ValueError(f"サポートされていないスペースタイプ: {type(space).__name__}")

    return space  # type: ignore


class BlenderConfigProperty:
    """Blender環境設定を管理するBoolPropertyの基底クラス

    この仕組みにより：
    - 設定の状態と実行を統一的に管理
    - 新しい設定の追加が簡単
    - デバッグとロギングが統一
    - 高度なパフォーマンス最適化
    """

    def __init__(
        self,
        name: str,
        description: str,
        get_func: Callable,
        set_func: Callable,
        cache_enabled: bool = True,
        async_update: bool = False,
    ):
        """
        Args:
            name: プロパティ名
            description: プロパティの説明
            get_func: 現在の設定値を取得する関数
            set_func: 設定を適用する関数 (bool値を受け取る)
            cache_enabled: キャッシュを有効にするか
            async_update: 非同期更新を使用するか
        """
        self.name = name
        self.description = description
        self.get_func = get_func
        self.set_func = set_func
        self.cache_enabled = cache_enabled
        self.async_update = async_update
        self.cache_key = f"config_{name.lower().replace(' ', '_')}"

    def create_property(self):
        """BoolPropertyを生成する"""
        get_func = self.get_func
        set_func = self.set_func
        name = self.name
        cache_key = self.cache_key
        cache_enabled = self.cache_enabled
        async_update = self.async_update

        def getter(self):
            try:
                # キャッシュからの取得を試行
                if cache_enabled:
                    cached_value = _performance_cache.get(cache_key)
                    if cached_value is not None:
                        return cached_value

                # 実際の値を取得
                value = get_func()

                # キャッシュに保存
                if cache_enabled:
                    _performance_cache.set(cache_key, value)

                return value
            except Exception as e:
                log.error(f"設定取得エラー ({name}): {e}")
                return False

        def setter(self, value):
            try:
                # 現在値との比較（不要な更新を回避）
                current = getter(self)
                if current == value:
                    return

                # キャッシュの無効化
                if cache_enabled:
                    _performance_cache.invalidate(cache_key)

                if async_update:
                    # 非同期更新
                    def async_apply():
                        try:
                            set_func(value)
                            log.info(f"設定変更（非同期）: {name} = {value}")
                        except Exception as e:
                            log.error(f"非同期設定適用エラー ({name}): {e}")

                    timeout(async_apply)
                else:
                    # 同期更新
                    set_func(value)
                    log.info(f"設定変更: {name} = {value}")

            except Exception as e:
                log.error(f"設定適用エラー ({name}): {e}")

        return BoolProperty(
            name=self.name, description=self.description, get=getter, set=setter
        )


def get_solid_view_state():
    """ソリッドビューの状態を取得"""
    try:
        space = validate_viewport_context()
        return space.shading.type == "SOLID"  # type: ignore
    except Exception:
        return False


def set_solid_view_state(enabled):
    """ソリッドビューの設定"""
    try:
        space = validate_viewport_context()
        space.shading.type = "SOLID" if enabled else "WIREFRAME"  # type: ignore
    except Exception as e:
        log.error(f"ソリッドビュー設定エラー: {e}")


def get_render_view_state():
    """レンダービューの状態を取得"""
    try:
        space = validate_viewport_context()
        return space.shading.type == "RENDERED"  # type: ignore
    except Exception:
        return False


def set_render_view_state(enabled):
    """レンダービューの設定"""
    try:
        space = validate_viewport_context()
        space.shading.type = "RENDERED" if enabled else "SOLID"  # type: ignore
    except Exception as e:
        log.error(f"レンダービュー設定エラー: {e}")


def get_wireframe_state():
    """ワイヤーフレーム表示の状態を取得"""
    try:
        space = validate_viewport_context()
        return space.shading.type == "WIREFRAME"  # type: ignore
    except Exception:
        return False


def set_wireframe_state(enabled):
    """ワイヤーフレーム表示の設定"""
    try:
        space = validate_viewport_context()
        space.shading.type = "WIREFRAME" if enabled else "SOLID"  # type: ignore
    except Exception as e:
        log.error(f"ワイヤーフレーム設定エラー: {e}")


def get_xray_state():
    """X-Ray表示の状態を取得"""
    try:
        space = validate_viewport_context()
        return space.shading.show_xray  # type: ignore
    except Exception:
        return False


def set_xray_state(enabled):
    """X-Ray表示の設定"""
    try:
        space = validate_viewport_context()
        space.shading.show_xray = enabled  # type: ignore
    except Exception as e:
        log.error(f"X-Ray設定エラー: {e}")


# # 設定プロパティの定義（パフォーマンス最適化付き）
# SOLID_VIEW_CONFIG = BlenderConfigProperty(
#     name="ソリッドビュー",
#     description="ビューポートをソリッドシェーディングに設定",
#     get_func=get_solid_view_state,
#     set_func=set_solid_view_state,
#     cache_enabled=True,
#     async_update=False,
# )

# RENDER_VIEW_CONFIG = BlenderConfigProperty(
#     name="レンダービュー",
#     description="ビューポートをレンダープレビューに設定",
#     get_func=get_render_view_state,
#     set_func=set_render_view_state,
#     cache_enabled=True,
#     async_update=True,  # レンダービューは重い処理なので非同期
# )

# WIREFRAME_CONFIG = BlenderConfigProperty(
#     name="ワイヤーフレーム",
#     description="ビューポートをワイヤーフレーム表示に設定",
#     get_func=get_wireframe_state,
#     set_func=set_wireframe_state,
#     cache_enabled=True,
#     async_update=False,
# )

# XRAY_CONFIG = BlenderConfigProperty(
#     name="X-Ray表示",
#     description="オブジェクトのX-Ray表示を切り替え",
#     get_func=get_xray_state,
#     set_func=set_xray_state,
#     cache_enabled=True,
#     async_update=False,
# )


# class BlenderConfigSettings(PropertyGroup):
#     """Blender環境設定のPropertyGroup

#     新しい設定を追加する場合は：
#     1. 設定用の関数を定義 (get_xxx_state, set_xxx_state)
#     2. BlenderConfigPropertyインスタンスを作成
#     3. このクラスにプロパティを追加
#     """

#     # ビューポート設定（パフォーマンス最適化済み）
#     solid_view: SOLID_VIEW_CONFIG.create_property()
#     render_view: RENDER_VIEW_CONFIG.create_property()
#     wireframe_view: WIREFRAME_CONFIG.create_property()
#     xray_display: XRAY_CONFIG.create_property()

#     def batch_update(self, settings_dict: Dict[str, bool]):
#         """バッチ更新: 複数設定を効率的に更新"""
#         start_time = time.perf_counter()

#         # キャッシュを一時的に無効化
#         _performance_cache.invalidate()

#         try:
#             for setting_name, value in settings_dict.items():
#                 if hasattr(self, setting_name):
#                     setattr(self, setting_name, value)

#             duration = time.perf_counter() - start_time
#             log.info(f"バッチ更新完了: {len(settings_dict)}項目 in {duration:.3f}s")

#         except Exception as e:
#             log.error(f"バッチ更新エラー: {e}")

#     def draw(self, layout):
#         """UIの描画"""
#         box = layout.box()
#         box.label(text="ビューポート設定", icon="SHADING_RENDERED")

#         # パフォーマンス情報の表示
#         stats = _profiler.get_stats()
#         if stats:
#             perf_box = box.box()
#             perf_box.label(text="パフォーマンス情報", icon="EXPERIMENTAL")
#             for operation, metrics in stats.items():
#                 if metrics["count"] > 0:
#                     avg_ms = metrics["avg"] * 1000
#                     perf_box.label(text=f"{operation}: {avg_ms:.1f}ms (avg)")

#         # ビューモード設定
#         col = box.column(align=True)
#         col.label(text="表示モード:")
#         row = col.row(align=True)
#         row.prop(self, "solid_view", toggle=True)
#         row.prop(self, "render_view", toggle=True)
#         row.prop(self, "wireframe_view", toggle=True)

#         # 表示オプション
#         col.separator()
#         col.label(text="表示オプション:")
#         col.prop(self, "xray_display")

#         # キャッシュ情報
#         cache_stats = _performance_cache.get_stats()
#         col.separator()
#         col.label(text=f"キャッシュ: {cache_stats['size']}/{cache_stats['max_size']}")


# class MONKEY_OT_TestBlenderConfig(Operator):
#     """Blender設定テスト用オペレータ"""

#     bl_idname = "monkey.test_blender_config"
#     bl_label = "設定テスト"
#     bl_description = "Blender設定システムのテスト"
#     bl_options = {"REGISTER", "UNDO"}

#     def execute(self, context):
#         settings = getattr(context.scene, "monkey_blender_config", None)
#         if not settings:
#             self.report({"ERROR"}, "設定が見つかりません")
#             return {"CANCELLED"}

#         # パフォーマンス測定付きテスト
#         start_time = time.perf_counter()

#         # 現在の設定を表示
#         self.report(
#             {"INFO"},
#             f"現在の設定: ソリッド={settings.solid_view}, "
#             f"レンダー={settings.render_view}, "
#             f"ワイヤー={settings.wireframe_view}, "
#             f"X-Ray={settings.xray_display}",
#         )

#         # パフォーマンス統計の表示
#         stats = _profiler.get_stats()
#         if stats:
#             for operation, metrics in stats.items():
#                 avg_ms = metrics["avg"] * 1000
#                 self.report({"INFO"}, f"{operation}: {avg_ms:.1f}ms平均")

#         duration = time.perf_counter() - start_time
#         self.report({"INFO"}, f"テスト実行時間: {duration*1000:.1f}ms")

#         return {"FINISHED"}


# class MONKEY_OT_ClearPerformanceCache(Operator):
#     """パフォーマンスキャッシュクリア"""

#     bl_idname = "monkey.clear_performance_cache"
#     bl_label = "キャッシュクリア"
#     bl_description = "パフォーマンスキャッシュをクリアします"
#     bl_options = {"REGISTER"}

#     def execute(self, context):
#         _performance_cache.invalidate()
#         _profiler.reset()
#         self.report({"INFO"}, "キャッシュとプロファイラをリセットしました")
#         return {"FINISHED"}


# class MONKEY_MT_BlenderConfigPie(Menu):
#     """Blender設定用のパイメニュー"""

#     bl_idname = "MONKEY_MT_blender_config_pie"
#     bl_label = "Blender設定"

#     def draw(self, context):
#         layout = self.layout
#         pie = layout.menu_pie()  # type: ignore

#         # 設定への参照を取得
#         settings = getattr(context.scene, "monkey_blender_config", None)
#         if not settings:
#             pie.label(text="設定が利用できません")
#             return

#         # 左 - ソリッドビュー
#         pie.prop(settings, "solid_view", icon="SHADING_SOLID")

#         # 右 - レンダービュー
#         pie.prop(settings, "render_view", icon="SHADING_RENDERED")

#         # 下 - ワイヤーフレーム
#         pie.prop(settings, "wireframe_view", icon="SHADING_WIRE")

#         # 上 - X-Ray
#         pie.prop(settings, "xray_display", icon="XRAY")

#         # 左下 - テスト
#         pie.operator("monkey.test_blender_config", icon="CONSOLE")

#         # 右下 - キャッシュクリア
#         pie.operator("monkey.clear_performance_cache", icon="TRASH")

#         # その他のスペース
#         pie.separator()
#         pie.separator()


# from ..keymap_manager import keymap_registry, KeymapDefinition

# keymap_registry.register_keymap_group(
#     group_name="TEST",
#     keymaps=[
#         KeymapDefinition(
#             operator_id="wm.call_menu_pie",
#             key="W",
#             value="PRESS",
#             shift=1,
#             ctrl=1,
#             properties={"name": "MONKEY_MT_blender_config_pie"},
#             name="3D View",
#             space_type="VIEW_3D",
#             region_type="WINDOW",
#         ),
#     ],
# )


def register():
    # bpy.types.Scene.monkey_blender_config = bpy.props.PointerProperty(  # type: ignore
    #     type=BlenderConfigSettings
    # )


def unregister():
    # if hasattr(bpy.types.Scene, "monkey_blender_config"):
    #     del bpy.types.Scene.monkey_blender_config  # type: ignore

    # キャッシュのクリア
    _performance_cache.invalidate()
    _profiler.reset()
