#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Triangle Manager - 三角形管理UI

DXF Viewerの機能とTriangleDataクラスを組み合わせた
三角形作成・管理用のUIを提供するモジュール
"""

import sys
import math
import os
import logging
from pathlib import Path

# 親ディレクトリをパスに追加
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# PySide6のインポート
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGraphicsView, QGraphicsScene, QLineEdit,
    QMessageBox, QGraphicsPolygonItem, QGraphicsLineItem, QDoubleSpinBox,
    QComboBox, QStatusBar, QFileDialog, QGraphicsTextItem, QGraphicsSimpleTextItem,
    QGraphicsRectItem, QSlider, QGraphicsEllipseItem
)
from PySide6.QtGui import (
    QPainter, QPen, QColor, QPolygonF, QDoubleValidator, QTransform,
    QTextOption
)
from PySide6.QtCore import Qt, QPointF, Signal, QObject, QSize

# ui.graphics_viewからDxfGraphicsViewをインポート
from ui.graphics_view import DxfGraphicsView

# TriangleDataクラスの定義を直接行う（外部ファイルのインポートを削除）
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

class TriangleData:
    """三角形のデータと計算ロジックを保持するクラス"""
    def __init__(self, a=0.0, b=0.0, c=0.0, p_ca=QPointF(0, 0), angle_deg=180.0, number=1, parent=None, connection_side=-1):
        self.number = number
        self.name = f"Tri_{number}"
        self.lengths = [float(a), float(b), float(c)]
        self.points = [QPointF(p_ca), QPointF(0, 0), QPointF(0, 0)]
        self.angle_deg = float(angle_deg)
        self.internal_angles_deg = [0.0, 0.0, 0.0]
        self.center_point = QPointF(0, 0)
        self.parent = parent
        self.connection_side = connection_side
        self.children = [None, None, None]
        self.color = QColor(0, 100, 200)
        
        if a > 0 and b > 0 and c > 0:
            if self.is_valid_lengths():
                self.calculate_points()
    
    def is_valid_lengths(self, a=None, b=None, c=None):
        """三角形の成立条件を確認"""
        a = a if a is not None else self.lengths[0]
        b = b if b is not None else self.lengths[1]
        c = c if c is not None else self.lengths[2]
        if a <= 0 or b <= 0 or c <= 0:
            return False
        return (a + b > c) and (b + c > a) and (c + a > b)
    
    def calculate_points(self):
        """三角形の頂点座標を計算"""
        p_ca = self.points[0]
        len_a = self.lengths[0]
        angle_rad = math.radians(self.angle_deg)
        
        # 点ABの計算
        p_ab = QPointF(p_ca.x() + len_a * math.cos(angle_rad), p_ca.y() + len_a * math.sin(angle_rad))
        self.points[1] = p_ab
        
        # 内角の計算（余弦定理）
        len_b = self.lengths[1]
        len_c = self.lengths[2]
        
        # 角A（頂点BC）
        if len_b * len_c > 0:
            cos_angle_a = (len_b**2 + len_c**2 - len_a**2) / (2 * len_b * len_c)
            cos_angle_a = max(-1.0, min(1.0, cos_angle_a))
            angle_a_rad = math.acos(cos_angle_a)
            angle_a_deg = math.degrees(angle_a_rad)
        else:
            angle_a_deg = 0
        
        # 角B（頂点CA）
        if len_a * len_c > 0:
            cos_angle_b = (len_a**2 + len_c**2 - len_b**2) / (2 * len_a * len_c)
            cos_angle_b = max(-1.0, min(1.0, cos_angle_b))
            angle_b_rad = math.acos(cos_angle_b)
            angle_b_deg = math.degrees(angle_b_rad)
        else:
            angle_b_deg = 0
        
        # 角C（頂点AB）
        if len_a * len_b > 0:
            cos_angle_c = (len_a**2 + len_b**2 - len_c**2) / (2 * len_a * len_b)
            cos_angle_c = max(-1.0, min(1.0, cos_angle_c))
            angle_c_rad = math.acos(cos_angle_c)
            angle_c_deg = math.degrees(angle_c_rad)
        else:
            angle_c_deg = 0
        
        # 内部角度を設定
        self.internal_angles_deg = [angle_a_deg, angle_b_deg, angle_c_deg]
        
        # 点BCの計算（一般的な方法）
        # CAからABへのベクトル
        vec_ca_to_ab = QPointF(p_ab.x() - p_ca.x(), p_ab.y() - p_ca.y())
        
        # 三角形の面積を計算（ヘロンの公式）
        s = (len_a + len_b + len_c) / 2  # 半周長
        area = math.sqrt(s * (s - len_a) * (s - len_b) * (s - len_c))  # 面積
        
        # 高さを計算
        height = 2 * area / len_a  # 辺Aに対する高さ
        
        # 点ABからの垂線の足からBCまでの距離
        base_to_bc = math.sqrt(len_c**2 - height**2)
        
        # 点BCの計算
        # 垂線の方向ベクトル（CA→ABを90度回転）
        perp_vec = QPointF(-vec_ca_to_ab.y(), vec_ca_to_ab.x())
        perp_vec_length = math.sqrt(perp_vec.x()**2 + perp_vec.y()**2)
        if perp_vec_length > 0:
            # 単位ベクトル化して高さを掛ける
            norm_perp_vec = QPointF(perp_vec.x() / perp_vec_length, perp_vec.y() / perp_vec_length)
            height_vec = QPointF(norm_perp_vec.x() * height, norm_perp_vec.y() * height)
            
            # ABからbase_to_bc分進んだ点
            if len_a > 0:
                base_vec = QPointF(vec_ca_to_ab.x() / len_a * (len_a - base_to_bc), 
                                  vec_ca_to_ab.y() / len_a * (len_a - base_to_bc))
                base_point = QPointF(p_ab.x() - base_vec.x(), p_ab.y() - base_vec.y())
                
                # 高さ方向に移動して点BCを求める
                self.points[2] = QPointF(base_point.x() + height_vec.x(), base_point.y() + height_vec.y())
            else:
                self.points[2] = p_ab  # エラー時の回避策
        else:
            self.points[2] = p_ab  # エラー時の回避策
        
        # 重心計算
        p_bc = self.points[2]
        self.center_point = QPointF((p_ca.x() + p_ab.x() + p_bc.x()) / 3.0, (p_ca.y() + p_ab.y() + p_bc.y()) / 3.0)
    
    def get_polygon(self) -> QPolygonF:
        """描画用のQPolygonFを返す"""
        return QPolygonF(self.points)
    
    def get_side_line(self, side_index: int) -> tuple:
        """指定された辺の両端点を返す (0:A, 1:B, 2:C)"""
        if side_index == 0:  # 辺A: CA→AB
            logger.debug(f"辺A({side_index})の両端点: {self.points[0]} → {self.points[1]}")
            return self.points[0], self.points[1]
        elif side_index == 1:  # 辺B: AB→BC
            logger.debug(f"辺B({side_index})の両端点: {self.points[1]} → {self.points[2]}")
            return self.points[1], self.points[2]
        elif side_index == 2:  # 辺C: BC→CA
            logger.debug(f"辺C({side_index})の両端点: {self.points[2]} → {self.points[0]}")
            return self.points[2], self.points[0]
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return None
    
    def get_connection_point_by_side(self, side_index: int) -> QPointF:
        """指定された接続辺の次の三角形の基準点を返す"""
        if side_index == 0:  # 辺A: CA→AB の場合、終点ABが次の三角形のCA点になる
            logger.debug(f"Triangle {self.number}: 辺A({side_index})の接続点はAB点")
            return self.points[1]  # 点AB（終点）を返す
        elif side_index == 1:  # 辺B: AB→BC の場合、終点BCが次の三角形のCA点になる
            logger.debug(f"Triangle {self.number}: 辺B({side_index})の接続点はBC点")
            return self.points[2]  # 点BC（終点）を返す
        elif side_index == 2:  # 辺C: BC→CA の場合、終点CAが次の三角形のCA点になる
            logger.debug(f"Triangle {self.number}: 辺C({side_index})の接続点はCA点")
            return self.points[0]  # 点CA（終点）を返す
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return self.points[0]  # デフォルトは点CA
    
    def get_angle_by_side(self, side_index: int) -> float:
        """指定された接続辺の次の三角形の配置角度を計算"""
        if side_index == 0:  # 辺A: CA→AB の場合
            # CA点から見た角度を計算（CAからABへのベクトルの角度 + 180度）
            start = self.points[0]  # 点CA（始点）
            end = self.points[1]    # 点AB（終点）
            logger.debug(f"Triangle {self.number}: 辺A({side_index})の角度計算: {start} → {end}")
        elif side_index == 1:  # 辺B: AB→BC の場合
            # AB点から見た角度を計算（ABからBCへのベクトルの角度 + 180度）
            start = self.points[1]  # 点AB（始点）
            end = self.points[2]    # 点BC（終点）
            logger.debug(f"Triangle {self.number}: 辺B({side_index})の角度計算: {start} → {end}")
        elif side_index == 2:  # 辺C: BC→CA の場合
            # BC点から見た角度を計算（BCからCAへのベクトルの角度 + 180度）
            start = self.points[2]  # 点BC（始点）
            end = self.points[0]    # 点CA（終点）
            logger.debug(f"Triangle {self.number}: 辺C({side_index})の角度計算: {start} → {end}")
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return 0  # デフォルト角度
        
        # ベクトル角度を計算
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.degrees(math.atan2(dy, dx)) + 180  # 反対方向
        
        logger.debug(f"Triangle {self.number}: 辺{side_index}の接続角度 = {angle:.1f}°")
        return angle % 360  # 0-360度の範囲に正規化
    
    def set_child(self, child_triangle, side_index):
        """子三角形を接続"""
        if 0 <= side_index <= 2:
            self.children[side_index] = child_triangle
            child_triangle.parent = self
            child_triangle.connection_side = side_index

# ロガーの設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# TriangleItemSignalHelperクラス - TriangleItemからのシグナル中継用
class TriangleItemSignalHelper(QObject):
    """三角形アイテムからのシグナルを中継するヘルパークラス"""
    sideClicked = Signal(int, int)  # (三角形番号, 辺インデックス)

# TriangleItemクラス
class TriangleItem(QGraphicsPolygonItem):
    """三角形データを表示し、辺クリックを可能にするGraphicsItem"""
    
    def __init__(self, triangle_data: TriangleData, parent=None):
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
                arrow_size = 5  # 10から5に変更（0.5倍）
                
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
            
            # 辺データを保存
            dimension_text.setData(0, edge_index)
    
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
        # ホバー時に辺の視認性を向上
        for line in self.side_lines:
            pen = line.pen()
            pen.setColor(QColor(100, 200, 255, 100))
            line.setPen(pen)
        self.update()
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

# TriangleManagerウィンドウ
class TriangleManagerWindow(QMainWindow):
    """三角形管理UIのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # 寸法テキストのフォントサイズ（デフォルト値）
        self.dimension_font_size = 6
        
        # ウィンドウの設定
        self.setWindowTitle("Triangle Manager")
        self.resize(1200, 800)
        
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # ビューとシーンの設定
        self.view = DxfGraphicsView()
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        main_layout.addWidget(self.view, 1)
        
        # コントロールパネルの作成
        self.control_panel = self.create_control_panel()
        main_layout.addWidget(self.control_panel)
        
        # ステータスバーの設定
        self.statusBar().showMessage("準備完了")
        
        # データの初期化
        self.triangle_list = []
        self.selected_parent_number = -1
        self.selected_side_index = -1
        
        # 最初の三角形を作成
        self.reset_all()
    
    def create_control_panel(self):
        """コントロールパネルを作成"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # 情報表示部分
        info_group = QWidget()
        info_layout = QVBoxLayout(info_group)
        
        # 選択情報
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("選択中:"))
        self.selected_info_label = QLabel("なし")
        selection_layout.addWidget(self.selected_info_label)
        info_layout.addLayout(selection_layout)
        
        # 寸法テキストサイズ設定
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("寸法サイズ:"))
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(2)
        self.font_size_slider.setMaximum(12)
        self.font_size_slider.setValue(self.dimension_font_size)
        self.font_size_slider.setTickPosition(QSlider.TicksBelow)
        self.font_size_slider.setTickInterval(1)
        self.font_size_slider.valueChanged.connect(self.update_dimension_font_size)
        font_size_layout.addWidget(self.font_size_slider)
        
        # サイズ表示ラベル
        self.font_size_label = QLabel(f"{self.dimension_font_size}")
        font_size_layout.addWidget(self.font_size_label)
        
        info_layout.addLayout(font_size_layout)
        layout.addWidget(info_group)
        
        # 入力部分
        input_group = QWidget()
        input_layout = QVBoxLayout(input_group)
        
        # 辺の長さ入力
        lengths_layout = QHBoxLayout()
        
        # 辺B（親三角形との接続辺の反対）の長さ
        lengths_layout.addWidget(QLabel("辺B:"))
        self.new_len_b_input = QLineEdit()
        self.new_len_b_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        self.new_len_b_input.setText("80.0")
        lengths_layout.addWidget(self.new_len_b_input)
        
        # 辺C（もう一方の辺）の長さ
        lengths_layout.addWidget(QLabel("辺C:"))
        self.new_len_c_input = QLineEdit()
        self.new_len_c_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        self.new_len_c_input.setText("80.0")
        lengths_layout.addWidget(self.new_len_c_input)
        
        input_layout.addLayout(lengths_layout)
        
        # ボタン
        buttons_layout = QHBoxLayout()
        
        # 追加ボタン
        self.add_button = QPushButton("三角形を追加")
        self.add_button.clicked.connect(self.add_triangle)
        buttons_layout.addWidget(self.add_button)
        
        # リセットボタン
        reset_button = QPushButton("リセット")
        reset_button.clicked.connect(self.reset_all)
        buttons_layout.addWidget(reset_button)
        
        # 全体表示ボタン
        fit_button = QPushButton("全体表示")
        fit_button.clicked.connect(self.fit_view)
        buttons_layout.addWidget(fit_button)
        
        input_layout.addLayout(buttons_layout)
        
        layout.addWidget(input_group)
        
        return panel
    
    def reset_all(self):
        """すべてのデータをリセット"""
        # データのクリア
        self.triangle_list.clear()
        self.selected_parent_number = -1
        self.selected_side_index = -1
        
        # ビューのクリア
        self.view.clear_scene()
        
        # 最初の三角形を作成
        initial_triangle = TriangleData(100.0, 100.0, 100.0, QPointF(0, 0), 180.0, 1)
        self.add_triangle_data(initial_triangle)
        
        # 選択情報をリセット
        self.selected_info_label.setText("なし")
        
        # ビューをリセット
        self.fit_view()
        
        self.statusBar().showMessage("リセットしました")
    
    def add_triangle_data(self, triangle_data: TriangleData):
        """三角形データを追加して表示"""
        # リストに追加
        self.triangle_list.append(triangle_data)
        
        # シーンアイテムの作成
        triangle_item = TriangleItem(triangle_data)
        self.view.scene().addItem(triangle_item)
        
        # 辺クリックシグナルの接続
        triangle_item.signalHelper.sideClicked.connect(self.handle_side_clicked)
        
        # 寸法テキストとその背景をシーンに追加
        for dim_info in triangle_item.dimension_items:
            text = dim_info['text']
            bg = dim_info['bg']
            mid_x = dim_info['mid_x']
            mid_y = dim_info['mid_y']
            angle = dim_info['angle']
            
            # 現在のフォントサイズで更新
            font = text.font()
            font.setPointSize(self.dimension_font_size)
            text.setFont(font)
            
            # テキストサイズ変更に伴い背景サイズも調整
            text_rect = text.boundingRect()
            bg.setRect(text_rect)
            
            # 描画原点を示す青いドット（サイズを半分に）
            origin_dot = QGraphicsEllipseItem(-1, -1, 2, 2)
            origin_dot.setBrush(QColor(0, 0, 255))  # 青色
            origin_dot.setPen(QPen(Qt.NoPen))
            
            # ZValueを設定（背景が最背面、テキストが中間、青ドットが最前面）
            bg.setZValue(0)  # 最背面
            text.setZValue(1)  # 中間
            origin_dot.setZValue(2)  # 最前面
            
            # シーンに追加（背景を最初に追加して最背面に）
            self.view.scene().addItem(bg)
            self.view.scene().addItem(text)
            self.view.scene().addItem(origin_dot)
            
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
            
            # デバッグ情報として寸法情報とテキスト位置を関連付け
            text.setData(1, {'mid_x': mid_x, 'mid_y': mid_y, 'angle': angle})
            bg.setData(0, text)  # 背景とテキストを関連付け
        
        # ラベルの追加（三角形番号表示）
        label = QGraphicsTextItem(str(triangle_data.number))
        # テキストを中央揃えに
        document = label.document()
        document.setDefaultTextOption(QTextOption(Qt.AlignCenter))
        
        # テキストの位置を調整（重心に配置）
        rect = label.boundingRect()
        label.setPos(
            triangle_data.center_point.x() - rect.width() / 2,
            triangle_data.center_point.y() - rect.height() / 2
        )
        
        # テキストのフォントと色を調整
        font = label.font()
        font.setBold(True)
        font.setPointSize(10)
        label.setFont(font)
        label.setDefaultTextColor(QColor(0, 0, 0))
        
        self.view.scene().addItem(label)
        
        # シーンとビューを更新
        self.view.initialize_view()
    
    def handle_side_clicked(self, triangle_number, side_index):
        """三角形の辺がクリックされた時の処理"""
        # 選択情報を更新
        self.selected_parent_number = triangle_number
        self.selected_side_index = side_index
        
        # 表示を更新
        triangle = next((t for t in self.triangle_list if t.number == triangle_number), None)
        if triangle:
            # 辺の表示名マッピング（インデックスから名前へ）
            edge_name_mapping = {
                0: "A",  # インデックス0 → 辺A (CA→AB)
                1: "B",  # インデックス1 → 辺B (AB→BC)
                2: "C"   # インデックス2 → 辺C (BC→CA)
            }
            edge_name = edge_name_mapping[side_index]
            
            self.selected_info_label.setText(f"三角形 {triangle_number} の辺 {edge_name}")
            
            # ステータスバーに選択情報を表示
            # 辺の両端点を直接頂点配列から取得
            # 頂点インデックスマッピング
            edge_points_mapping = {
                0: (0, 1),  # 辺A: CA→AB
                1: (1, 2),  # 辺B: AB→BC
                2: (2, 0)   # 辺C: BC→CA
            }
            start_idx, end_idx = edge_points_mapping[side_index]
            p1 = triangle.points[start_idx]
            p2 = triangle.points[end_idx]
            edge_length = triangle.lengths[side_index]
            
            # 頂点名マッピング（辺のインデックスから頂点の名前ペアへ）
            edge_vertices_mapping = {
                0: ("CA", "AB"),  # 辺A
                1: ("AB", "BC"),  # 辺B
                2: ("BC", "CA")   # 辺C
            }
            start_vertex, end_vertex = edge_vertices_mapping[side_index]
            
            # より詳細な情報をステータスバーに表示
            self.statusBar().showMessage(
                f"三角形 {triangle_number} の辺 {edge_name}: "
                f"{start_vertex}({p1.x():.1f}, {p1.y():.1f}) → "
                f"{end_vertex}({p2.x():.1f}, {p2.y():.1f}), "
                f"長さ: {edge_length:.1f}"
            )
            
            # 選択された辺をハイライト
            # まず、すべての三角形の選択をクリア
            for item in self.view.scene().items():
                if isinstance(item, TriangleItem):
                    if item.triangle_data.number == triangle_number:
                        # 選択された三角形の辺をハイライト
                        item.highlight_selected_side(side_index)
                    else:
                        # 他の三角形の選択をクリア
                        item.highlight_selected_side(None)
    
    def add_triangle(self):
        """選択された辺に新しい三角形を追加"""
        # 選択チェック
        if self.selected_parent_number < 0 or self.selected_side_index < 0:
            QMessageBox.warning(self, "選択エラー", "三角形の辺が選択されていません")
            return
        
        # デバッグログ - 選択情報
        logger.debug(f"三角形追加開始: 親={self.selected_parent_number}, 選択辺={self.selected_side_index}")
        
        # 親三角形の取得
        parent_triangle = next((t for t in self.triangle_list if t.number == self.selected_parent_number), None)
        if not parent_triangle:
            QMessageBox.warning(self, "エラー", "親三角形が見つかりません")
            return
        
        # 既に接続されているかチェック
        if parent_triangle.children[self.selected_side_index] is not None:
            QMessageBox.warning(self, "接続エラー", "この辺には既に三角形が接続されています")
            return
        
        # 新しい辺の長さを取得
        try:
            len_b = float(self.new_len_b_input.text())
            len_c = float(self.new_len_c_input.text())
        except ValueError:
            QMessageBox.warning(self, "入力エラー", "辺の長さには有効な数値を入力してください")
            return
        
        # 辺の長さ（親の辺の長さを新しい三角形の辺Aとして使用）
        len_a = parent_triangle.lengths[self.selected_side_index]
        
        # デバッグログ - 辺の長さ
        logger.debug(f"新しい三角形の辺の長さ: A={len_a:.1f}, B={len_b:.1f}, C={len_c:.1f}")
        
        # 三角形の成立条件をチェック
        new_triangle = TriangleData()
        if not new_triangle.is_valid_lengths(len_a, len_b, len_c):
            QMessageBox.warning(self, "三角形エラー", f"指定された辺の長さ ({len_a:.1f}, {len_b:.1f}, {len_c:.1f}) では三角形が成立しません")
            return
        
        # 接続点（次の三角形の基準点）
        connection_point = parent_triangle.get_connection_point_by_side(self.selected_side_index)
        
        # 辺の両端点を取得（デバッグ用）
        side_points = parent_triangle.get_side_line(self.selected_side_index)
        if side_points:
            p1, p2 = side_points
            # 辺の頂点名を取得
            edge_vertices_mapping = {
                0: ("CA", "AB"),  # 辺A
                1: ("AB", "BC"),  # 辺B
                2: ("BC", "CA")   # 辺C
            }
            start_vertex, end_vertex = edge_vertices_mapping[self.selected_side_index]
            logger.debug(f"選択された辺の両端点: {start_vertex}({p1.x():.1f}, {p1.y():.1f}) → "
                         f"{end_vertex}({p2.x():.1f}, {p2.y():.1f})")
        
        # 接続角度
        connection_angle = parent_triangle.get_angle_by_side(self.selected_side_index)
        
        # デバッグログ - 接続情報
        logger.debug(f"接続点: ({connection_point.x():.1f}, {connection_point.y():.1f}), 角度: {connection_angle:.1f}度")
        
        # 新しい三角形番号
        new_number = len(self.triangle_list) + 1
        
        # 新しい三角形を作成
        new_triangle = TriangleData(
            a=len_a, b=len_b, c=len_c,
            p_ca=connection_point,
            angle_deg=connection_angle,
            number=new_number
        )
        
        # 親子関係の設定
        parent_triangle.set_child(new_triangle, self.selected_side_index)
        
        # デバッグログ - 頂点情報
        logger.debug(f"新しい三角形 {new_number} の頂点:")
        logger.debug(f"  CA: ({new_triangle.points[0].x():.1f}, {new_triangle.points[0].y():.1f})")
        logger.debug(f"  AB: ({new_triangle.points[1].x():.1f}, {new_triangle.points[1].y():.1f})")
        logger.debug(f"  BC: ({new_triangle.points[2].x():.1f}, {new_triangle.points[2].y():.1f})")
        
        # 三角形を追加
        self.add_triangle_data(new_triangle)
        
        # 選択をクリア
        self.selected_parent_number = -1
        self.selected_side_index = -1
        self.selected_info_label.setText("なし")
        
        # ビューを全体表示に更新
        self.fit_view()
        
        self.statusBar().showMessage(f"三角形 {new_number} を追加しました")
    
    def fit_view(self):
        """ビューを全ての三角形が見える大きさに調整"""
        self.view.fit_scene_in_view()
    
    def update_dimension_font_size(self, size):
        """寸法テキストのフォントサイズを更新"""
        self.dimension_font_size = size
        self.font_size_label.setText(f"{size}")
        
        # 既存の全ての三角形の寸法テキストサイズを更新
        for item in self.view.scene().items():
            if isinstance(item, QGraphicsSimpleTextItem):
                # データ属性からチェックして、寸法テキストかどうか確認
                if item.data(0) is not None and isinstance(item.data(0), int) and 0 <= item.data(0) <= 2:
                    # フォントサイズを更新
                    font = item.font()
                    font.setPointSize(size)
                    item.setFont(font)
                    
                    # 関連情報を取得
                    dim_info = item.data(1)
                    if dim_info:
                        mid_x = dim_info['mid_x']
                        mid_y = dim_info['mid_y']
                        angle = dim_info['angle']
                        
                        # バウンディングボックスを再計算
                        text_rect = item.boundingRect()
                        
                        # 背景アイテムを探して更新
                        for bg in self.view.scene().items():
                            if isinstance(bg, QGraphicsRectItem) and bg.data(0) == item:
                                # 背景サイズをテキストサイズに合わせて更新
                                bg.setRect(text_rect)
                                
                                # ZValueを再設定（背景が最背面）
                                bg.setZValue(0)
                                item.setZValue(1)
                                
                                # 変形行列を作成
                                transform = QTransform()
                                transform.translate(mid_x, mid_y)
                                
                                # 辺の角度に合わせて回転
                                if 90 <= angle <= 270:
                                    transform.rotate(angle + 180)
                                else:
                                    transform.rotate(angle)
                                
                                # 辺上の原点と、テキスト位置を分離
                                # 青ドット用の変形行列を探して更新
                                for dot in self.view.scene().items():
                                    if isinstance(dot, QGraphicsEllipseItem) and dot.brush().color() == QColor(0, 0, 255):
                                        # ドットとテキストの位置関係をチェック
                                        dot_pos = dot.pos()
                                        text_pos = item.pos()
                                        
                                        # 同じ位置にあるドットを探す
                                        if abs(dot_pos.x() - text_pos.x()) < 20 and abs(dot_pos.y() - text_pos.y()) < 20:
                                            # ドットは辺上に配置
                                            dot.setTransform(transform)
                                            break
                                
                                # テキスト用の変形行列（辺から少し離す）
                                text_transform = QTransform(transform)
                                text_transform.translate(0, 1)
                                
                                # テキストと背景を正確に中央揃えするための位置調整
                                bg_transform = QTransform(text_transform)
                                
                                # テキストの中心が原点に来るよう調整（左右は中央揃え、上下は上揃えに）
                                text_transform.translate(-text_rect.width()/2, 0)
                                bg_transform.translate(-text_rect.width()/2, 0)
                                
                                # 変形を適用
                                item.setTransform(text_transform)
                                bg.setTransform(bg_transform)
                                break
        
        # ビューを更新
        self.view.update()

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    window = TriangleManagerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 