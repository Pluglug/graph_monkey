# PME 10個アイテム実装ガイド - 実証済みノウハウ

## 🎯 実装成功の要点

PMEスタイルの10個アイテムPie Menuを実装する際に発見した重要なポイントと解決方法をまとめます。

## 🔑 成功の鍵となった技術要素

### 1. **レイアウト構造の理解**
```python
# 基本構造
pie = layout.menu_pie()

# 標準8個（Blender標準）
for i in range(8):
    pie.operator(...)

# 拡張2個（PME独自）
pie.separator() × 2  # 重要：分離
col1 = pie.column()  # 9番目用
col2 = pie.column()  # 10番目用（別のカラム）
```

### 2. **PMEの実際の配置ロジック**
```python
# PMEの実装に基づく条件分岐
if has_item8 or has_item9:
    pie.separator()
    pie.separator()

if has_item8:  # 9番目
    col = pie.column()
    # 上部ギャップ → アイテム
    
elif has_item9:  # 9番目が空の場合
    pie.separator()

if has_item9:  # 10番目
    col2 = pie.column()
    # アイテム → 下部ギャップ
```

### 3. **ギャップサイズの重要性**
```python
# 重要：PMEと同じ直接値を使用
gap.scale_y = pie_extra_slot_gap_size  # デフォルト25

# NG例：小さすぎる値
gap.scale_y = pie_extra_slot_gap_size / 10.0  # 被りの原因
```

## 🚨 失敗パターンと解決方法

### 問題1: 9番目が2番目に被る
**原因**: 同一columnでの連続配置
```python
# NG: 同じカラムに配置
col = pie.column()
col.operator("dummy_09")
col.operator("dummy_10")  # 被る

# OK: 別々のカラムに配置
col1 = pie.column()
col1.operator("dummy_09")

col2 = pie.column()  # 新しいカラム
col2.operator("dummy_10")
```

### 問題2: 10番目が見当たらない
**原因**: PMEの条件分岐ロジックの誤解
```python
# NG: 独立した処理
if has_item8:
    # 9番目処理
if has_item9:
    # 10番目処理

# OK: PMEと同じ条件分岐
if has_item8:
    # 9番目処理
elif has_item9:
    # separatorを追加
if has_item9:
    # 10番目処理
```

### 問題3: ギャップサイズが小さすぎる
**原因**: スケール値の誤解
```python
# NG: 過小なスケール
gap.scale_y = 5 / 10.0  # 0.5（小さすぎ）

# OK: PMEと同じ値
gap.scale_y = 25  # 十分なスペース
```

## 📊 PMEのデータ構造理解

### PMIアイテム配列
```python
pm.pmis[0-7]  # 標準の8個
pm.pmis[8]    # 9番目（pmi8、上部中央）
pm.pmis[9]    # 10番目（pmi9、下部中央）
```

### レイアウトヘルパーの役割
```python
lh.lt(col.column(), operator_context='INVOKE_DEFAULT')
lh.layout.scale_y = 1.5  # アイテムサイズ調整
```

## 🎨 ベストプラクティス

### 1. **段階的実装**
```python
# Step 1: 標準8個の確認
pie.operator(...) × 8

# Step 2: 分離の確認  
pie.separator() × 2

# Step 3: 9番目の追加
col = pie.column()
gap + item

# Step 4: 10番目の追加
col2 = pie.column()
item + gap
```

### 2. **設定の外部化**
```python
class PME_Settings(bpy.types.PropertyGroup):
    pie_extra_slot_gap_size: IntProperty(
        default=25,  # 十分な初期値
        min=3,
        max=100,
    )
```

### 3. **デバッグ用の可視化**
```python
# 設定パネルで動的調整
layout.prop(settings, "pie_extra_slot_gap_size")
layout.operator("view3d.pme_demo_call_fixed")
```

## 🔧 実装テンプレート

### 最小構成
```python
def draw(self, context):
    layout = self.layout
    pie = layout.menu_pie()
    
    # 標準8個
    for i in range(8):
        pie.operator(f"dummy_{i+1:02d}")
    
    # 拡張2個
    gap_size = 25
    
    pie.separator()
    pie.separator()
    
    # 9番目
    col = pie.column()
    gap = col.column()
    gap.separator()
    gap.scale_y = gap_size
    
    item = col.column()
    item.scale_y = 1.5
    item.operator("dummy_09")
    
    # 10番目
    col2 = pie.column()
    item2 = col2.column()
    item2.scale_y = 1.5
    item2.operator("dummy_10")
    
    gap2 = col2.column()
    gap2.separator()
    gap2.scale_y = gap_size
```

## 📈 パフォーマンス考慮事項

### 1. **条件チェック**
```python
# アイテム存在チェックを事前に実行
has_item8 = check_item_exists(8)
has_item9 = check_item_exists(9)

# 無駄な処理を避ける
if not (has_item8 or has_item9):
    return  # 拡張アイテムなし
```

### 2. **レイアウト最適化**
```python
# column()の再利用を避ける
col1 = pie.column()  # 9番目専用
col2 = pie.column()  # 10番目専用
```

## 🎯 重要な発見

### 1. **BlenderのPie Menu制限**
- `menu_pie()`は8個までが自動配置
- 9個目以降は予測不可能な位置
- PMEは`column()`で独立配置して回避

### 2. **ギャップサイズの影響**
- 小さすぎると被りが発生
- 大きすぎるとレイアウトが崩れる
- デフォルト25が実用的

### 3. **条件分岐の重要性**
- PMEの実装は`if`/`elif`/`if`構造
- 単純な`if`×2では正しく動作しない

## 🔗 関連ファイル

- `operators.py:_draw_pm()`: PMEの実装参考
- `preferences.py`: ギャップサイズ設定
- `layout_helper.py`: レイアウト制御
- `Notes/pie_menu_10_items_sample_fixed.py`: 動作する実装例

## 🏆 成功指標

✅ **標準8個が正しい位置に配置**  
✅ **9番目が上部中央に配置（被りなし）**  
✅ **10番目が下部中央に配置**  
✅ **ギャップサイズで調整可能**  
✅ **PMEの実装と同じ動作**  

このガイドに従うことで、PMEと同等の10個アイテムPie Menuが実装できます！ 