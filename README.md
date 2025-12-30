# Graph Monkey

WASDナビゲーションから始まった個人用ツールキット。アニメーション作業で欲しくなった機能を随時追加しています。

![MonKeyの基本操作](docs/images/wasd_navigation.gif)

---

## 目次

- [クイックスタート](#クイックスタート)
- [WASD ナビゲーション](#wasd-ナビゲーション)
- [Channel Navigator](#channel-navigator)
- [フレーム移動と Peek](#フレーム移動と-peek)
- [Pieメニュー](#pieメニュー)
- [UI拡張機能](#ui拡張機能)
- [便利機能](#便利機能)
- [ポーズモード支援](#ポーズモード支援)
- [設定リファレンス](#設定リファレンス)

---

## クイックスタート

### キーボードレイアウト

<img src="docs/images/keyboard_layout.png" width="50%">

| 色 | キー | 用途 |
|----|------|------|
| 🔴 | `Alt + WASD/QE` | [キーフレーム・チャンネル・ハンドル選択](#wasd-ナビゲーション) |
| 🟠 | `Y` 長押し | [Channel Navigator](#channel-navigator) |
| 🟢 | `1234` | [フレーム移動](#フレーム移動と-peek)（3D Viewでも利用可能） |
| 🔵 | `F` | [選択カーブにフォーカス](#フォーカス操作) |
| 🟡 | `Shift + T/C` | [Pieメニュー](#pieメニュー) |

---

## WASD ナビゲーション

Graph Editorでのキーフレーム編集を高速化する中核機能です。**キーボード操作だけで素早くキーフレームを編集**できるワークフローを提供します。

**Alt + WASD** でキーフレーム間・チャンネル間を自由に移動。マウスを使わず、キーボードだけで完結する直感的な操作を実現します。

| キー | 動作 |
|------|------|
| `Alt + A` / `Alt + D` | 左右のキーフレームへ移動 |
| `Alt + W` / `Alt + S` | 上下のチャンネルへ移動 |
| `+ Shift` | 拡張選択 |

<img src="docs/images/wasd_navigation.gif" width="70%">

### ハンドル選択

キーフレームのベジェハンドルを素早く選択します。

| キー | 動作 |
|------|------|
| `Alt + Q` / `Alt + E` | 左右のハンドルを選択 |
| `+ Shift` | 拡張選択 |

<img src="docs/images/handle_selection.gif" width="70%">

### フォーカス操作

| キー | 動作 |
|------|------|
| `F` | 再生範囲内で選択カーブにフォーカス |
| `Alt + F` | 選択カーブ全体を表示 |

### Auto Focus

<img src="docs/images/wasd_autofocus.gif" width="70%">

**Auto Focus on Channel Change** を有効にすると、W/Sでチャンネルを切り替えた時に選択カーブへ自動的にフォーカスします。複数のチャンネルを比較する際に便利です。

**Auto Follow Current Frame** を有効にすると、A/Dでキーフレームを移動した時に現在フレームが自動追従します（選択キーが1つの場合のみ）。

---

## Channel Navigator

`Y`キーを**長押し**すると、インタラクティブなチャンネル管理ポップアップが表示されます。

<img src="docs/images/channel_navigator.gif" width="70%">

### 操作方法

| 操作 | 動作 |
|------|------|
| マウスオーバー | チャンネル選択を切り替え |
| `Ctrl + クリック` | ソロ表示 |
| `H` / `L` / `M` | Hide / Lock / Mute トグル |
| マウスホイール | スクロール（8チャンネル以上で必要） |

Auto Focus on Channel Changeが有効なら、チャンネルを切り替えると自動的にそのカーブにフォーカスします。

<img src="docs/images/channel_navigator_autofocus.gif" width="70%">

---

## フレーム移動と Peek

Timeline、Dopesheet、Graph Editor、**View3Dなどどのエディタからでも**使えるフレーム移動機能です。

### フレームジャンプ

| キー | 動作 |
|------|------|
| `1` / `2` | 1フレーム戻る / 進む |
| `3` / `4` | 前 / 次のキーフレームへジャンプ |

<img src="docs/images/keyframe_jump_peek.gif" width="70%">

### キーフレームタイプフィルター

Timeline/Dopesheetヘッダーのフィルターで、**特定のキーフレームタイプのみをジャンプ対象**にできます。

<img src="docs/images/keyframe_filter.gif" width="70%">

KEYFRAME、BREAKDOWN、EXTREME等から選択可能。例えばKEYFRAMEとBREAKDOWNのみ選択すれば、他のタイプは`3`/`4`でスキップされます。

### Peek (パラ)

`Shift + 3/4` で隣のキーフレームを**一時的にプレビュー**します。指パラと似た感覚で前後のポーズを素早く確認できます。

```mermaid
flowchart LR
    A["Shift+3/4 押下"] --> B["プレビュー中"]
    B --> C{"離す順序"}
    C -->|"両方同時"| D["元に戻る"]
    C -->|"Shift先"| E["移動先に留まる"]
```

**Peek中の操作**: `1`/`2`で追加オフセット、`Q`でリセット

---

## Pieメニュー

### キー整列 Pie（Shift + T）

Graph Editorでキーフレームを整列するPieメニューです。

<img src="docs/images/key_align_pie.gif" width="70%">

| 項目 | 動作 |
|------|------|
| Left / Right | フレーム軸で整列（左端/右端） |
| Top / Bottom | 値軸で整列（最大値/最小値） |
| Flat | ハンドルを水平化（ウェイト付きにも対応） |

### Transform Pie（Shift + C）

Graph Editorの変形設定を素早く変更するPieメニューです。

<img src="docs/images/config_pie.png" width="50%">

Pivot Point（Center / Individual / Cursor）とプロポーショナル編集の切り替えができます。

---

## UI拡張機能

### Action ツールバー

Graph Editorのヘッダーに追加されるAction管理ボタン群です。通常Dopesheet Action Editorでしか見れない情報を、Graph Editorでも操作できるようにします。

<img src="docs/images/graph_topbar.png" width="100%">

### 補間タイプ切り替え

Graph Editorヘッダーに補間タイプ（CONSTANT / LINEAR / BEZIER）のアイコンボタンを追加。新規キーフレームの補間タイプを素早く切り替えられます。

### F-Curves設定パネル

Graph EditorのNパネル（View）にF-Curves設定を追加。Preferencesを開かずに補間設定を変更できます。

### 再生速度コントローラー

Dopesheet/Timelineヘッダーに追加される再生速度コントロールです。

<img src="docs/images/playback_speed_controller.png" width="70%">

スライダーで0.01x〜9.0xの速度調整、プリセットボタン（¼x/½x/1x/2x）でワンクリック設定。Storeボタンでオリジナル範囲を保存してから速度を変更してください。

### Channel Selection Overlay

選択中のF-Curve名をGraph Editor上に常時表示します。

<img src="docs/images/channel_overlay.png" width="50%">

### Sync Visible Range

複数のタイムベースエディタ間で表示範囲をロックします。

<img src="docs/images/sync_visible_range.png" width="50%">

ヘッダー左端の🔒アイコンをクリック。ロック中は、あるエディタでスクロール/ズームすると他のエディタ（Dopesheet、Graph Editor、NLA等）も連動します。

### チャンネル展開/折りたたみ

| キー | 動作 |
|------|------|
| `Shift + A` | 全チャンネル展開 |
| `Ctrl + Shift + A` | 全チャンネル折りたたみ |

---

## 便利機能

### Run Scripts

**File → Run Scripts** メニューから、blendファイル内に保存されたテキストを直接実行できます。

<img src="docs/images/run_scripts.png" width="100%">

Text Editorを開かなくても、blendファイル内のPythonスクリプトを実行可能。リグUIの実行などに便利です。

### Clean Animation Preview

再生速度コントローラーの隣にある**Clean Animation Preview**ボタンで、不要な表示要素を一時的に非表示にしてアニメーションをプレビューできます。

<img src="docs/images/clean_animation_preview.gif" width="70%">

ボーン名、軸表示、メッシュなどを一括非表示にして、クリーンな状態でアニメーションを確認できます。

---

## ポーズモード支援

3D Viewのポーズ編集を支援する機能です。

### Pose Transform Visualizer

ボーンの回転量・移動量を3Dビュー上に視覚的に表示します。`V`キーで切り替え可能。

<img src="docs/images/pose_visualizer.gif" width="90%">

円弧で回転量、矢印で移動量を可視化。カラースキームはHeat（変化が大きいほど赤）、Cool（青）、Grayscaleから選択可能。

### Bone Collection Solo

選択中のボーンが属するBone Collectionをソロ表示します（Blender 4.0+）。

| キー | 動作 |
|------|------|
| `/` | 選択ボーンのコレクションをソロ |
| `Alt + /` | ソロ解除 |

<img src="docs/images/bone_collection_solo.gif" width="70%">

---

## 設定リファレンス

**Edit → Preferences → Add-ons → MonKey** で設定を変更できます。

### Graph Editor

| 項目 | デフォルト | 説明 |
|------|-----------|------|
| Auto Focus on Channel Change | ON | チャンネル移動後に自動フォーカス |
| Auto Follow Current Frame | OFF | キーフレーム選択時に現在フレーム追従 |

### Channel Navigator

| 項目 | デフォルト | 説明 |
|------|-----------|------|
| Box Height / Width | 28 / 280 | ポップアップサイズ |
| Text Size | 12 | テキストサイズ |
| Max Display Count | 8 | 最大表示チャンネル数 |

### Channel Overlay

| 項目 | デフォルト | 説明 |
|------|-----------|------|
| Font Size | 24 | フォントサイズ |
| Alignment | TOP_RIGHT | 表示位置（9箇所から選択） |

### Pose Visualizer

| 項目 | デフォルト | 説明 |
|------|-----------|------|
| Show Rotation / Location | ON / ON | 回転/移動可視化 |
| Color Scheme | Heat | Heat / Cool / Grayscale |

---

## トラブルシューティング

**キーバインドが動作しない**
- Preferences → Keymapで該当キーマップが有効か確認
- 他アドオンとの競合を確認
- 正しいエディタで操作しているか確認

**Channel Navigatorが表示されない**
- `Y`キーは**長押し**で動作します（タップではない）

**再生速度変更後にフレーム範囲がおかしい**
- Storeボタンでオリジナル範囲を保存してから速度を変更してください
