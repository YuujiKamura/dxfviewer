#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ShapeAdapter - 形状アダプタークラス

既存のTriangleDataと新しいTriangleShapeの間の互換性を提供するアダプター
"""

import logging
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from ..geometry.triangle_shape import TriangleData

# ロガー設定
logger = logging.getLogger(__name__)

class TriangleAdapter:
    """既存のTriangleDataと互換性を持つTriangleShapeアダプター"""
    
    @staticmethod
    def triangle_data_to_shape(triangle_data):
        """TriangleDataインスタンスからTriangleShapeインスタンスを作成"""
        if not triangle_data:
            return None
        
        # 新しいTriangleShapeを作成
        shape = TriangleData(
            a=triangle_data.lengths[0],
            b=triangle_data.lengths[1],
            c=triangle_data.lengths[2],
            p_ca=QPointF(triangle_data.points[0]),
            angle_deg=triangle_data.angle_deg,
            number=triangle_data.number
        )
        
        # 色を設定
        shape.color = QColor(triangle_data.color)
        
        # 親子関係を設定
        if triangle_data.parent:
            shape.parent = triangle_data.parent
            shape.connection_point = triangle_data.connection_side
        
        return shape
    
    @staticmethod
    def triangle_shape_to_data(triangle_shape, triangle_data_class):
        """TriangleShapeインスタンスからTriangleDataインスタンスを作成
        
        Args:
            triangle_shape: 変換元のTriangleShapeインスタンス
            triangle_data_class: 使用するTriangleDataクラス
        """
        if not triangle_shape:
            return None
        
        # 新しいTriangleDataを作成
        data = triangle_data_class(
            a=triangle_shape.lengths[0],
            b=triangle_shape.lengths[1],
            c=triangle_shape.lengths[2],
            p_ca=QPointF(triangle_shape.points[0]),
            angle_deg=triangle_shape.angle_deg,
            number=triangle_shape.number
        )
        
        # 色を設定
        data.color = QColor(triangle_shape.color)
        
        # 親子関係を設定
        if triangle_shape.parent:
            data.parent = triangle_shape.parent
            data.connection_side = triangle_shape.connection_point
        
        return data
    
    @staticmethod
    def update_triangle_data_from_shape(triangle_data, triangle_shape):
        """既存のTriangleDataをTriangleShapeの内容で更新"""
        if not triangle_data or not triangle_shape:
            return False
        
        # 辺の長さを更新
        triangle_data.lengths = triangle_shape.lengths.copy()
        
        # 位置と角度を更新
        triangle_data.points[0] = QPointF(triangle_shape.points[0])
        triangle_data.angle_deg = triangle_shape.angle_deg
        
        # 座標を再計算
        triangle_data.calculate_points()
        
        # 色を更新
        triangle_data.color = QColor(triangle_shape.color)
        
        return True
    
    @staticmethod
    def update_triangle_shape_from_data(triangle_shape, triangle_data):
        """既存のTriangleShapeをTriangleDataの内容で更新"""
        if not triangle_shape or not triangle_data:
            return False
        
        # プロパティを更新
        properties = {
            'lengths': triangle_data.lengths.copy(),
            'position': QPointF(triangle_data.points[0]),
            'angle_deg': triangle_data.angle_deg
        }
        
        # 更新の実行
        result = triangle_shape.update_with_new_properties(**properties)
        
        # 色を更新
        if result:
            triangle_shape.color = QColor(triangle_data.color)
        
        return result


class ShapeAdapterFactory:
    """形状アダプターを生成するファクトリークラス"""
    
    @staticmethod
    def create_adapter_for_triangle(triangle_data_class):
        """指定されたTriangleDataクラスに対応するアダプターを返す"""
        return TriangleAdapter 