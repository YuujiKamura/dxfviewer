#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RectangleShape - 四角形クラス

BaseShapeを継承し、内部的に2つの三角形で構成された四角形を提供します。
幅員1、延長、幅員2、センター位置プロパティにより形状を定義します。
"""

import math
import logging
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPolygonF
from enum import Enum

from ..base.base_shape import BaseShape
from .triangle_shape import TriangleData

# ロガー設定
logger = logging.getLogger(__name__)

class CenterPosition(Enum):
    """センター位置を表す列挙型"""
    LEFT = "左"
    CENTER = "中"
    RIGHT = "右"

class RectangleShape(BaseShape):
    """四角形を表すクラス（内部的に2つの三角形で構成）"""
    
    def __init__(self, width1=0.0, length=0.0, width2=None, center_position=CenterPosition.CENTER, p_ca=QPointF(0, 0), angle_deg=0.0, number=1):
        """四角形の初期化
        
        Args:
            width1 (float): 幅員1
            length (float): 延長
            width2 (float, optional): 幅員2（None指定時はwidth1と同値）
            center_position (CenterPosition): センター位置（左/中/右）
            p_ca (QPointF): 四角形の基準位置
            angle_deg (float): 四角形の回転角度（度数法）
            number (int): 四角形の識別番号
        """
        super().__init__(p_ca, angle_deg, number)
        self.name = f"Rectangle_{number}"
        
        # 四角形固有のプロパティ
        self.width1 = float(width1)
        self.length = float(length)
        self.width2 = float(width2) if width2 is not None else self.width1
        self.center_position = center_position
        self.points = [QPointF() for _ in range(4)]  # 4頂点
        
        # 内部三角形
        self.triangles = [None, None]
        
        # 頂点計算
        if width1 > 0 and length > 0 and self.width2 > 0:
            self._create_triangles()
            self.calculate_points()
    
    def _create_triangles(self):
        """内部三角形を生成"""
        # 基準位置の計算
        base_pos = self._calculate_base_position()
        
        # 角度をラジアンに変換
        angle_rad = math.radians(self.angle_deg)
        
        # 三角形1: 左下, 左上, 右上
        # 変形した台形の場合の三角形も計算する
        a_length = self.width1  # A辺 = 幅員1
        b_length = self.length  # B辺 = 延長
        
        # 三角形1の対角線長（ピタゴラスの定理）
        c_length = math.sqrt(a_length**2 + b_length**2)
        
        self.triangles[0] = TriangleData(
            a=a_length,
            b=b_length,
            c=c_length,
            p_ca=base_pos,
            angle_deg=self.angle_deg + 90,  # 90度回転（幅員方向が最初の辺）
            number=self.number * 100 + 1  # 内部番号
        )
        
        # 三角形2: 接続点, 右上, 右下
        # 三角形1のB辺（延長）に接続
        # C辺が幅員2に該当
        
        # 三角形1のB辺の終点座標（右上頂点）を計算
        height_dir_x = -math.sin(angle_rad)
        height_dir_y = math.cos(angle_rad)
        
        right_top_x = base_pos.x() + self.length * math.cos(angle_rad) + self.width1 * height_dir_x
        right_top_y = base_pos.y() + self.length * math.sin(angle_rad) + self.width1 * height_dir_y
        right_top = QPointF(right_top_x, right_top_y)
        
        # 三角形2の基準点（右上）
        tri2_base = right_top
        
        # 三角形2の各辺
        tri2_a = c_length  # A辺 = 三角形1の対角線長
        tri2_b = self.width2  # B辺 = 幅員2
        tri2_c = self.length  # C辺 = 延長
        
        # 対角線の角度を計算
        diag_angle = math.degrees(math.atan2(self.width1, self.length)) + self.angle_deg
        
        self.triangles[1] = TriangleData(
            a=tri2_a,
            b=tri2_b,
            c=tri2_c,
            p_ca=base_pos,  # 最初の三角形と同じ基準点
            angle_deg=diag_angle,  # 対角線方向
            number=self.number * 100 + 2  # 内部番号
        )
    
    def _calculate_base_position(self):
        """センター位置プロパティに基づいて基準位置を計算"""
        # 元の基準位置を保存
        original_pos = QPointF(self.position)
        
        # 角度をラジアンに変換
        angle_rad = math.radians(self.angle_deg)
        
        # 幅員方向の単位ベクトル（90度回転）
        width_dir_x = -math.sin(angle_rad)
        width_dir_y = math.cos(angle_rad)
        
        # センター位置に応じて基準位置を調整
        if self.center_position == CenterPosition.CENTER:
            # 中央配置: 元の位置から幅員1の半分を引く
            offset_x = -self.width1/2 * width_dir_x
            offset_y = -self.width1/2 * width_dir_y
            return QPointF(original_pos.x() + offset_x, original_pos.y() + offset_y)
            
        elif self.center_position == CenterPosition.RIGHT:
            # 右配置: 元の位置から幅員1を引く
            offset_x = -self.width1 * width_dir_x
            offset_y = -self.width1 * width_dir_y
            return QPointF(original_pos.x() + offset_x, original_pos.y() + offset_y)
            
        else:  # LEFT
            # 左配置: 元の位置をそのまま使用
            return original_pos
    
    def calculate_points(self):
        """四角形の頂点座標を計算"""
        # 内部三角形がない場合は作成
        if not self.triangles[0] or not self.triangles[1]:
            self._create_triangles()
        
        # 基準位置
        base_pos = self._calculate_base_position()
        
        # 角度をラジアンに変換
        angle_rad = math.radians(self.angle_deg)
        
        # 幅員方向の単位ベクトル（90度回転）
        width_dir_x = -math.sin(angle_rad)
        width_dir_y = math.cos(angle_rad)
        
        # 左下頂点
        self.points[0] = QPointF(base_pos)
        
        # 右下頂点
        self.points[1] = QPointF(
            base_pos.x() + self.length * math.cos(angle_rad),
            base_pos.y() + self.length * math.sin(angle_rad)
        )
        
        # 右上頂点
        self.points[2] = QPointF(
            self.points[1].x() + self.width2 * width_dir_x,
            self.points[1].y() + self.width2 * width_dir_y
        )
        
        # 左上頂点
        self.points[3] = QPointF(
            base_pos.x() + self.width1 * width_dir_x,
            base_pos.y() + self.width1 * width_dir_y
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
            (self.points[0], self.points[1]),  # 下辺（延長）
            (self.points[1], self.points[2]),  # 右辺（幅員2）
            (self.points[2], self.points[3]),  # 上辺（延長）
            (self.points[3], self.points[0])   # 左辺（幅員1）
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
        if side_index in (0, 2):  # 下辺と上辺（延長）
            return self.length
        elif side_index == 1:  # 右辺（幅員2）
            return self.width2
        elif side_index == 3:  # 左辺（幅員1）
            return self.width1
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
        
        # 幅員1を更新
        width1 = properties.get('width1', None)
        if width1 is not None:
            if width1 <= 0:
                logger.warning(f"Rectangle {self.number}: 無効な幅員1 {width1}")
                return False
            self.width1 = float(width1)
            updated = True
        
        # 延長を更新
        length = properties.get('length', None)
        if length is not None:
            if length <= 0:
                logger.warning(f"Rectangle {self.number}: 無効な延長 {length}")
                return False
            self.length = float(length)
            updated = True
        
        # 幅員2を更新
        width2 = properties.get('width2', None)
        if width2 is not None:
            if width2 <= 0:
                logger.warning(f"Rectangle {self.number}: 無効な幅員2 {width2}")
                return False
            self.width2 = float(width2)
            updated = True
        
        # センター位置を更新
        center_position = properties.get('center_position', None)
        if center_position is not None:
            if isinstance(center_position, CenterPosition):
                self.center_position = center_position
                updated = True
            else:
                logger.warning(f"Rectangle {self.number}: 無効なセンター位置 {center_position}")
                return False
        
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
        if len(new_lengths) < 3:
            logger.warning(f"Rectangle {self.number}: 無効な長さリスト（3要素必要）: {new_lengths}")
            return False
        
        return self.update_with_new_properties(
            width1=new_lengths[0],
            length=new_lengths[1],
            width2=new_lengths[2]
        )
    
    def is_connection_side(self, side_index: int) -> bool:
        """指定された辺が接続可能かどうかを返す"""
        # 幅員の辺（1: 右辺=幅員2, 3: 左辺=幅員1）のみ接続可能
        return side_index in (1, 3)
    
    def get_connection_point_for_side(self, side_index: int) -> QPointF:
        """指定された辺の接続点を返す（内部メソッド）"""
        if not self.is_connection_side(side_index):
            logger.warning(f"Rectangle {self.number}: 辺{side_index}は接続できません（幅員の辺のみ接続可能）")
            # デフォルトとしては中点を返す
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
        return f"{base_info}, 幅員1={self.width1:.1f}, 延長={self.length:.1f}, 幅員2={self.width2:.1f}, センター位置={self.center_position.value}"
    
    def get_triangles(self) -> list:
        """内部三角形を取得"""
        return self.triangles
    
    @property
    def width(self):
        """互換性のために残す: 幅（length）を返す"""
        return self.length
        
    @property
    def height(self):
        """互換性のために残す: 高さ（幅員1）を返す"""
        return self.width1 