from ...keymap_manager import KeymapDefinition, keymap_registry


calculator_keymaps = [
    KeymapDefinition(
        operator_id="wm.numeric_input",
        key="RIGHTMOUSE",
        value="PRESS",
        ctrl=True,
        properties={},
        name="User Interface",
        space_type="EMPTY",
        region_type="WINDOW",
        description="Open calculator with Ctrl+Right Click on numeric properties",
    ),
]


keymap_registry.register_keymap_group(
    "Calculator On Numeric Property Fields", calculator_keymaps
)
