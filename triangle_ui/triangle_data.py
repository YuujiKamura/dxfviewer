#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleData - 三角形データクラス

三角形の寸法、頂点座標、接続関係を管理するクラス
"""

import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPolygonF
import logging

# ロガー設定
logger = logging.getLogger(__name__)

class TriangleData:
    """三角形のデータと計算ロジックを保持するクラス"""
    def __init__(self, a=0.0, b=0.0, c=0.0, p_ca=QPointF(0, 0), angle_deg=180.0, number=1, parent=None, connection_side=-1):
        self.number = number
        self.name = f"Tri_{number}"
        self.lengths = [float(a), float(b), float(c)]
        self.points = [QPointF(p_ca), QPointF(0, 0), QPointF(0, 0)]
        self.angle_deg = float(angle_deg)
        self.internal_angles_deg = [0.0, 0.0, 0.0]
        self.center_point = QPointF(0, 0)
        self.parent = parent
        self.connection_side = connection_side
        self.children = [None, None, None]
        self.color = QColor(0, 100, 200)
        
        if a > 0 and b > 0 and c > 0:
            if self.is_valid_lengths():
                self.calculate_points()
    
    def is_valid_lengths(self, a=None, b=None, c=None):
        """三角形の成立条件を確認"""
        a = a if a is not None else self.lengths[0]
        b = b if b is not None else self.lengths[1]
        c = c if c is not None else self.lengths[2]
        if a <= 0 or b <= 0 or c <= 0:
            return False
        return (a + b > c) and (b + c > a) and (c + a > b)
    
    def calculate_points(self):
        """三角形の頂点座標を計算"""
        p_ca = self.points[0]
        len_a = self.lengths[0]
        angle_rad = math.radians(self.angle_deg)
        
        # 点ABの計算
        p_ab = QPointF(p_ca.x() + len_a * math.cos(angle_rad), p_ca.y() + len_a * math.sin(angle_rad))
        self.points[1] = p_ab
        
        # 内角の計算（余弦定理）
        len_b = self.lengths[1]
        len_c = self.lengths[2]
        
        # 角A（頂点BC）
        if len_b * len_c > 0:
            cos_angle_a = (len_b**2 + len_c**2 - len_a**2) / (2 * len_b * len_c)
            cos_angle_a = max(-1.0, min(1.0, cos_angle_a))
            angle_a_rad = math.acos(cos_angle_a)
            angle_a_deg = math.degrees(angle_a_rad)
        else:
            angle_a_deg = 0
        
        # 角B（頂点CA）
        if len_a * len_c > 0:
            cos_angle_b = (len_a**2 + len_c**2 - len_b**2) / (2 * len_a * len_c)
            cos_angle_b = max(-1.0, min(1.0, cos_angle_b))
            angle_b_rad = math.acos(cos_angle_b)
            angle_b_deg = math.degrees(angle_b_rad)
        else:
            angle_b_deg = 0
        
        # 角C（頂点AB）
        if len_a * len_b > 0:
            cos_angle_c = (len_a**2 + len_b**2 - len_c**2) / (2 * len_a * len_b)
            cos_angle_c = max(-1.0, min(1.0, cos_angle_c))
            angle_c_rad = math.acos(cos_angle_c)
            angle_c_deg = math.degrees(angle_c_rad)
        else:
            angle_c_deg = 0
        
        # 内部角度を設定
        self.internal_angles_deg = [angle_a_deg, angle_b_deg, angle_c_deg]
        
        # 点BCの計算（一般的な方法）
        # CAからABへのベクトル
        vec_ca_to_ab = QPointF(p_ab.x() - p_ca.x(), p_ab.y() - p_ca.y())
        
        # 三角形の面積を計算（ヘロンの公式）
        s = (len_a + len_b + len_c) / 2  # 半周長
        area = math.sqrt(s * (s - len_a) * (s - len_b) * (s - len_c))  # 面積
        
        # 高さを計算
        height = 2 * area / len_a  # 辺Aに対する高さ
        
        # 点ABからの垂線の足からBCまでの距離
        base_to_bc = math.sqrt(len_c**2 - height**2)
        
        # 点BCの計算
        # 垂線の方向ベクトル（CA→ABを90度回転）
        perp_vec = QPointF(-vec_ca_to_ab.y(), vec_ca_to_ab.x())
        perp_vec_length = math.sqrt(perp_vec.x()**2 + perp_vec.y()**2)
        if perp_vec_length > 0:
            # 単位ベクトル化して高さを掛ける
            norm_perp_vec = QPointF(perp_vec.x() / perp_vec_length, perp_vec.y() / perp_vec_length)
            height_vec = QPointF(norm_perp_vec.x() * height, norm_perp_vec.y() * height)
            
            # ABからbase_to_bc分進んだ点
            if len_a > 0:
                base_vec = QPointF(vec_ca_to_ab.x() / len_a * (len_a - base_to_bc), 
                                  vec_ca_to_ab.y() / len_a * (len_a - base_to_bc))
                base_point = QPointF(p_ab.x() - base_vec.x(), p_ab.y() - base_vec.y())
                
                # 高さ方向に移動して点BCを求める
                self.points[2] = QPointF(base_point.x() + height_vec.x(), base_point.y() + height_vec.y())
            else:
                self.points[2] = p_ab  # エラー時の回避策
        else:
            self.points[2] = p_ab  # エラー時の回避策
        
        # 重心計算
        p_bc = self.points[2]
        self.center_point = QPointF((p_ca.x() + p_ab.x() + p_bc.x()) / 3.0, (p_ca.y() + p_ab.y() + p_bc.y()) / 3.0)
    
    def get_polygon(self) -> QPolygonF:
        """描画用のQPolygonFを返す"""
        return QPolygonF(self.points)
    
    def get_side_line(self, side_index: int) -> tuple:
        """指定された辺の両端点を返す (0:A, 1:B, 2:C)"""
        if side_index == 0:  # 辺A: CA→AB
            logger.debug(f"辺A({side_index})の両端点: {self.points[0]} → {self.points[1]}")
            return self.points[0], self.points[1]
        elif side_index == 1:  # 辺B: AB→BC
            logger.debug(f"辺B({side_index})の両端点: {self.points[1]} → {self.points[2]}")
            return self.points[1], self.points[2]
        elif side_index == 2:  # 辺C: BC→CA
            logger.debug(f"辺C({side_index})の両端点: {self.points[2]} → {self.points[0]}")
            return self.points[2], self.points[0]
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return None
    
    def get_connection_point_by_side(self, side_index: int) -> QPointF:
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
    
    def get_angle_by_side(self, side_index: int) -> float:
        """指定された辺に接続する次の三角形の回転角度を返す"""
        if side_index == 0:  # 辺A: CA→AB
            # AB方向から180度逆向き
            return (self.angle_deg + 180) % 360
        elif side_index == 1:  # 辺B: AB→BC
            # AB→BC向きの角度を計算
            vec_ab_to_bc = QPointF(self.points[2].x() - self.points[1].x(), 
                                   self.points[2].y() - self.points[1].y())
            angle_rad = math.atan2(vec_ab_to_bc.y(), vec_ab_to_bc.x())
            # 180度回転（逆向き）
            return (math.degrees(angle_rad) + 180) % 360
        elif side_index == 2:  # 辺C: BC→CA
            # BC→CA向きの角度を計算
            vec_bc_to_ca = QPointF(self.points[0].x() - self.points[2].x(), 
                                   self.points[0].y() - self.points[2].y())
            angle_rad = math.atan2(vec_bc_to_ca.y(), vec_bc_to_ca.x())
            # 180度回転（逆向き）
            return (math.degrees(angle_rad) + 180) % 360
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return 0
    
    def set_child(self, child_triangle, side_index):
        """指定した辺に接続する子三角形を設定"""
        if 0 <= side_index < 3:
            self.children[side_index] = child_triangle
            logger.debug(f"Triangle {self.number}の辺{side_index}に子三角形{child_triangle.number}を接続しました")
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}") 