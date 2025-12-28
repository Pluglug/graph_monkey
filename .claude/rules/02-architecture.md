# Module Loading System

The addon uses an **automatic dependency-resolving module loader** in `addon.py`:

1. **Pattern-based discovery**: Modules matching patterns in `__init__.py` are collected
2. **AST-based dependency analysis**: Import statements are parsed to detect dependencies
3. **Topological sorting**: Kahn's algorithm determines load order
4. **Automatic class registration**: All `bpy.types.bpy_struct` subclasses are registered in dependency order

```python
# __init__.py configures which modules to load
addon.init_addon(
    module_patterns=[
        "constants",
        "preferences",
        "keymap_manager",
        "operators.*",
        "ui.*",
        "utils.*",
    ],
    use_reload=use_reload,
)
```

## Key Implication

**No manual `register_class()` calls needed** - place your module in the right directory, follow naming conventions, and the framework handles registration automatically.

## Dependencies

For non-obvious dependencies, add module-level `DEPENDS_ON` list:

```python
DEPENDS_ON = ["utils.some_utility"]
```

Use `TYPE_CHECKING` for import-only type hints to avoid circular imports:

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .some_module import SomeType
```
