"""Pose calculation utilities for bone rotation visualization."""

import math

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector


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
    レストポーズと現在のポーズの回転差分を計算。
    
    Args:
        pose_bone: bpy.types.PoseBone
        
    Returns:
        tuple: (rotation_quaternion, angle_degrees)
            - rotation_quaternion: 回転差分のQuaternion
            - angle_degrees: 回転角度（度数法）
    """
    rest_matrix = get_bone_rest_matrix(pose_bone)
    current_matrix = get_bone_current_matrix(pose_bone)
    
    # 回転成分のみを抽出
    rest_rotation = rest_matrix.to_quaternion()
    current_rotation = current_matrix.to_quaternion()
    
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
    レストポーズからのEuler角での回転差分を取得（各軸ごと）。
    ボーンの回転モードに従う。
    
    Args:
        pose_bone: bpy.types.PoseBone
        
    Returns:
        tuple: (x_degrees, y_degrees, z_degrees)
    """
    rest_matrix = get_bone_rest_matrix(pose_bone)
    current_matrix = get_bone_current_matrix(pose_bone)
    
    # 回転モードを取得
    rotation_mode = pose_bone.rotation_mode
    
    if rotation_mode == 'QUATERNION':
        # Quaternionモードの場合はEuler角に変換（XYZ順）
        rest_euler = rest_matrix.to_euler('XYZ')
        current_euler = current_matrix.to_euler('XYZ')
    elif rotation_mode == 'AXIS_ANGLE':
        # Axis-Angleモードの場合もEuler角に変換
        rest_euler = rest_matrix.to_euler('XYZ')
        current_euler = current_matrix.to_euler('XYZ')
    else:
        # Eulerモード（XYZ, XZY, YXZ, YZX, ZXY, ZYX）
        rest_euler = rest_matrix.to_euler(rotation_mode)
        current_euler = current_matrix.to_euler(rotation_mode)
    
    # 差分を計算
    diff_x = math.degrees(current_euler.x - rest_euler.x)
    diff_y = math.degrees(current_euler.y - rest_euler.y)
    diff_z = math.degrees(current_euler.z - rest_euler.z)
    
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


def get_bone_axes_world(pose_bone, rest_pose: bool = False) -> tuple[Vector, Vector, Vector, Vector]:
    """
    ボーンのローカル軸（X, Y, Z）をワールド空間のベクトルとして取得。
    
    Args:
        pose_bone: bpy.types.PoseBone
        rest_pose: Trueの場合はレストポーズの軸を取得
        
    Returns:
        tuple: (origin, x_axis, y_axis, z_axis)
            - origin: 軸の原点（ボーンのhead位置）
            - x_axis, y_axis, z_axis: 各軸の方向ベクトル（正規化済み）
    """
    if rest_pose:
        matrix = get_bone_rest_matrix(pose_bone)
    else:
        matrix = get_bone_current_matrix(pose_bone)
    
    # ボーンのheadを原点とする
    armature = pose_bone.id_data
    origin = armature.matrix_world @ pose_bone.head
    
    # 各軸の方向ベクトル（回転のみ適用）
    x_axis = matrix.to_3x3() @ Vector((1, 0, 0))
    y_axis = matrix.to_3x3() @ Vector((0, 1, 0))
    z_axis = matrix.to_3x3() @ Vector((0, 0, 1))
    
    x_axis.normalize()
    y_axis.normalize()
    z_axis.normalize()
    
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

