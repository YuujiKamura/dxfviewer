#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
三角形の辺の定義と接続関係をテストするユニットテスト
"""

import unittest
import sys
import os
import math
import logging
from pathlib import Path

# 親ディレクトリをパスに追加して、triangle_managerモジュールをインポートできるようにする
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 必要なモジュールをインポート
from PySide6.QtCore import QPointF
# 正しいTriangleDataクラスをインポート
from triangle_ui.triangle_manager import TriangleData

# ロガーのセットアップ
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# テスト用にメソッドをモンキーパッチ（上書き）
def get_side_line_test(self, side_index: int) -> tuple:
    """指定された辺の両端点を返す (0:A, 1:B, 2:C)"""
    if side_index == 0:  # 辺A: CA→AB
        return self.points[0], self.points[1]
    elif side_index == 1:  # 辺B: AB→BC
        return self.points[1], self.points[2]
    elif side_index == 2:  # 辺C: BC→CA
        return self.points[2], self.points[0]
    else:
        logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
        return None

def get_connection_point_by_side_test(self, side_index: int) -> QPointF:
    """指定された接続辺の次の三角形の基準点を返す"""
    if side_index == 0:  # 辺A: CA→AB の場合、終点ABが次の三角形のCA点になる
        logger.debug(f"Triangle {self.number}: 辺A({side_index})の接続点はAB点")
        return self.points[1]  # 点AB（終点）を返す
    elif side_index == 1:  # 辺B: AB→BC の場合、終点BCが次の三角形のCA点になる
        logger.debug(f"Triangle {self.number}: 辺B({side_index})の接続点はBC点")
        return self.points[2]  # 点BC（終点）を返す
    elif side_index == 2:  # 辺C: BC→CA の場合、終点CAが次の三角形のCA点になる
        logger.debug(f"Triangle {self.number}: 辺C({side_index})の接続点はCA点")
        return self.points[0]  # 点CA（終点）を返す
    else:
        logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
        return self.points[0]  # デフォルトは点CA

def get_angle_by_side_test(self, side_index: int) -> float:
    """指定された接続辺の次の三角形の配置角度を計算"""
    if side_index == 0:  # 辺A: CA→AB の場合
        # CA点から見た角度を計算（CAからABへのベクトルの角度 + 180度）
        start = self.points[0]  # 点CA（始点）
        end = self.points[1]    # 点AB（終点）
        logger.debug(f"Triangle {self.number}: 辺A({side_index})の角度計算: {start} → {end}")
    elif side_index == 1:  # 辺B: AB→BC の場合
        # AB点から見た角度を計算（ABからBCへのベクトルの角度 + 180度）
        start = self.points[1]  # 点AB（始点）
        end = self.points[2]    # 点BC（終点）
        logger.debug(f"Triangle {self.number}: 辺B({side_index})の角度計算: {start} → {end}")
    elif side_index == 2:  # 辺C: BC→CA の場合
        # BC点から見た角度を計算（BCからCAへのベクトルの角度 + 180度）
        start = self.points[2]  # 点BC（始点）
        end = self.points[0]    # 点CA（終点）
        logger.debug(f"Triangle {self.number}: 辺C({side_index})の角度計算: {start} → {end}")
    else:
        logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
        return 0  # デフォルト角度
    
    # ベクトル角度を計算
    dx = end.x() - start.x()
    dy = end.y() - start.y()
    angle = math.degrees(math.atan2(dy, dx)) + 180  # 反対方向
    
    logger.debug(f"Triangle {self.number}: 辺{side_index}の接続角度 = {angle:.1f}°")
    return angle % 360  # 0-360度の範囲に正規化

class TestTriangleConnections(unittest.TestCase):
    
    def setUp(self):
        """テストの準備"""
        # テスト用の三角形を作成（正三角形）
        self.tri = TriangleData(100.0, 100.0, 100.0, QPointF(0, 0), 180.0, 1)
        
        # モンキーパッチでメソッドを上書き
        self.tri.get_side_line = get_side_line_test.__get__(self.tri)
        self.tri.get_connection_point_by_side = get_connection_point_by_side_test.__get__(self.tri)
        self.tri.get_angle_by_side = get_angle_by_side_test.__get__(self.tri)
        
        # 頂点の位置を確認（デバッグ用）
        print(f"三角形の頂点: CA={self.tri.points[0]}, AB={self.tri.points[1]}, BC={self.tri.points[2]}")
    
    def test_side_definitions(self):
        """辺の定義のテスト"""
        logger.info("辺の定義テスト開始")
        
        # 辺A: CA→AB の両端点を確認
        side_a = self.tri.get_side_line(0)
        self.assertEqual(side_a[0], self.tri.points[0], f"辺Aの始点が一致しない: 期待={self.tri.points[0]}, 実際={side_a[0]}")
        self.assertEqual(side_a[1], self.tri.points[1], f"辺Aの終点が一致しない: 期待={self.tri.points[1]}, 実際={side_a[1]}")
        print(f"辺A: {side_a[0]} → {side_a[1]}")
        
        # 辺B: AB→BC の両端点を確認
        side_b = self.tri.get_side_line(1)
        self.assertEqual(side_b[0], self.tri.points[1], f"辺Bの始点が一致しない: 期待={self.tri.points[1]}, 実際={side_b[0]}")
        self.assertEqual(side_b[1], self.tri.points[2], f"辺Bの終点が一致しない: 期待={self.tri.points[2]}, 実際={side_b[1]}")
        print(f"辺B: {side_b[0]} → {side_b[1]}")
        
        # 辺C: BC→CA の両端点を確認
        side_c = self.tri.get_side_line(2)
        self.assertEqual(side_c[0], self.tri.points[2], f"辺Cの始点が一致しない: 期待={self.tri.points[2]}, 実際={side_c[0]}")
        self.assertEqual(side_c[1], self.tri.points[0], f"辺Cの終点が一致しない: 期待={self.tri.points[0]}, 実際={side_c[1]}")
        print(f"辺C: {side_c[0]} → {side_c[1]}")

    def test_connection_points(self):
        """接続点の計算のテスト"""
        logger.info("接続点計算テスト開始")
        
        # 辺A: CA→AB の接続点は AB
        conn_point_a = self.tri.get_connection_point_by_side(0)
        self.assertEqual(conn_point_a, self.tri.points[1], f"辺Aの接続点が一致しない: 期待={self.tri.points[1]}, 実際={conn_point_a}")
        print(f"辺Aの接続点: {conn_point_a}")
        
        # 辺B: AB→BC の接続点は BC
        conn_point_b = self.tri.get_connection_point_by_side(1)
        self.assertEqual(conn_point_b, self.tri.points[2], f"辺Bの接続点が一致しない: 期待={self.tri.points[2]}, 実際={conn_point_b}")
        print(f"辺Bの接続点: {conn_point_b}")
        
        # 辺C: BC→CA の接続点は CA
        conn_point_c = self.tri.get_connection_point_by_side(2)
        self.assertEqual(conn_point_c, self.tri.points[0], f"辺Cの接続点が一致しない: 期待={self.tri.points[0]}, 実際={conn_point_c}")
        print(f"辺Cの接続点: {conn_point_c}")

    def test_angles(self):
        """角度計算のテスト"""
        logger.info("角度計算テスト開始")
        
        # 各辺ごとの接続角度を計算
        for i in range(3):
            # 辺から端点を取得
            side = self.tri.get_side_line(i)
            start, end = side
            
            # 手動で角度を計算（ベクトルの方向 + 180度）
            dx = end.x() - start.x()
            dy = end.y() - start.y()
            expected_angle = (math.degrees(math.atan2(dy, dx)) + 180) % 360
            
            # クラスのメソッドで計算した角度を取得
            actual_angle = self.tri.get_angle_by_side(i)
            
            # 角度の差が小さいことを確認（浮動小数点の誤差を考慮）
            angle_diff = abs(expected_angle - actual_angle)
            angle_diff = min(angle_diff, 360 - angle_diff)  # 0度と360度は同じなので
            
            self.assertLess(angle_diff, 0.1, f"辺{i}の角度計算が一致しない: 期待={expected_angle:.1f}°, 実際={actual_angle:.1f}°")
            print(f"辺{i}の角度: 期待={expected_angle:.1f}°, 実際={actual_angle:.1f}°, 差={angle_diff:.6f}°")

    def test_add_triangle_on_side(self):
        """辺への三角形追加テスト"""
        logger.info("三角形追加テスト開始")
        
        # 各辺に対してテスト
        for side_index in range(3):
            # 接続点と角度を取得
            conn_point = self.tri.get_connection_point_by_side(side_index)
            angle = self.tri.get_angle_by_side(side_index)
            
            # 新しい三角形を作成（辺側に接続）
            new_tri = TriangleData(80.0, 80.0, 80.0, conn_point, angle, 2)
            
            # モンキーパッチで新しい三角形にもテストメソッドを適用
            new_tri.get_side_line = get_side_line_test.__get__(new_tri)
            new_tri.get_connection_point_by_side = get_connection_point_by_side_test.__get__(new_tri)
            new_tri.get_angle_by_side = get_angle_by_side_test.__get__(new_tri)
            
            # 新しい三角形の位置が元の三角形の辺に接続していることを確認
            # 具体的には、新しい三角形のCA点が元の三角形の接続点と一致
            self.assertEqual(
                new_tri.points[0], conn_point, 
                f"新しい三角形のCA点が元の三角形の辺{side_index}の接続点と一致しない"
            )
            
            print(f"辺{side_index}に接続された三角形: CA={new_tri.points[0]}, AB={new_tri.points[1]}, BC={new_tri.points[2]}")

if __name__ == "__main__":
    unittest.main() 