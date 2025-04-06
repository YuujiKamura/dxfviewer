#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleGraphicsItem - 三角形グラフィックアイテム

三角形データをグラフィックスシーンに表示するためのアイテムクラス
"""

import math
import logging
from PySide6.QtWidgets import (
    QGraphicsPolygonItem, QGraphicsLineItem
)
from PySide6.QtGui import QPen, QColor
from PySide6.QtCore import Qt, QPointF, Signal, QObject

# ラベル関連ユーティリティをインポート
from .triangle_labels import (
    create_vertex_labels,
    create_edge_labels,
    create_dimension_labels,
    create_triangle_number_label,
    add_dimension_labels_to_scene
)

# ロガー設定
logger = logging.getLogger(__name__)

# TriangleItemSignalHelperクラス - TriangleItemからのシグナル中継用
class TriangleItemSignalHelper(QObject):
    """三角形アイテムからのシグナルを中継するヘルパークラス"""
    sideClicked = Signal(int, int)  # (三角形番号, 辺インデックス)

# TriangleItemクラス
class TriangleItem(QGraphicsPolygonItem):
    """三角形データを表示し、辺クリックを可能にするGraphicsItem"""
    
    def __init__(self, triangle_data, parent=None):
        super().__init__(triangle_data.get_polygon(), parent)
        self.triangle_data = triangle_data
        self.signalHelper = TriangleItemSignalHelper()
        self.setPen(QPen(triangle_data.color, 1, Qt.SolidLine))
        self.setAcceptHoverEvents(True)
        
        # 辺を表すラインアイテム
        self.side_lines = []
        # 寸法テキストとその背景を格納するリスト
        self.dimension_items = []
        
        # 辺と頂点の対応関係を明確にする
        # ユーザー指定の辺の定義：
        # 辺A (インデックス0): self.points[0](CA) → self.points[1](AB)
        # 辺B (インデックス1): self.points[1](AB) → self.points[2](BC)
        # 辺C (インデックス2): self.points[2](BC) → self.points[0](CA)
        self.edge_definition = [
            {"index": 0, "name": "A", "start_point": "CA", "end_point": "AB", "points_index": (0, 1)},
            {"index": 1, "name": "B", "start_point": "AB", "end_point": "BC", "points_index": (1, 2)},
            {"index": 2, "name": "C", "start_point": "BC", "end_point": "CA", "points_index": (2, 0)}
        ]
        
        # 頂点ラベルの作成
        create_vertex_labels(self, triangle_data)
        
        # 各辺の処理
        self._create_side_lines()
        
        # 辺ラベルの作成
        create_edge_labels(self, triangle_data, self.edge_definition)
        
        # 寸法ラベルの作成
        self.dimension_items = create_dimension_labels(self, triangle_data, self.edge_definition)
    
    def _create_side_lines(self):
        """辺のラインアイテムを作成"""
        for edge in self.edge_definition:
            edge_index = edge["index"]
            edge_name = edge["name"]
            
            # 直接頂点インデックスから両端点を取得
            start_idx, end_idx = edge["points_index"]
            p1 = self.triangle_data.points[start_idx]
            p2 = self.triangle_data.points[end_idx]
            
            logger.debug(f"三角形 {self.triangle_data.number} の辺 {edge_name}: "
                       f"{edge['start_point']}({p1.x():.1f}, {p1.y():.1f}) → "
                       f"{edge['end_point']}({p2.x():.1f}, {p2.y():.1f})")
            
            # 辺のライン作成
            line = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y(), self)
            line.setData(0, edge_index)  # 辺のインデックスを保存
            # 通常時は透過、選択・ホバー時に色を変える
            pen = QPen(Qt.transparent, 10)
            pen.setCapStyle(Qt.RoundCap)
            line.setPen(pen)
            line.setAcceptHoverEvents(True)
            line.setCursor(Qt.PointingHandCursor)
            self.side_lines.append(line)
            
            # 辺の方向を示す矢印を追加
            self._add_arrow_to_line(p1, p2)
    
    def _add_arrow_to_line(self, p1, p2):
        """辺の方向を示す矢印を追加"""
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = math.sqrt(dx * dx + dy * dy)
        
        if length > 0:
            # 線の60%位置に矢印を作成
            arrow_pos = 0.6
            arrow_x = p1.x() + dx * arrow_pos
            arrow_y = p1.y() + dy * arrow_pos
            
            # 単位ベクトル
            unit_dx = dx / length
            unit_dy = dy / length
            
            # 矢印の大きさ
            arrow_size = 3  # 小さめに設定
            
            # 矢印の先端
            arrow_tip_x = arrow_x + unit_dx * arrow_size
            arrow_tip_y = arrow_y + unit_dy * arrow_size
            
            # 矢印の後ろの点（-30度）
            angle1 = math.radians(-30)
            arrow_back1_x = arrow_tip_x - arrow_size * (unit_dx * math.cos(angle1) - unit_dy * math.sin(angle1))
            arrow_back1_y = arrow_tip_y - arrow_size * (unit_dx * math.sin(angle1) + unit_dy * math.cos(angle1))
            
            # 矢印の後ろの点（+30度）
            angle2 = math.radians(30)
            arrow_back2_x = arrow_tip_x - arrow_size * (unit_dx * math.cos(angle2) - unit_dy * math.sin(angle2))
            arrow_back2_y = arrow_tip_y - arrow_size * (unit_dx * math.sin(angle2) + unit_dy * math.cos(angle2))
            
            # 矢印を描画
            arrow_color = QColor(0, 0, 0, 150)  # 半透明の黒
            
            # 矢印の線
            arrow_line1 = QGraphicsLineItem(arrow_tip_x, arrow_tip_y, arrow_back1_x, arrow_back1_y, self)
            arrow_line1.setPen(QPen(arrow_color, 1.5))
            
            arrow_line2 = QGraphicsLineItem(arrow_tip_x, arrow_tip_y, arrow_back2_x, arrow_back2_y, self)
            arrow_line2.setPen(QPen(arrow_color, 1.5))
    
    def mousePressEvent(self, event):
        """三角形内のクリックイベント処理"""
        # クリックされた辺を検出
        for line in self.side_lines:
            if line.isUnderMouse():
                side_index = line.data(0)
                self.signalHelper.sideClicked.emit(self.triangle_data.number, side_index)
                break
        
        # 選択されていない場合は親クラスの処理を呼ぶ
        super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        """ホバー進入イベント処理"""
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """ホバー退出イベント処理"""
        # ホバー解除時に戻す
        for line in self.side_lines:
            pen = line.pen()
            # 選択されている辺は色を変えない
            if self.signalHelper.property("selected_side") == line.data(0):
                pen.setColor(QColor(255, 255, 0, 150))  # 黄色
            else:
                pen.setColor(Qt.transparent)
            line.setPen(pen)
        self.update()
        super().hoverLeaveEvent(event)
    
    def highlight_selected_side(self, side_index):
        """選択された辺をハイライト"""
        # 以前に選択された辺の色をリセット
        prev_selected = self.signalHelper.property("selected_side")
        if prev_selected is not None:
            for line in self.side_lines:
                if line.data(0) == prev_selected:
                    pen = line.pen()
                    pen.setColor(Qt.transparent)
                    line.setPen(pen)
                    break
        
        # 新しく選択された辺をハイライト
        self.signalHelper.setProperty("selected_side", side_index)
        for line in self.side_lines:
            if line.data(0) == side_index:
                pen = line.pen()
                pen.setColor(QColor(255, 255, 0, 150))  # 黄色
                line.setPen(pen)
                break
        
        self.update()

def add_triangle_item_to_scene(scene, triangle_data, dimension_font_size=6):
    """三角形アイテムをシーンに追加する"""
    # シーンアイテムの作成
    triangle_item = TriangleItem(triangle_data)
    scene.addItem(triangle_item)
    
    # 寸法テキストとその背景をシーンに追加
    add_dimension_labels_to_scene(scene, triangle_item.dimension_items, dimension_font_size)
    
    # 三角形番号ラベルの追加
    create_triangle_number_label(scene, triangle_data)
    
    return triangle_item 