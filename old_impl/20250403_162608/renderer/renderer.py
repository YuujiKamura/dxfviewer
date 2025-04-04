#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFレンダラーモジュール

DXFエンティティをQGraphicsSceneに描画する機能を提供します。
コアモジュールで定義されたDXFエンティティを受け取り、
PySide6のグラフィックアイテムに変換します。
"""

import logging
from typing import Any, Dict, List, Tuple, Optional

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont
from PySide6.QtCore import QPointF, QRectF, QLineF, Qt

# DXFエンティティのインポート
from core.dxf_entities import (
    DxfEntity, DxfLine, DxfCircle, DxfArc, DxfPolyline, DxfText
)

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
    
    def render_entities(self, entities: List[DxfEntity]) -> int:
        """
        エンティティリストを描画
        
        Args:
            entities: 描画するエンティティのリスト
            
        Returns:
            int: 正常に描画されたエンティティの数
        """
        success_count = 0
        
        for entity in entities:
            try:
                item = self.render_entity(entity)
                if item:
                    success_count += 1
            except Exception as e:
                logger.error(f"エンティティの描画中にエラー: {str(e)}")
        
        return success_count
    
    def render_entity(self, entity: DxfEntity) -> Optional[QGraphicsItem]:
        """
        単一のエンティティを描画
        
        Args:
            entity: 描画するエンティティ
            
        Returns:
            QGraphicsItem: 作成されたグラフィックアイテム
            サポートされていないエンティティタイプの場合はNone
        """
        # エンティティタイプに応じた描画メソッドの呼び出し
        if isinstance(entity, DxfLine):
            return self.render_line(entity)
        elif isinstance(entity, DxfCircle):
            return self.render_circle(entity)
        elif isinstance(entity, DxfArc):
            return self.render_arc(entity)
        elif isinstance(entity, DxfPolyline):
            return self.render_polyline(entity)
        elif isinstance(entity, DxfText):
            return self.render_text(entity)
        else:
            logger.warning(f"サポートされていないエンティティタイプ: {type(entity)}")
            return None
    
    def rgb_to_qcolor(self, rgb: Tuple[int, int, int]) -> QColor:
        """
        RGB値からQColorオブジェクトに変換
        
        Args:
            rgb: (R, G, B)の3要素タプル
            
        Returns:
            QColor: 変換されたQColorオブジェクト
        """
        return QColor(rgb[0], rgb[1], rgb[2])
    
    def render_line(self, line: DxfLine) -> QGraphicsItem:
        """線の描画"""
        pen = QPen(self.rgb_to_qcolor(line.color))
        pen.setWidthF(line.width)
        
        # Y座標を反転して描画（DXFは下が正、Qtは下が負）
        item = self.scene.addLine(
            QLineF(
                QPointF(line.start_x, -line.start_y),
                QPointF(line.end_x, -line.end_y)
            ),
            pen
        )
        item.setFlag(QGraphicsItem.ItemIsSelectable)
        return item
    
    def render_circle(self, circle: DxfCircle) -> QGraphicsItem:
        """円の描画"""
        pen = QPen(self.rgb_to_qcolor(circle.color))
        pen.setWidthF(circle.width)
        
        # 円の左上座標を計算（中心から半径を引く）
        x = circle.center_x - circle.radius
        y = -circle.center_y - circle.radius
        
        item = self.scene.addEllipse(
            QRectF(x, y, circle.radius * 2, circle.radius * 2),
            pen
        )
        item.setFlag(QGraphicsItem.ItemIsSelectable)
        return item
    
    def render_arc(self, arc: DxfArc) -> QGraphicsItem:
        """円弧の描画"""
        pen = QPen(self.rgb_to_qcolor(arc.color))
        pen.setWidthF(arc.width)
        
        # 角度の調整（DXFは反時計回り、Qtは時計回り）
        qt_start_angle = (90 - arc.start_angle) % 360
        qt_span_angle = ((arc.start_angle - arc.end_angle) % 360)
        
        # 円弧の左上座標
        x = arc.center_x - arc.radius
        y = -arc.center_y - arc.radius
        
        # 円弧のパスを作成
        arc_path = QPainterPath()
        rect = QRectF(x, y, arc.radius * 2, arc.radius * 2)
        arc_path.arcMoveTo(rect, qt_start_angle)
        arc_path.arcTo(rect, qt_start_angle, -qt_span_angle)
        
        item = self.scene.addPath(arc_path, pen)
        item.setFlag(QGraphicsItem.ItemIsSelectable)
        return item
    
    def render_polyline(self, polyline: DxfPolyline) -> QGraphicsItem:
        """ポリラインの描画"""
        pen = QPen(self.rgb_to_qcolor(polyline.color))
        pen.setWidthF(polyline.width)
        
        # ポリラインのパスを作成
        path = QPainterPath()
        
        # Y座標を反転
        transformed_points = [(p[0], -p[1]) for p in polyline.points]
        
        if transformed_points:
            path.moveTo(QPointF(transformed_points[0][0], transformed_points[0][1]))
            for point in transformed_points[1:]:
                path.lineTo(QPointF(point[0], point[1]))
        
        # 閉じたポリラインかどうか
        if polyline.is_closed:
            path.closeSubpath()
        
        item = self.scene.addPath(path, pen)
        item.setFlag(QGraphicsItem.ItemIsSelectable)
        return item
    
    def render_text(self, text: DxfText) -> QGraphicsItem:
        """テキストの描画"""
        # テキストアイテムの作成
        text_item = self.scene.addText(text.text, QFont("Arial", text.height))
        text_item.setDefaultTextColor(self.rgb_to_qcolor(text.color))
        
        # 位置の計算
        width = text_item.boundingRect().width()
        height = text_item.boundingRect().height()
        
        # 基本位置（デフォルトは左下揃え）
        base_x = text.pos_x
        base_y = -text.pos_y - height
        
        # 水平方向の配置
        if text.h_align == 0:  # 左揃え
            pass
        elif text.h_align == 2:  # 右揃え
            base_x -= width
        elif text.h_align == 4 or text.h_align == 1:  # 中央揃え
            base_x -= width/2
        
        # 垂直方向の配置
        if text.v_align == 0:  # ベースライン
            pass
        elif text.v_align == 1:  # 下揃え
            pass
        elif text.v_align == 2:  # 中央揃え
            base_y += height/2
        elif text.v_align == 3:  # 上揃え
            base_y += height
        
        # 位置の設定
        text_item.setPos(base_x, base_y)
        
        # 回転の適用
        if text.rotation != 0:
            # 回転の中心を設定
            text_item.setTransformOriginPoint(0, 0)
            text_item.setRotation(-text.rotation)  # DXFとQtで回転方向が逆
        
        text_item.setFlag(QGraphicsItem.ItemIsSelectable)
        return text_item 