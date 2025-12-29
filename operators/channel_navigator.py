# pyright: reportInvalidTypeForm=false
"""
Channel Navigator for Graph Editor

Grease Pencil Tools の layer_navigator.py を参考に、
Graph Editor のチャンネル（FCurve）をポップアップUIで操作できるようにする。

機能:
- チャンネル一覧表示（visible_fcurves + hide=True）
- マウスオーバーで選択切り替え（layer_navigatorスタイル）
- Ctrl+クリックでSolo（Hide方式）、再度Ctrlクリックで解除
- Hide/Lock/Muteトグル
- キーボードショートカット（H/L/M）
- キーフレーム選択の転送
"""

import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from bpy.props import IntProperty
from pathlib import Path

from ..addon import get_prefs
from ..keymap_manager import KeymapDefinition, keymap_registry
from ..utils.logging import get_logger
from .channel_selection_overlay import gen_channel_info_line, get_fcurve_display_color
from .dopesheet_helper import get_selected_keyframes

log = get_logger(__name__)

# Icon cache
_icon_cache = {}


def get_icon(img_name):
    """Load and cache icon image"""
    store_name = '.monkey_nav_' + img_name
    
    if store_name in _icon_cache:
        img = _icon_cache[store_name]
        if img and img.name in bpy.data.images:
            return img
    
    img = bpy.data.images.get(store_name)
    if not img:
        icon_folder = Path(__file__).parent.parent / 'icons'
        icon_path = (icon_folder / img_name).with_suffix('.png')
        if icon_path.exists():
            img = bpy.data.images.load(filepath=str(icon_path), check_existing=False)
            img.name = store_name
        else:
            log.warning(f"Icon not found: {icon_path}")
            return None
    
    _icon_cache[store_name] = img
    return img


def get_fcurves_for_navigator(context):
    """
    visible_fcurves + hide=TrueのFカーブを取得
    dopesheetフィルタは維持しつつ、hideされたものも含める
    """
    visible = list(context.visible_fcurves) if context.visible_fcurves else []
    visible_set = set(visible)
    
    # 現在のオブジェクトのアクションからhide=TrueのFカーブを追加
    obj = context.object
    if obj and obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            if fc.hide and fc not in visible_set:
                visible.append(fc)
    
    return visible


def rectangle_tris_from_coords(quad_list):
    """Get a list of Vector corner for a triangle
    return a list of TRI for gpu drawing"""
    return [
        # tri 1
        quad_list[0],
        quad_list[1],
        quad_list[2],
        # tri 2
        quad_list[0],
        quad_list[3],
        quad_list[2],
    ]


def round_to_ceil_even(f):
    import math

    if math.floor(f) % 2 == 0:
        return math.floor(f)
    else:
        return math.floor(f) + 1


class GRAPH_OT_channel_navigator(bpy.types.Operator):
    """Navigate and manage FCurve channels with a viewport interactive OSD"""

    bl_idname = "graph.channel_navigator"
    bl_label = "Channel Navigator"
    bl_description = "Navigate FCurve channels with an interactive popup"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    @classmethod
    def poll(cls, context):
        return (
            context.area is not None
            and context.area.type == "GRAPH_EDITOR"
            and (context.visible_fcurves or 
                 (context.object and context.object.animation_data and 
                  context.object.animation_data.action))
        )

    # --- Colors (alpha will be overridden by settings) ---
    lines_color = (0.5, 0.5, 0.5, 1.0)
    active_channel_color = (0.28, 0.45, 0.7, 1.0)  # Blue (active color)
    text_color = (0.8, 0.8, 0.8, 1.0)
    muted_text_color = (0.5, 0.5, 0.5, 1.0)
    hidden_text_color = (0.4, 0.4, 0.4, 1.0)

    def invoke(self, context, event):
        self.fcurves = get_fcurves_for_navigator(context)
        if not self.fcurves:
            self.report({"WARNING"}, "No fcurves found")
            return {"CANCELLED"}

        self.key = event.type
        self.mouse = self.init_mouse = Vector((event.mouse_region_x, event.mouse_region_y))

        # UI Scaling
        ui_scale = context.preferences.system.ui_scale
        prefs = get_prefs(context)
        nav_prefs = prefs.channel_navigator

        self.px_h = int(nav_prefs.box_height * ui_scale)
        self.px_w = int(nav_prefs.box_width * ui_scale)
        self.text_size = int(nav_prefs.text_size * ui_scale)
        self.max_display = nav_prefs.max_display_count
        self.icon_margin = int(20 * ui_scale)
        self.icon_size = int(14 * ui_scale)
        self.color_bar_width = int(6 * ui_scale)
        self.bg_alpha = nav_prefs.bg_alpha

        # Load icons
        self.icon_tex = {
            'hide_on': get_icon('hide_on'),
            'hide_off': get_icon('hide_off'),
            'lock_on': get_icon('lock_on'),
            'lock_off': get_icon('lock_off'),
            'mute_on': get_icon('mute_on'),
            'mute_off': get_icon('mute_off'),
        }
        self.icon_tex_coord = [
            Vector((0, 0)),
            Vector((self.icon_size, 0)),
            Vector((self.icon_size, self.icon_size)),
            Vector((0, self.icon_size)),
        ]

        # State
        self.scroll_offset = 0
        self.current_idx = None  # Currently hovered/active index
        self.dragging = False
        self.drag_mode = None  # 'hide', 'lock', 'mute', None
        self.pressed = False

        # Store original state for cancel
        self.original_selection = {fc: fc.select for fc in self.fcurves}
        self.original_hide = {fc: fc.hide for fc in self.fcurves}
        self.original_keyframe_selection = self._store_keyframe_selection()

        # Find current active index (first selected fcurve)
        self.org_idx = self._find_active_index()
        self.current_idx = self.org_idx

        self.setup(context)

        self.current_area = context.area
        self._handle = bpy.types.SpaceGraphEditor.draw_handler_add(
            self._draw_callback, (context,), "WINDOW", "POST_PIXEL"
        )

        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {"RUNNING_MODAL"}

    def _find_active_index(self):
        """Find index of currently selected (active) fcurve"""
        for i, fc in enumerate(self.fcurves):
            if fc.select:
                return i
        return 0

    def _store_keyframe_selection(self):
        """Store keyframe selection state for all fcurves"""
        state = {}
        for fc in self.fcurves:
            kf_states = []
            for kf in fc.keyframe_points:
                kf_states.append({
                    "control": kf.select_control_point,
                    "left": kf.select_left_handle,
                    "right": kf.select_right_handle,
                })
            state[fc] = kf_states
        return state

    def _transfer_keyframe_selection(self, from_fc, to_fc):
        """Transfer keyframe selection from one fcurve to another"""
        if from_fc == to_fc:
            return
        
        selected = get_selected_keyframes(from_fc.keyframe_points)
        if not selected:
            return
        
        # Deselect source fcurve
        from_fc.select = False
        for kf in from_fc.keyframe_points:
            kf.select_control_point = False
            kf.select_left_handle = False
            kf.select_right_handle = False
        
        # Select target fcurve
        to_fc.select = True
        
        # Transfer keyframe selection to nearest keyframes
        for item in selected:
            src_frame = item["keyframe"].co[0]
            # Find nearest keyframe in target
            if to_fc.keyframe_points:
                target_kf = min(
                    to_fc.keyframe_points,
                    key=lambda k: abs(k.co[0] - src_frame)
                )
                target_kf.select_control_point = item["control_point"]
                if item["left_handle"]:
                    target_kf.select_left_handle = True
                if item["right_handle"]:
                    target_kf.select_right_handle = True

    def setup(self, context):
        """Setup UI layout"""
        ui_scale = context.preferences.system.ui_scale

        # Calculate display count
        self.display_count = min(len(self.fcurves), self.max_display)

        # Calculate total height
        total_height = self.px_h * self.display_count

        # Position popup so that the current channel is at the mouse cursor
        # current_idx is the fcurve list index, we need to calculate its display position
        # Display is bottom-to-top, so display_idx = display_count - 1 - (fcurve_idx - scroll_offset)
        
        # First, determine scroll_offset so current channel is visible
        if self.org_idx is not None:
            # Try to center the current channel in the display
            half_display = self.display_count // 2
            self.scroll_offset = max(0, self.org_idx - half_display)
            max_scroll = max(0, len(self.fcurves) - self.display_count)
            self.scroll_offset = min(self.scroll_offset, max_scroll)
            
            # Calculate display position of current channel
            display_idx = self.display_count - 1 - (self.org_idx - self.scroll_offset)
            display_idx = max(0, min(display_idx, self.display_count - 1))
            
            # Position so this display_idx is at mouse Y
            # y_of_channel_center = bottom + display_idx * px_h + px_h/2
            # We want: y_of_channel_center = mouse.y
            # So: bottom = mouse.y - display_idx * px_h - px_h/2
            self.bottom = int(self.init_mouse.y - display_idx * self.px_h - self.px_h / 2)
        else:
            self.bottom = int(self.init_mouse.y - total_height / 2)
        
        self.left = int(self.init_mouse.x - self.px_w / 2)

        # Clamp to region bounds
        region_w, region_h = context.region.width, context.region.height
        margin = int(10 * ui_scale)

        if self.left < margin:
            self.left = margin
        if self.left + self.px_w > region_w - margin:
            self.left = region_w - margin - self.px_w

        if self.bottom < margin:
            self.bottom = margin
        if self.bottom + total_height > region_h - margin:
            self.bottom = region_h - margin - total_height

        self.right = self.left + self.px_w
        self.top = self.bottom + total_height

        # Pre-calculate box template
        self.case = [
            Vector((0, 0)),
            Vector((0, self.px_h)),
            Vector((self.px_w, self.px_h)),
            Vector((self.px_w, 0)),
        ]

        # Calculate click zones for icons (right side)
        # Layout: [color_bar][text...][mute][lock][hide]
        self.hide_zone_x = self.right - self.icon_margin
        self.lock_zone_x = self.right - self.icon_margin * 2
        self.mute_zone_x = self.right - self.icon_margin * 3

        # Text position
        self.text_x = self.left + self.color_bar_width + int(8 * ui_scale)

        # Build static line batch
        lines = []
        for i in range(self.display_count + 1):
            y = self.bottom + i * self.px_h
            lines += [(self.left, y), (self.right, y)]
        # Vertical lines
        lines += [
            (self.left, self.bottom),
            (self.left, self.top),
            (self.right, self.bottom),
            (self.right, self.top),
        ]

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        self.batch_lines = batch_for_shader(shader, "LINES", {"pos": lines})

        # Scroll indicator setup
        self.needs_scroll = len(self.fcurves) > self.max_display

    def modal(self, context, event):
        context.area.tag_redraw()
        self.mouse = Vector((event.mouse_region_x, event.mouse_region_y))

        # Cancel
        if event.type in {"RIGHTMOUSE", "ESC"}:
            self._restore_original_state()
            self.stop_mod(context)
            return {"CANCELLED"}

        # Confirm on key release
        if event.type == self.key and event.value == "RELEASE":
            self._apply_focus(context)
            self.stop_mod(context)
            return {"FINISHED"}

        # Scroll handling
        if event.type == "WHEELUPMOUSE" and self.needs_scroll:
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif event.type == "WHEELDOWNMOUSE" and self.needs_scroll:
            max_scroll = len(self.fcurves) - self.display_count
            self.scroll_offset = min(max_scroll, self.scroll_offset + 1)

        # Get hovered display index
        hovered_display_idx = self._get_hovered_display_idx()

        # Keyboard shortcuts for current selection
        if event.type == "H" and event.value == "PRESS":
            self._toggle_property_for_current("hide")
        elif event.type == "L" and event.value == "PRESS":
            self._toggle_property_for_current("lock")
        elif event.type == "M" and event.value == "PRESS":
            self._toggle_property_for_current("mute")

        # Mouse click for icon toggles and solo
        if event.type == "LEFTMOUSE":
            if event.value == "PRESS":
                self.pressed = True
                self._handle_click(context, event, hovered_display_idx)
            elif event.value == "RELEASE":
                self.pressed = False
                self.dragging = False
                self.drag_mode = None

        # Drag for batch toggle
        if self.pressed and self.dragging and self.drag_mode and hovered_display_idx is not None:
            fc = self._get_fcurve_at_display_idx(hovered_display_idx)
            if fc:
                self._apply_drag_toggle(fc)

        # Mouse-over selection (like layer_navigator)
        # Only change selection if mouse is in the list area (not on icons)
        if hovered_display_idx is not None and not self.dragging:
            # Check if mouse is in text area (not icon area)
            if self.mouse.x < self.mute_zone_x:
                new_idx = self._display_idx_to_fcurve_idx(hovered_display_idx)
                if new_idx is not None and new_idx != self.current_idx:
                    self._change_channel(new_idx)

        return {"RUNNING_MODAL"}

    def _get_hovered_display_idx(self):
        """Get which display index is being hovered (or None)"""
        if not (self.left <= self.mouse.x <= self.right):
            return None
        if not (self.bottom <= self.mouse.y <= self.top):
            return None

        # Calculate display index from bottom
        rel_y = self.mouse.y - self.bottom
        display_idx = int(rel_y // self.px_h)

        if 0 <= display_idx < self.display_count:
            return display_idx
        return None

    def _get_fcurve_at_display_idx(self, display_idx):
        """Get fcurve at display index (accounting for scroll)"""
        # Display is bottom-to-top, fcurves list is top-to-bottom
        actual_idx = self.scroll_offset + (self.display_count - 1 - display_idx)
        if 0 <= actual_idx < len(self.fcurves):
            return self.fcurves[actual_idx]
        return None

    def _display_idx_to_fcurve_idx(self, display_idx):
        """Convert display index to fcurve list index"""
        actual_idx = self.scroll_offset + (self.display_count - 1 - display_idx)
        if 0 <= actual_idx < len(self.fcurves):
            return actual_idx
        return None

    def _change_channel(self, new_idx):
        """Change to a new channel with keyframe selection transfer"""
        if new_idx == self.current_idx:
            return
        if new_idx < 0 or new_idx >= len(self.fcurves):
            return

        from_fc = self.fcurves[self.current_idx] if self.current_idx is not None else None
        to_fc = self.fcurves[new_idx]

        # Transfer keyframe selection
        if from_fc and from_fc != to_fc:
            self._transfer_keyframe_selection(from_fc, to_fc)
        else:
            # Just select the new channel
            for fc in self.fcurves:
                fc.select = (fc == to_fc)
            to_fc.select = True

        self.current_idx = new_idx
        log.debug(f"Changed to channel {new_idx}: {to_fc.data_path}")

    def _handle_click(self, context, event, hovered_display_idx):
        """Handle mouse click for icons and solo"""
        if hovered_display_idx is None:
            return

        fc = self._get_fcurve_at_display_idx(hovered_display_idx)
        if not fc:
            return

        # Check if clicking on icon zones
        if self.mouse.x >= self.hide_zone_x:
            # Hide toggle
            fc.hide = not fc.hide
            self.dragging = True
            self.drag_mode = "hide"
            self._drag_value = fc.hide
            return
        elif self.mouse.x >= self.lock_zone_x:
            # Lock toggle
            fc.lock = not fc.lock
            self.dragging = True
            self.drag_mode = "lock"
            self._drag_value = fc.lock
            return
        elif self.mouse.x >= self.mute_zone_x:
            # Mute toggle
            fc.mute = not fc.mute
            self.dragging = True
            self.drag_mode = "mute"
            self._drag_value = fc.mute
            return

        # Solo handling (Ctrl+click)
        if event.ctrl:
            self._solo_channel(fc)

    def _apply_drag_toggle(self, fc):
        """Apply toggle value when dragging over channels"""
        if self.drag_mode == "hide":
            fc.hide = self._drag_value
        elif self.drag_mode == "lock":
            fc.lock = self._drag_value
        elif self.drag_mode == "mute":
            fc.mute = self._drag_value

    def _toggle_property_for_current(self, prop_name):
        """Toggle property for current channel"""
        if self.current_idx is None:
            return
        fc = self.fcurves[self.current_idx]
        current_value = getattr(fc, prop_name)
        setattr(fc, prop_name, not current_value)

    def _solo_channel(self, target_fc):
        """Solo a single channel (hide others), or unsolo if already solo"""
        # Check if target is already solo (only one visible)
        visible_count = sum(1 for fc in self.fcurves if not fc.hide)
        is_solo = (visible_count == 1 and not target_fc.hide)
        
        if is_solo:
            # Unsolo: restore all to visible (unhide all)
            for fc in self.fcurves:
                fc.hide = False
            log.debug("Unsolo: all channels visible")
        else:
            # Solo: hide all except target
            for fc in self.fcurves:
                fc.hide = (fc != target_fc)
            log.debug(f"Solo: {target_fc.data_path}")
        
        # Also select the target
        for fc in self.fcurves:
            fc.select = (fc == target_fc)
        self.current_idx = self.fcurves.index(target_fc)

    def _restore_original_state(self):
        """Restore original selection, hide, and keyframe selection state on cancel"""
        # Restore fcurve selection and hide
        for fc, was_selected in self.original_selection.items():
            fc.select = was_selected
        for fc, was_hidden in self.original_hide.items():
            fc.hide = was_hidden
        
        # Restore keyframe selection
        for fc, kf_states in self.original_keyframe_selection.items():
            for i, state in enumerate(kf_states):
                if i < len(fc.keyframe_points):
                    kf = fc.keyframe_points[i]
                    kf.select_control_point = state["control"]
                    kf.select_left_handle = state["left"]
                    kf.select_right_handle = state["right"]

    def _apply_focus(self, context):
        """Apply focus to selected curves if enabled
        
        Focus logic:
        - If 2+ keyframes are selected at different frames -> focus on that range
        - If 0-1 keyframes selected or all at same frame -> focus on playback range
        """
        prefs = get_prefs(context)
        if not prefs.auto_focus_on_channel_change:
            return

        # Check if we have selected curves with keyframes
        selected_fcurves = [fc for fc in self.fcurves if fc.select and not fc.hide]
        if not selected_fcurves:
            return

        # Determine if we should use frame range or keyframe range
        # Count selected keyframes across all selected curves
        selected_keyframe_frames = []
        for fc in selected_fcurves:
            for kf in fc.keyframe_points:
                if kf.select_control_point:
                    selected_keyframe_frames.append(kf.co[0])

        # Use frame range if 0-1 unique frames selected
        unique_frames = set(selected_keyframe_frames)
        use_frame_range = len(unique_frames) < 2

        log.debug(f"Focus: {len(unique_frames)} unique frames, use_frame_range={use_frame_range}")

        try:
            bpy.ops.graph.view_selected_curves_range(
                include_handles=True, use_frame_range=use_frame_range
            )
        except Exception as e:
            log.warning(f"Failed to focus: {e}")

    def _draw_callback(self, context):
        """Draw the navigator UI"""
        if context.area != self.current_area:
            return

        font_id = 0
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        gpu.state.blend_set("ALPHA")
        gpu.state.line_width_set(1.0)

        shader.bind()

        normal_rects = []
        hidden_rects = []
        muted_rects = []
        color_bars = []
        active_case = []

        active_width = float(round_to_ceil_even(4.0 * context.preferences.system.ui_scale))

        # Build rectangles for each displayed fcurve
        for display_idx in range(self.display_count):
            fc = self._get_fcurve_at_display_idx(display_idx)
            if not fc:
                continue

            fcurve_idx = self._display_idx_to_fcurve_idx(display_idx)
            is_current = (fcurve_idx == self.current_idx)

            corner = Vector((self.left, self.bottom + self.px_h * display_idx))
            case_coords = [v + corner for v in self.case]

            # Color bar on left (dimmed if hidden/muted)
            alpha = 0.3 if (fc.hide or fc.mute) else 0.9
            fc_color = get_fcurve_display_color(fc, alpha=alpha)
            color_bar = [
                corner,
                corner + Vector((0, self.px_h)),
                corner + Vector((self.color_bar_width, self.px_h)),
                corner + Vector((self.color_bar_width, 0)),
            ]
            color_bars.append((rectangle_tris_from_coords(color_bar), fc_color))

            # Background based on state (all use self.bg_alpha)
            if fc.mute:
                muted_rects += rectangle_tris_from_coords(case_coords)
            elif fc.hide:
                hidden_rects += rectangle_tris_from_coords(case_coords)
            else:
                normal_rects += rectangle_tris_from_coords(case_coords)

            # Current channel border (the one mouse is over / selected)
            if is_current:
                px_offset = int(active_width / 2)
                border_points = [
                    corner + Vector((px_offset, 0)),
                    corner + Vector((self.px_w - px_offset, 0)),
                    corner + Vector((self.px_w, px_offset)),
                    corner + Vector((self.px_w, self.px_h - px_offset)),
                    corner + Vector((self.px_w - px_offset, self.px_h)),
                    corner + Vector((px_offset, self.px_h)),
                    corner + Vector((0, self.px_h - px_offset)),
                    corner + Vector((0, px_offset)),
                ]
                active_case = []
                for i in range(len(border_points)):
                    active_case += [border_points[i], border_points[(i + 1) % len(border_points)]]

        # Define colors with user-configured alpha
        bg_color = (0.1, 0.1, 0.1, self.bg_alpha)
        hidden_bg_color = (0.08, 0.08, 0.08, self.bg_alpha)
        muted_bg_color = (0.05, 0.05, 0.05, min(1.0, self.bg_alpha + 0.02))

        # Draw backgrounds
        shader.uniform_float("color", bg_color)
        batch_bg = batch_for_shader(shader, "TRIS", {"pos": normal_rects})
        batch_bg.draw(shader)

        shader.uniform_float("color", hidden_bg_color)
        batch_hidden = batch_for_shader(shader, "TRIS", {"pos": hidden_rects})
        batch_hidden.draw(shader)

        shader.uniform_float("color", muted_bg_color)
        batch_muted = batch_for_shader(shader, "TRIS", {"pos": muted_rects})
        batch_muted.draw(shader)

        # Draw color bars
        for bar_coords, bar_color in color_bars:
            shader.uniform_float("color", bar_color)
            batch_bar = batch_for_shader(shader, "TRIS", {"pos": bar_coords})
            batch_bar.draw(shader)

        # Draw lines
        gpu.state.line_width_set(2.0)
        shader.uniform_float("color", self.lines_color)
        self.batch_lines.draw(shader)

        # Draw active border
        if active_case:
            gpu.state.line_width_set(active_width)
            shader.uniform_float("color", self.active_channel_color)
            batch_active = batch_for_shader(shader, "LINES", {"pos": active_case})
            batch_active.draw(shader)

        gpu.state.line_width_set(1.0)
        gpu.state.blend_set("NONE")

        # Draw text and icons
        self._draw_texts(context, font_id)

        # Draw scroll indicators
        if self.needs_scroll:
            self._draw_scroll_indicators(context, font_id)

    def _draw_texts(self, context, font_id):
        """Draw channel names and icon indicators"""
        mid_height = int(self.px_h / 2)
        text_y_offset = int(self.text_size / 2.5)
        icon_y_offset = int(self.icon_size / 2)

        # Collect icons to draw
        icons_to_draw = {'hide_on': [], 'hide_off': [], 'lock_on': [], 'lock_off': [], 
                         'mute_on': [], 'mute_off': []}

        for display_idx in range(self.display_count):
            fc = self._get_fcurve_at_display_idx(display_idx)
            if not fc:
                continue

            fcurve_idx = self._display_idx_to_fcurve_idx(display_idx)
            is_current = (fcurve_idx == self.current_idx)

            y_base = self.bottom + display_idx * self.px_h + mid_height

            # Channel name
            channel_name, _ = gen_channel_info_line(fc)
            # Truncate if too long
            max_chars = int((self.mute_zone_x - self.text_x) / (self.text_size * 0.6))
            if len(channel_name) > max_chars:
                channel_name = channel_name[: max_chars - 3] + "..."

            # Text color based on state
            if fc.hide:
                text_color = self.hidden_text_color
            elif fc.mute:
                text_color = self.muted_text_color
            elif is_current:
                text_color = (1.0, 1.0, 1.0, 1.0)  # Bright white for current
            else:
                text_color = self.text_color

            blf.size(font_id, self.text_size)
            blf.color(font_id, *text_color)
            blf.position(font_id, self.text_x, y_base - text_y_offset, 0)
            blf.draw(font_id, channel_name)

            # Collect icon positions
            icon_y = y_base - icon_y_offset
            
            # Mute icon
            mute_key = 'mute_on' if fc.mute else 'mute_off'
            mute_coord = Vector((self.mute_zone_x, icon_y))
            icons_to_draw[mute_key].append([v + mute_coord for v in self.icon_tex_coord])
            
            # Lock icon
            lock_key = 'lock_on' if fc.lock else 'lock_off'
            lock_coord = Vector((self.lock_zone_x, icon_y))
            icons_to_draw[lock_key].append([v + lock_coord for v in self.icon_tex_coord])
            
            # Hide icon
            hide_key = 'hide_on' if fc.hide else 'hide_off'
            hide_coord = Vector((self.hide_zone_x, icon_y))
            icons_to_draw[hide_key].append([v + hide_coord for v in self.icon_tex_coord])

        # Draw all icons
        gpu.state.blend_set("ALPHA")
        for icon_name, coord_list in icons_to_draw.items():
            img = self.icon_tex.get(icon_name)
            if not img:
                continue
            texture = gpu.texture.from_image(img)
            for coords in coord_list:
                shader_tex = gpu.shader.from_builtin('IMAGE')
                batch_icons = batch_for_shader(
                    shader_tex, 'TRI_FAN',
                    {
                        "pos": coords,
                        "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
                    },
                )
                shader_tex.bind()
                shader_tex.uniform_sampler("image", texture)
                batch_icons.draw(shader_tex)
        gpu.state.blend_set("NONE")

    def _draw_scroll_indicators(self, _context, font_id):
        """Draw scroll position indicators"""
        if self.scroll_offset > 0:
            # Show "more above" indicator
            blf.size(font_id, self.text_size)
            blf.color(font_id, 0.7, 0.7, 0.7, 0.8)
            blf.position(font_id, self.left + self.px_w / 2 - 10, self.top + 5, 0)
            blf.draw(font_id, f"▲ {self.scroll_offset}")

        max_scroll = len(self.fcurves) - self.display_count
        if self.scroll_offset < max_scroll:
            # Show "more below" indicator
            remaining = max_scroll - self.scroll_offset
            blf.size(font_id, self.text_size)
            blf.color(font_id, 0.7, 0.7, 0.7, 0.8)
            blf.position(font_id, self.left + self.px_w / 2 - 10, self.bottom - self.text_size - 5, 0)
            blf.draw(font_id, f"▼ {remaining}")

    def stop_mod(self, context):
        """Clean up and stop the modal operator"""
        bpy.types.SpaceGraphEditor.draw_handler_remove(self._handle, "WINDOW")
        context.area.tag_redraw()


# --- Settings PropertyGroup ---


class ChannelNavigatorSettings(bpy.types.PropertyGroup):
    box_height: IntProperty(
        name="Box Height",
        description="Height of each channel box",
        default=28,
        min=20,
        max=60,
        subtype="PIXEL",
    )

    box_width: IntProperty(
        name="Box Width",
        description="Width of the navigator popup",
        default=280,
        min=150,
        max=500,
        subtype="PIXEL",
    )

    text_size: IntProperty(
        name="Text Size",
        description="Channel name text size",
        default=12,
        min=8,
        max=24,
        subtype="PIXEL",
    )

    max_display_count: IntProperty(
        name="Max Display",
        description="Maximum number of channels to display at once",
        default=8,
        min=3,
        max=30,
    )

    bg_alpha: bpy.props.FloatProperty(
        name="Background Alpha",
        description="Background transparency",
        default=0.96,
        min=0.3,
        max=1.0,
        subtype="FACTOR",
    )

    def draw(self, context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.label(text="Channel Navigator Settings", icon="FCURVE")
        col.prop(self, "box_height")
        col.prop(self, "box_width")
        col.prop(self, "text_size")
        col.prop(self, "max_display_count")
        col.prop(self, "bg_alpha")


# --- Keymap ---

keymap_channel_navigator = [
    KeymapDefinition(
        operator_id="graph.channel_navigator",
        key="Y",
        value="PRESS",
        name="Graph Editor",
        space_type="GRAPH_EDITOR",
        description="Open Channel Navigator popup",
    ),
]

keymap_registry.register_keymap_group("Channel Navigator", keymap_channel_navigator)

