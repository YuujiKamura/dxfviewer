#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Triangle UIアプリケーション

TriangleManagerWindowを使用した三角形UI管理アプリケーション
"""

import sys
import logging
from pathlib import Path

# 親ディレクトリをパスに追加
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# PySide6のインポート
from PySide6.QtWidgets import QApplication

# triangle_managerからTriangleManagerWindowをインポート
from triangle_ui.triangle_manager import TriangleManagerWindow, TriangleData
from PySide6.QtCore import QPointF

# ロガーの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    """メインアプリケーション実行関数"""
    app = QApplication(sys.argv)
    window = TriangleManagerWindow()
    window.show()
    logger.info("アプリケーションが起動しました")
    sys.exit(app.exec())

def run_automated_tests():
    """自動テストを実行する関数"""
    logger.info("自動テストを開始します...")
    app = QApplication(sys.argv)
    
    # TriangleManagerWindowのインスタンスを作成
    window = TriangleManagerWindow()
    
    # 初期三角形の確認
    if len(window.triangle_list) == 1:
        logger.info("テスト1: 初期三角形が正しく作成されました")
    else:
        logger.error("テスト1: 初期三角形の作成に失敗しました")
    
    # 三角形の追加テスト
    initial_count = len(window.triangle_list)
    
    # 辺を選択
    window.handle_side_clicked(1, 0)  # 三角形1の辺Aを選択
    
    # 新しい三角形のパラメータを設定
    window.new_len_b_input.setText("120.0")
    window.new_len_c_input.setText("80.0")
    
    # 三角形を追加
    window.add_triangle()
    
    # 三角形が追加されたか確認
    if len(window.triangle_list) == initial_count + 1:
        logger.info("テスト2: 三角形の追加に成功しました")
    else:
        logger.error("テスト2: 三角形の追加に失敗しました")
    
    # 三角形の更新テスト
    # 辺を選択
    window.handle_side_clicked(2, 1)  # 三角形2の辺Bを選択
    
    # 新しい寸法を設定
    window.new_len_b_input.setText("150.0")
    window.new_len_c_input.setText("100.0")
    
    # 三角形を更新
    result = window.update_selected_triangle()
    
    if result:
        logger.info("テスト3: 三角形の更新に成功しました")
    else:
        logger.error("テスト3: 三角形の更新に失敗しました")
    
    # 座標伝播テスト - 親三角形の更新による子三角形への影響
    # 親三角形のデータを保存
    parent_triangle = window.get_triangle_by_number(1)
    parent_sides_before = [parent_triangle.lengths[0], parent_triangle.lengths[1], parent_triangle.lengths[2]]
    parent_coords_before = [
        (parent_triangle.points[0].x(), parent_triangle.points[0].y()),
        (parent_triangle.points[1].x(), parent_triangle.points[1].y()),
        (parent_triangle.points[2].x(), parent_triangle.points[2].y())
    ]
    
    # 子三角形のデータを保存
    child_triangle = window.get_triangle_by_number(2)
    child_coords_before = [
        (child_triangle.points[0].x(), child_triangle.points[0].y()),
        (child_triangle.points[1].x(), child_triangle.points[1].y()),
        (child_triangle.points[2].x(), child_triangle.points[2].y())
    ]
    
    # 親三角形を選択して更新
    window.handle_side_clicked(1, 1)  # 三角形1の辺Bを選択
    window.new_len_b_input.setText("120.0")  # 変更する寸法
    window.new_len_c_input.setText("90.0")   # 変更する寸法
    
    # 親三角形を更新
    result = window.update_selected_triangle()
    
    if result:
        # 親三角形の更新後のデータ
        parent_triangle = window.get_triangle_by_number(1)
        parent_sides_after = [parent_triangle.lengths[0], parent_triangle.lengths[1], parent_triangle.lengths[2]]
        parent_coords_after = [
            (parent_triangle.points[0].x(), parent_triangle.points[0].y()),
            (parent_triangle.points[1].x(), parent_triangle.points[1].y()),
            (parent_triangle.points[2].x(), parent_triangle.points[2].y())
        ]
        
        # 子三角形の更新後のデータ
        child_triangle = window.get_triangle_by_number(2)
        child_coords_after = [
            (child_triangle.points[0].x(), child_triangle.points[0].y()),
            (child_triangle.points[1].x(), child_triangle.points[1].y()),
            (child_triangle.points[2].x(), child_triangle.points[2].y())
        ]
        
        # 親三角形の寸法が変更されたか確認
        if parent_sides_before != parent_sides_after:
            logger.info(f"テスト4-1: 親三角形の寸法が正しく更新されました")
            logger.debug(f"  変更前: {parent_sides_before}")
            logger.debug(f"  変更後: {parent_sides_after}")
        else:
            logger.error("テスト4-1: 親三角形の寸法が更新されていません")
        
        # 親三角形の座標が変更されたか確認
        if parent_coords_before != parent_coords_after:
            logger.info(f"テスト4-2: 親三角形の座標が正しく更新されました")
            logger.debug(f"  変更前: {parent_coords_before}")
            logger.debug(f"  変更後: {parent_coords_after}")
        else:
            logger.error("テスト4-2: 親三角形の座標が更新されていません")
        
        # 子三角形の座標が変更されたか確認
        if child_coords_before != child_coords_after:
            logger.info(f"テスト4-3: 子三角形の座標が正しく伝播更新されました")
            logger.debug(f"  変更前: {child_coords_before}")
            logger.debug(f"  変更後: {child_coords_after}")
        else:
            logger.error("テスト4-3: 子三角形の座標が伝播更新されていません")
    else:
        logger.error("テスト4: 親三角形の更新に失敗しました")
    
    logger.info("自動テスト完了")
    
    return 0  # 正常終了

if __name__ == "__main__":
    # コマンドライン引数で自動テストを指定できるようにする
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(run_automated_tests())
    else:
        logger.info("Triangle UIアプリケーションを起動しています...")
        main() 