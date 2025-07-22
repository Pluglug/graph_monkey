"""
電卓機能のキーマップ定義

ホットキーで直接電卓を起動できます。
"""

from ...keymap_manager import KeymapDefinition, keymap_registry


# 電卓起動のキーマップ定義
calculator_keymaps = [
    # マウス右クリック + Alt で電卓起動（プロパティフィールド上で）
    KeymapDefinition(
        operator_id="wm.numeric_input",
        key="RIGHTMOUSE",
        value="PRESS",
        ctrl=True,
        shift=True,
        properties={},
        name="User Interface",
        space_type="EMPTY",
        region_type="WINDOW",
        description="Open calculator with Ctrl+Right Click on numeric properties",
    ),
    # # Numpad Enter で電卓起動（任意の場所で）
    # KeymapDefinition(
    #     operator_id="wm.numeric_input",
    #     key="NUMPAD_ENTER",
    #     value="PRESS",
    #     shift=True,
    #     properties={},
    #     name="Screen",
    #     space_type="EMPTY",
    #     region_type="WINDOW",
    #     description="Open calculator with Shift+Numpad Enter",
    # ),
    # # F12キー で電卓起動（代替ホットキー）
    # KeymapDefinition(
    #     operator_id="wm.numeric_input",
    #     key="F12",
    #     value="PRESS",
    #     ctrl=True,
    #     properties={},
    #     name="Screen",
    #     space_type="EMPTY",
    #     region_type="WINDOW",
    #     description="Open calculator with Ctrl+F12",
    # ),
]


keymap_registry.register_keymap_group("Calculator Hotkeys", calculator_keymaps)
