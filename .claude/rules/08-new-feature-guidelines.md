# 新機能追加ガイドライン

新しいOperator/PropertyGroup/UI要素を追加する際のチェックリスト。

## 必須事項

### 1. モジュール冒頭のdocstring

```python
"""
機能の概要を1-2行で説明。

主な機能:
- 機能A: 簡潔な説明
- 機能B: 簡潔な説明

使用例: どのような場面で使うか
"""
```

### 2. 公開関数のdocstring

モジュール外から呼ばれる関数、複雑なロジックを持つ関数には必須:

```python
def gen_channel_info_line(fcurve):
    """
    Fカーブから人間が分かりやすいチャンネル名を生成。

    Args:
        fcurve: F-Curve オブジェクト

    Returns:
        tuple[str, tuple]: (チャンネル名, RGBA色タプル)
    """
```

### 3. PropertyGroup追加時

- [ ] ファイル冒頭に `# pyright: reportInvalidTypeForm=false` を追加
- [ ] `preferences.py` に `PointerProperty` を登録
- [ ] `.draw()` メソッドで設定UI実装
- [ ] すべてのプロパティにデフォルト値を明示

### 4. Operator追加時

- [ ] `poll()` を実装してコンテキストチェック
- [ ] `bl_description` を充実させる（ツールチップで表示される）
- [ ] 適切な `bl_options` 設定 (`{"UNDO"}` など)
- [ ] エラー時は `self.report()` でユーザーに通知

### 5. 型ヒント

複雑な関数には戻り値の型ヒントを追加:

```python
def select_target_frame(frames: list[int], current: int, go_next: bool) -> int | None:
    """..."""
```

## 推奨事項

### コード構成の判断基準

- **100行以下**: 1つのクラス/関数群でOK
- **100-200行**: 分割を検討してもいいが必須ではない
- **200行超**: ヘルパー関数を別モジュールに抽出検討

### リファクタリングが必要な兆候

コード内にマークを残す:

```python
# TODO(refactor): このヘルパーは utils に移動すべき
# FIXME: キャッシュ処理を共通化
# NOTE: Blender 4.4以降は新API利用可能
```

### 依存関係の明示

`addon.py` の自動解決で足りない場合のみ:

```python
# 循環importを避けるため、TYPE_CHECKINGで型ヒント用のみインポート
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .some_module import SomeType

# または、特殊な読み込み順序が必要な場合
DEPENDS_ON = ["utils.special_module"]
```

## CLAUDE.md / rules 更新タイミング

以下の場合のみドキュメント更新を検討:

- **新しいパターン**: 既存ルールに当てはまらない新機能
- **ユーティリティ追加**: 他の開発者が再利用すべき関数
- **大きな機能**: 複数ファイルに跨る機能追加

小規模な修正・個別Operatorの追加では不要。

## 機能追加前の自問

- [ ] 既存のモジュールに追加できるか?
- [ ] 似た機能が既に存在しないか? (`utils/`, `operators/` を確認)
- [ ] ユーザーに設定させる必要があるか? → PropertyGroup
- [ ] キーマップが必要か? → `keymap_registry.register_keymap_group()`

## Operator命名規則

| コンテキスト | プレフィックス | 例 |
|-------------|--------------|-----|
| Graph Editor | `GRAPH_OT_` | `GRAPH_OT_monkey_horizontally` |
| Pose Mode | `POSE_OT_` | `POSE_OT_solo_selected_bone_collections` |
| 汎用 | `MONKEY_OT_` | `MONKEY_OT_toggle_channel_selection_overlay` |
| キーフレーム系 | `keyframe.` (idname) | `keyframe.jump_within_range` |
