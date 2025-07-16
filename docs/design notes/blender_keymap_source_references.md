# Blender KeyMap システム - C ソースコード参照リスト

## 主要なファイルと関数

### 1. イベントシステム・KeyMap選択の中核
- **ファイル**: `source/blender/windowmanager/intern/wm_event_system.cc`
  - `wm_handlers_do_intern()` - Line 3414
    - メインのイベント処理ループ
    - 登録されたハンドラーを優先度順に実行
  - `wm_eventmatch()` - Line 1582
    - イベントとKeyMapアイテムのマッチング処理
  - `wm_handler_operator_call()` - Line 1866
    - KeyMapマッチ時のオペレータ実行

### 2. KeyMap管理・ポーリング
- **ファイル**: `source/blender/windowmanager/intern/wm_keymap.cc`
  - `WM_keymap_poll()` - Line 470
    - KeyMapの有効性チェック（poll関数の実行）
  - `WM_keymap_find_all()` - Line 907
    - KeyMapの検索・取得
  - `WM_keymap_active()` - Line 937
    - アクティブなKeyMapの取得
  - `WM_keymap_ensure()` - Line 794
    - KeyMapの作成・登録

### 3. KeyMapハンドラー管理
- **ファイル**: `source/blender/windowmanager/intern/wm_event_system.cc`
  - `WM_event_get_keymaps_from_handler()` - Line 6480
    - ハンドラーからKeyMapリストを取得
  - `WM_event_add_keymap_handler()` - Line 6415
    - KeyMapハンドラーの追加・登録

### 4. コンテキスト推測・KeyMap決定
- **ファイル**: `source/blender/windowmanager/intern/wm_keymap_utils.cc`
  - `WM_keymap_guess_from_context()` - Line 77
    - コンテキストからKeyMapを推測
    - space_type、modeに基づくKeyMap決定ロジック

## スペース別KeyMap登録

### 5. 3D View のKeyMap登録
- **ファイル**: `source/blender/editors/space_view3d/space_view3d.cc`
  - `view3d_main_region_init()` - Line 332
    - 3D ViewのWINDOWリージョン用KeyMap登録
    - 優先度順にすべてのモード別KeyMapを登録
  - `view3d_header_region_init()` - Line 372
    - 3D ViewのHEADERリージョン用KeyMap登録
  - `view3d_tools_region_init()` - Line 403
    - 3D ViewのTOOLSリージョン用KeyMap登録

### 6. 画像エディタのKeyMap登録
- **ファイル**: `source/blender/editors/space_image/space_image.cc`
  - `image_main_region_init()` - Line 294
    - 画像エディタのWINDOWリージョン用KeyMap登録

### 7. ノードエディタのKeyMap登録
- **ファイル**: `source/blender/editors/space_node/space_node.cc`
  - `node_main_region_init()` - Line 389
    - ノードエディタのWINDOWリージョン用KeyMap登録

### 8. アウトライナーのKeyMap登録
- **ファイル**: `source/blender/editors/space_outliner/space_outliner.cc`
  - `outliner_main_region_init()` - Line 222
    - アウトライナーのWINDOWリージョン用KeyMap登録

### 9. プロパティエディタのKeyMap登録
- **ファイル**: `source/blender/editors/space_buttons/space_buttons.cc`
  - `buttons_main_region_init()` - Line 170
    - プロパティエディタのWINDOWリージョン用KeyMap登録

## モード別KeyMap定義

### 10. 3D View KeyMap定義
- **ファイル**: `source/blender/editors/space_view3d/view3d_ops.cc`
  - `view3d_keymap()` - Line 236
    - 3D View基本KeyMapの定義

### 11. メッシュ編集KeyMap定義
- **ファイル**: `source/blender/editors/mesh/mesh_ops.cc`
  - `mesh_keymap()` - Line 364
    - メッシュ編集モードのKeyMap定義
    - Poll関数: `ED_operator_editmesh`

### 12. オブジェクトモードKeyMap定義
- **ファイル**: `source/blender/editors/object/object_ops.cc`
  - `object_keymap()` - Line 339
    - オブジェクトモードのKeyMap定義
    - Poll関数: `object_mode_poll`

### 13. スカルプトモードKeyMap定義
- **ファイル**: `source/blender/editors/sculpt_paint/sculpt_ops.cc`
  - `sculpt_keymap()` - Line 1162
    - スカルプトモードのKeyMap定義
    - Poll関数: `SCULPT_mode_poll`

### 14. ペイントモードKeyMap定義
- **ファイル**: `source/blender/editors/sculpt_paint/paint_ops.cc`
  - `paint_keymap()` - Line 1086
    - ペイントモード全般のKeyMap定義
  - `weight_paint_keymap()` - Line 1094
    - ウェイトペイントのKeyMap定義
    - Poll関数: `weight_paint_mode_poll`
  - `vertex_paint_keymap()` - Line 1102
    - 頂点ペイントのKeyMap定義
    - Poll関数: `vertex_paint_mode_poll`

### 15. ポーズモードKeyMap定義
- **ファイル**: `source/blender/editors/armature/armature_ops.cc`
  - `pose_keymap()` - Line 287
    - ポーズモードのKeyMap定義
    - Poll関数: `pose_mode_poll`

### 16. アーマチュア編集KeyMap定義
- **ファイル**: `source/blender/editors/armature/armature_ops.cc`
  - `armature_keymap()` - Line 320
    - アーマチュア編集モードのKeyMap定義
    - Poll関数: `armature_edit_poll`

## Poll関数の実装

### 17. 基本的なPoll関数
- **ファイル**: `source/blender/editors/screen/screen_ops.cc`
  - `ED_operator_editmesh()` - Line 156
    - メッシュ編集モード判定
  - `ED_operator_editarmature()` - Line 184
    - アーマチュア編集モード判定
  - `ED_operator_posemode()` - Line 208
    - ポーズモード判定
  - `ED_operator_object()` - Line 234
    - オブジェクトモード判定

### 18. ペイントモード用Poll関数
- **ファイル**: `source/blender/editors/sculpt_paint/sculpt_ops.cc`
  - `SCULPT_mode_poll()` - Line 89
    - スカルプトモード判定
- **ファイル**: `source/blender/editors/sculpt_paint/paint_ops.cc`
  - `weight_paint_mode_poll()` - Line 52
    - ウェイトペイントモード判定
  - `vertex_paint_mode_poll()` - Line 58
    - 頂点ペイントモード判定

## コンテキスト取得

### 19. コンテキスト情報の取得
- **ファイル**: `source/blender/blenkernel/intern/context.cc`
  - `CTX_data_mode_enum()` - Line 1056
    - 現在のモード（enum値）を取得
  - `CTX_wm_space_data()` - Line 344
    - 現在のSpaceDataを取得
  - `CTX_wm_area()` - Line 300
    - 現在のAreaを取得
  - `CTX_wm_region()` - Line 312
    - 現在のRegionを取得
  - `CTX_data_edit_object()` - Line 798
    - 編集中のオブジェクトを取得

### 20. データ型定義
- **ファイル**: `source/blender/makesdna/DNA_space_types.h`
  - `eSpace_Type` - Line 95
    - スペースタイプの定義
  - `eRegionType` - Line 1582
    - リージョンタイプの定義

- **ファイル**: `source/blender/makesdna/DNA_object_enums.h`
  - `eObjectMode` - Line 34
    - オブジェクトモードの定義

## 重要なデータ構造

### 21. KeyMapデータ構造
- **ファイル**: `source/blender/makesdna/DNA_windowmanager_types.h`
  - `wmKeyMap` - Line 293
    - KeyMap構造体の定義
  - `wmKeyMapItem` - Line 249
    - KeyMapアイテム構造体の定義
  - `wmEventHandler_Keymap` - Line 364
    - KeyMapハンドラー構造体の定義

## バージョン固有の注意点

### Blender 3.2以降の変更点
- **ファイル**: `source/blender/editors/space_view3d/space_view3d.cc`
  - Grease Pencil関連のKeyMapが大幅に変更
  - 新しいCurves編集モードが追加

### Blender 4.0以降の変更点
- **ファイル**: `source/blender/editors/space_view3d/space_view3d.cc`
  - Point Cloud編集モードが追加
  - Grease Pencil v3対応の新しいKeyMapが追加

## 実装パターン

### KeyMap登録の典型的なパターン
```c
// 1. KeyMapの確保
wmKeyMap *keymap = WM_keymap_ensure(wm->defaultconf, "KeyMap名", spaceid, regionid);

// 2. Poll関数の設定
keymap->poll = poll_function;

// 3. ハンドラーに登録
WM_event_add_keymap_handler(&region->handlers, keymap);
```

### Poll関数の典型的なパターン
```c
static bool mode_poll(bContext *C)
{
    // コンテキストから必要な情報を取得
    Object *obedit = CTX_data_edit_object(C);
    
    // 条件チェック
    if (obedit && obedit->type == OB_MESH) {
        return true;
    }
    return false;
}
```

この参照リストは、PMEのkeymap_helper改善に必要な、BlenderのKeyMap選択ロジックの完全な実装詳細を提供します。