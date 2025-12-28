# pyright: reportInvalidTypeForm=false
"""Pose transform visualizer for displaying bone transform differences in 3D viewport."""

import math

import bpy
import gpu
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
)
from bpy.types import Operator
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix, Vector

from ..addon import get_prefs
from ..keymap_manager import KeymapDefinition, keymap_registry
from ..utils.bone_transform_utils import (
    get_bone_axes_world,
    get_bone_transform_difference,
    magnitude_to_color,
    should_display_bone,
)
from ..utils.logging import get_logger

log = get_logger(__name__)


def create_axis_line_geometry(origin: Vector, axis: Vector, length: float):
    """
    軸の線分ジオメトリを生成。

    Args:
        origin: 原点
        axis: 軸の方向ベクトル（正規化済み）
        length: 軸の長さ

    Returns:
        list: [(start_point, end_point), ...]
    """
    end_point = origin + (axis * length)
    return [origin, end_point]


def create_arc_geometry(
    origin: Vector,
    start_vec: Vector,
    end_vec: Vector,
    radius: float,
    segments: int = 32,
) -> list:
    """
    扇形の円弧ジオメトリを生成（三角形メッシュ）。

    Args:
        origin: 扇形の中心点
        start_vec: 開始方向ベクトル（正規化済み）
        end_vec: 終了方向ベクトル（正規化済み）
        radius: 半径
        segments: 分割数（多いほど滑らか）

    Returns:
        list: 三角形の頂点リスト [(v1, v2, v3), ...]
    """
    # 回転軸を計算
    rotation_axis = start_vec.cross(end_vec)

    # 角度が非常に小さい場合はスキップ
    if rotation_axis.length < 0.001:
        return []

    rotation_axis.normalize()

    # 回転角度を計算
    angle = start_vec.angle(end_vec)

    # 円弧の頂点を生成
    vertices = [origin]  # 中心点

    for i in range(segments + 1):
        t = i / segments
        current_angle = angle * t

        # start_vecを回転軸周りに回転
        rotation_matrix = Matrix.Rotation(current_angle, 4, rotation_axis)
        rotated_vec = rotation_matrix @ start_vec
        point = origin + (rotated_vec * radius)
        vertices.append(point)

    # 三角形を生成（扇形）
    triangles = []
    for i in range(segments):
        triangles.extend([origin, vertices[i + 1], vertices[i + 2]])

    return triangles


def create_rotation_arc_geometry(
    pose_bone,
    rest_axis: Vector,
    current_axis: Vector,
    origin: Vector,
    radius: float,
    segments: int = 32,
) -> list:
    """
    レストポーズと現在のポーズの間の回転円弧を生成。

    Args:
        pose_bone: bpy.types.PoseBone
        rest_axis: レストポーズの軸方向
        current_axis: 現在のポーズの軸方向
        origin: 円弧の中心点
        radius: 半径
        segments: 分割数

    Returns:
        list: 三角形の頂点リスト
    """
    return create_arc_geometry(origin, rest_axis, current_axis, radius, segments)


def _update_enabled(self, context):
    """Called when enabled property is changed."""
    if self.enabled:
        pose_transform_visualizer_handler.start()
        log.info("Pose transform visualizer enabled via preferences")
    else:
        pose_transform_visualizer_handler.stop()
        log.info("Pose transform visualizer disabled via preferences")

    # リドロー
    for area in context.screen.areas:
        if area.type == "VIEW_3D":
            area.tag_redraw()


class PoseTransformVisualizerSettings(bpy.types.PropertyGroup):
    """Pose transform visualizer settings."""

    enabled: BoolProperty(
        name="Enable Transform Visualizer",
        description="Display bone transform differences (rotation, location, scale) in 3D viewport",
        default=False,
        update=_update_enabled,
    )

    display_style: EnumProperty(
        name="Display Style",
        description="What to display in the viewport",
        items=[
            ("BOTH", "Both", "Display both rest and current axes"),
            ("AXES_ONLY", "Axes Only", "Display only axes without arcs"),
            (
                "DIFF_ONLY",
                "Difference Only",
                "Display only rotation difference indicators",
            ),
        ],
        default="BOTH",
    )

    angle_threshold: FloatProperty(
        name="Angle Threshold",
        description="Minimum rotation angle to display (0 = always display)",
        default=0.0,
        min=0.0,
        max=180.0,
        unit="ROTATION",
        subtype="ANGLE",
    )

    axis_length: FloatProperty(
        name="Axis Length",
        description="Length of the axis indicators",
        default=0.2,
        min=0.01,
        max=10.0,
        subtype="DISTANCE",
    )

    axis_thickness: FloatProperty(
        name="Axis Thickness",
        description="Base thickness of the axis lines",
        default=2.0,
        min=1.0,
        max=10.0,
    )

    scale_by_rotation: BoolProperty(
        name="Scale by Rotation",
        description="Scale axis thickness based on rotation amount",
        default=True,
    )

    show_arc: BoolProperty(
        name="Show Rotation Arc",
        description="Display rotation difference as colored arc",
        default=True,
    )

    arc_radius: FloatProperty(
        name="Arc Radius",
        description="Radius of the rotation arc",
        default=0.15,
        min=0.01,
        max=10.0,
        subtype="DISTANCE",
    )

    arc_segments: IntProperty(
        name="Arc Segments",
        description="Number of segments for arc smoothness",
        default=24,
        min=6,
        max=64,
    )

    arc_opacity: FloatProperty(
        name="Arc Opacity",
        description="Opacity of the rotation arc",
        default=0.3,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    arc_color_x: FloatVectorProperty(
        name="X Arc Color",
        description="Color of the X-axis rotation arc",
        default=(1.0, 1.0, 0.0),
        size=3,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    arc_color_y: FloatVectorProperty(
        name="Y Arc Color",
        description="Color of the Y-axis rotation arc",
        default=(1.0, 1.0, 0.0),
        size=3,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    arc_color_z: FloatVectorProperty(
        name="Z Arc Color",
        description="Color of the Z-axis rotation arc",
        default=(1.0, 1.0, 0.0),
        size=3,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    draw_on_top: BoolProperty(
        name="Draw on Top",
        description="Draw visualization on top of everything (disable depth test)",
        default=False,
    )

    # Location visualization settings
    show_location: BoolProperty(
        name="Show Location Offset",
        description="Display location offset from rest pose",
        default=False,
    )

    location_line_thickness: FloatProperty(
        name="Location Line Thickness",
        description="Thickness of the location offset line",
        default=2.0,
        min=1.0,
        max=10.0,
    )

    location_threshold: FloatProperty(
        name="Location Threshold",
        description="Minimum location offset to display (0 = always display)",
        default=0.01,
        min=0.0,
        max=1.0,
        subtype="DISTANCE",
    )

    location_line_color: FloatVectorProperty(
        name="Location Line Color",
        description="Color of the location offset line",
        default=(1.0, 0.5, 0.0),  # Orange
        size=3,
        min=0.0,
        max=1.0,
        subtype="COLOR",
    )

    location_line_opacity: FloatProperty(
        name="Location Line Opacity",
        description="Opacity of the location offset line",
        default=0.6,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
    )

    use_dashed_line: BoolProperty(
        name="Use Dashed Line",
        description="Draw location offset line as dashed line",
        default=True,
    )

    dash_length: FloatProperty(
        name="Dash Length",
        description="Length of each dash segment",
        default=0.02,
        min=0.001,
        max=1.0,
        subtype="DISTANCE",
    )

    gap_length: FloatProperty(
        name="Gap Length",
        description="Length of gap between dashes",
        default=0.01,
        min=0.001,
        max=1.0,
        subtype="DISTANCE",
    )

    # TODO: 将来的に色のマッピングを実装
    # use_location_color_mapping: BoolProperty(
    #     name="Color by Distance",
    #     description="Color the line based on distance (heat map)",
    #     default=False,
    # )

    def draw(self, _context, layout):
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()

        col.label(text="Pose Transform Visualizer", icon="ARMATURE_DATA")
        col.prop(self, "enabled")

        col.separator()

        col.prop(self, "display_style")
        col.prop(self, "angle_threshold")
        col.prop(self, "draw_on_top")

        col.separator()
        col.label(text="Axis Display")
        col.prop(self, "axis_length")
        col.prop(self, "axis_thickness")
        col.prop(self, "scale_by_rotation")

        col.separator()
        col.label(text="Rotation Arc")
        col.prop(self, "show_arc")

        if self.show_arc:
            sub = col.column()
            sub.prop(self, "arc_radius")
            sub.prop(self, "arc_segments")
            sub.prop(self, "arc_opacity")

            sub.separator()
            sub.label(text="Arc Colors")
            sub.prop(self, "arc_color_x")
            sub.prop(self, "arc_color_y")
            sub.prop(self, "arc_color_z")

        col.separator()
        col.label(text="Location Offset")
        col.prop(self, "show_location")

        if self.show_location:
            sub = col.column()
            sub.prop(self, "location_threshold")
            sub.prop(self, "location_line_thickness")
            sub.prop(self, "location_line_color")
            sub.prop(self, "location_line_opacity")
            
            sub.separator()
            sub.prop(self, "use_dashed_line")
            if self.use_dashed_line:
                subsub = sub.column()
                subsub.prop(self, "dash_length")
                subsub.prop(self, "gap_length")


class PoseTransformVisualizerHandler:
    """Handler for drawing pose transform visualization in 3D viewport."""

    def __init__(self):
        self.draw_handler = None
        self.shader_3d_uniform_color = gpu.shader.from_builtin("UNIFORM_COLOR")
        self.shader_3d_smooth_color = gpu.shader.from_builtin("SMOOTH_COLOR")

    def start(self):
        """Start the draw handler."""
        if self.draw_handler is None:
            self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                self._draw_callback_wrapper, (), "WINDOW", "POST_VIEW"
            )
            log.info("Pose transform visualizer started")

    def stop(self):
        """Stop the draw handler."""
        if self.draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, "WINDOW")
            self.draw_handler = None
            log.info("Pose transform visualizer stopped")

    def is_active(self):
        """Check if the handler is active."""
        return self.draw_handler is not None

    def _draw_callback_wrapper(self, *_args, **_kwargs):
        """Wrapper for the draw callback."""
        context = bpy.context
        self._draw_callback(context)

    def _draw_callback(self, context):
        """Main draw callback."""
        # コンテキストチェック
        if not context:
            return

        # ポーズモードでない場合はスキップ
        if not hasattr(context, "mode") or context.mode != "POSE":
            return

        # アーマチュアが選択されていない場合はスキップ
        if not context.active_object or context.active_object.type != "ARMATURE":
            return

        # オーバーレイ設定をチェック
        space_data = context.space_data
        if space_data and hasattr(space_data, "overlay"):
            overlay = space_data.overlay
            # show_overlays または show_extras がオフの場合は表示しない
            if not overlay.show_overlays or not overlay.show_extras:
                return

        try:
            pr = get_prefs(context)
            settings = pr.pose_visualizer
        except:
            return

        if not settings.enabled:
            return

        # 選択中のボーンを取得
        selected_bones = context.selected_pose_bones

        if not selected_bones:
            return

        # 深度テストの設定
        if settings.draw_on_top:
            gpu.state.depth_test_set("NONE")  # 最前面に描画
        else:
            gpu.state.depth_test_set("LESS_EQUAL")  # 通常の深度テスト

        gpu.state.depth_mask_set(True)
        gpu.state.blend_set("ALPHA")

        try:
            for pose_bone in selected_bones:
                # 閾値チェック（angle_thresholdはラジアンで保存されているため、度に変換）
                threshold_degrees = math.degrees(settings.angle_threshold)
                if not should_display_bone(pose_bone, threshold_degrees):
                    continue

                self._draw_bone_transform(context, pose_bone, settings)
        finally:
            # 状態をリセット
            gpu.state.depth_test_set("NONE")
            gpu.state.blend_set("NONE")

    def _draw_bone_transform(self, context, pose_bone, settings):
        """Draw transform visualization (rotation, location, etc.) for a single bone."""
        # レストポーズと現在のポーズの軸を取得
        rest_origin, rest_x, rest_y, rest_z = get_bone_axes_world(
            pose_bone, rest_pose=True
        )
        current_origin, current_x, current_y, current_z = get_bone_axes_world(
            pose_bone, rest_pose=False
        )

        # 変形情報を取得
        transform_diff = get_bone_transform_difference(pose_bone)
        angle_degrees = transform_diff.rotation_angle_deg

        # 軸の太さを計算（回転量に応じて変化）
        base_thickness = settings.axis_thickness
        if settings.scale_by_rotation:
            # 0-180度を1.0-3.0倍にマッピング
            scale_factor = 1.0 + (min(angle_degrees, 180.0) / 180.0) * 2.0
            thickness = base_thickness * scale_factor
        else:
            thickness = base_thickness

        gpu.state.line_width_set(thickness)

        # 表示スタイルに応じて描画
        if settings.display_style in ["BOTH", "AXES_ONLY"]:
            # レストポーズの軸を描画（半透明グレー）
            self._draw_axes(
                rest_origin,
                rest_x,
                rest_y,
                rest_z,
                settings.axis_length,
                alpha=0.3,
                use_rest_colors=True,
            )

            # 現在のポーズの軸を描画（カラー）
            self._draw_axes(
                current_origin,
                current_x,
                current_y,
                current_z,
                settings.axis_length,
                alpha=1.0,
                use_rest_colors=False,
            )

        # 回転円弧を描画
        if settings.show_arc and settings.display_style in ["BOTH", "DIFF_ONLY"]:
            self._draw_rotation_arcs(
                pose_bone,
                rest_origin,
                rest_x,
                rest_y,
                rest_z,
                current_x,
                current_y,
                current_z,
                settings,
            )

        # 位置オフセットを描画
        if settings.show_location:
            self._draw_location_offset(pose_bone, transform_diff, settings)

    def _draw_axes(
        self, origin, x_axis, y_axis, z_axis, length, alpha=1.0, use_rest_colors=False
    ):
        """Draw XYZ axes."""
        if use_rest_colors:
            # レストポーズは半透明グレー
            colors = [
                (0.5, 0.5, 0.5, alpha),
                (0.5, 0.5, 0.5, alpha),
                (0.5, 0.5, 0.5, alpha),
            ]
        else:
            # 現在のポーズは標準色（X=赤、Y=緑、Z=青）
            colors = [
                (1.0, 0.0, 0.0, alpha),  # X: Red
                (0.0, 1.0, 0.0, alpha),  # Y: Green
                (0.0, 0.0, 1.0, alpha),  # Z: Blue
            ]

        axes = [x_axis, y_axis, z_axis]

        for axis, color in zip(axes, colors):
            coords = create_axis_line_geometry(origin, axis, length)

            batch = batch_for_shader(
                self.shader_3d_uniform_color,
                "LINES",
                {"pos": coords},
            )

            self.shader_3d_uniform_color.bind()
            self.shader_3d_uniform_color.uniform_float("color", color)
            batch.draw(self.shader_3d_uniform_color)

    def _draw_rotation_arcs(
        self,
        pose_bone,
        origin,
        rest_x,
        rest_y,
        rest_z,
        current_x,
        current_y,
        current_z,
        settings,
    ):
        """Draw rotation arcs for each axis."""
        # 各軸ごとに円弧を描画（色は設定から取得）
        axis_pairs = [
            (rest_x, current_x, (*settings.arc_color_x, settings.arc_opacity)),  # X軸
            (rest_y, current_y, (*settings.arc_color_y, settings.arc_opacity)),  # Y軸
            (rest_z, current_z, (*settings.arc_color_z, settings.arc_opacity)),  # Z軸
        ]

        for rest_axis, current_axis, color in axis_pairs:
            # 角度が非常に小さい場合はスキップ
            angle = rest_axis.angle(current_axis)
            if angle < 0.001:
                continue

            # 円弧ジオメトリを生成
            arc_vertices = create_arc_geometry(
                origin,
                rest_axis,
                current_axis,
                settings.arc_radius,
                settings.arc_segments,
            )

            if not arc_vertices:
                continue

            # 描画
            batch = batch_for_shader(
                self.shader_3d_uniform_color,
                "TRIS",
                {"pos": arc_vertices},
            )

            self.shader_3d_uniform_color.bind()
            self.shader_3d_uniform_color.uniform_float("color", color)
            batch.draw(self.shader_3d_uniform_color)

    def _draw_location_offset(self, pose_bone, transform_diff, settings):
        """Draw location offset from rest pose as a line."""
        # 閾値チェック
        if not transform_diff.has_location_change:
            return

        location_magnitude = transform_diff.location_offset.length
        if location_magnitude < settings.location_threshold:
            return

        armature = pose_bone.id_data

        # 現在の位置（ボーンのhead）
        current_pos = armature.matrix_world @ pose_bone.head

        # レストポーズの位置を計算
        # ローカルオフセット（transform_diff.location_offset）を、
        # 親の現在の変形を考慮してワールド空間に変換
        # parent_matrix = 親の変形を含むマトリックス（自身のmatrix_basisを除く）
        parent_matrix = pose_bone.matrix @ pose_bone.matrix_basis.inverted()
        location_offset_world = parent_matrix.to_3x3() @ transform_diff.location_offset
        rest_pos = current_pos - location_offset_world

        # 色の計算
        # TODO: 将来的に距離に応じた色マッピングを実装
        # if settings.use_location_color_mapping:
        #     color = magnitude_to_color(
        #         location_magnitude,
        #         min_value=0.0,
        #         max_value=1.0,
        #         color_scheme="heat",
        #         alpha=settings.location_line_opacity,
        #     )
        # else:
        #     color = (*settings.location_line_color, settings.location_line_opacity)
        color = (*settings.location_line_color, settings.location_line_opacity)

        # ラインの太さを設定
        gpu.state.line_width_set(settings.location_line_thickness)

        # 点線または実線で描画
        if settings.use_dashed_line:
            coords = self._create_dashed_line(
                rest_pos, 
                current_pos, 
                settings.dash_length, 
                settings.gap_length
            )
        else:
            coords = [rest_pos, current_pos]

        if not coords:
            return

        batch = batch_for_shader(
            self.shader_3d_uniform_color,
            "LINES",
            {"pos": coords},
        )

        self.shader_3d_uniform_color.bind()
        self.shader_3d_uniform_color.uniform_float("color", color)
        batch.draw(self.shader_3d_uniform_color)

    def _create_dashed_line(self, start: Vector, end: Vector, dash_length: float, gap_length: float) -> list:
        """
        Create a dashed line by generating alternating dash segments.
        
        Args:
            start: Start position
            end: End position
            dash_length: Length of each dash
            gap_length: Length of gap between dashes
            
        Returns:
            list: Line segment coordinates [(p1, p2), (p3, p4), ...]
        """
        direction = end - start
        total_length = direction.length
        
        if total_length < 0.001:
            return []
        
        direction.normalize()
        
        coords = []
        current_length = 0.0
        pattern_length = dash_length + gap_length
        
        while current_length < total_length:
            # ダッシュの開始
            dash_start = start + direction * current_length
            dash_end_length = min(current_length + dash_length, total_length)
            dash_end = start + direction * dash_end_length
            
            coords.extend([dash_start, dash_end])
            
            # 次のダッシュへ移動（ギャップを含む）
            current_length += pattern_length
        
        return coords


# グローバルハンドラーインスタンス
pose_transform_visualizer_handler = PoseTransformVisualizerHandler()


class MONKEY_OT_toggle_pose_transform_visualizer(Operator):
    """Toggle the pose transform visualizer"""

    bl_idname = "pose.toggle_transform_visualizer"
    bl_label = "Toggle Pose Transform Visualizer"

    def execute(self, context):
        pr = get_prefs(context)
        pr.pose_visualizer.enabled = not pr.pose_visualizer.enabled

        if pr.pose_visualizer.enabled:
            pose_transform_visualizer_handler.start()
            self.report({"INFO"}, "Pose transform visualizer enabled")
        else:
            pose_transform_visualizer_handler.stop()
            self.report({"INFO"}, "Pose transform visualizer disabled")

        # リドロー
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        return {"FINISHED"}


keymaps = [
    KeymapDefinition(
        operator_id="pose.toggle_transform_visualizer",
        key="V",
        value="PRESS",
        name="Pose",
        space_type="EMPTY",
        region_type="WINDOW",
        description="Toggle pose transform visualizer",
    ),
]
keymap_registry.register_keymap_group("Pose Transform Visualizer", keymaps)


def register():
    """Register the visualizer on addon enable."""
    log.info("pose_transform_visualizer.register() called")

    # タイマーで遅延起動（Preferencesがロードされた後に実行）
    def delayed_start():
        try:
            context = bpy.context
            pr = get_prefs(context)
            log.info(f"Delayed start: enabled={pr.pose_visualizer.enabled}")
            if pr.pose_visualizer.enabled:
                pose_transform_visualizer_handler.start()
                log.info("Auto-started pose transform visualizer")
        except Exception as e:
            log.warning(f"Could not auto-start pose visualizer: {e}")
            import traceback

            traceback.print_exc()
        return None  # タイマーを一度だけ実行

    # 0.1秒後に実行
    bpy.app.timers.register(delayed_start, first_interval=0.1)


def unregister():
    """Unregister the visualizer on addon disable."""
    pose_transform_visualizer_handler.stop()
