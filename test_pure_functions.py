#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
純粋関数の同一性を検証するテストスクリプト。
同一の入力に対して常に同一の出力が得られることを確認します。
"""

import unittest
import pure_dxf_functions as pdf

class TestPureFunctions(unittest.TestCase):
    """
    純粋関数の検証テストクラス
    """
    
    def test_line_data_identity(self):
        """同一の入力に対して、LineDataが同一であることを検証"""
        line_data1 = pdf.compute_line_data((0, 0), (100, 100))
        line_data2 = pdf.compute_line_data((0, 0), (100, 100))
        self.assertEqual(line_data1, line_data2)
        
    def test_circle_data_identity(self):
        """同一の入力に対して、CircleDataが同一であることを検証"""
        circle_data1 = pdf.compute_circle_data((50, 50), 30)
        circle_data2 = pdf.compute_circle_data((50, 50), 30)
        self.assertEqual(circle_data1, circle_data2)
        
    def test_arc_data_identity(self):
        """同一の入力に対して、ArcDataが同一であることを検証"""
        arc_data1 = pdf.compute_arc_data((50, 50), 30, 0, 90)
        arc_data2 = pdf.compute_arc_data((50, 50), 30, 0, 90)
        self.assertEqual(arc_data1, arc_data2)
        
    def test_polyline_data_identity(self):
        """同一の入力に対して、PolylineDataが同一であることを検証"""
        points = [(0, 0), (10, 10), (20, 0)]
        polyline_data1 = pdf.compute_polyline_data(points)
        polyline_data2 = pdf.compute_polyline_data(points)
        self.assertEqual(polyline_data1, polyline_data2)
        
    def test_text_data_identity(self):
        """同一の入力に対して、TextDataが同一であることを検証"""
        text_data1 = pdf.compute_text_data("テスト", (10, 10), 5)
        text_data2 = pdf.compute_text_data("テスト", (10, 10), 5)
        self.assertEqual(text_data1, text_data2)
        
    def test_theme_colors_identity(self):
        """同一のテーマ名に対して、同一の色が返されることを検証"""
        colors1 = pdf.get_theme_colors("ダーク")
        colors2 = pdf.get_theme_colors("ダーク")
        self.assertEqual(colors1, colors2)
        
        colors3 = pdf.get_theme_colors("ライト")
        colors4 = pdf.get_theme_colors("ライト")
        self.assertEqual(colors3, colors4)
        
    def test_verify_identical_output(self):
        """verify_identical_output関数の動作を検証"""
        # 同一の結果を返す場合
        result = pdf.verify_identical_output(
            lambda x, y: x + y,
            (1, 2),
            (1, 2)
        )
        self.assertTrue(result)
        
        # 異なる結果を返す場合
        result = pdf.verify_identical_output(
            lambda x, y: x + y,
            (1, 2),
            (2, 3)
        )
        self.assertFalse(result)
        
    def test_different_instances_equal(self):
        """異なるインスタンスが等価であることを検証"""
        # 同一の入力から生成された異なるインスタンスの比較
        line1 = pdf.LineData(0, 0, 100, 100, 1.0, (255, 255, 255))
        line2 = pdf.LineData(0, 0, 100, 100, 1.0, (255, 255, 255))
        self.assertEqual(line1, line2)
        
        # 値が異なる場合は等価ではない
        line3 = pdf.LineData(0, 0, 100, 100, 2.0, (255, 255, 255))
        self.assertNotEqual(line1, line3)

if __name__ == "__main__":
    print("純粋関数の同一性テストを実行中...")
    unittest.main() 