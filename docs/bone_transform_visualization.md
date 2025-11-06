# Bone Transform Visualization - 開発者ガイド

## 📖 概要

ボーンの変形（位置、回転、スケール）を3Dビューポートで視覚化するためのフレームワーク。
将来の拡張を見据えた設計で、再利用可能なユーティリティとして整理されています。

## 🏗️ アーキテクチャ

### モジュール構成

```
MonKey/
├── utils/
│   ├── bone_transform_utils.py  # 🆕 統合ユーティリティ（推奨）
│   └── pose_utils.py             # 後方互換性のため保持
└── operators/
    └── pose_rotation_visualizer.py  # 回転可視化の実装例
```

### 設計思想

1. **分離と再利用性**
   - データ取得（`bone_transform_utils.py`）
   - 描画ロジック（`pose_rotation_visualizer.py`）
   
2. **拡張性**
   - 新しい変形タイプ（スケール、位置）を簡単に追加可能
   - カスタムカラースキームに対応

3. **パフォーマンス**
   - 選択ボーンのみ処理
   - キャッシュ可能なデータ構造

## 🔧 コア機能

### 1. BoneTransformDifference データクラス

ボーンの変形情報を包括的に保持：

```python
from MonKey.utils.bone_transform_utils import get_bone_transform_difference

# ボーンの変形情報を取得
diff = get_bone_transform_difference(pose_bone)

# 位置
print(f"位置オフセット: {diff.location_offset}")
print(f"移動距離: {diff.location_magnitude}")

# 回転
print(f"回転角度: {diff.rotation_angle_deg}°")
print(f"回転軸: {diff.rotation_axis}")

# スケール
print(f"スケール差分: {diff.scale_diff}")
print(f"スケール変化: {diff.scale_magnitude}")

# 変化チェック
if diff.has_rotation_change:
    print("回転あり")
```

### 2. 軸の取得

ボーンのローカル座標軸をワールド空間で取得：

```python
from MonKey.utils.bone_transform_utils import get_bone_axes_world

# 現在のポーズの軸
origin, x_axis, y_axis, z_axis = get_bone_axes_world(pose_bone, rest_pose=False)
# Y軸 = ヘッド→テール方向

# レストポーズの軸
rest_origin, rest_x, rest_y, rest_z = get_bone_axes_world(pose_bone, rest_pose=True)
```

**重要**: Y軸がボーンの長軸（ヘッド→テール方向）です。

### 3. 色のマッピング

変形量を色に変換（ヒートマップ）：

```python
from MonKey.utils.bone_transform_utils import magnitude_to_color

# 回転角度を色に変換
color = magnitude_to_color(
    magnitude=45.0,      # 45度
    min_value=0.0,       # 0度 = 青
    max_value=180.0,     # 180度 = 赤
    color_scheme="heat"  # ヒートマップ
)

# color_scheme オプション:
# - "heat": 青→緑→黄→赤（推奨）
# - "rainbow": 虹色
# - "grayscale": グレースケール
```

## 🎨 実装例

### 例1: 回転可視化（既存実装）

```python
# operators/pose_rotation_visualizer.py

from ..utils.bone_transform_utils import (
    get_bone_axes_world,
    get_bone_transform_difference,
)

# 変形情報を取得
diff = get_bone_transform_difference(pose_bone)

# 閾値チェック
if diff.rotation_angle_deg < threshold:
    return  # 小さな回転は無視

# 軸を取得
rest_origin, rest_x, rest_y, rest_z = get_bone_axes_world(pose_bone, True)
curr_origin, curr_x, curr_y, curr_z = get_bone_axes_world(pose_bone, False)

# 描画...
```

### 例2: 位置可視化（将来の実装）

```python
def visualize_location(pose_bone, settings):
    """位置のオフセットを矢印で表示する例"""
    diff = get_bone_transform_difference(pose_bone)
    
    if not diff.has_location_change:
        return
    
    # 色を距離に応じて変更
    color = magnitude_to_color(
        diff.location_magnitude,
        min_value=0.0,
        max_value=1.0,  # 1.0ユニット
        color_scheme="heat"
    )
    
    # レストポーズの位置
    rest_pos = get_rest_position(pose_bone)
    # 現在の位置
    current_pos = get_current_position(pose_bone)
    
    # 矢印を描画
    draw_arrow(rest_pos, current_pos, color)
```

### 例3: スケール可視化（将来の実装）

```python
def visualize_scale(pose_bone, settings):
    """スケールの変化を球の大きさで表示する例"""
    diff = get_bone_transform_difference(pose_bone)
    
    if not diff.has_scale_change:
        return
    
    # スケールに応じた色
    color = magnitude_to_color(
        abs(diff.scale_magnitude),
        min_value=0.0,
        max_value=2.0,  # 2倍まで
        color_scheme="heat"
    )
    
    # ボーンの位置に球を描画（大きさ = スケール）
    origin = pose_bone.head
    radius = diff.scale_magnitude
    draw_sphere(origin, radius, color)
```

## 📊 データ構造

### BoneTransformDifference の属性

| 属性 | 型 | 説明 |
|------|-----|------|
| `location_offset` | Vector | 位置のオフセット（XYZ） |
| `location_magnitude` | float | 移動距離 |
| `rotation_quat` | Quaternion | 回転差分 |
| `rotation_angle_deg` | float | 回転角度（度） |
| `rotation_axis` | Vector | 回転軸 |
| `scale_diff` | Vector | スケール差分（各軸） |
| `scale_magnitude` | float | 平均スケール変化 |
| `has_location_change` | bool | 位置変化あり |
| `has_rotation_change` | bool | 回転変化あり |
| `has_scale_change` | bool | スケール変化あり |
| `has_any_change` | bool | 何らかの変化あり |
| `total_magnitude` | float | 総合的な変形量（0-1+） |

## 🚀 拡張ガイド

### 新しい可視化機能を追加する手順

1. **データ取得**: `bone_transform_utils.py` の関数を使用
2. **描画ロジック**: 新しいオペレーターを作成
3. **設定UI**: `PoseVisualizerSettings` に設定を追加
4. **描画ハンドラー**: `SpaceView3D.draw_handler_add()` で登録

### 例: 新しい可視化タイプの追加

```python
# operators/pose_location_visualizer.py

class PoseLocationVisualizerHandler:
    def _draw_callback(self, context):
        for pose_bone in context.selected_pose_bones:
            diff = get_bone_transform_difference(pose_bone)
            
            if diff.has_location_change:
                self._draw_location_arrow(pose_bone, diff)
    
    def _draw_location_arrow(self, pose_bone, diff):
        # 矢印の描画ロジック
        pass
```

## 💡 ベストプラクティス

### パフォーマンス

1. **選択ボーンのみ処理**
   ```python
   selected_bones = context.selected_pose_bones
   for bone in selected_bones:
       # 処理
   ```

2. **閾値による早期リターン**
   ```python
   if not should_display_bone(bone, threshold):
       continue
   ```

3. **変化チェック**
   ```python
   diff = get_bone_transform_difference(bone)
   if not diff.has_any_change:
       continue
   ```

### コードの可読性

1. **データクラスを活用**
   ```python
   # Good
   diff = get_bone_transform_difference(bone)
   angle = diff.rotation_angle_deg
   
   # Avoid
   _, angle = get_rotation_difference(bone)  # 古い方法
   ```

2. **明示的な命名**
   ```python
   # Good
   rest_origin, rest_x, rest_y, rest_z = get_bone_axes_world(bone, rest_pose=True)
   
   # Avoid
   o, x, y, z = get_bone_axes_world(bone, True)
   ```

## 🔍 トラブルシューティング

### 軸の向きがおかしい

**問題**: 描画される軸がBlenderのギズモと一致しない

**解決**:
- 現在のポーズ: `pose_bone.x_axis`, `pose_bone.y_axis`, `pose_bone.z_axis` を使用
- レストポーズ: `matrix_basis` の逆変換を使用

```python
# 正しい方法
x_axis = pose_bone.x_axis.copy()  # Blenderの内部計算を使用
```

### 親の回転が含まれてしまう

**問題**: 子ボーンの表示に親の回転が影響する

**解決**: `matrix_basis` を使用（親の影響を除外）

```python
# ローカル変形のみ
local_matrix = pose_bone.matrix_basis
```

### 色が正しく表示されない

**問題**: ヒートマップの色がおかしい

**解決**: `min_value` と `max_value` を適切に設定

```python
color = magnitude_to_color(
    angle,
    min_value=0.0,
    max_value=180.0,  # 最大値を変形タイプに応じて調整
    color_scheme="heat"
)
```

## 📚 参考資料

- [Blender Manual - Bones](https://docs.blender.org/manual/)
- `matrix_basis`: ボーンのローカル変形（親の影響なし）
- Y軸がヘッド→テール方向（Blenderのボーン座標系）

## 🔮 今後の展開

### 実装予定の機能

1. **位置可視化**
   - 矢印で移動方向と距離を表示
   - グリッドスナップ表示

2. **スケール可視化**
   - 球やボックスでスケール変化を表示
   - 各軸ごとの非均等スケール

3. **統合ビュー**
   - 位置・回転・スケールを同時表示
   - カスタマイズ可能なレイアウト

4. **アニメーション対応**
   - タイムライン上での変化を可視化
   - キーフレーム間の補間表示

5. **エクスポート機能**
   - 変形データのCSV出力
   - スクリーンショット/動画キャプチャ

## 🤝 コントリビューション

新しい可視化機能を追加する際は、このガイドに従ってください。
質問や提案があれば、issueを作成してください。

