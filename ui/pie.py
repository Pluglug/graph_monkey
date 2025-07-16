"""
Blender環境設定プロパティシステム

このモジュールは、Blenderの環境設定を管理するBoolPropertyの統一的な仕組みを提供します。

## 主な機能:
- 設定の状態取得と実行を統一管理
- エラーハンドリングとロギング
- メンテナンスしやすい設計

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
"""

from bpy.types import Menu, PropertyGroup, Operator
from bpy.props import BoolProperty
import bpy
from ..utils.logging import get_logger

log = get_logger(__name__)


class BlenderConfigProperty:
    """Blender環境設定を管理するBoolPropertyの基底クラス

    この仕組みにより：
    - 設定の状態と実行を統一的に管理
    - 新しい設定の追加が簡単
    - デバッグとロギングが統一
    """

    def __init__(self, name, description, get_func, set_func):
        """
        Args:
            name: プロパティ名
            description: プロパティの説明
            get_func: 現在の設定値を取得する関数
            set_func: 設定を適用する関数 (bool値を受け取る)
        """
        self.name = name
        self.description = description
        self.get_func = get_func
        self.set_func = set_func

    def create_property(self):
        """BoolPropertyを生成する"""
        get_func = self.get_func
        set_func = self.set_func
        name = self.name

        def getter(self):
            try:
                return get_func()
            except Exception as e:
                log.error(f"設定取得エラー ({name}): {e}")
                return False

        def setter(self, value):
            try:
                current = get_func()
                if current != value:
                    set_func(value)
                    log.info(f"設定変更: {name} = {value}")
            except Exception as e:
                log.error(f"設定適用エラー ({name}): {e}")

        return BoolProperty(
            name=self.name, description=self.description, get=getter, set=setter
        )


def get_solid_view_state():
    """ソリッドビューの状態を取得"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading") and hasattr(space.shading, "type"):
        return space.shading.type == "SOLID"
    return False


def set_solid_view_state(enabled):
    """ソリッドビューの設定"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading"):
        space.shading.type = "SOLID" if enabled else "WIREFRAME"


def get_render_view_state():
    """レンダービューの状態を取得"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading") and hasattr(space.shading, "type"):
        return space.shading.type == "RENDERED"
    return False


def set_render_view_state(enabled):
    """レンダービューの設定"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading"):
        space.shading.type = "RENDERED" if enabled else "SOLID"


def get_wireframe_state():
    """ワイヤーフレーム表示の状態を取得"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading") and hasattr(space.shading, "type"):
        return space.shading.type == "WIREFRAME"
    return False


def set_wireframe_state(enabled):
    """ワイヤーフレーム表示の設定"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading"):
        space.shading.type = "WIREFRAME" if enabled else "SOLID"


def get_xray_state():
    """X-Ray表示の状態を取得"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading") and hasattr(space.shading, "show_xray"):
        return space.shading.show_xray
    return False


def set_xray_state(enabled):
    """X-Ray表示の設定"""
    context = bpy.context
    space = context.space_data
    if hasattr(space, "shading"):
        space.shading.show_xray = enabled


# 設定プロパティの定義
SOLID_VIEW_CONFIG = BlenderConfigProperty(
    name="ソリッドビュー",
    description="ビューポートをソリッドシェーディングに設定",
    get_func=get_solid_view_state,
    set_func=set_solid_view_state,
)

RENDER_VIEW_CONFIG = BlenderConfigProperty(
    name="レンダービュー",
    description="ビューポートをレンダープレビューに設定",
    get_func=get_render_view_state,
    set_func=set_render_view_state,
)

WIREFRAME_CONFIG = BlenderConfigProperty(
    name="ワイヤーフレーム",
    description="ビューポートをワイヤーフレーム表示に設定",
    get_func=get_wireframe_state,
    set_func=set_wireframe_state,
)

XRAY_CONFIG = BlenderConfigProperty(
    name="X-Ray表示",
    description="オブジェクトのX-Ray表示を切り替え",
    get_func=get_xray_state,
    set_func=set_xray_state,
)


class BlenderConfigSettings(PropertyGroup):
    """Blender環境設定のPropertyGroup

    新しい設定を追加する場合は：
    1. 設定用の関数を定義 (get_xxx_state, set_xxx_state)
    2. BlenderConfigPropertyインスタンスを作成
    3. このクラスにプロパティを追加
    """

    # ビューポート設定
    solid_view: SOLID_VIEW_CONFIG.create_property()
    render_view: RENDER_VIEW_CONFIG.create_property()
    wireframe_view: WIREFRAME_CONFIG.create_property()
    xray_display: XRAY_CONFIG.create_property()

    def draw(self, layout):
        """UIの描画"""
        box = layout.box()
        box.label(text="ビューポート設定", icon="SHADING_RENDERED")

        # ビューモード設定
        col = box.column(align=True)
        col.label(text="表示モード:")
        row = col.row(align=True)
        row.prop(self, "solid_view", toggle=True)
        row.prop(self, "render_view", toggle=True)
        row.prop(self, "wireframe_view", toggle=True)

        # 表示オプション
        col.separator()
        col.label(text="表示オプション:")
        col.prop(self, "xray_display")


class MONKEY_OT_TestBlenderConfig(Operator):
    """Blender設定テスト用オペレータ"""

    bl_idname = "monkey.test_blender_config"
    bl_label = "設定テスト"
    bl_description = "Blender設定システムのテスト"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.monkey_blender_config

        # 現在の設定を表示
        self.report(
            {"INFO"},
            f"現在の設定: ソリッド={settings.solid_view}, "
            f"レンダー={settings.render_view}, "
            f"ワイヤー={settings.wireframe_view}, "
            f"X-Ray={settings.xray_display}",
        )

        return {"FINISHED"}


class MONKEY_MT_BlenderConfigPie(Menu):
    """Blender設定用のパイメニュー"""

    bl_idname = "MONKEY_MT_blender_config_pie"
    bl_label = "Blender設定"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        # 設定への参照を取得
        settings = getattr(context.scene, "monkey_blender_config", None)
        if not settings:
            pie.label(text="設定が利用できません")
            return

        # 左 - ソリッドビュー
        pie.prop(settings, "solid_view", icon="SHADING_SOLID")

        # 右 - レンダービュー
        pie.prop(settings, "render_view", icon="SHADING_RENDERED")

        # 下 - ワイヤーフレーム
        pie.prop(settings, "wireframe_view", icon="SHADING_WIRE")

        # 上 - X-Ray
        pie.prop(settings, "xray_display", icon="XRAY")

        # 左下 - テスト
        pie.operator("monkey.test_blender_config", icon="CONSOLE")

        # その他のスペース
        pie.separator()
        pie.separator()
        pie.separator()


from ..keymap_manager import keymap_registry, KeymapDefinition

keymap_registry.register_keymap_group(
    group_name="TEST",
    keymaps=[
        KeymapDefinition(
            operator_id="wm.call_menu_pie",
            key="W",
            value="PRESS",
            shift=1,
            ctrl=1,
            properties={"name": "MONKEY_MT_blender_config_pie"},
            name="3D View",
            space_type="VIEW_3D",
            region_type="WINDOW",
        ),
    ],
)


def register():
    bpy.types.Scene.monkey_blender_config = bpy.props.PointerProperty(
        type=BlenderConfigSettings
    )


def unregister():
    if hasattr(bpy.types.Scene, "monkey_blender_config"):
        del bpy.types.Scene.monkey_blender_config
