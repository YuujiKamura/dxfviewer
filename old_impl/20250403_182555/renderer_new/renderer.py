#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFレンダラーモジュール

DXFエンティティをQGraphicsSceneに描画する機能を提供します。
"""

import logging
from typing import Any, Dict, List, Tuple, Optional

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont
from PySide6.QtCore import QPointF, QRectF, QLineF, Qt

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

class DxfRenderer:
    """DXFエンティティをQGraphicsSceneに描画するレンダラークラス"""
    
    def __init__(self, scene: QGraphicsScene):
        """
        レンダラーの初期化
        
        Args:
            scene: 描画先のグラフィックスシーン
        """
        self.scene = scene
    
    def rgb_to_qcolor(self, rgb: Tuple[int, int, int]) -> QColor:
        """
        RGB値からQColorオブジェクトに変換
        
        Args:
            rgb: (R, G, B)の3要素タプル
            
        Returns:
            QColor: 変換されたQColorオブジェクト
        """
        return QColor(rgb[0], rgb[1], rgb[2])
    
    def render_text(self, text_str: str, pos_x: float, pos_y: float, 
                    height: float = 12.0, color: Tuple[int, int, int] = (0, 0, 0),
                    h_align: int = 0, v_align: int = 0, rotation: float = 0.0) -> QGraphicsItem:
        """
        テキストの描画
        
        Args:
            text_str: 表示するテキスト
            pos_x: X座標位置
            pos_y: Y座標位置
            height: テキストの高さ
            color: 色（RGB）
            h_align: 水平方向の配置（0=左, 2=右, 4=中央）
            v_align: 垂直方向の配置（0=ベース, 1=下, 2=中央, 3=上）
            rotation: 回転角度（度数法）
            
        Returns:
            QGraphicsItem: 作成されたテキストアイテム
        """
        # テキストアイテムの作成
        text_item = self.scene.addText(text_str, QFont("Arial", height))
        text_item.setDefaultTextColor(self.rgb_to_qcolor(color))
        
        # 位置の計算
        width = text_item.boundingRect().width()
        height = text_item.boundingRect().height()
        
        # 基本位置（デフォルトは左下揃え）
        base_x = pos_x
        base_y = -pos_y - height
        
        # 水平方向の配置
        if h_align == 0:  # 左揃え
            pass
        elif h_align == 2:  # 右揃え
            base_x -= width
        elif h_align == 4 or h_align == 1:  # 中央揃え
            base_x -= width/2
        
        # 垂直方向の配置
        if v_align == 0:  # ベースライン
            pass
        elif v_align == 1:  # 下揃え
            pass
        elif v_align == 2:  # 中央揃え
            base_y += height/2
        elif v_align == 3:  # 上揃え
            base_y += height
        
        # 位置の設定
        text_item.setPos(base_x, base_y)
        
        # 回転の適用
        if rotation != 0:
            # 回転の中心を設定
            text_item.setTransformOriginPoint(0, 0)
            text_item.setRotation(-rotation)  # DXFとQtで回転方向が逆
        
        text_item.setFlag(QGraphicsItem.ItemIsSelectable)
        return text_item 