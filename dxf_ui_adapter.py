#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF処理の純粋関数とUIの橋渡しをするアダプターモジュール。
データ計算とUI描画を分離し、テスト可能な構造を提供します。
"""

from typing import List, Tuple, Dict, Any, Optional
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath, QTransform
from PySide6.QtCore import QPointF, QRectF, QLineF, Qt

# 純粋関数モジュールをインポート
import pure_dxf_functions as pdf

class DXFSceneAdapter:
    """
    純粋なデータ構造からグラフィックスシーンへの変換を行うアダプタークラス
    """
    
    def __init__(self, scene: QGraphicsScene):
        """
        アダプタークラスの初期化
        
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
    
    def draw_line(self, line_data: pdf.LineData) -> QGraphicsItem:
        """
        LineDataを基にシーンに線を描画
        
        Args:
            line_data: 線の描画データ
            
        Returns:
            QGraphicsItem: 作成された線オブジェクト
        """
        pen = QPen(self.rgb_to_qcolor(line_data.color))
        pen.setWidthF(line_data.width)
        
        # Y座標を反転して描画（DXFは下が正、Qtは下が負）
        line = self.scene.addLine(
            QLineF(
                QPointF(line_data.start_x, -line_data.start_y),
                QPointF(line_data.end_x, -line_data.end_y)
            ),
            pen
        )
        line.setFlag(QGraphicsItem.ItemIsSelectable)
        return line
    
    def draw_circle(self, circle_data: pdf.CircleData) -> QGraphicsItem:
        """
        CircleDataを基にシーンに円を描画
        
        Args:
            circle_data: 円の描画データ
            
        Returns:
            QGraphicsItem: 作成された円オブジェクト
        """
        pen = QPen(self.rgb_to_qcolor(circle_data.color))
        pen.setWidthF(circle_data.width)
        
        # 円の左上座標を計算（中心から半径を引く）
        x = circle_data.center_x - circle_data.radius
        y = -circle_data.center_y - circle_data.radius
        
        circle = self.scene.addEllipse(
            QRectF(x, y, circle_data.radius * 2, circle_data.radius * 2),
            pen
        )
        circle.setFlag(QGraphicsItem.ItemIsSelectable)
        return circle
    
    def draw_arc(self, arc_data: pdf.ArcData) -> QGraphicsItem:
        """
        ArcDataを基にシーンに円弧を描画
        
        Args:
            arc_data: 円弧の描画データ
            
        Returns:
            QGraphicsItem: 作成された円弧オブジェクト
        """
        pen = QPen(self.rgb_to_qcolor(arc_data.color))
        pen.setWidthF(arc_data.width)
        
        # 角度の調整（DXFは反時計回り、Qtは時計回り）
        qt_start_angle = (90 - arc_data.start_angle) % 360
        qt_span_angle = ((arc_data.start_angle - arc_data.end_angle) % 360)
        
        # 円弧の左上座標
        x = arc_data.center_x - arc_data.radius
        y = -arc_data.center_y - arc_data.radius
        
        # 円弧のパスを作成
        arc_path = QPainterPath()
        rect = QRectF(x, y, arc_data.radius * 2, arc_data.radius * 2)
        arc_path.arcMoveTo(rect, qt_start_angle)
        arc_path.arcTo(rect, qt_start_angle, -qt_span_angle)
        
        arc = self.scene.addPath(arc_path, pen)
        arc.setFlag(QGraphicsItem.ItemIsSelectable)
        return arc
    
    def draw_polyline(self, polyline_data: pdf.PolylineData) -> QGraphicsItem:
        """
        PolylineDataを基にシーンにポリラインを描画
        
        Args:
            polyline_data: ポリラインの描画データ
            
        Returns:
            QGraphicsItem: 作成されたポリラインオブジェクト
        """
        pen = QPen(self.rgb_to_qcolor(polyline_data.color))
        pen.setWidthF(polyline_data.width)
        
        # ポリラインのパスを作成
        path = QPainterPath()
        
        # 座標変換（y座標の反転）
        transformed_points = [(p[0], -p[1]) for p in polyline_data.points]
        
        if transformed_points:
            path.moveTo(QPointF(transformed_points[0][0], transformed_points[0][1]))
            for point in transformed_points[1:]:
                path.lineTo(QPointF(point[0], point[1]))
        
        # 閉じたポリラインかどうか
        if polyline_data.is_closed:
            path.closeSubpath()
        
        polyline = self.scene.addPath(path, pen)
        polyline.setFlag(QGraphicsItem.ItemIsSelectable)
        return polyline
    
    def draw_text(self, text_data: pdf.TextData) -> QGraphicsItem:
        """
        TextDataを基にシーンにテキストを描画
        
        Args:
            text_data: テキストの描画データ
            
        Returns:
            QGraphicsItem: 作成されたテキストオブジェクト
        """
        # テキストアイテムの作成
        text_item = self.scene.addText(text_data.text, QFont("Arial", text_data.height))
        text_item.setDefaultTextColor(self.rgb_to_qcolor(text_data.color))
        
        # 位置の計算
        width = text_item.boundingRect().width()
        height = text_item.boundingRect().height()
        
        # 基本位置（デフォルトは左下揃え）
        base_x = text_data.pos_x
        base_y = -text_data.pos_y - height
        
        # 水平方向の配置
        if text_data.h_align == 0:  # 左揃え
            pass
        elif text_data.h_align == 2:  # 右揃え
            base_x -= width
        elif text_data.h_align == 4:  # 中央揃え
            base_x -= width/2
        
        # 垂直方向の配置
        if text_data.v_align == 0:  # ベースライン
            pass
        elif text_data.v_align == 1:  # 下揃え
            pass
        elif text_data.v_align == 2:  # 中央揃え
            base_y += height/2
        elif text_data.v_align == 3:  # 上揃え
            base_y += height
        
        text_item.setPos(base_x, base_y)
        
        # 回転の適用
        if text_data.rotation:
            # 回転の中心点を設定
            if text_data.h_align == 0:  # 左揃え
                text_item.setTransformOriginPoint(0, height)
            elif text_data.h_align == 2:  # 右揃え
                text_item.setTransformOriginPoint(width, height)
            elif text_data.h_align == 4:  # 中央揃え
                text_item.setTransformOriginPoint(width/2, height/2)
            else:
                text_item.setTransformOriginPoint(0, height)
                
            # Qtの回転は時計回り、DXFは反時計回りなので反転
            text_item.setRotation(-text_data.rotation)
        
        return text_item
    
    def draw_entity_result(self, result: pdf.Result) -> Optional[QGraphicsItem]:
        """
        エンティティ処理結果をシーンに描画
        
        Args:
            result: エンティティ処理結果
            
        Returns:
            Optional[QGraphicsItem]: 作成されたグラフィックスアイテム、失敗時はNone
        """
        if not result.success or result.data is None:
            return None
        
        data = result.data
        
        if isinstance(data, pdf.LineData):
            return self.draw_line(data)
        elif isinstance(data, pdf.CircleData):
            return self.draw_circle(data)
        elif isinstance(data, pdf.ArcData):
            return self.draw_arc(data)
        elif isinstance(data, pdf.PolylineData):
            return self.draw_polyline(data)
        elif isinstance(data, pdf.TextData):
            return self.draw_text(data)
        else:
            return None
    
    def set_scene_theme(self, theme_name: str) -> None:
        """
        シーンにテーマを適用
        
        Args:
            theme_name: テーマ名
        """
        bg_color, line_color = pdf.get_theme_colors(theme_name)
        self.scene.setBackgroundBrush(QBrush(QColor(*bg_color)))
    
    def apply_color_to_all_items(self, color: Tuple[int, int, int]) -> None:
        """
        シーン内のすべてのアイテムに色を適用
        
        Args:
            color: 適用する色 (R, G, B)
        """
        qcolor = self.rgb_to_qcolor(color)
        
        for item in self.scene.items():
            if isinstance(item, (QGraphicsItem)):
                # テキストの場合
                if hasattr(item, 'setDefaultTextColor'):
                    item.setDefaultTextColor(qcolor)
                # パスや線の場合
                elif hasattr(item, 'setPen'):
                    pen = item.pen()
                    pen.setColor(qcolor)
                    item.setPen(pen)

# UI側で利用するための関数
def process_dxf_entity_for_ui(scene: QGraphicsScene, entity, color: Tuple[int, int, int], default_width: float=1.0) -> Tuple[bool, str]:
    """
    DXFエンティティを処理してUIに描画する関数
    
    Args:
        scene: 描画先のグラフィックスシーン
        entity: DXFエンティティ
        color: 描画色 (R, G, B)
        default_width: デフォルト線幅
        
    Returns:
        Tuple[bool, str]: (成功したか, メッセージ)
    """
    # エンティティからデータを抽出
    result = pdf.process_entity_data(entity, color, default_width)
    
    # アダプターを使ってデータをシーンに描画
    adapter = DXFSceneAdapter(scene)
    graphics_item = adapter.draw_entity_result(result)
    
    # 結果を返す
    if result.success and graphics_item is not None:
        return True, f"エンティティ {entity.dxftype() if hasattr(entity, 'dxftype') else '不明'} を描画しました"
    else:
        return False, result.error or "エンティティの描画に失敗しました" 