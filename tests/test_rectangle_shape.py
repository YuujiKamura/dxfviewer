#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RectangleShapeのユニットテスト

幅員1、延長、幅員2、センター位置を持つRectangleShapeクラスの各機能をテストします。
"""

import unittest
import math
from PySide6.QtCore import QPointF
import sys
import os

# テスト対象モジュールへのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shapes.geometry.rectangle_shape import RectangleShape, CenterPosition

class TestRectangleShape(unittest.TestCase):
    """RectangleShapeクラスのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # 基本的な四角形（すべての角が90度）
        self.rect1 = RectangleShape(
            width1=100,
            length=200,
            width2=100,
            center_position=CenterPosition.CENTER,
            p_ca=QPointF(100, 100),
            angle_deg=0,
            number=1
        )
        
        # 台形（幅員1≠幅員2）
        self.rect2 = RectangleShape(
            width1=120,
            length=200,
            width2=80,
            center_position=CenterPosition.LEFT,
            p_ca=QPointF(400, 100),
            angle_deg=0,
            number=2
        )
        
        # 回転した四角形
        self.rect3 = RectangleShape(
            width1=100,
            length=200,
            width2=100,
            center_position=CenterPosition.RIGHT,
            p_ca=QPointF(700, 100),
            angle_deg=45,
            number=3
        )
    
    def test_init_values(self):
        """初期化時の値が正しく設定されるかテスト"""
        self.assertEqual(self.rect1.width1, 100)
        self.assertEqual(self.rect1.length, 200)
        self.assertEqual(self.rect1.width2, 100)
        self.assertEqual(self.rect1.center_position, CenterPosition.CENTER)
        self.assertEqual(self.rect1.angle_deg, 0)
        self.assertEqual(self.rect1.number, 1)
        
        # width2がNoneの場合はwidth1と同値になることを確認
        rect = RectangleShape(width1=100, length=200, p_ca=QPointF(0, 0))
        self.assertEqual(rect.width2, 100)
    
    def test_points_calculation_rectangle(self):
        """長方形の頂点計算が正しいかテスト（幅員1 = 幅員2の場合）"""
        # センター配置の場合、position = 左下基準点ではなく幅員方向の中央点になる
        # 角度が0度の場合、幅員方向ベクトルは (0, 1) となる
        # 左下頂点は基準位置から幅員1/2分Y方向にずれる
        expected_left_bottom = QPointF(100.0, 50.0)  # 左下 (position.x, position.y-width1/2)
        self.assertAlmostEqual(self.rect1.points[0].x(), expected_left_bottom.x())
        self.assertAlmostEqual(self.rect1.points[0].y(), expected_left_bottom.y())
        
        # 右下頂点
        expected_right_bottom = QPointF(300.0, 50.0)  # 左下 + (length, 0)
        self.assertAlmostEqual(self.rect1.points[1].x(), expected_right_bottom.x())
        self.assertAlmostEqual(self.rect1.points[1].y(), expected_right_bottom.y())
        
        # 右上頂点
        expected_right_top = QPointF(300.0, 150.0)  # 右下 + (0, width2)
        self.assertAlmostEqual(self.rect1.points[2].x(), expected_right_top.x())
        self.assertAlmostEqual(self.rect1.points[2].y(), expected_right_top.y())
        
        # 左上頂点
        expected_left_top = QPointF(100.0, 150.0)  # 左下 + (0, width1)
        self.assertAlmostEqual(self.rect1.points[3].x(), expected_left_top.x())
        self.assertAlmostEqual(self.rect1.points[3].y(), expected_left_top.y())
    
    def test_points_calculation_trapezoid(self):
        """台形の頂点計算が正しいかテスト（幅員1 ≠ 幅員2の場合）"""
        # LEFT配置の場合、position = 左下基準点そのもの
        expected_left_bottom = QPointF(400.0, 100.0)
        self.assertAlmostEqual(self.rect2.points[0].x(), expected_left_bottom.x())
        self.assertAlmostEqual(self.rect2.points[0].y(), expected_left_bottom.y())
        
        # 右下頂点
        expected_right_bottom = QPointF(600.0, 100.0)  # 左下 + (length, 0)
        self.assertAlmostEqual(self.rect2.points[1].x(), expected_right_bottom.x())
        self.assertAlmostEqual(self.rect2.points[1].y(), expected_right_bottom.y())
        
        # 右上頂点
        expected_right_top = QPointF(600.0, 180.0)  # 右下 + (0, width2)
        self.assertAlmostEqual(self.rect2.points[2].x(), expected_right_top.x())
        self.assertAlmostEqual(self.rect2.points[2].y(), expected_right_top.y())
        
        # 左上頂点
        expected_left_top = QPointF(400.0, 220.0)  # 左下 + (0, width1)
        self.assertAlmostEqual(self.rect2.points[3].x(), expected_left_top.x())
        self.assertAlmostEqual(self.rect2.points[3].y(), expected_left_top.y())
    
    def test_points_calculation_rotated(self):
        """回転した四角形の頂点計算が正しいかテスト"""
        # 回転行列の適用をチェック
        sin45 = math.sin(math.radians(45))
        cos45 = math.cos(math.radians(45))
        
        # RIGHT配置の場合、position = 左下基準点 + width1 * 幅員方向単位ベクトル
        # 幅員方向ベクトル = (-sin(angle), cos(angle))
        expected_left_bottom_x = 700.0 - 100.0 * (-sin45)
        expected_left_bottom_y = 100.0 - 100.0 * cos45
        
        self.assertAlmostEqual(self.rect3.points[0].x(), expected_left_bottom_x, places=1)
        self.assertAlmostEqual(self.rect3.points[0].y(), expected_left_bottom_y, places=1)
    
    def test_center_point(self):
        """中心点の計算が正しいかテスト"""
        # rect1の中心点
        expected_center = QPointF(200.0, 100.0)  # 4頂点の平均
        self.assertAlmostEqual(self.rect1.center_point.x(), expected_center.x())
        self.assertAlmostEqual(self.rect1.center_point.y(), expected_center.y())
    
    def test_side_length(self):
        """辺の長さが正しいかテスト"""
        # rect1の辺の長さ
        self.assertAlmostEqual(self.rect1.get_side_length(0), 200.0)  # 下辺（延長）
        self.assertAlmostEqual(self.rect1.get_side_length(1), 100.0)  # 右辺（幅員2）
        self.assertAlmostEqual(self.rect1.get_side_length(2), 200.0)  # 上辺（延長）
        self.assertAlmostEqual(self.rect1.get_side_length(3), 100.0)  # 左辺（幅員1）
        
        # rect2の辺の長さ
        self.assertAlmostEqual(self.rect2.get_side_length(0), 200.0)  # 下辺（延長）
        self.assertAlmostEqual(self.rect2.get_side_length(1), 80.0)   # 右辺（幅員2）
        self.assertAlmostEqual(self.rect2.get_side_length(2), 200.0)  # 上辺（延長）
        self.assertAlmostEqual(self.rect2.get_side_length(3), 120.0)  # 左辺（幅員1）
    
    def test_update_properties(self):
        """プロパティ更新が正しく動作するかテスト"""
        rect = RectangleShape(
            width1=100,
            length=200,
            width2=100,
            center_position=CenterPosition.CENTER,
            p_ca=QPointF(100, 100),
            angle_deg=0
        )
        
        # プロパティを更新
        result = rect.update_with_new_properties(
            width1=150,
            length=250,
            width2=120,
            center_position=CenterPosition.LEFT,
            angle_deg=30
        )
        
        self.assertTrue(result)
        self.assertEqual(rect.width1, 150)
        self.assertEqual(rect.length, 250)
        self.assertEqual(rect.width2, 120)
        self.assertEqual(rect.center_position, CenterPosition.LEFT)
        self.assertEqual(rect.angle_deg, 30)
    
    def test_update_lengths(self):
        """辺の長さ更新が正しく動作するかテスト"""
        rect = RectangleShape(
            width1=100,
            length=200,
            width2=100,
            center_position=CenterPosition.CENTER,
            p_ca=QPointF(100, 100),
            angle_deg=0
        )
        
        # 辺の長さを更新
        result = rect.update_with_new_lengths([150, 250, 120])
        
        self.assertTrue(result)
        self.assertEqual(rect.width1, 150)
        self.assertEqual(rect.length, 250)
        self.assertEqual(rect.width2, 120)
    
    def test_connection_side(self):
        """接続可能な辺の判定が正しいかテスト"""
        # 幅員の辺のみ接続可能
        self.assertFalse(self.rect1.is_connection_side(0))  # 下辺（延長）
        self.assertTrue(self.rect1.is_connection_side(1))   # 右辺（幅員2）
        self.assertFalse(self.rect1.is_connection_side(2))  # 上辺（延長）
        self.assertTrue(self.rect1.is_connection_side(3))   # 左辺（幅員1）
    
    def test_connection_point(self):
        """接続点の計算が正しいかテスト"""
        # 右辺の接続点
        expected_right_midpoint = QPointF(300.0, 100.0)  # 右辺の中点
        connection_point = self.rect1.get_connection_point_for_side(1)
        self.assertAlmostEqual(connection_point.x(), expected_right_midpoint.x())
        self.assertAlmostEqual(connection_point.y(), expected_right_midpoint.y())
        
        # 左辺の接続点
        expected_left_midpoint = QPointF(100.0, 100.0)  # 左辺の中点
        connection_point = self.rect1.get_connection_point_for_side(3)
        self.assertAlmostEqual(connection_point.x(), expected_left_midpoint.x())
        self.assertAlmostEqual(connection_point.y(), expected_left_midpoint.y())
    
    def test_connection_angle(self):
        """接続角度の計算が正しいかテスト"""
        # 右辺の接続角度
        expected_right_angle = 180  # 右辺の向き(90) + 90 = 180 度
        connection_angle = self.rect1.get_connection_angle_for_side(1)
        self.assertAlmostEqual(connection_angle, expected_right_angle)
        
        # 左辺の接続角度
        expected_left_angle = 0  # 左辺の向き(270) + 90 = 0/360 度
        connection_angle = self.rect1.get_connection_angle_for_side(3)
        self.assertAlmostEqual(connection_angle % 360, expected_left_angle)
    
    def test_contains_point(self):
        """点の内包判定が正しいかテスト"""
        # 四角形内部の点
        self.assertTrue(self.rect1.contains_point(QPointF(200, 100)))
        
        # 四角形外部の点
        self.assertFalse(self.rect1.contains_point(QPointF(400, 400)))
    
    def test_get_polygon(self):
        """ポリゴン取得が正しいかテスト"""
        polygon = self.rect1.get_polygon()
        self.assertEqual(polygon.size(), 4)  # 4頂点
    
    def test_internal_triangles(self):
        """内部三角形の取得が正しいかテスト"""
        triangles = self.rect1.get_triangles()
        self.assertEqual(len(triangles), 2)  # 2つの三角形
        
        # 三角形1のA辺が幅員1に対応
        self.assertAlmostEqual(triangles[0].lengths[0], self.rect1.width1)
        
        # 三角形1のB辺が延長に対応
        self.assertAlmostEqual(triangles[0].lengths[1], self.rect1.length)
        
        # 三角形2のB辺が幅員2に対応
        self.assertAlmostEqual(triangles[1].lengths[1], self.rect1.width2)
        
        # 三角形2のC辺が延長に対応
        self.assertAlmostEqual(triangles[1].lengths[2], self.rect1.length)

if __name__ == '__main__':
    unittest.main() 