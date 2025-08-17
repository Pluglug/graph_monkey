import bpy
import os
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime


class BlendTextExtractor:
    """
    .blendファイルからテキストブロックの情報を抽出するクラス
    """

    def __init__(self, ignore_dot_prefix: bool = True):
        """
        Args:
            ignore_dot_prefix: .で始まるテキストブロックを無視するかどうか
        """
        self.ignore_dot_prefix = ignore_dot_prefix
        self.extracted_data = []

    def extract_from_file(self, blend_filepath: str) -> List[Dict]:
        """
        指定された.blendファイルからテキストブロックを抽出

        Args:
            blend_filepath: .blendファイルのパス

        Returns:
            テキストブロック情報のリスト
        """
        if not os.path.exists(blend_filepath):
            print(f"エラー: ファイルが見つかりません: {blend_filepath}")
            return []

        if not blend_filepath.lower().endswith(".blend"):
            print(f"エラー: .blendファイルではありません: {blend_filepath}")
            return []

        text_blocks = []

        try:
            # .blendファイルをライブラリとして読み込み
            with bpy.data.libraries.load(blend_filepath, link=False) as (
                data_from,
                data_to,
            ):
                # 利用可能なテキストブロック名を取得
                available_texts = data_from.texts

                if not available_texts:
                    print(f"テキストブロックが見つかりませんでした: {blend_filepath}")
                    return []

                print(
                    f"発見されたテキストブロック数: {len(available_texts)} in {blend_filepath}"
                )

                # フィルタリング
                filtered_texts = []
                for text_name in available_texts:
                    if self.ignore_dot_prefix and text_name.startswith("."):
                        print(f"スキップ (ドット始まり): {text_name}")
                        continue
                    filtered_texts.append(text_name)

                # テキストブロックをアペンド
                data_to.texts = filtered_texts

            # アペンドされたテキストブロックから情報を抽出
            for text_name in filtered_texts:
                if text_name in bpy.data.texts:
                    text_block = bpy.data.texts[text_name]

                    # テキスト情報を収集
                    text_info = self._extract_text_info(text_block, blend_filepath)
                    text_blocks.append(text_info)

                    # 使用後にテキストブロックを削除（メモリ節約）
                    bpy.data.texts.remove(text_block)

        except Exception as e:
            print(
                f"エラー: {blend_filepath} の読み込み中にエラーが発生しました: {str(e)}"
            )
            return []

        return text_blocks

    def _extract_text_info(self, text_block, source_file: str) -> Dict:
        """
        テキストブロックから詳細情報を抽出
        """
        lines = text_block.as_string().split("\n")

        # 基本情報
        info = {
            "name": text_block.name,
            "source_file": source_file,
            "source_basename": os.path.basename(source_file),
            "line_count": len(lines),
            "char_count": len(text_block.as_string()),
            "is_modified": text_block.is_modified,
            "is_in_memory": text_block.is_in_memory,
            "extracted_at": datetime.now().isoformat(),
        }

        # プレビュー (最初の5行または200文字)
        preview_lines = lines[:5]
        preview_text = "\n".join(preview_lines)
        if len(preview_text) > 200:
            preview_text = preview_text[:200] + "..."
        info["preview"] = preview_text

        # 関数/クラス名の抽出 (Python用)
        info["functions"] = self._extract_functions(lines)
        info["classes"] = self._extract_classes(lines)

        # コメントから情報抽出
        info["description"] = self._extract_description(lines)

        return info

    def _extract_functions(self, lines: List[str]) -> List[str]:
        """Python関数名を抽出"""
        functions = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") and "(" in stripped:
                func_name = stripped[4 : stripped.index("(")].strip()
                functions.append(func_name)
        return functions

    def _extract_classes(self, lines: List[str]) -> List[str]:
        """Pythonクラス名を抽出"""
        classes = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class ") and ":" in stripped:
                class_name = stripped[6 : stripped.index(":")].strip()
                if "(" in class_name:
                    class_name = class_name[: class_name.index("(")].strip()
                classes.append(class_name)
        return classes

    def _extract_description(self, lines: List[str]) -> str:
        """コメントから説明を抽出"""
        for line in lines[:10]:  # 最初の10行をチェック
            stripped = line.strip()
            if stripped.startswith("#") and len(stripped) > 5:
                # # Description: のような形式を探す
                comment = stripped[1:].strip()
                if any(
                    keyword in comment.lower()
                    for keyword in ["description", "desc", "about", "説明"]
                ):
                    return comment
        return ""

    def scan_directory(self, directory: str, recursive: bool = True) -> List[Dict]:
        """
        ディレクトリ内の.blendファイルをスキャン

        Args:
            directory: スキャンするディレクトリ
            recursive: サブディレクトリも含めるかどうか

        Returns:
            全テキストブロック情報のリスト
        """
        all_text_blocks = []

        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(".blend"):
                        filepath = os.path.join(root, file)
                        text_blocks = self.extract_from_file(filepath)
                        all_text_blocks.extend(text_blocks)
        else:
            for file in os.listdir(directory):
                if file.lower().endswith(".blend"):
                    filepath = os.path.join(directory, file)
                    text_blocks = self.extract_from_file(filepath)
                    all_text_blocks.extend(text_blocks)

        return all_text_blocks

    def save_to_json(self, text_blocks: List[Dict], output_file: str) -> None:
        """
        抽出結果をJSONファイルに保存
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(text_blocks, f, indent=2, ensure_ascii=False)
            print(f"結果を保存しました: {output_file}")
        except Exception as e:
            print(f"保存エラー: {str(e)}")

    def print_summary(self, text_blocks: List[Dict]) -> None:
        """
        抽出結果のサマリーを表示
        """
        if not text_blocks:
            print("テキストブロックが見つかりませんでした。")
            return

        print(f"\n=== 抽出サマリー ===")
        print(f"総テキストブロック数: {len(text_blocks)}")

        # ファイル別の統計
        file_stats = {}
        for block in text_blocks:
            basename = block["source_basename"]
            if basename not in file_stats:
                file_stats[basename] = 0
            file_stats[basename] += 1

        print(f"ファイル数: {len(file_stats)}")
        print("\nファイル別テキストブロック数:")
        for filename, count in sorted(file_stats.items()):
            print(f"  {filename}: {count}")

        # 関数/クラスがあるもの
        with_functions = [b for b in text_blocks if b["functions"]]
        with_classes = [b for b in text_blocks if b["classes"]]

        print(f"\n関数を含むテキストブロック: {len(with_functions)}")
        print(f"クラスを含むテキストブロック: {len(with_classes)}")


# 使用例
def main():
    # 基本的な使用方法
    extractor = BlendTextExtractor(ignore_dot_prefix=True)

    # 単一ファイルから抽出
    # text_blocks = extractor.extract_from_file("/path/to/your/file.blend")

    # ディレクトリをスキャン
    # text_blocks = extractor.scan_directory("/path/to/blend/files", recursive=True)

    # 現在のBlenderファイルのテキストブロックを確認（テスト用）
    print("現在のBlenderファイルのテキストブロック:")
    for text in bpy.data.texts:
        print(f"  - {text.name} ({len(text.as_string())} chars)")

    # 実際の使用例（パスを適切に変更してください）
    """
    # 例: 特定のディレクトリをスキャン
    text_blocks = extractor.scan_directory("C:/BlenderAssets/", recursive=True)
    
    # 結果を表示
    extractor.print_summary(text_blocks)
    
    # JSONで保存
    extractor.save_to_json(text_blocks, "text_blocks_catalog.json")
    
    # 特定の検索
    rigui_blocks = [b for b in text_blocks if 'rigui' in b['name'].lower()]
    print(f"RIGUI関連: {len(rigui_blocks)} 個")
    """


if __name__ == "__main__":
    main()

# Note: ReadmeやTextは無視したほうがいいかも。
