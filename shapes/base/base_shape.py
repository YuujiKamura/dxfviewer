#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BaseShape - 図形の基底クラス

すべての図形クラスの基底となるクラスを定義します。
"""

import math
import logging
from abc import ABC, abstractmethod
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPolygonF

# ロガー設定
logger = logging.getLogger(__name__)

class BaseShape(ABC):
    """図形の基底クラス"""
    
    def __init__(self, position=QPointF(0, 0), angle_deg=0.0, number=1):
        """図形の基本初期化
        
        Args:
            position (QPointF): 図形の基準位置
            angle_deg (float): 図形の回転角度（度数法）
            number (int): 図形の識別番号
        """
        self.position = QPointF(position)  # 基準位置
        self.angle_deg = float(angle_deg)  # 回転角度
        self.number = int(number)          # 識別番号
        self.name = f"Shape_{number}"      # 図形名
        self.center_point = QPointF(position)  # 中心点（初期値は基準位置と同じ）
        self.points = []                  # 頂点リスト
        
        # 色属性
        self.color = QColor(0, 100, 200)  # デフォルト色
    
    @abstractmethod
    def calculate_points(self):
        """図形の頂点座標を計算する（抽象メソッド）"""
        pass
    
    @abstractmethod
    def get_polygon(self) -> QPolygonF:
        """描画用のQPolygonFを返す（抽象メソッド）"""
        pass
    
    @abstractmethod
    def get_bounds(self) -> tuple:
        """図形の境界を返す（抽象メソッド）"""
        pass
    
    @abstractmethod
    def contains_point(self, point: QPointF) -> bool:
        """点が図形内にあるかチェック（抽象メソッド）"""
        pass
    
    @abstractmethod
    def get_sides(self) -> list:
        """図形の辺を表すリストを返す（抽象メソッド）"""
        pass
    
    @abstractmethod
    def get_side_line(self, side_index: int) -> tuple:
        """指定された辺の両端点を返す（抽象メソッド）"""
        pass
    
    @abstractmethod
    def get_side_length(self, side_index: int) -> float:
        """指定された辺の長さを返す（抽象メソッド）"""
        pass
    
    @abstractmethod
    def get_side_midpoint(self, side_index: int) -> QPointF:
        """指定された辺の中点を返す（抽象メソッド）"""
        pass
    
    @abstractmethod
    def update_with_new_properties(self, **properties) -> bool:
        """図形のプロパティを更新する（抽象メソッド）"""
        pass
    
    def get_detailed_info(self) -> str:
        """図形の詳細情報を文字列として返す"""
        return f"{self.name}: 位置=({self.position.x():.1f}, {self.position.y():.1f}), 角度={self.angle_deg:.1f}度"
    
    def set_color(self, color: QColor) -> None:
        """図形の色を設定"""
        self.color = QColor(color)
    
    def get_color(self) -> QColor:
        """図形の色を取得"""
        return self.color 