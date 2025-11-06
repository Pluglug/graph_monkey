# Bone Transform Utils - クイックスタート

## 🚀 5分でわかる使い方

### 基本的な使い方

```python
import bpy
from MonKey.utils.bone_transform_utils import get_bone_transform_difference

# ポーズモードでボーンを選択
pose_bone = bpy.context.selected_pose_bones[0]

# 変形情報を取得
diff = get_bone_transform_difference(pose_bone)

# 結果を表示
print(f"回転: {diff.rotation_angle_deg:.1f}°")
print(f"位置: {diff.location_magnitude:.3f}")
print(f"スケール: {diff.scale_magnitude:.3f}")
```

### よく使うパターン

#### パターン1: 回転角度をチェック

```python
if diff.has_rotation_change:
    print(f"ボーンが {diff.rotation_angle_deg:.1f}° 回転しています")
```

#### パターン2: 軸を取得

```python
from MonKey.utils.bone_transform_utils import get_bone_axes_world

# 現在のポーズの軸（X, Y, Z）
origin, x_axis, y_axis, z_axis = get_bone_axes_world(pose_bone)
print(f"Y軸（ヘッド→テール方向）: {y_axis}")
```

#### パターン3: 色を取得（ヒートマップ）

```python
from MonKey.utils.bone_transform_utils import magnitude_to_color

# 角度に応じた色
color = magnitude_to_color(
    diff.rotation_angle_deg,
    min_value=0.0,
    max_value=180.0,
    color_scheme="heat"  # 青→緑→黄→赤
)
print(f"色: RGB{color}")
```

## 📦 提供される機能

| 関数 | 説明 |
|------|------|
| `get_bone_transform_difference(bone)` | 位置・回転・スケールの差分を取得 |
| `get_bone_axes_world(bone, rest_pose)` | ボーンの軸ベクトルを取得 |
| `magnitude_to_color(value, ...)` | 値を色に変換 |
| `should_display_bone(bone, threshold)` | 表示判定 |

## 🎨 色スキーム

```python
# ヒートマップ（青→赤）
magnitude_to_color(value, color_scheme="heat")

# 虹色
magnitude_to_color(value, color_scheme="rainbow")

# グレースケール
magnitude_to_color(value, color_scheme="grayscale")
```

## 💡 ヒント

### ローカル変形のみ取得

```python
# 親の影響を除いた、そのボーン自身の変形のみ
diff = get_bone_transform_difference(pose_bone)
# ✓ matrix_basis を使用（親の回転は含まれない）
```

### Y軸 = ボーンの方向

```python
# Blenderのボーン座標系
origin, x, y, z = get_bone_axes_world(bone)
# y = ヘッド→テール方向
```

### 変形の種類を判定

```python
diff = get_bone_transform_difference(bone)

if diff.has_rotation_change:
    print("回転あり")
if diff.has_location_change:
    print("移動あり")
if diff.has_scale_change:
    print("スケールあり")
```

## 📚 詳細なドキュメント

より詳しい情報は `bone_transform_visualization.md` を参照してください。

