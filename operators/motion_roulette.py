# pyright: reportInvalidTypeForm=false
"""
Motion Practice Roulette
日常動作アニメーション練習用のルーレットシステム

機能:
- 動作、感情、状況、技術フォーカス、複雑さをランダムに選択
- Blenderのポップアップダイアログで結果を表示
- 3回まで引き直し可能
- 確定後はオーバーレイで表示
- デッキ定義はJSONで管理（AIによる拡張対応）
"""

import json
import os
import random
from typing import Dict, List, Any, Optional, Set

import blf
import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import (
    IntProperty,
    StringProperty,
    BoolProperty,
    PointerProperty,
)

from ..utils.logging import get_logger
from ..utils.overlay_utils import calculate_aligned_position

log = get_logger(__name__)

# ==============================
# デッキ管理
# ==============================

_decks_cache: Optional[Dict[str, Any]] = None

COMPLEXITY_LABELS = {1: "単発", 2: "2ステップ", 3: "ミニ演技"}


def get_decks_path() -> str:
    """デッキJSONファイルのパスを取得"""
    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(addon_dir, "resources", "roulette_decks.json")


def validate_decks(data: Dict[str, Any]) -> List[str]:
    """
    デッキデータの整合性をチェック

    Returns:
        エラーメッセージのリスト（空なら問題なし）
    """
    errors: List[str] = []

    # 1. 必須キー確認
    required_keys = ["version", "categories", "moods", "contexts", "tech_focuses", "tag_to_tech", "motions"]
    for key in required_keys:
        if key not in data:
            errors.append(f"必須キー '{key}' がありません")

    if errors:
        return errors  # 必須キーがないと以降のチェックができない

    moods = data.get("moods", {})
    contexts = data.get("contexts", {})
    categories = data.get("categories", {})
    tech_focuses = data.get("tech_focuses", {})
    tag_to_tech = data.get("tag_to_tech", {})
    motions = data.get("motions", {})

    # 2. tag_to_tech の tech_id が tech_focuses に存在するか
    for tag, tech_ids in tag_to_tech.items():
        for tech_id in tech_ids:
            if tech_id not in tech_focuses:
                errors.append(f"tag_to_tech[{tag}] の '{tech_id}' が tech_focuses に存在しません")

    # 3. 各 motion の参照整合性チェック
    for motion_id, motion in motions.items():
        # category チェック
        cat = motion.get("category")
        if cat and cat not in categories:
            errors.append(f"motion '{motion_id}' の category '{cat}' が categories に存在しません")

        # allowed_moods チェック
        for mood_id in motion.get("allowed_moods", []):
            if mood_id not in moods:
                errors.append(f"motion '{motion_id}' の allowed_moods '{mood_id}' が moods に存在しません")

        # allowed_contexts チェック
        for ctx_id in motion.get("allowed_contexts", []):
            if ctx_id not in contexts:
                errors.append(f"motion '{motion_id}' の allowed_contexts '{ctx_id}' が contexts に存在しません")

        # tags チェック（tag_to_tech に存在するか）
        for tag in motion.get("tags", []):
            if tag not in tag_to_tech:
                errors.append(f"motion '{motion_id}' の tag '{tag}' が tag_to_tech に存在しません")

        # complexity_weights が全部 0 でないか
        cw = motion.get("complexity_weights", {})
        if cw and all(int(v) == 0 for v in cw.values()):
            errors.append(f"motion '{motion_id}' の complexity_weights がすべて 0 です")

    return errors


def load_decks(force_reload: bool = False) -> Dict[str, Any]:
    """
    デッキをJSONから読み込む（キャッシュ＆バリデーション機能付き）

    Raises:
        FileNotFoundError: JSONファイルが見つからない
        json.JSONDecodeError: JSONの構文エラー
        ValueError: 整合性チェックエラー
    """
    global _decks_cache

    if _decks_cache is not None and not force_reload:
        return _decks_cache

    decks_path = get_decks_path()

    with open(decks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 整合性チェック
    errors = validate_decks(data)
    if errors:
        for err in errors:
            log.error(f"Deck validation error: {err}")
        raise ValueError(f"roulette_decks.json に {len(errors)} 件のエラーがあります: {errors[0]}")

    _decks_cache = data
    log.debug(f"Loaded roulette decks from {decks_path}")
    return _decks_cache


def get_motions() -> Dict[str, Any]:
    return load_decks().get("motions", {})


def get_moods() -> Dict[str, Any]:
    return load_decks().get("moods", {})


def get_contexts() -> Dict[str, Any]:
    return load_decks().get("contexts", {})


def get_tech_focuses() -> Dict[str, Any]:
    return load_decks().get("tech_focuses", {})


def get_tag_to_tech() -> Dict[str, List[str]]:
    return load_decks().get("tag_to_tech", {})


def get_categories() -> Dict[str, str]:
    return load_decks().get("categories", {})


# ==============================
# ユーティリティ
# ==============================

def weighted_choice(items: List[str], weights: List[int]) -> str:
    """重み付きランダム選択"""
    total = sum(weights)
    if total == 0:
        return items[0] if items else ""
    r = random.uniform(0, total)
    upto = 0.0
    for item, w in zip(items, weights):
        upto += w
        if upto >= r:
            return item
    return items[-1]


def choose_motion(
    category_filter: Optional[List[str]] = None,
    exclude_ids: Optional[Set[str]] = None
) -> str:
    """
    モーションをランダム選択

    Args:
        category_filter: 許可するカテゴリのリスト（Noneなら全て）
        exclude_ids: 除外するmotion_idのセット
    """
    motions = get_motions()
    items = []

    for motion_id, motion in motions.items():
        # カテゴリフィルタ
        if category_filter and motion.get("category") not in category_filter:
            continue
        # 除外リスト
        if exclude_ids and motion_id in exclude_ids:
            continue
        items.append(motion_id)

    if not items:
        raise RuntimeError("指定条件に対応するモーションがありません")

    weights = [1] * len(items)
    return weighted_choice(items, weights)


def choose_mood(motion_id: str) -> str:
    """モーションに対応するムードをランダム選択"""
    motions = get_motions()
    moods = get_moods()
    motion = motions[motion_id]
    allowed = motion.get("allowed_moods") or list(moods.keys())
    weights = [moods[m]["weight"] for m in allowed]
    return weighted_choice(allowed, weights)


def choose_context(motion_id: str) -> str:
    """モーションに対応するコンテキストをランダム選択"""
    motions = get_motions()
    contexts = get_contexts()
    motion = motions[motion_id]
    allowed = motion.get("allowed_contexts") or list(contexts.keys())
    weights = [contexts[c]["weight"] for c in allowed]
    return weighted_choice(allowed, weights)


def choose_tech_focus(motion_id: str) -> str:
    """モーションに対応する技術フォーカスをランダム選択"""
    motions = get_motions()
    tech_focuses = get_tech_focuses()
    tag_to_tech = get_tag_to_tech()

    motion = motions[motion_id]
    tags = motion.get("tags", [])
    candidate_ids = set()
    for t in tags:
        for tech_id in tag_to_tech.get(t, []):
            candidate_ids.add(tech_id)

    if not candidate_ids:
        candidate_ids = set(tech_focuses.keys())

    candidates = list(candidate_ids)
    weights = [tech_focuses[tid]["weight"] for tid in candidates]
    return weighted_choice(candidates, weights)


def choose_complexity(motion_id: str) -> int:
    """モーションに対応する複雑さレベルをランダム選択"""
    motions = get_motions()
    wmap = motions[motion_id].get("complexity_weights", {"1": 1, "2": 1, "3": 1})
    levels = sorted(wmap.keys())
    weights = [int(wmap[lvl]) for lvl in levels]
    return int(weighted_choice(levels, weights))


def spin_roulette(
    result: "RouletteResult",
    category_filter: Optional[List[str]] = None
) -> None:
    """ルーレットをスピンして結果をPropertyGroupに格納"""
    motions = get_motions()
    moods = get_moods()
    contexts = get_contexts()
    tech_focuses = get_tech_focuses()

    motion_id = choose_motion(category_filter=category_filter)
    mood_id = choose_mood(motion_id)
    context_id = choose_context(motion_id)
    tech_id = choose_tech_focus(motion_id)
    complexity = choose_complexity(motion_id)

    # ID を保存（将来の履歴/再利用/除外用）
    result.motion_id = motion_id
    result.mood_id = mood_id
    result.context_id = context_id
    result.tech_id = tech_id

    # ラベルを保存（UI表示用）
    result.motion = motions[motion_id]["label"]
    result.mood = moods[mood_id]["label"]
    result.context = contexts[context_id]["label"]
    result.tech = tech_focuses[tech_id]["label"]
    result.complexity = complexity


# ==============================
# PropertyGroup
# ==============================


class RouletteResult(PropertyGroup):
    """ルーレット結果を格納するPropertyGroup"""

    # ID（内部用：履歴/再利用/除外）
    motion_id: StringProperty(name="Motion ID", default="")
    mood_id: StringProperty(name="Mood ID", default="")
    context_id: StringProperty(name="Context ID", default="")
    tech_id: StringProperty(name="Tech ID", default="")

    # ラベル（UI表示用）
    motion: StringProperty(name="動作", default="")
    mood: StringProperty(name="感情", default="")
    context: StringProperty(name="状況", default="")
    tech: StringProperty(name="技術", default="")

    complexity: IntProperty(name="複雑さ", default=1, min=1, max=3)
    remaining_rerolls: IntProperty(name="残り引き直し回数", default=3, min=0, max=3)
    is_confirmed: BoolProperty(name="確定済み", default=False)
    show_overlay: BoolProperty(name="オーバーレイ表示", default=False)


# ==============================
# オーバーレイ描画
# ==============================

_draw_handler = None


def draw_roulette_overlay():
    """3Dビューにルーレット結果をオーバーレイ表示"""
    wm = bpy.context.window_manager
    result = getattr(wm, "roulette_result", None)

    if not result or not result.show_overlay or not result.is_confirmed:
        return

    region = bpy.context.region
    if not region:
        return

    font_id = 0
    font_size = 16
    line_height = 22
    padding = 15
    text_color = (1.0, 1.0, 1.0, 0.9)
    shadow_color = (0.0, 0.0, 0.0, 0.8)

    complexity_label = COMPLEXITY_LABELS.get(result.complexity, "")
    lines = [
        "【今日の練習テーマ】",
        f"動作: {result.motion}",
        f"感情: {result.mood}",
        f"状況: {result.context}",
        f"技術: {result.tech}",
        f"複雑さ: Lv.{result.complexity} ({complexity_label})",
    ]

    blf.size(font_id, font_size)
    max_width = max(blf.dimensions(font_id, line)[0] for line in lines)
    total_height = line_height * len(lines)

    x, y = calculate_aligned_position(
        alignment="BOTTOM_RIGHT",
        space_width=region.width,
        space_height=region.height,
        object_width=max_width,
        object_height=total_height,
        offset_x=padding,
        offset_y=padding,
    )

    for i, line in enumerate(lines):
        line_y = y + total_height - (i + 1) * line_height

        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, *shadow_color)
        blf.shadow_offset(font_id, 2, -2)

        blf.color(font_id, *text_color)
        blf.position(font_id, x, line_y, 0)
        blf.draw(font_id, line)

    blf.disable(font_id, blf.SHADOW)


def register_draw_handler():
    """描画ハンドラを登録"""
    global _draw_handler
    if _draw_handler is None:
        _draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_roulette_overlay, (), 'WINDOW', 'POST_PIXEL'
        )


def unregister_draw_handler():
    """描画ハンドラを解除"""
    global _draw_handler
    if _draw_handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler, 'WINDOW')
        _draw_handler = None


# ==============================
# Blender オペレーター
# ==============================


class MONKEY_OT_roulette_spin(Operator):
    """日常動作練習用ルーレットをスピン"""
    bl_idname = "monkey.roulette_spin"
    bl_label = "Motion Roulette"
    bl_description = "日常動作アニメーション練習のためのランダムお題を生成"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        # register前やアンロード時の AttributeError を防ぐ
        result = getattr(context.window_manager, "roulette_result", None)
        if result is None:
            return True  # 初回は実行可能
        return not result.is_confirmed

    def execute(self, context):
        result = context.window_manager.roulette_result

        # JSON 読み込み＆バリデーション（エラーはここで握る）
        try:
            load_decks(force_reload=True)
        except FileNotFoundError:
            self.report({'ERROR'}, "roulette_decks.json が見つかりません")
            return {'CANCELLED'}
        except json.JSONDecodeError as e:
            self.report({'ERROR'}, f"JSON構文エラー: {e}")
            return {'CANCELLED'}
        except ValueError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        # 初期化
        result.remaining_rerolls = 3
        result.is_confirmed = False

        # 最初のスピン
        spin_roulette(result)

        # ダイアログを表示
        return bpy.ops.monkey.roulette_dialog('INVOKE_DEFAULT')


class MONKEY_OT_roulette_dialog(Operator):
    """ルーレット結果ダイアログ"""
    bl_idname = "monkey.roulette_dialog"
    bl_label = "今日の1h練習テーマ"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        # OK ボタン = 確定
        result = context.window_manager.roulette_result
        result.is_confirmed = True
        result.show_overlay = True

        register_draw_handler()

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report({'INFO'}, "練習テーマを確定しました")
        return {'FINISHED'}

    def cancel(self, context):
        # キャンセル = 確定しない（再度 spin 可能）
        # 注意: この挙動は意図的。ダイアログを閉じただけでは確定しない。
        pass

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        layout = self.layout
        result = context.window_manager.roulette_result

        box = layout.box()
        col = box.column(align=True)

        col.label(text=f"動作: {result.motion}", icon='ARMATURE_DATA')
        col.label(text=f"感情: {result.mood}", icon='HEART')
        col.label(text=f"状況: {result.context}", icon='WORLD')
        col.label(text=f"技術: {result.tech}", icon='MODIFIER')

        complexity_label = COMPLEXITY_LABELS.get(result.complexity, "")
        col.label(
            text=f"複雑さ: Lv.{result.complexity} ({complexity_label})",
            icon='LINENUMBERS_ON'
        )

        layout.separator()
        box2 = layout.box()
        box2.label(text="推奨方針", icon='INFO')
        col2 = box2.column(align=True)
        col2.scale_y = 0.8
        col2.label(text="・尺: 2〜4秒のクリップを目安に")

        if result.complexity == 1:
            col2.label(text="・単一動作に集中、ポーズと重心の流れを詰める")
        elif result.complexity == 2:
            col2.label(text="・2ステップ構成、タイミングと間を意識")
        else:
            col2.label(text="・3ステップの小シーケンス、感情変化も入れる")

        col2.label(text="・1時間で「気持ち悪さを3つ減らす」を目標に")

        layout.separator()
        row = layout.row()

        if result.remaining_rerolls > 0:
            row.operator(
                "monkey.roulette_reroll",
                text=f"引き直す (残り{result.remaining_rerolls}回)",
                icon='FILE_REFRESH'
            )
        else:
            row.label(text="引き直し回数を使い切りました", icon='ERROR')


class MONKEY_OT_roulette_reroll(Operator):
    """ルーレットを引き直す"""
    bl_idname = "monkey.roulette_reroll"
    bl_label = "Reroll"
    bl_description = "ルーレットを引き直す"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        result = context.window_manager.roulette_result

        if result.remaining_rerolls > 0:
            result.remaining_rerolls -= 1
            spin_roulette(result)

        return {'FINISHED'}


class MONKEY_OT_roulette_toggle_overlay(Operator):
    """オーバーレイ表示をトグル"""
    bl_idname = "monkey.roulette_toggle_overlay"
    bl_label = "Toggle Roulette Overlay"
    bl_description = "ルーレット結果のオーバーレイ表示を切り替え"
    bl_options = {'REGISTER'}

    def execute(self, context):
        result = getattr(context.window_manager, "roulette_result", None)

        if not result or not result.is_confirmed:
            self.report({'WARNING'}, "まだ練習テーマが確定されていません")
            return {'CANCELLED'}

        result.show_overlay = not result.show_overlay

        if result.show_overlay:
            register_draw_handler()
        else:
            unregister_draw_handler()

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        status = "表示" if result.show_overlay else "非表示"
        self.report({'INFO'}, f"オーバーレイを{status}にしました")
        return {'FINISHED'}


class MONKEY_OT_roulette_reset(Operator):
    """ルーレットをリセット（新しいテーマを引けるようにする）"""
    bl_idname = "monkey.roulette_reset"
    bl_label = "Reset Roulette"
    bl_description = "ルーレットをリセットして新しいテーマを引けるようにする"
    bl_options = {'REGISTER'}

    def execute(self, context):
        result = getattr(context.window_manager, "roulette_result", None)
        if not result:
            return {'CANCELLED'}

        # リセット
        result.is_confirmed = False
        result.show_overlay = False
        result.motion_id = ""
        result.mood_id = ""
        result.context_id = ""
        result.tech_id = ""
        result.motion = ""
        result.mood = ""
        result.context = ""
        result.tech = ""
        result.complexity = 1
        result.remaining_rerolls = 3

        unregister_draw_handler()

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        self.report({'INFO'}, "ルーレットをリセットしました")
        return {'FINISHED'}


# ==============================
# 登録
# ==============================


def register():
    bpy.types.WindowManager.roulette_result = PointerProperty(type=RouletteResult)


def unregister():
    unregister_draw_handler()
    del bpy.types.WindowManager.roulette_result
