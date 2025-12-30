"""
シンプルな国際化(i18n)モジュール。

Blenderの言語設定に基づいて英語/日本語を切り替える。

使用例:
    from .utils.i18n import _
    label = _("WASD_DESC")  # 言語に応じたテキストを取得
"""

import bpy

# 翻訳辞書
# キー: 識別子, 値: {"en": 英語, "ja": 日本語}
TRANSLATIONS = {
    # === Addon Description ===
    "ADDON_DESC": {
        "en": "Animation workflow toolkit for Graph Editor.\nKeyboard-driven keyframe editing and channel management.",
        "ja": "Graph Editor用アニメーションワークフローツールキット。\nキーボード操作によるキーフレーム編集とチャンネル管理。",
    },

    # === Quick Start ===
    "QUICK_START": {
        "en": "Quick Start (Graph Editor)",
        "ja": "クイックスタート (Graph Editor)",
    },
    "QUICK_START_DESC": {
        "en": "Learn the basics in 1 minute:",
        "ja": "1分で基本を覚える:",
    },
    "WASD_QUICK": {
        "en": "Alt+WASD: Navigate keyframes/channels",
        "ja": "Alt+WASD: キーフレーム/チャンネル移動",
    },
    "NUM_QUICK": {
        "en": "1234: Frame jump (works in 3D View too)",
        "ja": "1234: フレームジャンプ (3D Viewでも使用可)",
    },
    "NAV_QUICK": {
        "en": "Y (hold): Channel Navigator",
        "ja": "Y (長押し): Channel Navigator",
    },
    "PIE_QUICK": {
        "en": "Shift+T/C: Pie menus",
        "ja": "Shift+T/C: Pieメニュー",
    },

    # === Features ===
    "FEATURES": {
        "en": "Features",
        "ja": "機能一覧",
    },
    "FEATURE_WASD": {
        "en": "WASD Navigation - Keyboard-based keyframe editing in Graph Editor",
        "ja": "WASDナビゲーション - Graph Editorでのキーボード操作",
    },
    "FEATURE_NAVIGATOR": {
        "en": "Channel Navigator - Interactive channel switching (Y key hold)",
        "ja": "Channel Navigator - インタラクティブなチャンネル切り替え (Y長押し)",
    },
    "FEATURE_PEEK": {
        "en": "Peek - Preview adjacent keyframes temporarily (Shift+3/4)",
        "ja": "Peek - 隣のキーフレームを一時プレビュー (Shift+3/4)",
    },
    "FEATURE_PIE": {
        "en": "Pie Menus - Quick access to alignment and transform settings",
        "ja": "Pieメニュー - 整列・変形設定への素早いアクセス",
    },
    "FEATURE_PLAYBACK": {
        "en": "Playback Speed Controller - Adjust playback speed with time remapping",
        "ja": "再生速度コントローラー - タイムリマップで再生速度を調整",
    },
    "FEATURE_VISUALIZER": {
        "en": "Pose Visualizer - Visualize bone rotation/location changes (V key)",
        "ja": "Pose Visualizer - ボーンの回転/移動量を可視化 (Vキー)",
    },

    # === Tab Names ===
    "TAB_HOW_TO_USE": {
        "en": "How to use",
        "ja": "使い方",
    },
    "TAB_SETTINGS": {
        "en": "Settings",
        "ja": "設定",
    },
    "TAB_KEYMAP": {
        "en": "Keymap",
        "ja": "キーマップ",
    },

    # === Settings Labels ===
    "GRAPH_EDITOR_SETTINGS": {
        "en": "Graph Editor",
        "ja": "Graph Editor",
    },
    "CHANNEL_NAV_SETTINGS": {
        "en": "Channel Navigator",
        "ja": "Channel Navigator",
    },
    "OVERLAY_SETTINGS": {
        "en": "Channel Overlay",
        "ja": "Channel Overlay",
    },
    "POSE_VISUALIZER_SETTINGS": {
        "en": "Pose Visualizer",
        "ja": "Pose Visualizer",
    },
    "PLAYBACK_SETTINGS": {
        "en": "Playback Preview",
        "ja": "再生プレビュー",
    },
    "CHANNEL_MOVE": {
        "en": "Channel Movement (Alt+W/S)",
        "ja": "チャンネル移動 (Alt+W/S)",
    },
    "KEYFRAME_MOVE": {
        "en": "Keyframe Movement (Alt+A/D)",
        "ja": "キーフレーム移動 (Alt+A/D)",
    },

    # === Documentation Link ===
    "DOC_LINK": {
        "en": "See README for full documentation",
        "ja": "詳細はREADMEを参照",
    },
    "GITHUB_URL": {
        "en": "https://github.com/Pluglug/graph_monkey",
        "ja": "https://github.com/Pluglug/graph_monkey",
    },
}


def get_language():
    """Blenderの言語設定を取得（ja/en）"""
    locale = bpy.app.translations.locale
    if locale and locale.startswith("ja"):
        return "ja"
    return "en"


def _(key, **kwargs):
    """
    翻訳テキストを取得する。

    Args:
        key: 翻訳キー
        **kwargs: format()に渡す引数

    Returns:
        翻訳されたテキスト。キーが見つからない場合はキーをそのまま返す。
    """
    lang = get_language()

    if key in TRANSLATIONS:
        text = TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get("en", key))
    else:
        # キーが見つからない場合はそのまま返す
        text = key

    if kwargs:
        text = text.format(**kwargs)

    return text


def get_all_keys():
    """すべての翻訳キーを取得（デバッグ用）"""
    return list(TRANSLATIONS.keys())
