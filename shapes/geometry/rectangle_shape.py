#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RectangleShape - 四角形クラス

BaseShapeを継承し、内部的に2つの三角形で構成された四角形を提供します。
"""

import math
import logging
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPolygonF

from ..base.base_shape import BaseShape
from .triangle_shape import TriangleData

# ロガー設定
logger = logging.getLogger(__name__)

class RectangleShape(BaseShape):
    """四角形を表すクラス（内部的に2つの三角形で構成）"""
    
    def __init__(self, width=0.0, height=0.0, p_ca=QPointF(0, 0), angle_deg=0.0, number=1):
        """四角形の初期化
        
        Args:
            width (float): 幅
            height (float): 高さ
            p_ca (QPointF): 四角形の基準位置（左下頂点）
            angle_deg (float): 四角形の回転角度（度数法）
            number (int): 四角形の識別番号
        """
        super().__init__(p_ca, angle_deg, number)
        self.name = f"Rectangle_{number}"
        
        # 四角形固有のプロパティ
        self.width = float(width)
        self.height = float(height)
        self.points = [QPointF() for _ in range(4)]  # 4頂点
        
        # 内部三角形
        self.triangles = [None, None]
        
        # 頂点計算
        if width > 0 and height > 0:
            self._create_triangles()
            self.calculate_points()
    
    def _create_triangles(self):
        """内部三角形を生成"""
        # 対角線の長さを計算
        diagonal = math.sqrt(self.width**2 + self.height**2)
        
        # 左下を基準位置とする
        base_pos = self.position
        
        # 三角形1: 左下, 左上, 右上（反時計回り）
        # 辺の長さ: 高さ, 幅, 対角線
        self.triangles[0] = TriangleData(
            a=self.height,
            b=self.width,
            c=diagonal,
            p_ca=base_pos,
            angle_deg=self.angle_deg + 90,  # 90度回転（高さ方向が最初の辺）
            number=self.number * 100 + 1  # 内部番号
        )
        
        # 三角形2: 左下, 右上, 右下（反時計回り）
        # 辺の長さ: 対角線, 高さ, 幅
        # 右上頂点を計算
        angle_rad = math.radians(self.angle_deg)
        top_right_x = base_pos.x() + self.width * math.cos(angle_rad)
        top_right_y = base_pos.y() + self.width * math.sin(angle_rad)
        
        # 対角線の角度を計算
        diag_angle = math.degrees(math.atan2(self.height, self.width)) + self.angle_deg
        
        self.triangles[1] = TriangleData(
            a=diagonal,
            b=self.height,
            c=self.width,
            p_ca=base_pos,
            angle_deg=diag_angle,  # 対角線方向
            number=self.number * 100 + 2  # 内部番号
        )
    
    def calculate_points(self):
        """四角形の頂点座標を計算"""
        # 内部三角形がない場合は作成
        if not self.triangles[0] or not self.triangles[1]:
            self._create_triangles()
        
        # 基準位置（左下）
        self.points[0] = QPointF(self.position)
        
        # 角度をラジアンに変換
        angle_rad = math.radians(self.angle_deg)
        
        # 右下頂点
        self.points[1] = QPointF(
            self.position.x() + self.width * math.cos(angle_rad),
            self.position.y() + self.width * math.sin(angle_rad)
        )
        
        # 高さ方向の単位ベクトル（幅方向に90度回転）
        height_dir_x = -math.sin(angle_rad)
        height_dir_y = math.cos(angle_rad)
        
        # 右上頂点
        self.points[2] = QPointF(
            self.points[1].x() + self.height * height_dir_x,
            self.points[1].y() + self.height * height_dir_y
        )
        
        # 左上頂点
        self.points[3] = QPointF(
            self.position.x() + self.height * height_dir_x,
            self.position.y() + self.height * height_dir_y
        )
        
        # 中心点を計算（4頂点の平均）
        center_x = sum(p.x() for p in self.points) / 4
        center_y = sum(p.y() for p in self.points) / 4
        self.center_point = QPointF(center_x, center_y)
        
        # 内部三角形の座標も更新
        self._update_triangle_points()
    
    def _update_triangle_points(self):
        """内部三角形の座標を更新"""
        # 三角形1: 左下(0), 左上(3), 右上(2)
        tri1_points = [self.points[0], self.points[3], self.points[2]]
        self.triangles[0].points = tri1_points.copy()
        self.triangles[0].position = QPointF(tri1_points[0])
        
        # 三角形2: 左下(0), 右上(2), 右下(1)
        tri2_points = [self.points[0], self.points[2], self.points[1]]
        self.triangles[1].points = tri2_points.copy()
        self.triangles[1].position = QPointF(tri2_points[0])
        
        # 内部三角形の座標計算は自動実行しない（実装の違いに対応）
    
    def get_polygon(self) -> QPolygonF:
        """描画用のQPolygonFを返す"""
        return QPolygonF(self.points)
    
    def get_bounds(self) -> tuple:
        """四角形の境界を返す"""
        min_x = min(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_x = max(p.x() for p in self.points)
        max_y = max(p.y() for p in self.points)
        return (min_x, min_y, max_x, max_y)
    
    def contains_point(self, point: QPointF) -> bool:
        """点が四角形内にあるかチェック"""
        return self.get_polygon().containsPoint(point, Qt.OddEvenFill)
    
    def get_sides(self) -> list:
        """四角形の辺を表す(始点, 終点)のリストを返す"""
        return [
            (self.points[0], self.points[1]),  # 下辺
            (self.points[1], self.points[2]),  # 右辺
            (self.points[2], self.points[3]),  # 上辺
            (self.points[3], self.points[0])   # 左辺
        ]
    
    def get_side_line(self, side_index: int) -> tuple:
        """指定された辺の両端点を返す"""
        sides = self.get_sides()
        if 0 <= side_index < len(sides):
            p1, p2 = sides[side_index]
            logger.debug(f"Rectangle {self.number}: 辺{side_index}の両端点: {p1} → {p2}")
            return p1, p2
        else:
            logger.warning(f"Rectangle {self.number}: 無効な辺インデックス {side_index}")
            return None
    
    def get_side_length(self, side_index: int) -> float:
        """指定された辺の長さを返す"""
        if side_index in (0, 2):  # 下辺と上辺
            return self.width
        elif side_index in (1, 3):  # 右辺と左辺
            return self.height
        else:
            logger.warning(f"Rectangle {self.number}: 無効な辺インデックス {side_index}")
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
            logger.warning(f"Rectangle {self.number}: 無効な辺インデックス {side_index}")
            return QPointF(0, 0)
    
    def update_with_new_properties(self, **properties) -> bool:
        """四角形のプロパティを更新（汎用メソッド）"""
        updated = False
        
        # 幅を更新
        width = properties.get('width', None)
        if width is not None:
            if width <= 0:
                logger.warning(f"Rectangle {self.number}: 無効な幅 {width}")
                return False
            self.width = float(width)
            updated = True
        
        # 高さを更新
        height = properties.get('height', None)
        if height is not None:
            if height <= 0:
                logger.warning(f"Rectangle {self.number}: 無効な高さ {height}")
                return False
            self.height = float(height)
            updated = True
        
        # 位置を更新
        position = properties.get('position', None)
        if position:
            self.position = QPointF(position)
            updated = True
        
        # 角度を更新
        angle_deg = properties.get('angle_deg', None)
        if angle_deg is not None:
            self.angle_deg = float(angle_deg)
            updated = True
        
        # 更新があった場合は座標を再計算
        if updated:
            self._create_triangles()  # 内部三角形を再作成
            self.calculate_points()
        
        return True
    
    def update_with_new_lengths(self, new_lengths) -> bool:
        """四角形の辺の長さを更新する（互換性メソッド）"""
        # 四角形では使用しないが、インターフェース互換性のために提供
        logger.warning("Rectangle.update_with_new_lengths: このメソッドは四角形では適切ではありません。update_with_new_properties(width=..., height=...)を使用してください。")
        return False
    
    def get_connection_point_for_side(self, side_index: int) -> QPointF:
        """指定された辺の接続点を返す（内部メソッド）"""
        return self.get_side_midpoint(side_index)
    
    def get_connection_point_by_side(self, side_index: int) -> QPointF:
        """指定された接続辺の次の図形の基準点を返す（互換性メソッド）"""
        return self.get_connection_point_for_side(side_index)
    
    def get_connection_angle_for_side(self, side_index: int) -> float:
        """指定された辺に接続する図形の回転角度を返す（内部メソッド）"""
        if 0 <= side_index < 4:
            # 辺の両端点を取得
            sides = self.get_sides()
            p1, p2 = sides[side_index]
            
            # 辺の角度を計算
            angle_rad = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            angle_deg = math.degrees(angle_rad)
            
            # 辺に垂直な角度を返す（辺の向きに90度加える）
            connection_angle = angle_deg + 90
            return connection_angle
        else:
            logger.warning(f"Rectangle {self.number}: 無効な辺インデックス {side_index}")
            return self.angle_deg
    
    def get_angle_by_side(self, side_index: int) -> float:
        """指定された辺に接続する次の図形の回転角度を返す（互換性メソッド）"""
        return self.get_connection_angle_for_side(side_index)
    
    def get_detailed_info(self) -> str:
        """四角形の詳細情報を文字列として返す"""
        base_info = super().get_detailed_info()
        return f"{base_info}, 幅={self.width:.1f}, 高さ={self.height:.1f}"
    
    def get_triangles(self) -> list:
        """内部三角形を取得"""
        return self.triangles 