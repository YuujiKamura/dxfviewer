#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleItem - 三角形表示アイテム

三角形データをグラフィックスシーンに表示するためのアイテムクラス
"""

import math
import logging
from PySide6.QtWidgets import (
    QGraphicsPolygonItem, QGraphicsLineItem, QGraphicsTextItem,
    QGraphicsSimpleTextItem, QGraphicsRectItem, QGraphicsEllipseItem
)
from PySide6.QtGui import QPen, QColor, QBrush, QTransform
from PySide6.QtCore import Qt, QPointF, Signal, QObject

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
        edge_definition = [
            {"index": 0, "name": "A", "start_point": "CA", "end_point": "AB", "points_index": (0, 1)},
            {"index": 1, "name": "B", "start_point": "AB", "end_point": "BC", "points_index": (1, 2)},
            {"index": 2, "name": "C", "start_point": "BC", "end_point": "CA", "points_index": (2, 0)}
        ]
        
        # 頂点名と座標のマッピング
        vertex_mapping = [
            {"name": "CA", "index": 0, "point": self.triangle_data.points[0]},
            {"name": "AB", "index": 1, "point": self.triangle_data.points[1]},
            {"name": "BC", "index": 2, "point": self.triangle_data.points[2]}
        ]
        
        # 頂点位置のログ出力（デバッグ用）
        vertices = self.triangle_data.points
        logger.debug(f"三角形 {triangle_data.number} の頂点: CA={vertices[0]}, AB={vertices[1]}, BC={vertices[2]}")
        
        # 頂点ラベルを追加
        vertex_names = ["CA", "AB", "BC"]
        for i, name in enumerate(vertex_names):
            vertex = vertices[i]
            # 頂点ラベルを追加
            text_item = QGraphicsTextItem(name, self)
            text_item.setDefaultTextColor(QColor(0, 0, 255))  # 青色
            font = text_item.font()
            font.setBold(True)
            text_item.setFont(font)
            
            # テキストアイテムの位置を調整（頂点の少し横）
            # テキストの中心を頂点に合わせるよう調整
            text_rect = text_item.boundingRect()
            text_item.setPos(
                vertex.x() - text_rect.width() / 2,
                vertex.y() - text_rect.height() - 5  # 頂点の少し上に表示
            )
        
        # 各辺の処理
        for edge in edge_definition:
            edge_index = edge["index"]
            edge_name = edge["name"]
            
            # 直接頂点インデックスから両端点を取得
            start_idx, end_idx = edge["points_index"]
            p1 = self.triangle_data.points[start_idx]
            p2 = self.triangle_data.points[end_idx]
            
            logger.debug(f"三角形 {triangle_data.number} の辺 {edge_name}: "
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
            
            # 辺の方向を示す矢印を追加（線の中央付近）
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
            
            # 辺の名前ラベルを追加（辺の中央に表示）
            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2

            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.sqrt(dx * dx + dy * dy)

            # 辺名ラベルを追加
            label_item = QGraphicsTextItem(edge_name, self)
            label_item.setDefaultTextColor(QColor(255, 0, 0))  # 赤色
            font = label_item.font()
            font.setBold(True)
            font.setPointSize(12)
            label_item.setFont(font)
            
            # テキストアイテムの位置を調整
            text_rect = label_item.boundingRect()
            label_item.setPos(
                mid_x + text_rect.width() / 2,
                mid_y + text_rect.height() / 2
            )
            
            # 辺の寸法値を表示するテキスト
            edge_length = self.triangle_data.lengths[edge_index]
            
            # 辺の角度を計算
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            
            # SimpleTextItemを使用
            dimension_text = QGraphicsSimpleTextItem()
            # 長さを表示（辺の名前と長さを表示）
            dimension_text.setText(f"{edge_name}: {edge_length:.1f}")
            dimension_text.setBrush(QColor(0, 0, 0))  # テキスト色を黒に
            
            # フォントを調整（太字・サイズ）
            font = dimension_text.font()
            font.setPointSize(6)  # デフォルトサイズを6に変更
            font.setBold(True)
            dimension_text.setFont(font)
            
            # テキストアイテムのサイズを取得
            text_rect = dimension_text.boundingRect()
            
            # テキストの背景を作成
            bg_rect = QGraphicsRectItem(text_rect)
            bg_rect.setBrush(QColor(255, 255, 255, 180))  # 半透明の白
            bg_rect.setPen(QPen(Qt.NoPen))  # 枠線なし
            
            # アイテムの位置情報を保存
            dimension_info = {
                'text': dimension_text,
                'bg': bg_rect,
                'mid_x': mid_x,
                'mid_y': mid_y,
                'angle': angle_deg,
                'side_index': edge_index,
                'side_name': edge_name
            }
            self.dimension_items.append(dimension_info)
            
            # アイテムにデータを設定（クリック時の辺の特定用）
            dimension_text.setData(0, edge_index)  # 辺インデックスを保存
            dimension_text.setData(1, self.triangle_data.number)  # 三角形番号を保存
            bg_rect.setData(0, edge_index)  # 辺インデックスを保存
            bg_rect.setData(1, self.triangle_data.number)  # 三角形番号を保存
    
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
    for dim_info in triangle_item.dimension_items:
        text = dim_info['text']
        bg = dim_info['bg']
        mid_x = dim_info['mid_x']
        mid_y = dim_info['mid_y']
        angle = dim_info['angle']
        
        # 現在のフォントサイズで更新
        font = text.font()
        font.setPointSize(dimension_font_size)
        text.setFont(font)
        
        # テキストサイズ変更に伴い背景サイズも調整
        text_rect = text.boundingRect()
        bg.setRect(text_rect)
        
        # 描画原点を示す青いドット
        origin_dot = QGraphicsEllipseItem(-1, -1, 2, 2)
        origin_dot.setBrush(QColor(0, 0, 255))  # 青色
        origin_dot.setPen(QPen(Qt.NoPen))
        
        # ZValueを設定（背景が最背面、テキストが中間、青ドットが最前面）
        bg.setZValue(0)  # 最背面
        text.setZValue(1)  # 中間
        origin_dot.setZValue(2)  # 最前面
        
        # シーンに追加（背景を最初に追加して最背面に）
        scene.addItem(bg)
        scene.addItem(text)
        scene.addItem(origin_dot)
        
        # 辺上の変形行列を作成（テキスト位置の基準となる）
        edge_transform = QTransform()
        edge_transform.translate(mid_x, mid_y)
        
        # 辺の角度に合わせて回転
        if 90 <= angle <= 270:
            edge_transform.rotate(angle + 180)
        else:
            edge_transform.rotate(angle)
        
        # 青ドットは辺上に配置（オフセットなし）
        origin_dot.setTransform(edge_transform)
        
        # テキスト用の変形行列（辺から少し離す）
        text_transform = QTransform(edge_transform)
        text_transform.translate(0, 1)
        
        # 中央揃えになるよう調整
        text_rect = text.boundingRect()
        # 背景も同じサイズに更新
        bg.setRect(text_rect)
        
        # テキストと背景を正確に中央揃えするための位置調整
        bg_transform = QTransform(text_transform)
        
        # テキストの中心が原点に来るよう調整（左右は中央揃え、上下は上揃えに）
        text_transform.translate(-text_rect.width()/2, 0)
        bg_transform.translate(-text_rect.width()/2, 0)
        
        # 変形を適用
        text.setTransform(text_transform)
        bg.setTransform(bg_transform)
    
    # 三角形番号ラベルの追加
    label = QGraphicsTextItem(str(triangle_data.number))
    font = label.font()
    font.setBold(True)
    font.setPointSize(10)
    label.setFont(font)
    label.setDefaultTextColor(QColor(0, 0, 0))
    
    # テキストの位置を調整（重心に配置）
    rect = label.boundingRect()
    label.setPos(
        triangle_data.center_point.x() - rect.width() / 2,
        triangle_data.center_point.y() - rect.height() / 2
    )
    
    # 三角形番号をクリック可能にするための設定
    label.setData(0, triangle_data.number)  # 三角形番号を保存
    label.setCursor(Qt.PointingHandCursor)  # クリック可能なカーソルに変更
    
    scene.addItem(label)
    
    return triangle_item 