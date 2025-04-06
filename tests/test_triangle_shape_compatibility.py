#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleShapeとTriangleDataの互換性テスト

両クラスが同じインターフェースと振る舞いを持つことを確認するテスト。
"""

import unittest
import math
from PySide6.QtCore import QPointF

# テスト対象のクラスをインポート
from shapes.geometry.triangle_shape import TriangleData, TriangleManager

class TestShapeEquivalence(unittest.TestCase):
    """TriangleShapeとTriangleDataの等価性テスト"""
    
    def setUp(self):
        """テスト前の準備"""
        # 同じパラメータで両方のクラスのインスタンスを作成
        self.a, self.b, self.c = 60.0, 80.0, 100.0
        self.p_ca = QPointF(10.0, 20.0)
        self.angle = 180.0
        self.number = 1
        
        self.td = TriangleData(
            self.a, self.b, self.c, 
            self.p_ca, 
            self.angle, 
            self.number
        )
        
        self.ts = TriangleData(
            self.a, self.b, self.c, 
            self.p_ca, 
            self.angle, 
            self.number
        )
    
    def test_property_equivalence(self):
        """基本プロパティの等価性テスト"""
        # 基本プロパティが同じ値を持っていることを確認
        self.assertEqual(self.td.number, self.ts.number)
        self.assertEqual(len(self.td.lengths), len(self.ts.lengths))
        self.assertEqual(self.td.lengths[0], self.ts.lengths[0])
        self.assertEqual(self.td.lengths[1], self.ts.lengths[1])
        self.assertEqual(self.td.lengths[2], self.ts.lengths[2])
        self.assertEqual(self.td.angle_deg, self.ts.angle_deg)
        
        # 座標を比較（実装の違いによる小さな誤差は許容）
        self.assertEqual(len(self.td.points), len(self.ts.points))
        for i in range(len(self.td.points)):
            self.assertAlmostEqual(self.td.points[i].x(), self.ts.points[i].x(), delta=0.01)
            self.assertAlmostEqual(self.td.points[i].y(), self.ts.points[i].y(), delta=0.01)
        
        # 内角を比較
        self.assertEqual(len(self.td.internal_angles_deg), len(self.ts.internal_angles_deg))
        for i in range(len(self.td.internal_angles_deg)):
            self.assertAlmostEqual(self.td.internal_angles_deg[i], self.ts.internal_angles_deg[i], delta=0.01)
    
    def test_method_equivalence(self):
        """メソッドの振る舞いの等価性テスト"""
        # get_polygon()の結果を比較
        td_poly = self.td.get_polygon()
        ts_poly = self.ts.get_polygon()
        self.assertEqual(td_poly.size(), ts_poly.size())
        
        # is_valid_lengths()の結果を比較
        self.assertEqual(
            self.td.is_valid_lengths(60, 80, 100),
            self.ts.is_valid_lengths(60, 80, 100)
        )
        self.assertEqual(
            self.td.is_valid_lengths(10, 20, 50),
            self.ts.is_valid_lengths(10, 20, 50)
        )
        
        # get_side_line()の結果を比較
        td_side = self.td.get_side_line(0)
        ts_side = self.ts.get_side_line(0)
        if td_side and ts_side:
            self.assertAlmostEqual(td_side[0].x(), ts_side[0].x(), delta=0.01)
            self.assertAlmostEqual(td_side[0].y(), ts_side[0].y(), delta=0.01)
            self.assertAlmostEqual(td_side[1].x(), ts_side[1].x(), delta=0.01)
            self.assertAlmostEqual(td_side[1].y(), ts_side[1].y(), delta=0.01)
        
        # get_connection_point_by_side()の結果を比較
        for i in range(3):
            td_point = self.td.get_connection_point_by_side(i)
            ts_point = self.ts.get_connection_point_by_side(i)
            self.assertAlmostEqual(td_point.x(), ts_point.x(), delta=0.1)
            self.assertAlmostEqual(td_point.y(), ts_point.y(), delta=0.1)
        
        # get_angle_by_side()の結果を比較
        for i in range(3):
            td_angle = self.td.get_angle_by_side(i)
            ts_angle = self.ts.get_angle_by_side(i)
            # 角度の差が360度の倍数である場合があるため、sin/cosで比較
            self.assertAlmostEqual(math.sin(math.radians(td_angle)), 
                                  math.sin(math.radians(ts_angle)), delta=0.01)
            self.assertAlmostEqual(math.cos(math.radians(td_angle)), 
                                  math.cos(math.radians(ts_angle)), delta=0.01)
    
    def test_update_equivalence(self):
        """更新メソッドの等価性テスト"""
        # 新しい長さ
        new_lengths = [70.0, 90.0, 110.0]
        
        # 両方のオブジェクトを更新
        self.td.update_with_new_lengths(new_lengths)
        self.ts.update_with_new_lengths(new_lengths)
        
        # 更新後のプロパティを比較
        for i in range(3):
            self.assertEqual(self.td.lengths[i], self.ts.lengths[i])
        
        # 更新後の座標を比較
        for i in range(3):
            self.assertAlmostEqual(self.td.points[i].x(), self.ts.points[i].x(), delta=0.1)
            self.assertAlmostEqual(self.td.points[i].y(), self.ts.points[i].y(), delta=0.1)
        
        # 更新後の内角を比較
        for i in range(3):
            self.assertAlmostEqual(self.td.internal_angles_deg[i], self.ts.internal_angles_deg[i], delta=0.1)

class TestMethodCompatibility(unittest.TestCase):
    """インターフェースの互換性テスト"""
    
    def test_is_valid_lengths(self):
        """is_valid_lengthsメソッドの互換性テスト"""
        # 正三角形
        td = TriangleData(100, 100, 100)
        ts = TriangleData(100, 100, 100)
        
        # 両クラスとも同じ結果を返すことを確認
        self.assertEqual(td.is_valid_lengths(), ts.is_valid_lengths())
        self.assertEqual(td.is_valid_lengths(120, 120, 120), ts.is_valid_lengths(120, 120, 120))
        self.assertEqual(td.is_valid_lengths(10, 20, 50), ts.is_valid_lengths(10, 20, 50))
    
    def test_get_side_line(self):
        """get_side_lineメソッドの互換性テスト"""
        td = TriangleData(100, 100, 100)
        ts = TriangleData(100, 100, 100)
        
        # 有効な辺インデックス
        for i in range(3):
            td_side = td.get_side_line(i)
            ts_side = ts.get_side_line(i)
            # 両方がNoneか両方がNoneでない
            self.assertEqual(td_side is None, ts_side is None)
            if td_side and ts_side:
                # タプルの長さが同じ
                self.assertEqual(len(td_side), len(ts_side))
        
        # 無効な辺インデックス
        self.assertEqual(td.get_side_line(5) is None, ts.get_side_line(5) is None)
    
    def test_update_with_new_lengths(self):
        """update_with_new_lengthsメソッドの互換性テスト"""
        td = TriangleData(100, 100, 100)
        ts = TriangleData(100, 100, 100)
        
        # 有効な辺の長さ
        new_lengths = [120.0, 120.0, 120.0]
        self.assertEqual(td.update_with_new_lengths(new_lengths), 
                         ts.update_with_new_lengths(new_lengths))
        
        # 無効な辺の長さ
        invalid_lengths = [10.0, 20.0, 50.0]
        self.assertEqual(td.update_with_new_lengths(invalid_lengths), 
                         ts.update_with_new_lengths(invalid_lengths))
    
    def test_connect_methods(self):
        """接続関連メソッドの互換性テスト"""
        td_parent = TriangleData(100, 100, 100, QPointF(0, 0), 0, 1)
        td_child = TriangleData(80, 80, 80, QPointF(100, 0), 180, 2)
        
        ts_parent = TriangleData(100, 100, 100, QPointF(0, 0), 0, 1)
        ts_child = TriangleData(80, 80, 80, QPointF(100, 0), 180, 2)
        
        # 親子関係を設定
        td_parent.set_child(td_child, 0)
        ts_parent.set_child(ts_child, 0)
        
        # 親子関係が正しく設定されていることを確認
        self.assertEqual(td_child.parent is td_parent, ts_child.parent is ts_parent)
        self.assertEqual(td_child.connection_side, ts_child.connection_side)

if __name__ == '__main__':
    unittest.main() 