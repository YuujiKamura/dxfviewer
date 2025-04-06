#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleShape - 三角形クラス

BaseShapeを継承し、三角形特有の機能を提供します。
"""

import math
import logging
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPolygonF, QColor

from ..base.base_shape import BaseShape
from triangle_ui.triangle_geometry import get_side_points

# ロガー設定
logger = logging.getLogger(__name__)

class TriangleData(BaseShape):
    """三角形を表すクラス"""
    
    def __init__(self, a=0.0, b=0.0, c=0.0, p_ca=QPointF(0, 0), angle_deg=0.0, number=1, parent=None, connection_side=-1):
        """三角形の初期化
        
        Args:
            a (float): 辺Aの長さ
            b (float): 辺Bの長さ
            c (float): 辺Cの長さ
            p_ca (QPointF): 三角形の基準位置（頂点CA）
            angle_deg (float): 三角形の回転角度（度数法）
            number (int): 三角形の識別番号
            parent: 親三角形の参照
            connection_side: 親三角形との接続辺
        """
        super().__init__(p_ca, angle_deg, number)
        self.name = f"Tri_{number}"  # Triangle_ から Tri_ に変更
        
        # 三角形固有のプロパティ
        self.lengths = [float(a), float(b), float(c)]
        self.points = [QPointF(p_ca), QPointF(0, 0), QPointF(0, 0)]
        self.internal_angles_deg = [0.0, 0.0, 0.0]
        
        # 親子関係管理のプロパティを追加
        self.parent = parent
        self.connection_side = connection_side
        self.children = [None, None, None]
        
        # 色属性を追加
        self.color = QColor(0, 100, 200)
        
        # 三角形の成立条件を確認して座標計算
        if a > 0 and b > 0 and c > 0:
            if self.is_valid_lengths():
                self.calculate_points()
    
    def is_valid_lengths(self, a=None, b=None, c=None):
        """三角形の成立条件を確認"""
        a = a if a is not None else self.lengths[0]
        b = b if b is not None else self.lengths[1]
        c = c if c is not None else self.lengths[2]
        return (a + b > c) and (b + c > a) and (c + a > b)
    
    def calculate_points(self):
        """三角形の頂点座標を計算"""
        # 初期座標
        p_ca = self.position  # 頂点CA
        
        # 辺の長さ
        a, b, c = self.lengths
        
        # 角度をラジアンに変換
        angle_rad = math.radians(self.angle_deg)
        
        # 点ABの座標を計算（辺Aの長さ分、角度方向に進んだ点）
        p_ab_x = p_ca.x() + a * math.cos(angle_rad)
        p_ab_y = p_ca.y() + a * math.sin(angle_rad)
        p_ab = QPointF(p_ab_x, p_ab_y)
        
        # CAからABへのベクトル
        vec_ca_to_ab = QPointF(p_ab.x() - p_ca.x(), p_ab.y() - p_ca.y())
        
        # 三角形の面積と高さを計算
        # ヘロンの公式で面積を計算
        s = (a + b + c) / 2  # 半周長
        try:
            area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        except ValueError:
            area = 0
            
        height = 2 * area / a if a > 0 else 0  # 辺Aに対する高さ
        
        # 点ABからの垂線の足からBCまでの距離
        try:
            base_to_bc = math.sqrt(c**2 - height**2)
        except ValueError:
            # 数値誤差などによるエラー時は0とする
            logger.warning(f"数値計算エラー: len_c={c}, height={height}")
            base_to_bc = 0
        
        # 点BCの計算
        # 垂線の方向ベクトル (CA→ABを90度回転)
        perp_vec = QPointF(-vec_ca_to_ab.y(), vec_ca_to_ab.x())
        perp_vec_length = math.sqrt(perp_vec.x()**2 + perp_vec.y()**2)
        
        if perp_vec_length > 0:
            # 単位ベクトル化して高さを掛ける
            norm_perp_vec = QPointF(
                perp_vec.x() / perp_vec_length,
                perp_vec.y() / perp_vec_length
            )
            height_vec = QPointF(
                norm_perp_vec.x() * height,
                norm_perp_vec.y() * height
            )
            
            # ABからbase_to_bc分進んだ点
            if a > 0:
                base_vec = QPointF(
                    vec_ca_to_ab.x() / a * (a - base_to_bc),
                    vec_ca_to_ab.y() / a * (a - base_to_bc)
                )
                base_point = QPointF(
                    p_ab.x() - base_vec.x(),
                    p_ab.y() - base_vec.y()
                )
                
                # 高さ方向に移動して点BCを求める
                p_bc = QPointF(
                    base_point.x() + height_vec.x(),
                    base_point.y() + height_vec.y()
                )
            else:
                p_bc = p_ab  # エラー時の回避策
        else:
            p_bc = p_ab  # エラー時の回避策
        
        # 内角の計算
        self.internal_angles_deg = self.calculate_internal_angles()
        
        # 頂点座標を更新
        self.points = [p_ca, p_ab, p_bc]
        
        # 中心点を計算（3頂点の平均）
        center_x = (p_ca.x() + p_ab.x() + p_bc.x()) / 3
        center_y = (p_ca.y() + p_ab.y() + p_bc.y()) / 3
        self.center_point = QPointF(center_x, center_y)
    
    def calculate_internal_angles(self):
        """三角形の内角を計算"""
        a, b, c = self.lengths
        
        # 余弦定理を使って内角を計算
        cos_a = (b * b + c * c - a * a) / (2 * b * c)
        cos_a = max(-1.0, min(1.0, cos_a))  # -1.0から1.0の範囲に制限
        angle_a = math.degrees(math.acos(cos_a))
        
        cos_b = (c * c + a * a - b * b) / (2 * c * a)
        cos_b = max(-1.0, min(1.0, cos_b))
        angle_b = math.degrees(math.acos(cos_b))
        
        cos_c = (a * a + b * b - c * c) / (2 * a * b)
        cos_c = max(-1.0, min(1.0, cos_c))
        angle_c = math.degrees(math.acos(cos_c))
        
        return [angle_a, angle_b, angle_c]
    
    def get_polygon(self) -> QPolygonF:
        """描画用のQPolygonFを返す"""
        return QPolygonF(self.points)
    
    def get_bounds(self) -> tuple:
        """三角形の境界を返す"""
        min_x = min(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_x = max(p.x() for p in self.points)
        max_y = max(p.y() for p in self.points)
        return (min_x, min_y, max_x, max_y)
    
    def contains_point(self, point: QPointF) -> bool:
        """点が三角形内にあるかチェック"""
        return self.get_polygon().containsPoint(point, 0)
    
    def get_sides(self) -> list:
        """三角形の辺を表す(始点, 終点)のリストを返す"""
        return [
            (self.points[0], self.points[1]),  # 辺A: CA→AB
            (self.points[1], self.points[2]),  # 辺B: AB→BC
            (self.points[2], self.points[0])   # 辺C: BC→CA
        ]
    
    def get_side_line(self, side_index: int) -> tuple:
        """指定された辺の両端点を返す (0:A, 1:B, 2:C)"""
        sides = self.get_sides()
        if 0 <= side_index < len(sides):
            p1, p2 = sides[side_index]
            logger.debug(f"Triangle {self.number}: 辺{chr(65 + side_index)}({side_index})の両端点: {p1} → {p2}")
            return p1, p2
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return None
    
    def get_side_length(self, side_index: int) -> float:
        """指定された辺の長さを返す"""
        if 0 <= side_index < 3:
            return self.lengths[side_index]
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return 0.0
    
    def get_side_midpoint(self, side_index: int) -> QPointF:
        """指定された辺の中点を返す"""
        sides = self.get_sides()
        if 0 <= side_index < len(sides):
            p1, p2 = sides[side_index]
            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2
            return QPointF(mid_x, mid_y)
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return QPointF(0, 0)
    
    def update_with_new_properties(self, **properties) -> bool:
        """三角形のプロパティを更新（汎用メソッド）"""
        # 辺の長さを更新
        lengths = properties.get('lengths', None)
        if lengths:
            if not self.is_valid_lengths(lengths[0], lengths[1], lengths[2]):
                logger.warning(f"Triangle {self.number}: 無効な辺の長さ {lengths}")
                return False
            self.lengths = lengths.copy()
        
        # 位置を更新
        position = properties.get('position', None)
        if position:
            self.position = QPointF(position)
            self.points[0] = QPointF(position)
        
        # 角度を更新
        angle_deg = properties.get('angle_deg', None)
        if angle_deg is not None:
            self.angle_deg = float(angle_deg)
        
        # 座標を再計算
        self.calculate_points()
        return True
    
    def update_with_new_lengths(self, new_lengths) -> bool:
        """三角形の寸法を更新する（TriangleData互換）"""
        return self.update_with_new_properties(lengths=new_lengths)
    
    def get_connection_point_for_side(self, side_index: int) -> QPointF:
        """指定された辺の接続点を返す（内部メソッド）"""
        if 0 <= side_index < 3:
            # 辺の接続点インデックス (辺の終点が次の三角形の始点)
            connection_indices = [1, 2, 0]  # 各辺の終点インデックス
            
            if 0 <= side_index < 3:
                return self.points[connection_indices[side_index]]
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return self.position
    
    def get_connection_point_by_side(self, side_index: int) -> QPointF:
        """指定された接続辺の次の三角形の基準点を返す（TriangleData互換）"""
        return self.get_connection_point_for_side(side_index)
    
    def get_connection_angle_for_side(self, side_index: int) -> float:
        """指定された辺に接続する図形の回転角度を返す（内部メソッド）"""
        if 0 <= side_index < 3:
            if side_index == 0:  # 辺A: CA→AB
                # AB方向から180度逆向き
                return (self.angle_deg + 180) % 360
            
            elif side_index == 1:  # 辺B: AB→BC
                # AB→BC向きの角度を計算
                sides = self.get_sides()
                start, end = sides[side_index]
                vec_x = end.x() - start.x()
                vec_y = end.y() - start.y()
                angle_rad = math.atan2(vec_y, vec_x)
                # 180度回転（逆向き）
                return (math.degrees(angle_rad) + 180) % 360
            
            elif side_index == 2:  # 辺C: BC→CA
                # BC→CA向きの角度を計算
                sides = self.get_sides()
                start, end = sides[side_index]
                vec_x = end.x() - start.x()
                vec_y = end.y() - start.y()
                angle_rad = math.atan2(vec_y, vec_x)
                # 180度回転（逆向き）
                return (math.degrees(angle_rad) + 180) % 360
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return self.angle_deg
    
    def get_angle_by_side(self, side_index: int) -> float:
        """指定された辺に接続する次の三角形の回転角度を返す（TriangleData互換）"""
        return self.get_connection_angle_for_side(side_index)
    
    @staticmethod
    def get_detailed_edge_info(triangle, side_index):
        """三角形の辺の詳細情報を文字列として返す（純粋関数）"""
        if not triangle:
            return "選択なし"
        
        # 辺の表示名マッピング（インデックスから名前へ）
        edge_name_mapping = {
            0: "A",  # インデックス0 → 辺A (CA→AB)
            1: "B",  # インデックス1 → 辺B (AB→BC)
            2: "C"   # インデックス2 → 辺C (BC→CA)
        }
        edge_name = edge_name_mapping[side_index]
        
        # 辺の両端点を取得
        side_points = get_side_points(triangle.points, side_index)
        if not side_points:
            return "選択なし"
            
        p1, p2 = side_points
        edge_length = triangle.lengths[side_index]
        
        # 頂点名マッピング（辺のインデックスから頂点の名前ペアへ）
        edge_vertices_mapping = {
            0: ("CA", "AB"),  # 辺A
            1: ("AB", "BC"),  # 辺B
            2: ("BC", "CA")   # 辺C
        }
        start_vertex, end_vertex = edge_vertices_mapping[side_index]
        
        # 詳細情報を文字列として返す
        return (
            f"三角形 {triangle.number} の辺 {edge_name}: "
            f"{start_vertex}({p1.x():.1f}, {p1.y():.1f}) → "
            f"{end_vertex}({p2.x():.1f}, {p2.y():.1f}), "
            f"長さ: {edge_length:.1f}"
        )
    
    def get_detailed_info(self) -> str:
        """三角形の詳細情報を文字列として返す"""
        base_info = super().get_detailed_info()
        return f"{base_info}, 辺の長さ=(A:{self.lengths[0]:.1f}, B:{self.lengths[1]:.1f}, C:{self.lengths[2]:.1f})"
    
    def set_child(self, child_triangle, side_index):
        """指定した辺に接続する子三角形を設定"""
        if 0 <= side_index < 3:
            self.children[side_index] = child_triangle
            child_triangle.parent = self
            child_triangle.connection_side = side_index
            logger.debug(f"Triangle {self.number}の辺{side_index}に子三角形{child_triangle.number}を接続しました")
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}") 