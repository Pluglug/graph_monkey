# pyright: reportInvalidTypeForm=false
import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty
from bpy.types import DOPESHEET_HT_header, PropertyGroup

from ..addon import get_prefs
from ..utils.logging import get_logger

log = get_logger(__name__)


class PlaybackViewportManager:
    """Viewport tweaks that keep overlays and gizmos off during playback."""

    def __init__(self):
        self._original_states = {}
        self._is_active = False
        self._is_playing = False
        self._frame_handler = None
        self._playback_start_handler = None
        self._playback_end_handler = None
        log.debug("Initialized PlaybackViewportManager")

    def activate(self):
        """Register handlers that toggle viewport overlays."""
        if self._is_active:
            return

        try:
            handlers = bpy.app.handlers
            handlers.frame_change_pre.append(self._frame_change_handler)
            handlers.animation_playback_pre.append(self._playback_start_handler_fn)
            handlers.animation_playback_post.append(self._playback_end_handler_fn)

            self._frame_handler = self._frame_change_handler
            self._playback_start_handler = self._playback_start_handler_fn
            self._playback_end_handler = self._playback_end_handler_fn
            self._is_active = True
            log.info("Playback preview cleanup activated")
        except Exception as exc:
            log.error(f"Failed to activate playback preview: {exc}")
            self.deactivate()

    def deactivate(self):
        """Unregister handlers and restore viewport states."""
        if not self._is_active and not self._is_playing:
            return

        if self._is_playing:
            self._is_playing = False
            self._restore_viewport_states()

        handlers = bpy.app.handlers
        if self._frame_handler and self._frame_handler in handlers.frame_change_pre:
            handlers.frame_change_pre.remove(self._frame_handler)
        if (
            self._playback_start_handler
            and self._playback_start_handler in handlers.animation_playback_pre
        ):
            handlers.animation_playback_pre.remove(self._playback_start_handler)
        if (
            self._playback_end_handler
            and self._playback_end_handler in handlers.animation_playback_post
        ):
            handlers.animation_playback_post.remove(self._playback_end_handler)

        self._frame_handler = None
        self._playback_start_handler = None
        self._playback_end_handler = None
        self._is_active = False
        log.info("Playback preview cleanup deactivated")

    def _store_viewport_states(self):
        """Save the overlay/gizmo visibility for every VIEW_3D space."""
        self._original_states.clear()
        screen = getattr(bpy.context, "screen", None)
        if not screen:
            log.debug("No active screen to store viewport states")
            return

        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue

            space = area.spaces.active
            if not space:
                continue

            self._original_states[space] = {
                "show_overlays": space.overlay.show_overlays,
                "show_gizmo": space.show_gizmo,
            }
        log.debug(f"Stored viewport states for {len(self._original_states)} areas")

    def _restore_viewport_states(self):
        """Restore saved overlays/gizmos."""
        if not self._original_states:
            return

        restored = 0
        for space, states in list(self._original_states.items()):
            try:
                space.overlay.show_overlays = states.get("show_overlays", True)
                space.show_gizmo = states.get("show_gizmo", True)
                restored += 1
            except ReferenceError:
                log.warning("Viewport space reference invalid during restore")
            except Exception as exc:
                log.error(f"Could not restore viewport state: {exc}")

        self._original_states.clear()
        log.debug(f"Restored {restored} viewport areas")

    def _disable_viewport_features(self):
        """Turn off overlays and gizmos for all VIEW_3D spaces."""
        screen = getattr(bpy.context, "screen", None)
        if not screen:
            log.debug("No active screen to disable viewport features")
            return

        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue

            space = area.spaces.active
            if not space:
                continue

            try:
                space.overlay.show_overlays = False
                space.show_gizmo = False
            except Exception as exc:
                log.error(f"Failed to disable viewport features: {exc}")

    @persistent
    def _frame_change_handler(self, scene, _depsgraph):
        if not self._is_playing:
            return

        frame = scene.frame_current
        try:
            in_preview = False
            if scene.use_preview_range:
                in_preview = scene.frame_preview_start <= frame <= scene.frame_preview_end
            else:
                in_preview = scene.frame_start <= frame <= scene.frame_end

            if in_preview:
                if not self._original_states:
                    self._store_viewport_states()
                self._disable_viewport_features()
            elif self._original_states:
                self._restore_viewport_states()
        except Exception as exc:
            log.error(f"Playback viewport handler error: {exc}")

    @persistent
    def _playback_start_handler_fn(self, _scene, _depsgraph):
        self._is_playing = True
        log.debug("Playback preview started")

    @persistent
    def _playback_end_handler_fn(self, _scene, _depsgraph):
        self._is_playing = False
        if self._original_states:
            self._restore_viewport_states()
        log.debug("Playback preview stopped")


playback_preview_manager = PlaybackViewportManager()


def _on_enable_viewport_features(self, _context):
    if self.enable_viewport_features:
        playback_preview_manager.activate()
    else:
        playback_preview_manager.deactivate()


class PlaybackPreviewSettings(PropertyGroup):
    """Settings for the clean playback preview helpers."""

    enable_viewport_features: BoolProperty(
        name="Clean animation preview",
        description="Hide overlays and gizmos while playing the playback range",
        default=True,
        update=_on_enable_viewport_features,
    )

    def draw(self, _context, layout):
        row = layout.row()
        row.prop(self, "enable_viewport_features")
        row = layout.row()
        row.label(text="Automatically disables viewport overlays and gizmos when you play an animation")


def draw_dopesheet_header(self, context):
    try:
        prefs = get_prefs(context)
        preview_settings = prefs.playback_preview
    except Exception:
        return
    layout = self.layout
    layout.separator()
    layout.prop(
        preview_settings,
        "enable_viewport_features",
        text="",
        icon="SHADERFX",
        toggle=True,
    )


def _apply_initial_state():
    try:
        prefs = get_prefs()
    except Exception:
        return

    if prefs.playback_preview.enable_viewport_features:
        playback_preview_manager.activate()
    else:
        playback_preview_manager.deactivate()


def register():
    DOPESHEET_HT_header.append(draw_dopesheet_header)
    _apply_initial_state()


def unregister():
    playback_preview_manager.deactivate()
    if draw_dopesheet_header in DOPESHEET_HT_header:
        DOPESHEET_HT_header.remove(draw_dopesheet_header)

