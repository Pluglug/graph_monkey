"""
Pose calculation utilities for bone rotation visualization.

Note: このモジュールは後方互換性のために保持されています。
新しい機能は bone_transform_utils.py を使用してください。
"""

import math

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

# 新しいユーティリティからインポート（後方互換性）
from .bone_transform_utils import (
    BoneTransformDifference,
    get_bone_axes_world as _get_bone_axes_world,
    get_bone_transform_difference,
    magnitude_to_color,
    should_display_bone as _should_display_bone,
)


def get_bone_rest_matrix(pose_bone) -> Matrix:
    """
    ボーンのレストポーズのワールド空間マトリクスを取得。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        Matrix: レストポーズのワールド空間マトリクス
    """
    armature = pose_bone.id_data
    edit_bone = armature.data.bones[pose_bone.name]

    # レストポーズのマトリクスはボーン空間
    # ワールド空間に変換
    rest_matrix = armature.matrix_world @ edit_bone.matrix_local
    return rest_matrix


def get_bone_current_matrix(pose_bone) -> Matrix:
    """
    ボーンの現在のポーズのワールド空間マトリクスを取得。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        Matrix: 現在のポーズのワールド空間マトリクス
    """
    armature = pose_bone.id_data
    current_matrix = armature.matrix_world @ pose_bone.matrix
    return current_matrix


def get_rotation_difference(pose_bone) -> tuple[Quaternion, float]:
    """
    レストポーズと現在のポーズの回転差分を計算（ローカル空間）。
    親ボーンの影響を受けない、そのボーン自身の回転のみを計算。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        tuple: (rotation_quaternion, angle_degrees)
            - rotation_quaternion: 回転差分のQuaternion
            - angle_degrees: 回転角度（度数法）
    """
    # ローカル空間での回転を取得（親の影響を除外）
    # matrix_basis は親の変形を含まない、ボーン自身の変形のみ
    current_rotation = pose_bone.matrix_basis.to_quaternion()

    # レストポーズはアイデンティティ（回転なし）と比較
    rest_rotation = Quaternion()

    # 回転差分を計算
    rotation_diff = rest_rotation.rotation_difference(current_rotation)

    # 回転角度を計算（ラジアン→度）
    angle_radians = rotation_diff.angle
    angle_degrees = math.degrees(angle_radians)

    return rotation_diff, angle_degrees


def get_rotation_axis_angle(pose_bone) -> tuple[Vector, float]:
    """
    レストポーズからの回転軸と角度を取得。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        tuple: (axis_vector, angle_degrees)
            - axis_vector: 回転軸の単位ベクトル
            - angle_degrees: 回転角度（度数法）
    """
    rotation_quat, angle_degrees = get_rotation_difference(pose_bone)

    # Quaternionから軸角表現に変換
    axis = rotation_quat.axis

    return axis, angle_degrees


def get_euler_rotation_differences(pose_bone) -> tuple[float, float, float]:
    """
    レストポーズからのEuler角での回転差分を取得（各軸ごと、ローカル空間）。
    親ボーンの影響を除いた、そのボーン自身の回転のみ。
    ボーンの回転モードに従う。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        tuple: (x_degrees, y_degrees, z_degrees)
    """
    # ローカル空間での現在の回転（matrix_basis）
    current_matrix = pose_bone.matrix_basis

    # 回転モードを取得
    rotation_mode = pose_bone.rotation_mode

    if rotation_mode == "QUATERNION":
        # Quaternionモードの場合はEuler角に変換（XYZ順）
        current_euler = current_matrix.to_euler("XYZ")
    elif rotation_mode == "AXIS_ANGLE":
        # Axis-Angleモードの場合もEuler角に変換
        current_euler = current_matrix.to_euler("XYZ")
    else:
        # Eulerモード（XYZ, XZY, YXZ, YZX, ZXY, ZYX）
        current_euler = current_matrix.to_euler(rotation_mode)

    # レストポーズは回転なし（0, 0, 0）として差分を計算
    diff_x = math.degrees(current_euler.x)
    diff_y = math.degrees(current_euler.y)
    diff_z = math.degrees(current_euler.z)

    return diff_x, diff_y, diff_z


def get_bone_head_tail_world(pose_bone) -> tuple[Vector, Vector]:
    """
    ボーンのheadとtailのワールド座標を取得。

    Args:
        pose_bone: bpy.types.PoseBone

    Returns:
        tuple: (head_world, tail_world)
    """
    armature = pose_bone.id_data
    head_world = armature.matrix_world @ pose_bone.head
    tail_world = armature.matrix_world @ pose_bone.tail

    return head_world, tail_world


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
        # 現在のポーズの軸から、matrix_basisの逆回転を適用してレストポーズに戻す

        # 現在のワールド空間での完全なマトリックス（親の影響込み）
        full_matrix = armature.matrix_world @ pose_bone.matrix

        # matrix_basis の逆行列（このボーンのローカル変形を取り消す）
        matrix_basis_inv = pose_bone.matrix_basis.inverted()

        # レストポーズのマトリックス = 完全なマトリックス × basis の逆
        # つまり：親の姿勢 × レスト方向 = (親の姿勢 × レスト方向 × basis) × basis^-1
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


def should_display_bone(pose_bone, threshold_degrees: float) -> bool:
    """
    ボーンを表示すべきかどうか判定（閾値チェック）。

    Args:
        pose_bone: bpy.types.PoseBone
        threshold_degrees: 表示する最小角度（度）

    Returns:
        bool: True = 表示すべき
    """
    if threshold_degrees <= 0.0:
        return True  # 閾値0なら常に表示

    _, angle = get_rotation_difference(pose_bone)
    return angle >= threshold_degrees
