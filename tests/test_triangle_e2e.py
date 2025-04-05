import sys
import os
import unittest
from pathlib import Path
import time

# 親ディレクトリをパスに追加
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QPoint

from triangle_ui.triangle_manager import TriangleManagerWindow, TriangleData

class TestTriangleE2E(unittest.TestCase):
    """三角形UIのエンドツーエンドテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = TriangleManagerWindow()
        self.window.show()
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        self.window.close()
        del self.window
        # del self.app  # これを削除すると、複数のテストが継続的に実行できる
    
    def test_initial_triangle(self):
        """初期三角形の表示テスト"""
        # 初期三角形が1つ表示されていることを確認
        self.assertEqual(len(self.window.triangle_list), 1)
        
        # 初期三角形の属性を確認
        triangle = self.window.triangle_list[0]
        self.assertEqual(triangle.number, 1)
        self.assertEqual(triangle.lengths, [100.0, 100.0, 100.0])  # 全ての辺の長さが100
    
    def test_add_triangle(self):
        """三角形追加テスト"""
        # 初期状態の三角形数を確認
        initial_count = len(self.window.triangle_list)
        
        # 辺の選択をシミュレート
        self.window.handle_side_clicked(1, 0)  # 三角形1の辺Aを選択
        
        # 新しい三角形のパラメータを設定
        self.window.new_len_b_input.setText("120.0")
        self.window.new_len_c_input.setText("80.0")
        
        # 三角形追加ボタンをクリック
        QTest.mouseClick(self.window.add_button, Qt.LeftButton)
        
        # 三角形が追加されたことを確認
        self.assertEqual(len(self.window.triangle_list), initial_count + 1)
        
        # 追加された三角形の属性を確認
        new_triangle = self.window.get_triangle_by_number(2)
        self.assertEqual(new_triangle.lengths, [100.0, 120.0, 80.0])
        
        # 親三角形との接続を確認
        parent_triangle = self.window.get_triangle_by_number(1)
        self.assertEqual(new_triangle.parent.number, parent_triangle.number)  # 親三角形の番号が1であることを確認
        self.assertEqual(new_triangle.connection_side, 0)
        
        # 親三角形の子リストを確認
        child_triangle = parent_triangle.children[0]
        self.assertEqual(child_triangle.number, 2)  # 辺Aに子三角形2が接続
    
    def test_update_triangle(self):
        """三角形更新テスト"""
        # 最初に三角形を追加
        self.test_add_triangle()
        
        # 三角形2の辺Bを選択
        self.window.handle_side_clicked(2, 1)
        
        # 新しい寸法を設定
        self.window.new_len_b_input.setText("150.0")
        self.window.new_len_c_input.setText("100.0")
        
        # 更新前の座標を記録
        triangle_before = self.window.get_triangle_by_number(2)
        coords_before = [
            (triangle_before.points[0].x(), triangle_before.points[0].y()),
            (triangle_before.points[1].x(), triangle_before.points[1].y()),
            (triangle_before.points[2].x(), triangle_before.points[2].y())
        ]
        
        # 更新メソッドを直接呼び出し（ボタンがない場合）
        result = self.window.update_selected_triangle()
        
        # 更新後の座標を取得
        triangle_after = self.window.get_triangle_by_number(2)
        coords_after = [
            (triangle_after.points[0].x(), triangle_after.points[0].y()),
            (triangle_after.points[1].x(), triangle_after.points[1].y()),
            (triangle_after.points[2].x(), triangle_after.points[2].y())
        ]
        
        # 三角形の寸法が更新されたことを確認
        self.assertEqual(triangle_after.lengths, [150.0, 120.0, 100.0])
        
        # 座標が変更されたことを確認
        self.assertNotEqual(coords_before, coords_after)
    
    def test_coordinate_propagation(self):
        """座標伝播テスト"""
        # 最初に三角形を追加
        self.test_add_triangle()
        
        # 親三角形の更新前の子三角形座標を記録
        child_triangle_before = self.window.get_triangle_by_number(2)
        child_coords_before = [
            (child_triangle_before.points[0].x(), child_triangle_before.points[0].y()),
            (child_triangle_before.points[1].x(), child_triangle_before.points[1].y()),
            (child_triangle_before.points[2].x(), child_triangle_before.points[2].y())
        ]
        
        # 親三角形を選択して更新
        self.window.handle_side_clicked(1, 1)  # 三角形1の辺Bを選択
        
        # 新しい寸法を設定
        self.window.new_len_b_input.setText("120.0")
        self.window.new_len_c_input.setText("90.0")
        
        # 更新メソッドを直接呼び出し（ボタンがない場合）
        result = self.window.update_selected_triangle()
        
        # 親三角形の更新後の子三角形座標を取得
        child_triangle_after = self.window.get_triangle_by_number(2)
        child_coords_after = [
            (child_triangle_after.points[0].x(), child_triangle_after.points[0].y()),
            (child_triangle_after.points[1].x(), child_triangle_after.points[1].y()),
            (child_triangle_after.points[2].x(), child_triangle_after.points[2].y())
        ]
        
        # 子三角形の座標が変更されたことを確認（座標伝播が機能）
        self.assertNotEqual(child_coords_before, child_coords_after)
        
        # 親三角形が正しく更新されていることを確認
        parent_triangle = self.window.get_triangle_by_number(1)
        self.assertEqual(parent_triangle.lengths, [120.0, 100.0, 90.0])

if __name__ == '__main__':
    unittest.main() 