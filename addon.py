"""
Framework for Blender addon development

- Automatic module loading and dependency management
- Detection and resolution of circular dependencies
- Automatic class registration
"""

from __future__ import annotations

import importlib
import inspect
import os
import pkgutil
import re
import sys
import traceback
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Pattern, Set

import bpy
from bpy.utils import user_resource

if TYPE_CHECKING:
    from .preferences import MonKeyPreferences

# from .utils.logging import get_logger  # TODO: Printをログに変更
# log = get_logger(__name__)

# ======================================================
# グローバル設定
# ======================================================

DBG_INIT = True
CREATE_DEPENDENCY_GRAPH = True  # Create dependency graph
BACKGROUND = False
VERSION = (0, 0, 0)  # Addon version
BL_VERSION = (0, 0, 0)  # Supported Blender version

ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
ADDON_ID = os.path.basename(ADDON_PATH)
ADDON_PREFIX = "".join([s[0] for s in re.split(r"[_-]", ADDON_ID)]).upper()
ADDON_PREFIX_PY = ADDON_PREFIX.lower()

# モジュール管理用
MODULE_NAMES: List[str] = []  # ロード順序が解決されたモジュールリスト
MODULE_PATTERNS: List[Pattern] = []  # 読み込み対象のモジュールパターン


_class_cache: List[bpy.types.bpy_struct] = None

# ======================================================
# ユーティリティ関数
# ======================================================


def get_uprefs(context: bpy.types.Context = bpy.context) -> bpy.types.Preferences:
    """
    Get user preferences

    Args:
        context: Blender context (defaults to bpy.context)

    Returns:
        bpy.types.Preferences: User preferences

    Raises:
        AttributeError: If preferences cannot be accessed
    """
    preferences = getattr(context, "preferences", None)
    if preferences is not None:
        return preferences
    raise AttributeError("Could not access preferences")


def get_prefs(context: bpy.types.Context = bpy.context) -> MonKeyPreferences:
    """
    Get addon preferences

    Args:
        context: Blender context (defaults to bpy.context)

    Returns:
        bpy.types.AddonPreferences: Addon preferences

    Raises:
        KeyError: If addon is not found
    """
    user_prefs = get_uprefs(context)
    addon_prefs = user_prefs.addons.get(ADDON_ID)
    if addon_prefs is not None:
        return addon_prefs.preferences
    raise KeyError(f"Addon '{ADDON_ID}' not found")


def get_config_dir() -> str:
    """Gets the addon's configuration directory path."""
    config_path = user_resource("CONFIG", path="addons", create=True)
    return os.path.join(config_path, ADDON_ID)


def get_presets_dir() -> str:
    """Gets the pattern presets directory path. Creates the directory if it doesn't exist."""
    presets_dir = os.path.join(ADDON_PATH, "resources", "presets")
    os.makedirs(presets_dir, exist_ok=True)
    return presets_dir


def get_user_presets_dir() -> str:
    """Gets the user's pattern presets directory path. Creates the directory if it doesn't exist."""
    presets_dir = os.path.join(get_config_dir(), "presets")
    os.makedirs(presets_dir, exist_ok=True)
    return presets_dir


# ======================================================
# モジュール管理コア
# ======================================================


def init_addon(
    module_patterns: List[str],
    use_reload: bool = False,
    background: bool = False,
    prefix: str = None,
    prefix_py: str = None,
    force_order: List[str] = None,  # トラブルシューティング用
) -> None:
    """
    アドオンを初期化

    この関数は次の順序で処理を行います:
    1. モジュールパターンに基づいてロード対象モジュールを収集
    2. 各モジュールをロード（必要に応じてリロード）
    3. モジュール間の依存関係を解析
    4. トポロジカルソートによるロード順序の決定
    5. モジュールリストの保存とデバッグ情報の出力

    Args:
        module_patterns (List[str]): ロードするモジュールのパターンリスト
        use_reload (bool): リロードを使用するか
        background (bool): バックグラウンドモード
        prefix (str): オペレータ接頭辞
        prefix_py (str): Python用接頭辞
        force_order (List[str]): 強制的なモジュールロード順序（トラブルシューティング用）

    Example:
        init_addon(
            module_patterns=[
                "core",
                "utils.*",
                "operators.*_ops",
                "ui.panels"
            ],
            use_reload=True
        )
    """
    global VERSION, BL_VERSION, ADDON_PREFIX, ADDON_PREFIX_PY, _class_cache

    # 初期化処理
    _class_cache = None
    module = sys.modules[ADDON_ID]
    VERSION = module.bl_info.get("version", VERSION)
    BL_VERSION = module.bl_info.get("blender", BL_VERSION)

    if prefix:
        ADDON_PREFIX = prefix
    if prefix_py:
        ADDON_PREFIX_PY = prefix_py

    # パターンコンパイル
    MODULE_PATTERNS[:] = [
        re.compile(f"^{ADDON_ID}\.{p.replace('*', '.*')}$") for p in module_patterns
    ]

    # アドオンモジュール自体も追加
    MODULE_PATTERNS.append(re.compile(f"^{ADDON_ID}$"))

    # モジュール収集
    module_names = list(_collect_module_names())

    # モジュール事前ロード
    for module_name in module_names:
        try:
            if use_reload and module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)
        except Exception as e:
            print(f">>> Failed to load module {module_name}: {str(e)}")
            traceback.print_exception(type(e), e, e.__traceback__, limit=2)

    # 依存関係解決
    if force_order:
        # ------------------------------------------------------
        # トラブルシューティング用: 強制的なモジュールロード順序
        # ------------------------------------------------------
        if DBG_INIT:
            print("\n=== 強制指定されたモジュールロード順序を使用 ===")
        sorted_modules = _resolve_forced_order(force_order, module_names)
    else:
        # ------------------------------------------------------
        # 通常の依存関係解析による自動順序決定
        # ------------------------------------------------------
        sorted_modules = _sort_modules(module_names)

    MODULE_NAMES[:] = sorted_modules

    if DBG_INIT:
        print("\n=== 最終モジュールロード順序 ===")
        for i, mod in enumerate(MODULE_NAMES, 1):
            short = short_name(mod)
            print(f"{i:2d}. {short}")


def _resolve_forced_order(force_order: List[str], module_names: List[str]) -> List[str]:
    """
    強制的な順序指定のためのヘルパー関数（トラブルシューティング用）

    Args:
        force_order: 強制的な順序リスト
        module_names: 全モジュールリスト

    Returns:
        List[str]: 解決された順序リスト
    """
    # プレフィックスの追加（省略時の利便性向上）
    processed_order = []
    for mod in force_order:
        if not mod.startswith(ADDON_ID):
            full_name = f"{ADDON_ID}.{mod}"
        else:
            full_name = mod

        if full_name in module_names:
            processed_order.append(full_name)
        else:
            print(f"Warning: Specified module {full_name} not found")

    # 指定されていないモジュールを末尾に追加
    remaining = [m for m in module_names if m not in processed_order]
    return processed_order + remaining


# ======================================================
# 依存関係解析
# ======================================================


def _analyze_dependencies(module_names: List[str]) -> Dict[str, Set[str]]:
    """
    モジュール間の依存関係を解析

    複数のソースから依存関係を検出:
    1. インポート文の解析（import文、from-import文）
    2. クラスのプロパティ型（PointerProperty, CollectionProperty）
    3. 明示的に指定された依存関係（DEPENDS_ON属性）

    重要: グラフの方向は「依存先→依存元」（被依存関係）
    例: A→B はモジュールBがモジュールAを使用することを示す
    これはトポロジカルソートの際に正しいロード順序を得るため

    Returns:
        Dict[str, Set[str]]: 依存関係グラフ（key: モジュール, value: そのモジュールに依存する他のモジュール）
    """
    # インポート依存関係
    import_graph = _analyze_imports(module_names)

    # コード内での明示的・暗黙的依存関係
    graph = defaultdict(set)
    pdtype = bpy.props._PropertyDeferred

    # インポート依存関係をマージ
    # NOTE: _analyze_imports は {依存元: {依存先}} の辞書を返す。
    #       一方、トポロジカルソートで使う graph は {依存先: {依存元}} の形式にする必要がある。
    #       そのため、import_graph をイテレートし、依存関係を逆転させて graph に追加する。
    #       以前の実装 (graph[mod_name].update(deps)) では方向が逆だったため、循環依存が誤検出されていた。
    for (
        mod_name,
        deps,
    ) in import_graph.items():  # mod_name = 依存元, deps = 依存先のセット
        for dep in deps:  # dep = 依存先
            graph[dep].add(mod_name)  # graph[依存先].add(依存元)

    for mod_name in module_names:
        mod = sys.modules.get(mod_name)
        if not mod:
            continue

        # クラス依存関係解析
        for _, cls in inspect.getmembers(mod, _is_bpy_class):
            for prop in getattr(cls, "__annotations__", {}).values():
                if isinstance(prop, pdtype) and prop.function in [
                    bpy.props.PointerProperty,
                    bpy.props.CollectionProperty,
                ]:
                    dep_cls = prop.keywords.get("type")
                    if not dep_cls:
                        continue

                    dep_mod = dep_cls.__module__
                    # 同一モジュールなら依存関係扱いしない (誤検知防止)
                    if dep_mod == mod_name:
                        continue

                    # 依存関係の正しい方向: 依存先→依存元（被依存関係）
                    if dep_mod in module_names:
                        # 注: 方向は「依存先 → 依存元」
                        graph[dep_mod].add(mod_name)

        # 明示的依存関係
        if hasattr(mod, "DEPENDS_ON"):
            for dep in mod.DEPENDS_ON:
                # プレフィックスが付いていない場合は付与
                dep_full = f"{ADDON_ID}.{dep}" if not dep.startswith(ADDON_ID) else dep
                if dep_full in module_names:
                    # 注: 方向は「依存先 → 依存元」
                    graph[dep_full].add(mod_name)
                else:
                    if DBG_INIT:
                        print(
                            f"  警告: {mod_name} の依存先 {dep_full} が見つかりません"
                        )

    if DBG_INIT:
        print("\n=== 依存関係詳細 ===")
        for mod, deps in sorted(graph.items()):
            if deps:
                print(f"{short_name(mod)} は以下から依存されています:")
                for d in sorted(deps):
                    print(f"  → {short_name(d)}")

    return graph


def _analyze_imports(module_names: List[str]) -> Dict[str, Set[str]]:
    """
    インポート文から依存関係を解析する

    Python ASTを使用してインポート文を解析し、モジュール間の依存関係を抽出します。
    以下のパターンを処理:
    - 直接インポート: import x.y.z
    - 相対インポート: from .x import y
    - サブモジュールインポート: from x.y import z
    `if TYPE_CHECKING:` ブロック内のインポートは無視されます。

    Args:
        module_names: 解析対象のモジュール名リスト

    Returns:
        Dict[str, Set[str]]: モジュールが依存する他のモジュールのセット
        注: 方向は「依存元 → 依存先」（関数の呼び出し元で逆転）
    """
    import ast

    graph = defaultdict(set)

    class ImportVisitor(ast.NodeVisitor):
        def __init__(self, mod_name, graph):
            self.mod_name = mod_name
            self.graph = graph
            self.in_type_checking_block = False

        def visit_If(self, node: ast.If):
            # if TYPE_CHECKING: ブロックか判定
            is_type_checking = (
                isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"
            )
            original_state = self.in_type_checking_block
            if is_type_checking:
                self.in_type_checking_block = True

            # 子ノードを訪問 (If文のbody, orelse)
            self.generic_visit(node)

            # フラグを元に戻す
            self.in_type_checking_block = original_state

        def _add_dependency(self, imported_name):
            """依存関係をグラフに追加するヘルパー"""
            # アドオン内のモジュールのみ対象
            if imported_name.startswith(ADDON_ID):
                self.graph[self.mod_name].add(imported_name)
            # サブモジュールのインポートも解析（例: import x.y）
            # ただし、トップレベルのインポートのみ対象とする
            elif "." not in self.mod_name:  # トップレベルからのインポートの場合のみ考慮
                parts = imported_name.split(".")
                current_prefix = ""
                for part in parts:
                    current_prefix = (
                        f"{current_prefix}.{part}" if current_prefix else part
                    )
                    full_name = f"{ADDON_ID}.{current_prefix}"
                    if full_name in module_names:
                        self.graph[self.mod_name].add(full_name)

        def visit_Import(self, node: ast.Import):
            # TYPE_CHECKING ブロック内なら無視
            if self.in_type_checking_block:
                return

            for alias in node.names:
                self._add_dependency(alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom):
            # TYPE_CHECKING ブロック内なら無視
            if self.in_type_checking_block:
                return

            base_path = ""  # linter エラー回避のため初期化
            if node.module:
                module_path = node.module
                # 相対インポートの処理
                if node.level > 0:
                    parent_parts = self.mod_name.split(".")
                    if node.level > len(parent_parts) - 1:
                        return  # 範囲外の相対インポート
                    base_path = ".".join(parent_parts[: -node.level])
                    module_path = (
                        f"{base_path}.{module_path}" if module_path else base_path
                    )
                else:
                    # アドオン外からの絶対インポートの場合、プレフィックスをつける試み
                    if not module_path.startswith(ADDON_ID + "."):
                        potential_full_path = f"{ADDON_ID}.{module_path}"
                        if any(m.startswith(potential_full_path) for m in module_names):
                            module_path = potential_full_path

                # アドオン内のインポートか確認
                if module_path.startswith(ADDON_ID):
                    if module_path in module_names:
                        self.graph[self.mod_name].add(module_path)

                    # from A.B import C のようなケースで A.B.C がモジュールの場合
                    for alias in node.names:
                        if alias.name != "*":
                            full_submodule = f"{module_path}.{alias.name}"
                            if full_submodule in module_names:
                                self.graph[self.mod_name].add(full_submodule)
                # `from . import foo` のような場合 (module_pathが空) で、base_path がモジュールの場合
                elif node.level > 0 and not node.module and base_path in module_names:
                    self.graph[self.mod_name].add(base_path)

    for mod_name in module_names:
        mod = sys.modules.get(mod_name)
        if not mod:
            continue

        if not hasattr(mod, "__file__") or not mod.__file__:
            continue

        try:
            with open(mod.__file__, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=mod.__file__)
            visitor = ImportVisitor(mod_name, graph)
            visitor.visit(tree)

        except FileNotFoundError:
            print(f"File not found ({mod_name}): {mod.__file__}")
        except SyntaxError as e:
            print(f"Syntax error ({mod_name}): {str(e)}")
        except Exception as e:
            print(f"Unexpected error during import analysis ({mod_name}): {str(e)}")
            traceback.print_exc()

    if DBG_INIT:
        print("\n--- Import dependencies ---")
        for mod, deps in sorted(graph.items()):
            if deps:
                print(f"{short_name(mod)} depends on:")
                for d in sorted(deps):
                    print(f"  -> {short_name(d)}")
        print("-------------------------------------------------")

    return graph


def _sort_modules(module_names: List[str]) -> List[str]:
    """
    モジュールを依存関係順にソート

    依存グラフを構築し、トポロジカルソートを実行してロード順序を決定します。
    循環依存が検出された場合は警告を表示し、代替ソート方法を使用します。

    Returns:
        List[str]: 依存関係に基づいてソートされたモジュールリスト
    """
    # 依存関係解析
    graph = _analyze_dependencies(module_names)

    # フィルタリング - 実際に存在するモジュールのみを対象に
    filtered_graph = {
        n: {d for d in deps if d in module_names}
        for n, deps in graph.items()
        if n in module_names
    }

    # アドオン自体のモジュールが最初に来るようにする
    base_module = ADDON_ID
    for mod_name in module_names:
        if mod_name == base_module and base_module not in filtered_graph:
            filtered_graph[base_module] = set()

    # 全てのモジュールがグラフに含まれるようにする
    for mod_name in module_names:
        if mod_name not in filtered_graph:
            filtered_graph[mod_name] = set()

    try:
        # トポロジカルソートを試みる
        sorted_modules = _topological_sort(filtered_graph)

        # デバッグ出力
        if DBG_INIT:
            print("\n=== モジュールロード順序 ===")
            for idx, mod in enumerate(sorted_modules):
                deps = filtered_graph.get(mod, set())
                dep_str = ", ".join(short_name(d) for d in deps) if deps else "-"
                print(f"{idx+1:2d}. {short_name(mod)} (依存: {dep_str})")

        if CREATE_DEPENDENCY_GRAPH:
            # Generate Mermaid diagram (for detailed analysis)
            try:
                mermaid = _visualize_dependencies(graph)
                # Output directory
                debug_dir = os.path.join(ADDON_PATH, "docs", "debug")
                os.makedirs(debug_dir, exist_ok=True)
                viz_path = os.path.join(debug_dir, "module_dependencies.mmd")
                with open(viz_path, "w", encoding="utf-8") as f:
                    f.write(mermaid)
                print(f"Generated dependency graph: {viz_path}")
            except Exception as e:
                print(f"Error generating dependency graph: {str(e)}")

    except ValueError as e:
        # ------------------------------------------------------
        # 循環依存検出時の代替処理（フォールバック）
        # ------------------------------------------------------
        print(f"Warning: {str(e)}")
        print("Using alternative sorting method to resolve circular dependencies...")
        sorted_modules = _alternative_sort(filtered_graph, module_names)

    # 未処理モジュールを末尾に追加
    remaining = [m for m in module_names if m not in sorted_modules]
    if remaining:
        print(f"\nAdding unprocessed modules: {', '.join(remaining)}")
        sorted_modules.extend(remaining)

    return sorted_modules


def short_name(module_name: str) -> str:
    """
    モジュール名を短縮形で返す（アドオンIDを除去）

    Args:
        module_name: 完全なモジュール名

    Returns:
        str: アドオンIDを除いた短縮名
    """
    prefix = f"{ADDON_ID}."
    return module_name[len(prefix) :] if module_name.startswith(prefix) else module_name


def _topological_sort(graph: Dict[str, List[str]]) -> List[str]:
    """
    Kahnのアルゴリズムによるトポロジカルソート

    依存関係グラフからモジュールのロード順序を決定します。
    依存先が先にロードされるよう、結果を逆順にして返します。

    Args:
        graph: 依存関係グラフ（key: モジュール, value: そのモジュールに依存する他のモジュール）

    Returns:
        List[str]: ロード順序が解決されたモジュールリスト

    Raises:
        ValueError: 循環依存が検出された場合
    """
    # 入次数（依存されている数）の計算
    in_degree = defaultdict(int)
    for node in graph:
        for neighbor in graph[node]:
            in_degree[neighbor] += 1

    # 入次数0（他から依存されていない）のノードから開始
    queue = [node for node in graph if in_degree[node] == 0]
    sorted_order = []

    while queue:
        node = queue.pop(0)
        sorted_order.append(node)

        for neighbor in graph.get(node, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # 全ノードを処理できなかった場合は循環依存がある
    if len(sorted_order) != len(graph):
        cyclic = set(graph.keys()) - set(sorted_order)
        raise ValueError(f"Circular dependency detected: {', '.join(cyclic)}")

    # NOTE: Kahnのアルゴリズムは依存される側が先にくるリストを生成するため、逆順にする必要はない。
    #       以前の reversed() は誤りだったため削除。
    return sorted_order


def _alternative_sort(graph: Dict[str, Set[str]], module_names: List[str]) -> List[str]:
    """
    循環依存がある場合の代替ソートアルゴリズム

    循環依存が検出された場合のフォールバック処理です。
    次の優先度でモジュールをソートします:
    1. アドオン自体のモジュール
    2. ユーティリティモジュール
    3. コアモジュール
    4. その他のモジュール（依存数が少ない順）

    Args:
        graph: 依存関係グラフ
        module_names: 全モジュール名リスト

    Returns:
        List[str]: 妥当なソート順のモジュールリスト
    """
    # 循環依存部分の検出
    try:
        cycles = _detect_cycles(graph)
        if cycles:
            print("\n=== Detected circular dependencies ===")
            for i, cycle in enumerate(cycles, 1):
                print(
                    f"Circular {i}: {' → '.join(short_name(m) for m in cycle)} → {short_name(cycle[0])}"
                )
    except Exception as e:
        print(f"Circular dependency detection error: {str(e)}")
        cycles = []

    # 基本的なソート順：アドオンモジュール → util系 → core系 → 他のモジュール
    base_priority = {
        ADDON_ID: 0,  # 最優先
    }

    # 出次数（依存先数）の計算 - 依存先が少ないほど基本モジュール
    outdegree = {node: len(deps) for node, deps in graph.items()}

    # 優先度に基づく大まかなソート
    priority_groups = defaultdict(list)

    for mod in module_names:
        # 優先度の決定
        if mod in base_priority:
            priority = base_priority[mod]
        elif ".utils." in mod or mod.endswith(".utils"):
            priority = 1
        elif ".core." in mod or mod.endswith(".core"):
            priority = 2
        else:
            # 出次数を基にした優先度（依存先が少ないほど先に来る）
            priority = 10 + outdegree.get(mod, 0)

        priority_groups[priority].append(mod)

    # 結果の組み立て
    result = []
    for priority in sorted(priority_groups.keys()):
        # 同じ優先度内では名前でソート
        result.extend(sorted(priority_groups[priority]))

    return result


def _detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """
    グラフ内の循環依存を検出

    Tarjanのアルゴリズムを使用して強連結成分を検出し、循環依存を特定します。

    Args:
        graph: 依存関係グラフ

    Returns:
        List[List[str]]: 検出された循環のリスト
    """
    # Tarjanのアルゴリズムでの強連結成分検出
    visited = set()
    stack = []
    on_stack = set()
    index_map = {}
    low_link = {}
    index = 0
    cycles = []

    def strong_connect(node):
        nonlocal index
        index_map[node] = index
        low_link[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        visited.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                strong_connect(neighbor)
                low_link[node] = min(low_link[node], low_link[neighbor])
            elif neighbor in on_stack:
                low_link[node] = min(low_link[node], index_map[neighbor])

        # 強連結成分を見つけた場合
        if low_link[node] == index_map[node]:
            component = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                component.append(w)
                if w == node:
                    break

            # 2つ以上のノードを含む強連結成分は循環
            if len(component) > 1:
                cycles.append(component)

    for node in graph:
        if node not in visited:
            strong_connect(node)

    return cycles


def _visualize_dependencies(graph: Dict[str, Set[str]], file_path: str = None) -> str:
    """
    依存関係グラフをMermaid形式で視覚化

    デバッグと分析のためにモジュール依存関係をMermaid形式の図として生成します。

    Args:
        graph: 依存関係グラフ
        file_path: 出力ファイルパス（省略時は文字列を返す）

    Returns:
        str: Mermaid形式の図
    """
    # 全モジュールを収集（依存先のみのモジュールも含む）
    all_modules = set(graph.keys())
    for deps in graph.values():
        all_modules.update(deps)

    # ノード間の関係をエッジとして収集
    edges = []
    for module, deps in graph.items():
        for dep in deps:
            edges.append((module, dep))

    # 短縮名の生成（見やすくするため）
    prefix_len = len(f"{ADDON_ID}.")
    short_names = {
        mod: mod[prefix_len:] if mod.startswith(f"{ADDON_ID}.") else mod
        for mod in all_modules
    }

    # Mermaid図の生成
    mermaid = "---\n"
    mermaid += "config:\n"
    mermaid += "  theme: mc\n"
    mermaid += "  layout: elk\n"
    mermaid += "  flowchart:\n"
    mermaid += "    curve: basis\n"
    mermaid += "---\n"
    mermaid += "flowchart RL\n"

    # ノード定義
    for module in sorted(all_modules):
        short = short_names[module]
        node_id = short.replace(".", "_")

        # コアモジュールと通常モジュールで形状を分ける
        if "." not in short:
            mermaid += f"    {node_id}[{short}]\n"
        else:
            mermaid += f"    {node_id}({short})\n"

    # エッジ定義
    for src, dst in sorted(edges):
        src_id = short_names[src].replace(".", "_")
        dst_id = short_names[dst].replace(".", "_")
        mermaid += f"    {src_id} --> {dst_id}\n"

    # 出力
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(mermaid)

    return mermaid


# ======================================================
# モジュール登録/登録解除
# ======================================================


def register_modules() -> None:
    """
    全モジュールを登録

    次の順序で登録を行います:
    1. 全クラスを依存関係順にソート
    2. 各クラスをBlenderに登録
    3. 各モジュールのregister関数を呼び出し
    """
    if BACKGROUND and bpy.app.background:
        return

    classes = _get_classes()
    success = True

    # Register classes
    for cls in classes:
        try:
            _validate_class(cls)
            bpy.utils.register_class(cls)
            if DBG_INIT:
                print(f"✓ Registered: {cls.__name__}")
        except Exception as e:
            success = False
            print(f"✗ Failed to register class: {cls.__name__}")
            print(f"   Reason: {str(e)}")
            print(f"   Module: {cls.__module__}")
            if hasattr(cls, "__annotations__"):
                print(f"   Annotations: {list(cls.__annotations__.keys())}")

    # Initialize modules
    for mod_name in MODULE_NAMES:
        try:
            mod = sys.modules[mod_name]
            if hasattr(mod, "register"):
                mod.register()
                if DBG_INIT:
                    print(f"✓ Initialized: {mod_name}")
        except Exception as e:
            success = False
            print(f"✗ Failed to initialize module: {mod_name}")
            print(f"   Reason: {str(e)}")
            traceback.print_exc()

    if not success:
        print("Warning: Some components failed to initialize")


def unregister_modules() -> None:
    """
    全モジュールを登録解除

    登録の逆順で以下を行います:
    1. 各モジュールのunregister関数を呼び出し
    2. 各クラスの登録解除
    """
    if BACKGROUND and bpy.app.background:
        return

    # モジュール逆初期化
    for mod_name in reversed(MODULE_NAMES):
        try:
            mod = sys.modules[mod_name]
            if hasattr(mod, "unregister"):
                mod.unregister()
        except Exception as e:
            print(f"Module unregistration error: {mod_name} - {str(e)}")

    # クラス登録解除
    for cls in reversed(_get_classes()):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"Class unregistration error: {cls.__name__} - {str(e)}")


# ======================================================
# ヘルパー関数
# ======================================================


def _collect_module_names() -> List[str]:
    """
    パターンに一致するモジュール名を収集

    MODULE_PATTERNSに定義されたパターンに基づいて、
    アドオンディレクトリ内の対象モジュールを再帰的に検索します。

    Returns:
        List[str]: 対象モジュール名のリスト
    """

    def is_masked(name: str) -> bool:
        """指定されたモジュール名がパターンにマッチするか確認"""
        return any(p.match(name) for p in MODULE_PATTERNS)

    def scan(path: str, package: str) -> List[str]:
        """指定パスからモジュールを再帰的に検索"""
        modules = []
        for _, name, is_pkg in pkgutil.iter_modules([path]):
            # 非公開モジュール（_で始まる）はスキップ
            if name.startswith("_"):
                continue

            full_name = f"{package}.{name}"
            # パッケージなら再帰的に検索
            if is_pkg:
                modules.extend(scan(os.path.join(path, name), full_name))
            # パターンにマッチするモジュールを追加
            if is_masked(full_name):
                modules.append(full_name)
        return modules

    return scan(ADDON_PATH, ADDON_ID)


def _get_classes(force: bool = True) -> List[bpy.types.bpy_struct]:
    """
    登録対象クラスを取得

    モジュール内のBlenderクラスを抽出し、依存関係に基づいて
    適切な順序にソートします。キャッシュ機能も備えています。

    Args:
        force: キャッシュを無視して再取得するか

    Returns:
        List[bpy.types.bpy_struct]: 依存関係順にソートされたクラスリスト
    """
    global _class_cache
    if not force and _class_cache:
        return _class_cache

    class_deps = defaultdict(set)
    pdtype = getattr(bpy.props, "_PropertyDeferred", tuple)

    # クラス収集
    all_classes = []
    for mod_name in MODULE_NAMES:
        mod = sys.modules[mod_name]
        for _, cls in inspect.getmembers(mod, _is_bpy_class):
            # クラスの依存関係を収集（プロパティの型）
            deps = set()
            for prop in getattr(cls, "__annotations__", {}).values():
                if isinstance(prop, pdtype):
                    pfunc = getattr(prop, "function", None) or prop[0]
                    if pfunc in (
                        bpy.props.PointerProperty,
                        bpy.props.CollectionProperty,
                    ):
                        if dep_cls := prop.keywords.get("type"):
                            if dep_cls.__module__.startswith(ADDON_ID):
                                deps.add(dep_cls)
            class_deps[cls] = deps
            all_classes.append(cls)

    # 依存関係ソート（深さ優先探索）
    ordered = []
    visited = set()
    stack = []

    def visit(cls):
        """深さ優先探索による依存関係解決"""
        if cls in stack:
            cycle = " → ".join([c.__name__ for c in stack])
            raise ValueError(f"Circular class dependency: {cycle}")
        if cls not in visited:
            stack.append(cls)
            visited.add(cls)
            # 依存先を先に処理
            for dep in class_deps.get(cls, []):
                visit(dep)
            stack.pop()
            ordered.append(cls)

    # 全クラスを処理
    for cls in all_classes:
        if cls not in visited:
            visit(cls)

    if DBG_INIT:
        print("\n=== 登録クラス一覧 ===")
        for cls in ordered:
            print(f" - {cls.__name__}")

    _class_cache = ordered
    return ordered


def _is_bpy_class(obj) -> bool:
    """
    bpy構造体クラスか判定

    Blenderに登録可能なクラスを識別します。
    アドオン独自のクラスのみを検出します。

    Args:
        obj: 判定する対象

    Returns:
        bool: Blenderに登録可能なクラスの場合True
    """
    return (
        inspect.isclass(obj)
        and issubclass(obj, bpy.types.bpy_struct)
        and obj.__base__ is not bpy.types.bpy_struct
        and obj.__module__.startswith(ADDON_ID)
    )


def _validate_class(cls: bpy.types.bpy_struct) -> None:
    """
    Validate class validity

    Check if the class is valid for registration in Blender.

    Args:
        cls: The class to validate

    Raises:
        ValueError: If bl_rna attribute is missing
        TypeError: If the class is not of the appropriate type
    """
    if not hasattr(cls, "bl_rna"):
        raise ValueError(f"Class {cls.__name__} has no bl_rna attribute")
    if not issubclass(cls, bpy.types.bpy_struct):
        raise TypeError(f"Invalid class type: {cls.__name__}")


# ======================================================
# タイムアウト管理
# ======================================================


class Timeout:
    """
    遅延実行用オペレータ

    Blenderのイベントシステムを利用して、指定された関数を
    一定時間後に実行します。UIスレッドのブロックを回避する
    ために使用します。
    """

    bl_idname = f"{ADDON_PREFIX_PY}.timeout"
    bl_label = ""
    bl_options = {"INTERNAL"}

    idx: bpy.props.IntProperty(options={"SKIP_SAVE", "HIDDEN"})
    delay: bpy.props.FloatProperty(default=0.0001, options={"SKIP_SAVE", "HIDDEN"})

    _data: Dict[int, tuple] = dict()  # タイムアウト関数のデータ保持用
    _timer = None
    _finished = False

    def modal(self, context, event):
        if event.type == "TIMER":
            if self._finished:
                context.window_manager.event_timer_remove(self._timer)
                del self._data[self.idx]
                return {"FINISHED"}

            if self._timer.time_duration >= self.delay:
                self._finished = True
                try:
                    func, args = self._data[self.idx]
                    func(*args)
                except Exception as e:
                    print(f"Timeout error: {str(e)}")
        return {"PASS_THROUGH"}

    def execute(self, context):
        self._finished = False
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(
            self.delay, window=context.window
        )
        return {"RUNNING_MODAL"}


TimeoutOperator = type(
    "%s_OT_timeout" % ADDON_PREFIX, (Timeout, bpy.types.Operator), {}
)


def timeout(func: callable, *args) -> None:
    """
    関数を遅延実行

    Blenderのモーダルイベントを利用して関数を非同期で実行します。
    UI更新や時間のかかる処理の分散に役立ちます。

    Args:
        func: 実行する関数
        *args: 関数に渡す引数
    """
    idx = len(Timeout._data)
    while idx in Timeout._data:
        idx += 1
    Timeout._data[idx] = (func, args)
    getattr(bpy.ops, ADDON_PREFIX_PY).timeout(idx=idx)
