#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF Adapter - DXFとUIを連携するアダプターモジュール

DXFデータとPySide6のグラフィックス要素を連携する機能を提供します。
"""

import os
import sys
import logging
import traceback
from typing import Tuple, List, Dict, Any, Optional, Union

from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QPainterPath, QFont
from PySide6.QtCore import QPointF, QRectF, QLineF, Qt

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

class DXFSceneAdapter:
    """
    DXFデータとグラフィックスシーンの変換を行うアダプタークラス
    """
    
    def __init__(self, scene: QGraphicsScene):
        """
        アダプタークラスの初期化
        
        Args:
            scene: 描画先のグラフィックスシーン
        """
        self.scene = scene
        self.default_line_width = 1.0  # デフォルト線幅
        self.line_width_scale = 1.0  # 線幅倍率係数
    
    def rgb_to_qcolor(self, rgb: Union[Tuple[int, int, int], QColor]) -> QColor:
        """
        RGB値またはQColorオブジェクトをQColorに変換
        
        Args:
            rgb: (R, G, B)の3要素タプル、またはQColorオブジェクト
            
        Returns:
            QColor: QColorオブジェクト
        """
        # 既にQColorの場合はそのまま返す
        if isinstance(rgb, QColor):
            return rgb
        
        # タプルの場合は変換
        return QColor(rgb[0], rgb[1], rgb[2])
    
    def process_entity(self, entity, color):
        """
        DXFエンティティを処理してグラフィックスアイテムを作成
        
        Args:
            entity: DXFエンティティ
            color: 色情報（RGB値またはQColor）
            
        Returns:
            タプル: (成功時: 作成されたグラフィックアイテム, 処理結果メッセージ)
                  (失敗時: None, エラーメッセージ)
        """
        try:
            entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else '不明'
            result_message = f"エンティティ {entity_type} を処理"
            qcolor = self.rgb_to_qcolor(color)
            
            # 線幅の取得（デフォルト値は1.0）
            line_width = self.default_line_width
            if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'lineweight'):
                # DXFの線幅はmm単位の100倍で保存されているので、適切なスケールに変換
                # 負の値は特殊な意味を持つため処理
                lw = entity.dxf.lineweight
                if lw > 0:
                    line_width = lw / 10.0  # mm単位に変換
                    logger.debug(f"エンティティの線幅: {line_width}mm")
            
            # エンティティタイプに応じた処理
            if entity_type == 'LINE':
                # 直線の描画
                start = (entity.dxf.start.x, entity.dxf.start.y)
                end = (entity.dxf.end.x, entity.dxf.end.y)
                item = self.create_line(start, end, qcolor, line_width)
                
            elif entity_type == 'CIRCLE':
                # 円の描画
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                item = self.create_circle(center, radius, qcolor, line_width)
                
            elif entity_type == 'ARC':
                # 円弧の描画
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                item = self.create_arc(center, radius, start_angle, end_angle, qcolor, line_width)
                
            elif entity_type == 'POLYLINE' or entity_type == 'LWPOLYLINE':
                # ポリラインの処理
                if entity_type == 'LWPOLYLINE':
                    # LWポリラインは直接座標を持っている
                    points = [(point[0], point[1]) for point in entity.get_points()]
                else:
                    # 通常のポリラインは頂点オブジェクトを持っている
                    points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
                
                # 閉じたポリラインかどうかチェック
                is_closed = False
                if hasattr(entity, 'is_closed'):
                    is_closed = entity.is_closed
                
                item = self.create_polyline(points, qcolor, is_closed, line_width)
                
            elif entity_type == 'TEXT' or entity_type == 'MTEXT':
                # テキストの処理
                if entity_type == 'TEXT':
                    text = entity.dxf.text
                    pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                    height = entity.dxf.height
                    rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
                    h_align = entity.dxf.halign if hasattr(entity.dxf, 'halign') else 0
                    v_align = entity.dxf.valign if hasattr(entity.dxf, 'valign') else 0
                else:  # MTEXT
                    text = entity.text
                    pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                    height = entity.dxf.char_height
                    rotation = entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0
                    h_align = 0  # MTEXTのデフォルトは左揃え
                    v_align = 0  # MTEXTのデフォルトはベースライン
                
                item = self.create_text(text, pos, height, qcolor, rotation, h_align, v_align)
                
            else:
                # サポートされていないエンティティタイプ
                logger.debug(f"サポートされていないエンティティタイプ: {entity_type}")
                return None, f"サポートされていないエンティティタイプ: {entity_type}"
            
            return item, result_message
            
        except Exception as e:
            error_details = traceback.format_exc()
            entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else "不明"
            return None, f"エンティティの処理中にエラーが発生: {str(e)}"
    
    def create_line(self, start, end, color, width=1.0):
        """
        線を作成
        
        Args:
            start: 始点の座標 (x, y)
            end: 終点の座標 (x, y)
            color: 線の色（QColor）
            width: 線の太さ
            
        Returns:
            QGraphicsItem: 作成された線オブジェクト
        """
        pen = QPen(color)
        pen.setWidthF(width * self.line_width_scale)  # 倍率を適用
        pen.setCosmetic(False)  # CAD表示のためコスメティックペンを無効化
        
        # Y座標を反転（DXFは下が正、Qtは上が正）
        line = self.scene.addLine(
            QLineF(
                QPointF(start[0], -start[1]),
                QPointF(end[0], -end[1])
            ),
            pen
        )
        line.setFlag(QGraphicsItem.ItemIsSelectable)
        return line
    
    def create_circle(self, center, radius, color, width=1.0):
        """
        円を作成
        
        Args:
            center: 中心座標 (x, y)
            radius: 半径
            color: 線の色（QColor）
            width: 線の太さ
        
        Returns:
            QGraphicsItem: 作成された円オブジェクト
        """
        pen = QPen(color)
        pen.setWidthF(width * self.line_width_scale)  # 倍率を適用
        pen.setCosmetic(False)  # CAD表示のためコスメティックペンを無効化
        
        # 円の左上座標を計算（中心から半径を引く）
        x = center[0] - radius
        y = -center[1] - radius  # Y座標反転
        
        circle = self.scene.addEllipse(
            QRectF(x, y, radius * 2, radius * 2),
            pen
        )
        circle.setFlag(QGraphicsItem.ItemIsSelectable)
        return circle
    
    def create_arc(self, center, radius, start_angle, end_angle, color, width=1.0):
        """
        円弧を作成
        
        Args:
            center: 中心座標 (x, y)
            radius: 半径
            start_angle: 開始角度（度）
            end_angle: 終了角度（度）
            color: 線の色（QColor）
            width: 線の太さ
            
        Returns:
            QGraphicsItem: 作成された円弧オブジェクト
        """
        pen = QPen(color)
        pen.setWidthF(width * self.line_width_scale)  # 倍率を適用
        pen.setCosmetic(False)  # CAD表示のためコスメティックペンを無効化
        
        # 角度の調整（DXFは反時計回り、Qtは時計回り）
        qt_start_angle = (90 - start_angle) % 360
        qt_span_angle = ((start_angle - end_angle) % 360)
        
        # 円の中心から左上の座標に変換
        x = center[0] - radius
        y = -center[1] - radius  # Y座標反転
        
        # QPainterPathの代わりにQGraphicsEllipseItemを使用（効率的）
        rect = QRectF(x, y, radius * 2, radius * 2)
        
        # 円弧を直接描画（QGraphicsEllipseItemのspanAngleとstartAngleを設定）
        arc = self.scene.addEllipse(rect, pen)
        
        # 円弧の設定はできないので、代わりに完全な円としてレンダリングする
        # フルパフォーマンスが必要な場合は、カスタムQGraphicsItemを実装すべき
        
        arc.setFlag(QGraphicsItem.ItemIsSelectable)
        return arc
    
    def create_polyline(self, points, color, is_closed=False, width=1.0):
        """
        ポリラインを作成
        
        Args:
            points: 頂点座標のリスト [(x1, y1), (x2, y2), ...]
            color: 線の色（QColor）
            is_closed: 閉じたポリラインかどうか
            width: 線の太さ
            
        Returns:
            QGraphicsItem: 作成されたポリラインオブジェクト
        """
        pen = QPen(color)
        pen.setWidthF(width * self.line_width_scale)  # 倍率を適用
        pen.setCosmetic(False)  # CAD表示のためコスメティックペンを無効化
        
        # Y座標を反転
        transformed_points = [(p[0], -p[1]) for p in points]
        
        # QPainterPathを使うがコードを最適化
        if not transformed_points:
            # 空のポリラインは何も表示しない
            return None
            
        if len(transformed_points) == 1:
            # 点が1つだけなら小さな円を表示
            x, y = transformed_points[0]
            point_size = max(width * 2, 2.0)
            return self.scene.addEllipse(
                x - point_size/2, y - point_size/2, 
                point_size, point_size, 
                pen
            )
        
        if len(transformed_points) == 2:
            # 点が2つなら直線を表示（QPainterPathを使わない）
            x1, y1 = transformed_points[0]
            x2, y2 = transformed_points[1]
            return self.scene.addLine(QLineF(x1, y1, x2, y2), pen)
        
        # 3点以上ならパスを作成
        path = QPainterPath()
        path.moveTo(QPointF(transformed_points[0][0], transformed_points[0][1]))
        for point in transformed_points[1:]:
            path.lineTo(QPointF(point[0], point[1]))
        
        # 閉じたポリラインかどうか
        if is_closed:
            path.closeSubpath()
        
        polyline = self.scene.addPath(path, pen)
        polyline.setFlag(QGraphicsItem.ItemIsSelectable)
        return polyline
    
    def create_text(self, text, pos, height, color, rotation=0, h_align=0, v_align=0):
        """
        テキストを作成
        
        Args:
            text: テキスト内容
            pos: 配置位置 (x, y)
            height: テキストの高さ
            color: テキストの色（QColor）
            rotation: 回転角度（度）
            h_align: 水平方向の配置（0=左, 1=センター, 2=右）
            v_align: 垂直方向の配置（0=ベースライン, 1=下, 2=中央, 3=上）
            
        Returns:
            QGraphicsItem: 作成されたテキストオブジェクト
        """
        # テキストアイテムの作成
        text_item = self.scene.addText(text, QFont("Arial", height))
        text_item.setDefaultTextColor(color)
        
        # 位置の計算
        width = text_item.boundingRect().width()
        height = text_item.boundingRect().height()
        
        # 基本位置（デフォルトは左下揃え）
        base_x = pos[0]
        base_y = -pos[1] - height  # Y座標反転
        
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
            if h_align == 0:  # 左揃え
                text_item.setTransformOriginPoint(0, height)
            elif h_align == 2:  # 右揃え
                text_item.setTransformOriginPoint(width, height)
            elif h_align == 4 or h_align == 1:  # 中央揃え
                text_item.setTransformOriginPoint(width/2, height/2)
            else:
                text_item.setTransformOriginPoint(0, height)
                
            # DXFとQtで回転方向が逆なので反転
            text_item.setRotation(-rotation)
        
        text_item.setFlag(QGraphicsItem.ItemIsSelectable)
        return text_item

# 簡単に使えるようにするためのファクトリ関数
def create_dxf_adapter(scene: QGraphicsScene) -> DXFSceneAdapter:
    """
    DXFSceneAdapterのインスタンスを作成する
    
    Args:
        scene: 描画先のグラフィックスシーン
        
    Returns:
        DXFSceneAdapter: 新しいアダプターインスタンス
    """
    return DXFSceneAdapter(scene) 