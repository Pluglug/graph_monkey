# Blender UI Scale and Line Width Implementation Analysis

## Overview
This analysis examines the implementation of UI scaling and line width in Blender 5.0.0-alpha (source code analyzed), focusing on how `ui_scale` and `line_width` affect area gap calculations.

## Key Findings

### 1. UI Scale Implementation (wm_window.cc:619-651)

The UI scale system uses a multi-layered approach:

```python
def calculate_ui_scale(auto_dpi, ui_scale, ui_line_width):
    """
    Based on source/blender/windowmanager/intern/wm_window.cc:619-651
    """
    # Initialize UI scale if not set
    if ui_scale == 0:
        virtual_pixel = 1  # or 2 for VIRTUAL_PIXEL_DOUBLE
        if dpi == 0:
            ui_scale = virtual_pixel
        else:
            ui_scale = (virtual_pixel * dpi * 96.0) / (auto_dpi * 72.0)
        ui_scale = max(0.25, min(4.0, ui_scale))  # Clamp to 0.25-4.0
    
    # Apply platform-specific scaling
    auto_dpi *= GHOST_GetNativePixelSize(window_handle)
    dpi = auto_dpi * ui_scale * (72.0 / 96.0)
    
    # Calculate pixel size for drawing
    pixelsize = max(1, int(dpi / 64))
    pixelsize = max(1, pixelsize + ui_line_width)
    
    # Calculate scale factor (main UI scaling multiplier)
    scale_factor = dpi / 72.0
    
    # Widget unit: 18 user-scaled units + 2 * pixelsize borders
    widget_unit = int(round(18.0 * scale_factor)) + (2 * pixelsize)
    
    return {
        'dpi': dpi,
        'pixelsize': pixelsize,
        'scale_factor': scale_factor,
        'widget_unit': widget_unit
    }
```

### 2. Line Width Settings (rna_userdef.cc:5078-5083)

Line width has three preset values:

```python
LINE_WIDTH_VALUES = {
    'THIN': -1,    # Thinner lines than default
    'AUTO': 0,     # Automatic line width based on UI scale
    'THICK': 1     # Thicker lines than default
}
```

### 3. Area Gap Calculation (screen_draw.cc:176 & screen_geometry.cc:176)

The area gap is calculated using the `border_width` preference:

```python
def calculate_area_gap(border_width, ui_scale_factor):
    """
    Based on source/blender/editors/screen/screen_draw.cc:176
    and source/blender/editors/screen/screen_geometry.cc:176
    """
    # UI_SCALE_FAC is defined as U.scale_factor in DNA_theme_types.h:17
    edge_thickness = float(border_width) * ui_scale_factor
    
    # Border width is also used for minimum area calculations
    border_width_pixels = int(ceil(float(border_width) * ui_scale_factor))
    
    return {
        'edge_thickness': edge_thickness,
        'border_width_pixels': border_width_pixels
    }
```

### 4. Complete Gap Calculation Function

```python
def calculate_blender_area_gap(ui_scale=1.0, ui_line_width=0, border_width=2, auto_dpi=96.0):
    """
    Complete implementation based on Blender 5.0.0-alpha source code
    
    Args:
        ui_scale: UI scale factor (0.25-4.0)
        ui_line_width: Line width setting (-1=THIN, 0=AUTO, 1=THICK)
        border_width: Border width preference (1-10)
        auto_dpi: System DPI
    
    Returns:
        Dictionary with calculated values
    """
    # Step 1: Calculate DPI and pixel size
    dpi = auto_dpi * ui_scale * (72.0 / 96.0)
    pixelsize = max(1, int(dpi / 64))
    pixelsize = max(1, pixelsize + ui_line_width)
    
    # Step 2: Calculate scale factor
    scale_factor = dpi / 72.0
    
    # Step 3: Calculate area gap
    edge_thickness = float(border_width) * scale_factor
    border_width_pixels = int(ceil(float(border_width) * scale_factor))
    
    # Step 4: Widget unit calculation
    widget_unit = int(round(18.0 * scale_factor)) + (2 * pixelsize)
    
    return {
        'dpi': dpi,
        'pixelsize': pixelsize,
        'scale_factor': scale_factor,
        'edge_thickness': edge_thickness,
        'border_width_pixels': border_width_pixels,
        'widget_unit': widget_unit,
        'area_gap': edge_thickness  # Main area gap value
    }

# Example usage:
result = calculate_blender_area_gap(ui_scale=1.5, ui_line_width=0, border_width=2, auto_dpi=96.0)
print(f"Area gap: {result['area_gap']:.2f} pixels")
```

## Key Implementation Details

### UI Scale Macro (DNA_theme_types.h:17)
```c
#define UI_SCALE_FAC ((void)0, U.scale_factor)
```

### Border Width Usage (screen_draw.cc:176)
```c
const float edge_thickness = float(U.border_width) * UI_SCALE_FAC;
```

### Platform-Specific Scaling (wm_window.cc:635)
```c
auto_dpi *= GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));
```

## Platform Differences

1. **Windows/Linux**: Uses standard DPI scaling with GHOST_GetNativePixelSize()
2. **macOS**: Additional native pixel size scaling applied
3. **Default GPU Backend**: Metal on macOS, OpenGL elsewhere

## Changed in Blender 5.0+

- Line width now directly affects `pixelsize` calculation
- UI scale clamped to 0.25-4.0 range (previously different limits)
- Widget unit calculation includes pixelsize borders
- Border width affects both drawing and minimum area calculations

## Critical Code Locations

- **UI Scale calculation**: `source/blender/windowmanager/intern/wm_window.cc:619-651`
- **Area gap drawing**: `source/blender/editors/screen/screen_draw.cc:176`
- **Area geometry**: `source/blender/editors/screen/screen_geometry.cc:176`
- **UI Scale macro**: `source/blender/makesdna/DNA_theme_types.h:17`
- **Line width enum**: `source/blender/makesrna/intern/rna_userdef.cc:5078-5083`

## Summary

The area gap between Blender editors is calculated as:
**Area Gap = border_width × scale_factor**

Where `scale_factor = (auto_dpi × ui_scale × 72.0/96.0) / 72.0`

This ensures consistent visual spacing across different DPI settings and UI scales.