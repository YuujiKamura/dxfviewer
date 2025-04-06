# -*- coding: utf-8 -*-

"""
三角形UIのエンドツーエンドテスト

ユーザーインターフェースとの相互作用をテスト
"""

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

from shapes.geometry.triangle_shape import TriangleData
from triangle_ui.triangle_manager_ui import TriangleManagerWindow

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
    
    def test_triangle_manager_basic(self):
        """三角形マネージャーの基本機能テスト"""
        # 初期三角形が1つ表示されていることを確認
        self.assertEqual(len(self.window.triangle_manager.triangle_list), 1)
        
        # 初期三角形の属性を確認
        triangle = self.window.triangle_manager.triangle_list[0]
        self.assertEqual(triangle.number, 1)
        self.assertEqual(triangle.lengths, [100.0, 100.0, 100.0])  # 全ての辺の長さが100
        
        # 辺の選択をシミュレート
        self.window.handle_side_clicked(1, 0)  # 三角形1の辺Aを選択
        
        # 選択情報が更新されたことを確認
        self.assertEqual(self.window.selected_parent_number, 1)
        self.assertEqual(self.window.selected_side_index, 0)
        
        # 親三角形が正しく登録されていることを確認
        parent_triangle = self.window.triangle_manager.get_triangle_by_number(1)
        self.assertIsNotNone(parent_triangle)
        
        # 三角形マネージャーが正しく初期化されていることを確認
        self.assertIsNotNone(self.window.triangle_manager)
        self.assertEqual(self.window.triangle_manager.next_triangle_number, 2)

if __name__ == '__main__':
    unittest.main() 