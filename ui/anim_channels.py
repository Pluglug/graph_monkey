from ..keymap_manager import keymap_registry, KeymapDefinition


keymap_registry.register_keymap_group(
    group_name="Graph Pie",
    keymaps=[
        KeymapDefinition(
            operator_id="anim.channels_expand",
            key="A",
            value="PRESS",
            shift=1,
            properties={"all": True},
            name="Animation Channels",
            space_type="EMPTY",
            region_type="WINDOW",
            repeat=True,
        ),
    ],
)

keymap_registry.register_keymap_group(
    group_name="Graph Pie",
    keymaps=[
        KeymapDefinition(
            operator_id="anim.channels_collapse",
            key="A",
            value="PRESS",
            ctrl=1,
            shift=1,
            properties={"all": True},
            name="Animation Channels",
            space_type="EMPTY",
            region_type="WINDOW",
            repeat=True,
        ),
    ],
)
