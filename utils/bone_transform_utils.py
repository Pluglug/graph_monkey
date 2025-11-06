"""
Bone transformation utilities for pose mode visualization.

ボーンの変形情報（位置、回転、スケール）を包括的に取得・計算するユーティリティ。
将来の拡張（位置/スケール可視化、色のマッピングなど）に対応。
"""

import math
from dataclasses import dataclass
from typing import Optional

from mathutils import Euler, Matrix, Quaternion, Vector


@dataclass
class BoneTransformDifference:
    """
    ボーンのレストポーズと現在のポーズの変形差分を保持するデータクラス。

    Attributes:
        location_offset: 位置のオフセット（Vector）
        location_magnitude: 位置の変化量（float、距離）

        rotation_quat: 回転差分（Quaternion）
        rotation_angle_deg: 回転角度（度数法）
        rotation_axis: 回転軸（Vector、正規化済み）

        scale_diff: スケールの差分（Vector、各軸ごと）
        scale_magnitude: スケールの変化量（float、平均）

        has_location_change: 位置が変化しているか
        has_rotation_change: 回転が変化しているか
        has_scale_change: スケールが変化しているか
    """

    # 位置
    location_offset: Vector
    location_magnitude: float

    # 回転
    rotation_quat: Quaternion
    rotation_angle_deg: float
    rotation_axis: Vector

    # スケール
    scale_diff: Vector
    scale_magnitude: float

    # 変化フラグ
    has_location_change: bool
    has_rotation_change: bool
    has_scale_change: bool

    @property
    def has_any_change(self) -> bool:
        """何らかの変形があるかどうか。"""
        return (
            self.has_location_change
            or self.has_rotation_change
            or self.has_scale_change
        )

    @property
    def total_magnitude(self) -> float:
        """
        全体の変形量（正規化された値）。
        位置、回転、スケールを総合的に評価。
        0.0 = 変形なし、1.0以上 = 大きな変形
        """
        # 各変形を0-1の範囲にマッピングして合計
        loc_norm = min(self.location_magnitude / 1.0, 1.0)  # 1.0単位以上で1.0
        rot_norm = min(self.rotation_angle_deg / 180.0, 1.0)  # 180度以上で1.0
        scale_norm = min(abs(self.scale_magnitude) / 1.0, 1.0)  # 1.0倍以上で1.0

        return (loc_norm + rot_norm + scale_norm) / 3.0


def get_bone_transform_difference(
    pose_bone, threshold: float = 0.001
) -> BoneTransformDifference:
    """
    ボーンのレストポーズからの変形差分を包括的に計算。
    親ボーンの影響を除いた、そのボーン自身のローカル変形のみを取得。

    Args:
        pose_bone: bpy.types.PoseBone
        threshold: 変化と判定する閾値（デフォルト: 0.001）

    Returns:
        BoneTransformDifference: 変形差分情報
    """
    # matrix_basis からローカル変形を取得
    basis = pose_bone.matrix_basis

    # 位置の差分
    location_offset = basis.to_translation()
    location_magnitude = location_offset.length
    has_location = location_magnitude > threshold

    # 回転の差分
    rotation_quat = basis.to_quaternion()
    rest_quat = Quaternion()  # レストポーズ = 単位クォータニオン
    rotation_diff = rest_quat.rotation_difference(rotation_quat)
    rotation_angle_rad = rotation_diff.angle
    rotation_angle_deg = math.degrees(rotation_angle_rad)
    rotation_axis = (
        rotation_diff.axis if rotation_angle_rad > threshold else Vector((0, 1, 0))
    )
    has_rotation = rotation_angle_deg > math.degrees(threshold)

    # スケールの差分
    scale = basis.to_scale()
    scale_diff = Vector((scale.x - 1.0, scale.y - 1.0, scale.z - 1.0))
    scale_magnitude = sum(abs(s - 1.0) for s in scale) / 3.0  # 平均
    has_scale = scale_magnitude > threshold

    return BoneTransformDifference(
        location_offset=location_offset,
        location_magnitude=location_magnitude,
        rotation_quat=rotation_quat,
        rotation_angle_deg=rotation_angle_deg,
        rotation_axis=rotation_axis,
        scale_diff=scale_diff,
        scale_magnitude=scale_magnitude,
        has_location_change=has_location,
        has_rotation_change=has_rotation,
        has_scale_change=has_scale,
    )


def get_bone_axes_world(
    pose_bone, rest_pose: bool = False
) -> tuple[Vector, Vector, Vector, Vector]:
    """
    ボーンのローカル軸（X, Y, Z）をワールド空間のベクトルとして取得。

    Blenderのボーン座標系：
    - Y軸: ヘッド→テール方向（ボーンの長軸）
    - X軸, Z軸: ロール角で決定される

    Args:
        pose_bone: bpy.types.PoseBone
        rest_pose: Trueの場合はレストポーズの軸を取得

    Returns:
        tuple: (origin, x_axis, y_axis, z_axis)
            - origin: 軸の原点（ボーンのhead位置、ワールド空間）
            - x_axis, y_axis, z_axis: 各軸の方向ベクトル（正規化済み、ワールド空間）
    """
    armature = pose_bone.id_data

    # ボーンのheadをワールド空間で取得
    origin = armature.matrix_world @ pose_bone.head

    if rest_pose:
        # レストポーズの軸を計算
        # 現在のポーズから、matrix_basisの逆回転を適用してレストポーズに戻す
        full_matrix = armature.matrix_world @ pose_bone.matrix
        matrix_basis_inv = pose_bone.matrix_basis.inverted()
        rest_matrix = full_matrix @ matrix_basis_inv

        x_axis = (rest_matrix.to_3x3() @ Vector((1, 0, 0))).normalized()
        y_axis = (rest_matrix.to_3x3() @ Vector((0, 1, 0))).normalized()
        z_axis = (rest_matrix.to_3x3() @ Vector((0, 0, 1))).normalized()
    else:
        # 現在のポーズの軸
        # Blenderが計算済みの軸を直接使用（最も正確）
        x_axis = pose_bone.x_axis.copy()
        y_axis = pose_bone.y_axis.copy()
        z_axis = pose_bone.z_axis.copy()

    return origin, x_axis, y_axis, z_axis


def magnitude_to_color(
    magnitude: float,
    min_value: float = 0.0,
    max_value: float = 180.0,
    color_scheme: str = "heat",
) -> tuple[float, float, float]:
    """
    変形量を色にマッピング（ヒートマップ）。

    Args:
        magnitude: 変形量（例: 回転角度、移動距離）
        min_value: 最小値（この値以下は最も冷たい色）
        max_value: 最大値（この値以上は最も熱い色）
        color_scheme: 色スキーム
            - "heat": 青→緑→黄→赤（ヒートマップ）
            - "rainbow": 虹色（青→緑→黄→オレンジ→赤）
            - "grayscale": グレースケール

    Returns:
        tuple[float, float, float]: RGB色（0.0-1.0）
    """
    # 0.0-1.0 に正規化
    t = (magnitude - min_value) / (max_value - min_value)
    t = max(0.0, min(1.0, t))  # クランプ

    if color_scheme == "heat":
        # ヒートマップ: 青→シアン→緑→黄→赤
        if t < 0.25:
            # 青→シアン
            return (0.0, t * 4.0, 1.0)
        elif t < 0.5:
            # シアン→緑
            return (0.0, 1.0, 1.0 - (t - 0.25) * 4.0)
        elif t < 0.75:
            # 緑→黄
            return ((t - 0.5) * 4.0, 1.0, 0.0)
        else:
            # 黄→赤
            return (1.0, 1.0 - (t - 0.75) * 4.0, 0.0)

    elif color_scheme == "rainbow":
        # 虹色
        if t < 0.2:
            return (0.5, 0.0, 1.0)  # 紫
        elif t < 0.4:
            return (0.0, 0.5, 1.0)  # 青
        elif t < 0.6:
            return (0.0, 1.0, 0.5)  # 緑
        elif t < 0.8:
            return (1.0, 1.0, 0.0)  # 黄
        else:
            return (1.0, 0.0, 0.0)  # 赤

    elif color_scheme == "grayscale":
        # グレースケール
        return (t, t, t)

    else:
        # デフォルト: 緑→黄→赤
        if t < 0.5:
            return (t * 2.0, 1.0, 0.0)
        else:
            return (1.0, 1.0 - (t - 0.5) * 2.0, 0.0)


def get_rotation_euler_degrees(pose_bone) -> tuple[float, float, float]:
    """
    ボーンのローカル回転をEuler角（度数法）で取得。
    ボーンの回転モードに従う。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        tuple: (x_degrees, y_degrees, z_degrees)
    """
    basis = pose_bone.matrix_basis
    rotation_mode = pose_bone.rotation_mode

    if rotation_mode == "QUATERNION":
        euler = basis.to_euler("XYZ")
    elif rotation_mode == "AXIS_ANGLE":
        euler = basis.to_euler("XYZ")
    else:
        euler = basis.to_euler(rotation_mode)

    return (math.degrees(euler.x), math.degrees(euler.y), math.degrees(euler.z))


def should_display_bone(pose_bone, threshold_degrees: float = 0.0) -> bool:
    """
    ボーンを表示すべきかどうか判定（閾値チェック）。

    Args:
        pose_bone: bpy.types.PoseBone
        threshold_degrees: 表示する最小角度（度）

    Returns:
        bool: True = 表示すべき
    """
    if threshold_degrees <= 0.0:
        return True

    diff = get_bone_transform_difference(pose_bone)
    return diff.rotation_angle_deg >= threshold_degrees


# 後方互換性のためのエイリアス
def get_rotation_difference(pose_bone) -> tuple[Quaternion, float]:
    """
    レストポーズからの回転差分を取得（後方互換性のため）。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        tuple: (rotation_quaternion, angle_degrees)
    """
    diff = get_bone_transform_difference(pose_bone)
    return diff.rotation_quat, diff.rotation_angle_deg
