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
    QGraphicsRectItem, QSlider, QGraphicsEllipseItem, QFrame
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

# DXF出力用にezdxfをインポート
try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    logger.warning("ezdxfモジュールが見つかりません。DXF出力機能は利用できません。")
    logger.warning("インストールには: pip install ezdxf を実行してください。")

# UIデザイン定数 - 視覚的に整理された設定値
class UIConstants:
    # ウィンドウサイズ
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # コントロールサイズ
    CONTROL_HEIGHT = 36      # 標準コントロールの高さ
    BUTTON_HEIGHT = 36       # ボタンの高さ
    BUTTON_WIDTH = 120       # ボタンの幅
    INPUT_HEIGHT = 36        # 入力フィールドの高さ
    INPUT_WIDTH = 80         # 入力フィールドの幅
    SLIDER_HEIGHT = 30       # スライダーの高さ
    SLIDER_WIDTH = 150       # スライダーの幅
    
    # パネルとグループサイズ
    PANEL_MIN_HEIGHT = 200   # パネルの最小高さ
    GROUP_MIN_HEIGHT = 80    # グループの最小高さ
    PANEL_MARGIN = 10        # パネルの余白
    GROUP_MARGIN = 8         # グループの余白
    
    # フォントサイズ
    DEFAULT_FONT_SIZE = 10   # 基本フォントサイズ
    BUTTON_FONT_SIZE = 20    # ボタン用フォントサイズ（標準の2倍）
    LABEL_FONT_SIZE = 12     # ラベル用フォントサイズ
    INPUT_FONT_SIZE = 15     # 入力フィールド用フォントサイズ（基本の1.5倍）
    DIMENSION_FONT_SIZE = 6  # 三角形の寸法表示サイズ
    
    # 色の定義
    BACKGROUND_COLOR = "#f0f0f0"
    BUTTON_COLOR = "#e0e0e0"
    HIGHLIGHT_COLOR = "#d0d0d0"
    FORM_BACKGROUND = "#f8f8f8"
    
    # スタイルシート
    CONTROL_STYLE = f"""
        QWidget {{ background-color: {BACKGROUND_COLOR}; }}
        QPushButton {{ 
            min-height: {BUTTON_HEIGHT}px; 
            min-width: {BUTTON_WIDTH}px;
            background-color: {BUTTON_COLOR};
            padding: 5px;
            border: 1px solid #a0a0a0;
            border-radius: 4px;
            font-size: {BUTTON_FONT_SIZE}pt;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {HIGHLIGHT_COLOR}; }}
        QLineEdit {{ 
            min-height: {INPUT_HEIGHT}px; 
            min-width: {INPUT_WIDTH}px;
            padding: 3px;
            border: 1px solid #a0a0a0;
            border-radius: 4px;
            font-size: {INPUT_FONT_SIZE}pt;
            font-weight: bold;
        }}
        QLabel {{ 
            font-size: {LABEL_FONT_SIZE}pt; 
            min-height: {CONTROL_HEIGHT // 2}px;
        }}
        QSlider {{ 
            min-height: {SLIDER_HEIGHT}px; 
            min-width: {SLIDER_WIDTH}px;
        }}
        QGroupBox {{ 
            min-height: {GROUP_MIN_HEIGHT}px; 
            margin-top: {GROUP_MARGIN}px;
            margin-bottom: {GROUP_MARGIN}px;
            padding: {GROUP_MARGIN}px;
            border: 1px solid #c0c0c0;
            border-radius: 6px;
            background-color: {FORM_BACKGROUND};
        }}
        QVBoxLayout, QHBoxLayout {{ 
            margin: {PANEL_MARGIN}px; 
            spacing: {PANEL_MARGIN}px;
        }}
    """

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
                arrow_size = 3  # 10から5に変更（0.5倍）
                
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

# TriangleManagerウィンドウ
class TriangleManagerWindow(QMainWindow):
    """三角形管理UIのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # UIデザイン定数を適用
        self.dimension_font_size = UIConstants.DIMENSION_FONT_SIZE
        
        # ウィンドウの設定
        self.setWindowTitle("Triangle Manager")
        self.resize(UIConstants.WINDOW_WIDTH, UIConstants.WINDOW_HEIGHT)
        
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_widget.setStyleSheet(UIConstants.CONTROL_STYLE)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # ビューとシーンの設定
        self.view = DxfGraphicsView()
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        main_layout.addWidget(self.view, 1)
        
        # 背景クリック時のハンドラを設定
        self.view.scene().mouseReleaseEvent = self.scene_mouse_release_event
        
        # コントロールパネルの作成
        self.control_panel = self.create_control_panel()
        main_layout.addWidget(self.control_panel)
        
        # ステータスバーの設定
        self.statusBar().showMessage("準備完了")
        
        # データの初期化
        self.triangle_list = []
        self.selected_parent_number = -1
        self.selected_side_index = -1
        self.next_triangle_number = 1  # 次の三角形番号の初期化
        
        # 最初の三角形を作成
        self.reset_all()
        
        # 三角形選択コンボボックスを更新
        self.update_triangle_combo()
    
    def create_control_panel(self):
        """コントロールパネルを作成"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
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
        
        # 辺の長さ入力 - 3つの入力欄を並べるように変更
        lengths_layout = QHBoxLayout()
        
        # 三角形選択コンボボックス（左側に配置）
        lengths_layout.addWidget(QLabel("三角形選択:"))
        self.triangle_combo = QComboBox()
        self.triangle_combo.setMinimumWidth(100)
        self.triangle_combo.addItem("---", -1)  # デフォルト選択なし
        self.triangle_combo.currentIndexChanged.connect(self.on_triangle_selected)
        
        # フォントサイズを設定
        font = self.triangle_combo.font()
        font.setPointSize(15)  # UIConstants.INPUT_FONT_SIZEの値
        self.triangle_combo.setFont(font)
        
        lengths_layout.addWidget(self.triangle_combo)
        
        # 横方向のスペーサーを追加（縦の区切り線を追加）
        vertical_line = QFrame()
        vertical_line.setFrameShape(QFrame.VLine)
        vertical_line.setFrameShadow(QFrame.Sunken)
        lengths_layout.addWidget(vertical_line)
        
        # 辺A
        lengths_layout.addWidget(QLabel("辺A:"))
        self.new_len_a_input = QLineEdit()
        self.new_len_a_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        self.new_len_a_input.setText("100.0")
        lengths_layout.addWidget(self.new_len_a_input)
        
        # 辺B
        lengths_layout.addWidget(QLabel("辺B:"))
        self.new_len_b_input = QLineEdit()
        self.new_len_b_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        self.new_len_b_input.setText("80.0")
        lengths_layout.addWidget(self.new_len_b_input)
        
        # 辺C
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
        
        # 更新ボタン
        self.update_triangle_button = QPushButton("三角形を更新")
        self.update_triangle_button.clicked.connect(self.update_selected_triangle)
        self.update_triangle_button.setEnabled(False)  # 初期状態は無効
        buttons_layout.addWidget(self.update_triangle_button)
        
        # リセットボタン
        reset_button = QPushButton("ビューリセット")
        reset_button.clicked.connect(self.reset_all)
        buttons_layout.addWidget(reset_button)
        
        # 全体表示ボタン
        fit_button = QPushButton("全体表示")
        fit_button.clicked.connect(self.fit_view)
        buttons_layout.addWidget(fit_button)
        
        # DXF出力ボタンを追加
        if HAS_EZDXF:
            self.export_dxf_button = QPushButton("DXF出力")
            self.export_dxf_button.clicked.connect(self.export_to_dxf)
            buttons_layout.addWidget(self.export_dxf_button)
        
        input_layout.addLayout(buttons_layout)
        
        layout.addWidget(input_group)
        
        return panel
    
    def reset_all(self, create_initial=True):
        """すべてのデータをリセット
        
        Args:
            create_initial: 初期三角形を作成するかどうか。Falseの場合はリストのクリアだけ行う。
        """
        # データのクリア
        self.triangle_list.clear()
        self.selected_parent_number = -1
        self.selected_side_index = -1
        self.next_triangle_number = 1  # 三角形番号をリセット
        
        # コンボボックスをクリア
        self.triangle_combo.blockSignals(True)
        self.triangle_combo.clear()
        self.triangle_combo.addItem("---", -1)
        self.triangle_combo.blockSignals(False)
        
        # ビューのクリア
        self.view.clear_scene()
        
        # 最初の三角形を作成（オプション）
        if create_initial:
            initial_triangle = TriangleData(100.0, 100.0, 100.0, QPointF(0, 0), 180.0, 1)
            self.add_triangle_data(initial_triangle)
        
        # 選択情報をリセット
        self.selected_info_label.setText("なし")
        
        # ビューをリセット
        self.fit_view()
        
        self.statusBar().showMessage("ビューをリセットしました")
    
    def add_triangle_data(self, triangle_data: TriangleData):
        """三角形データを追加して表示"""
        # リストに追加
        self.triangle_list.append(triangle_data)
        
        # 次の三角形番号を更新（update_triangle_counter の代わりに直接更新）
        if triangle_data.number >= self.next_triangle_number:
            self.next_triangle_number = triangle_data.number + 1
        
        # コンボボックスに追加
        self.update_triangle_combo()
        
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
        
        # 三角形番号をクリック可能にするための設定
        label.setData(0, triangle_data.number)  # 三角形番号を保存
        label.setCursor(Qt.PointingHandCursor)  # クリック可能なカーソルに変更
        
        self.view.scene().addItem(label)
        
        # シーンとビューを更新
        self.view.initialize_view()
    
    def get_detailed_edge_info(self, triangle, side_index):
        """三角形の辺の詳細情報を文字列として返す（純粋関数）"""
        if not triangle:
            return "選択なし"
        
        # 辺の表示名マッピング（インデックスから名前へ）
        edge_name_mapping = {
            0: "A",  # インデックス0 → 辺A (CA→AB)
            1: "B",  # インデックス1 → 辺B (AB→BC)
            2: "C"   # インデックス2 → 辺C (BC→CA)
        }
        edge_name = edge_name_mapping[side_index]
        
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
        
        # 詳細情報を文字列として返す
        return (
            f"三角形 {triangle.number} の辺 {edge_name}: "
            f"{start_vertex}({p1.x():.1f}, {p1.y():.1f}) → "
            f"{end_vertex}({p2.x():.1f}, {p2.y():.1f}), "
            f"長さ: {edge_length:.1f}"
        )

    def handle_side_clicked(self, triangle_number, side_index):
        """三角形の辺がクリックされたときの処理"""
        # 選択情報を保存
        self.selected_parent_number = triangle_number
        self.selected_side_index = side_index
        
        # 選択された三角形を取得
        triangle = self.get_triangle_by_number(triangle_number)
        if not triangle:
            return
        
        # 選択情報を表示
        self.selected_info_label.setText(f"三角形 {triangle_number} の辺 {chr(65 + side_index)}")
        
        # 入力欄に現在の値をセット
        self.new_len_a_input.setText(f"{triangle.lengths[0]:.1f}")
        self.new_len_b_input.setText(f"{triangle.lengths[1]:.1f}")
        self.new_len_c_input.setText(f"{triangle.lengths[2]:.1f}")
        
        # 更新ボタンを有効化
        self.update_triangle_button.setEnabled(True)
        
        # コンボボックスの選択も更新
        self.triangle_combo.blockSignals(True)  # シグナルを一時停止して再帰呼び出しを防止
        index = self.triangle_combo.findData(triangle_number)
        if index >= 0:
            self.triangle_combo.setCurrentIndex(index)
        self.triangle_combo.blockSignals(False)  # シグナルを再開
        
        # 選択された辺をハイライト
        for item in self.view.scene().items():
            if isinstance(item, TriangleItem):
                if item.triangle_data.number == triangle_number:
                    # 選択された三角形の辺をハイライト
                    item.highlight_selected_side(side_index)
                else:
                    # 他の三角形の選択をクリア
                    item.highlight_selected_side(None)
        
        # 詳細情報をステータスバーに表示
        detailed_info = self.get_detailed_edge_info(triangle, side_index)
        self.statusBar().showMessage(detailed_info)
    
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
            len_a = float(self.new_len_a_input.text())
            len_b = float(self.new_len_b_input.text())
            len_c = float(self.new_len_c_input.text())
        except ValueError:
            QMessageBox.warning(self, "入力エラー", "辺の長さには有効な数値を入力してください")
            return
        
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
        new_number = self.next_triangle_number
        
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
        
        # 三角形カウンターを更新
        self.update_triangle_counter()
        
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

    def export_to_dxf(self):
        """三角形データをDXFファイルに出力する"""
        if not HAS_EZDXF:
            QMessageBox.warning(self, "DXF出力エラー", 
                               "ezdxfモジュールがインストールされていないため、DXF出力機能は利用できません。\n"
                               "インストールするには: pip install ezdxf を実行してください。")
            return
        
        if not self.triangle_list:
            QMessageBox.information(self, "DXF出力", "出力する三角形データがありません。")
            return
        
        # 保存ファイル名を取得
        file_path, _ = QFileDialog.getSaveFileName(
            self, "DXFファイルを保存", "", "DXF Files (*.dxf)"
        )
        
        if not file_path:
            return  # ユーザーがキャンセルした場合
        
        try:
            # R2010形式のDXFドキュメントを作成
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # 各三角形をポリラインとして追加
            for triangle_data in self.triangle_list:
                if triangle_data and triangle_data.points:
                    # 三角形の点を取得
                    points = [(p.x(), p.y(), 0) for p in triangle_data.points]
                    # 閉じたポリラインを作成
                    points.append(points[0])  # 最初の点を追加して閉じる
                    
                    # ポリラインをモデルスペースに追加
                    msp.add_lwpolyline(points)
                    
                    # 寸法テキストを追加
                    for i, length in enumerate(triangle_data.lengths):
                        # 辺の中点を計算
                        p1, p2 = triangle_data.get_side_line(i)
                        mid_x = (p1.x() + p2.x()) / 2
                        mid_y = (p1.y() + p2.y()) / 2
                        
                        # テキスト追加（最新のezdxfではパラメータ名が変更されている）
                        text = msp.add_text(f"{length:.1f}", height=length * 0.05)
                        text.dxf.insert = (mid_x, mid_y)
                        text.dxf.halign = 4  # 4=Middle
                        text.dxf.valign = 2  # 2=Middle
            
            # DXFファイルを保存
            doc.saveas(file_path)
            
            self.statusBar().showMessage(f"DXFファイルを保存しました: {file_path}")
            QMessageBox.information(self, "DXF出力", f"三角形データをDXFファイルに出力しました。\n{file_path}")
        
        except Exception as e:
            logger.error(f"DXF出力エラー: {str(e)}")
            QMessageBox.critical(self, "DXF出力エラー", f"DXFファイルの出力中にエラーが発生しました。\n{str(e)}")

    def update_triangle_counter(self):
        """三角形の番号カウンターを更新"""
        # 最大の三角形番号を見つけて次の番号を設定
        max_num = 0
        for tri in self.triangle_list:
            if tri.number > max_num:
                max_num = tri.number
        self.next_triangle_number = max_num + 1
        logger.debug(f"三角形カウンター更新: 次の番号 = {self.next_triangle_number}")

    def update_selected_triangle(self):
        """選択された三角形の寸法を更新し、子三角形の座標も再計算する"""
        # 選択チェック
        if self.selected_parent_number < 0:
            QMessageBox.warning(self, "選択エラー", "三角形が選択されていません")
            return False

        # 三角形を取得
        triangle = self.get_triangle_by_number(self.selected_parent_number)
        if not triangle:
            QMessageBox.warning(self, "エラー", "選択された三角形が見つかりません")
            return False
        
        # 新しい辺の長さを取得 - 3つすべての入力を使用
        try:
            new_len_a = float(self.new_len_a_input.text())
            new_len_b = float(self.new_len_b_input.text())
            new_len_c = float(self.new_len_c_input.text())
        except ValueError:
            QMessageBox.warning(self, "入力エラー", "辺の長さには有効な数値を入力してください")
            return False
        
        # 3つすべての辺の長さを直接設定
        new_lengths = [new_len_a, new_len_b, new_len_c]
        
        # 三角形の成立条件をチェック
        if not triangle.is_valid_lengths(new_lengths[0], new_lengths[1], new_lengths[2]):
            QMessageBox.warning(self, "三角形エラー", 
                                f"指定された辺の長さ({new_lengths[0]:.1f}, {new_lengths[1]:.1f}, {new_lengths[2]:.1f})では三角形が成立しません")
            return False
        
        # デバッグログ
        logger.debug(f"三角形 {triangle.number} を更新: 新しい辺の長さ = {new_lengths}")
        
        # 更新前の座標をログ出力
        logger.debug(f"更新前の座標 - CA({triangle.points[0].x():.1f}, {triangle.points[0].y():.1f}), "
                    f"AB({triangle.points[1].x():.1f}, {triangle.points[1].y():.1f}), "
                    f"BC({triangle.points[2].x():.1f}, {triangle.points[2].y():.1f})")
        
        # シンプルな座標更新ロジック
        self.update_triangle_and_propagate(triangle, new_lengths)
        
        # 三角形アイテムの更新（シーンの再描画）
        self.refresh_triangle_items()
        
        # ビューを更新
        self.fit_view()
        
        self.statusBar().showMessage(f"三角形 {triangle.number} を更新しました")
        return True
    
    def update_triangle_and_propagate(self, triangle, new_lengths):
        """三角形の寸法を更新し、子三角形に座標変更を伝播する"""
        # 更新前の子三角形の接続情報を保存
        children_info = []
        for i, child in enumerate(triangle.children):
            if child:
                children_info.append({
                    'index': i,
                    'child': child,
                    'old_point': QPointF(child.points[0]),
                    'old_angle': child.angle_deg
                })
        
        # 1. 三角形の寸法と座標を更新
        triangle.lengths = new_lengths
        triangle.calculate_points()
        
        # 更新後の座標をログ出力
        logger.debug(f"更新後の座標 - CA({triangle.points[0].x():.1f}, {triangle.points[0].y():.1f}), "
                    f"AB({triangle.points[1].x():.1f}, {triangle.points[1].y():.1f}), "
                    f"BC({triangle.points[2].x():.1f}, {triangle.points[2].y():.1f})")
        
        # 2. 子三角形の座標を更新
        for info in children_info:
            child = info['child']
            side_index = info['index']
            
            # 新しい接続点と角度
            new_p_ca = triangle.get_connection_point_by_side(side_index)
            new_angle = triangle.get_angle_by_side(side_index)
            
            # 子三角形の更新前情報をログ出力
            logger.debug(f"子三角形 {child.number} 更新前: 基準点=({info['old_point'].x():.1f}, {info['old_point'].y():.1f}), "
                       f"角度={info['old_angle']:.1f}")
            
            # 子三角形の基準点と角度を更新
            child.p_ca = new_p_ca
            child.angle_deg = new_angle
            child.points[0] = new_p_ca
            
            # 子三角形の座標を再計算
            child.calculate_points()
            
            # 更新後情報をログ出力
            logger.debug(f"子三角形 {child.number} 更新後: 基準点=({child.points[0].x():.1f}, {child.points[0].y():.1f}), "
                       f"角度={child.angle_deg:.1f}")
            
            # 3. 孫三角形があれば再帰的に更新
            if any(child.children):
                self.update_child_triangles_recursive(child)
    
    def update_child_triangles_recursive(self, parent):
        """子三角形を再帰的に更新する（シンプルなバージョン）"""
        for side_index, child in enumerate(parent.children):
            if not child:
                continue
                
            # 新しい接続点と角度
            new_p_ca = parent.get_connection_point_by_side(side_index)
            new_angle = parent.get_angle_by_side(side_index)
            
            # 接続点の更新前後をログ出力
            logger.debug(f"孫三角形 {child.number} 更新前: 基準点=({child.points[0].x():.1f}, {child.points[0].y():.1f})")
            
            # 子三角形の基準点と角度を更新
            child.p_ca = new_p_ca
            child.angle_deg = new_angle
            child.points[0] = new_p_ca
            
            # 座標を再計算
            child.calculate_points()
            
            logger.debug(f"孫三角形 {child.number} 更新後: 基準点=({child.points[0].x():.1f}, {child.points[0].y():.1f})")
            
            # さらに子がいれば再帰的に更新
            if any(child.children):
                self.update_child_triangles_recursive(child)
    
    def refresh_triangle_items(self):
        """すべての三角形アイテムを再構築"""
        # シーンをクリア
        self.view.scene().clear()
        
        # 三角形アイテムを再作成
        for triangle in self.triangle_list:
            # シーンアイテムの作成
            triangle_item = TriangleItem(triangle)
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
            
            # ラベルの追加（三角形番号表示）
            label = QGraphicsTextItem(str(triangle.number))
            # テキストを中央揃えに
            document = label.document()
            document.setDefaultTextOption(QTextOption(Qt.AlignCenter))
            
            # テキストの位置を調整（重心に配置）
            rect = label.boundingRect()
            label.setPos(
                triangle.center_point.x() - rect.width() / 2,
                triangle.center_point.y() - rect.height() / 2
            )
            
            # テキストのフォントと色を調整
            font = label.font()
            font.setBold(True)
            font.setPointSize(10)
            label.setFont(font)
            label.setDefaultTextColor(QColor(0, 0, 0))
            
            # 三角形番号をクリック可能にするための設定
            label.setData(0, triangle.number)  # 三角形番号を保存
            label.setCursor(Qt.PointingHandCursor)  # クリック可能なカーソルに変更
            
            self.view.scene().addItem(label)
        
        # シーンとビューを更新
        self.view.update()
    
    def get_triangle_by_number(self, number):
        """番号から三角形を取得"""
        return next((t for t in self.triangle_list if t.number == number), None)

    def clear_all_highlights(self):
        """すべての三角形の選択状態をクリア（純粋関数）"""
        # すべての三角形アイテムを取得
        for item in self.view.scene().items():
            if isinstance(item, TriangleItem):
                item.highlight_selected_side(None)
                item.setOpacity(1.0)  # 透明度をリセット
                pen = item.pen()
                pen.setWidth(1)  # 線の太さをリセット
                pen.setColor(item.triangle_data.color)  # 色をリセット
                item.setPen(pen)
        
        # 内部の選択状態もリセット
        self.selected_parent_number = -1
        self.selected_side_index = -1
        self.selected_info_label.setText("なし")
        self.update_triangle_button.setEnabled(False)
        
        # コンボボックスの選択をリセット
        self.triangle_combo.blockSignals(True)
        self.triangle_combo.setCurrentIndex(0)  # "---" を選択
        self.triangle_combo.blockSignals(False)
        
        # ステータスバーをクリア
        self.statusBar().showMessage("選択をクリアしました")

    def scene_mouse_release_event(self, event):
        """シーンのマウスリリースイベント処理（背景クリック処理を含む）"""
        # クリックされたアイテムを取得
        clicked_items = self.view.scene().items(event.scenePos())
        
        if clicked_items:
            # 最前面のアイテムから順に処理
            for item in clicked_items:
                # GraphicsTextItemの処理（三角形番号クリック）
                if isinstance(item, QGraphicsTextItem) and item.data(0) is not None:
                    triangle_number = item.data(0)
                    if isinstance(triangle_number, int):
                        # 三角形番号をクリックした場合、その三角形を選択
                        logging.debug(f"三角形番号 {triangle_number} をクリック")
                        self.handle_triangle_selected(triangle_number)
                        event.accept()
                        return
                # その他既存の処理（寸法のテキストや背景クリック）
                if isinstance(item, QGraphicsSimpleTextItem) and item.data(0) is not None:
                    # 三角形番号と辺インデックスを取得
                    side_index = item.data(0)
                    triangle_info = item.data(1)
                    
                    if triangle_info is not None and side_index is not None:
                        # 三角形の情報から、対応する三角形の番号を見つける
                        triangle_number = self.find_triangle_by_info(triangle_info)
                        
                        if triangle_number is not None:
                            # デバッグ出力
                            logging.debug(f"寸法テキスト/背景クリック: 三角形={triangle_info}, 辺={side_index}")
                            # 辺を選択状態にする
                            logging.debug(f"選択処理を実行: 三角形 {triangle_info} の辺 {side_index}")
                            self.handle_side_clicked(triangle_number, side_index)
                            event.accept()
                            return
                elif isinstance(item, QGraphicsRectItem) and item.data(0) is not None:
                    # QGraphicsRectItemは異なるデータ構造を持っている可能性がある
                    # 直接辺と三角形の情報を取得できるか試みる
                    text_item = item.data(0)
                    triangle_number = item.data(1)
                    
                    # text_itemがQGraphicsSimpleTextItemかチェック
                    if isinstance(text_item, QGraphicsSimpleTextItem) and triangle_number is not None:
                        side_index = text_item.data(0)
                        if side_index is not None:
                            # デバッグ出力
                            logging.debug(f"寸法テキストの背景クリック: 三角形={triangle_number}, 辺={side_index}")
                            # 辺を選択状態にする
                            logging.debug(f"選択処理を実行: 三角形 {triangle_number} の辺 {side_index}")
                            self.handle_side_clicked(triangle_number, side_index)
                            event.accept()
                            return
        else:
            # 背景クリック - すべての選択をクリア
            logging.debug("背景クリック: すべての選択をクリア")
            self.clear_all_highlights()
        
        # 親クラスの処理を呼び出す
        QGraphicsScene.mouseReleaseEvent(self.view.scene(), event)

    def find_triangle_by_info(self, triangle_info):
        """三角形情報から三角形番号を見つける"""
        # triangle_infoが整数の場合、そのまま返す（すでに三角形番号）
        if isinstance(triangle_info, int):
            return triangle_info
        
        # triangle_infoが辞書でない場合、処理できない
        if not isinstance(triangle_info, dict):
            logging.debug(f"三角形情報が辞書形式ではありません: {type(triangle_info)}")
            return None
        
        # 主要な情報（角度と中心点）を使用して一致する三角形を検索
        for i, triangle in enumerate(self.triangle_list):
            if triangle and i > 0:  # インデックス0は未使用なので1からスタート
                # 三角形の中心点と角度を取得
                angle = triangle.angle_deg
                mid_x = (triangle.points[0].x() + triangle.points[1].x() + triangle.points[2].x()) / 3
                mid_y = (triangle.points[0].y() + triangle.points[1].y() + triangle.points[2].y()) / 3
                
                # 数値の比較は許容誤差を考慮する
                if (abs(angle - triangle_info.get('angle', 0)) < 0.001 and
                    abs(mid_x - triangle_info.get('mid_x', 0)) < 0.001 and
                    abs(mid_y - triangle_info.get('mid_y', 0)) < 0.001):
                    return i
        
        return None

    def on_triangle_selected(self, index):
        """コンボボックスから三角形が選択されたときの処理"""
        # 選択された三角形番号を取得
        triangle_number = self.triangle_combo.currentData()
        
        # 無効な選択の場合は何もしない
        if triangle_number == -1:
            return
        
        # 三角形を取得
        triangle = self.get_triangle_by_number(triangle_number)
        if not triangle:
            return
        
        # 選択情報を更新（辺は選択されていない状態）
        self.selected_parent_number = triangle_number
        self.selected_side_index = -1  # 辺は選択されていない
        
        # 三角形の情報をフォームに反映
        self.new_len_a_input.setText(f"{triangle.lengths[0]:.1f}")
        self.new_len_b_input.setText(f"{triangle.lengths[1]:.1f}")
        self.new_len_c_input.setText(f"{triangle.lengths[2]:.1f}")
        
        # 選択情報を表示
        self.selected_info_label.setText(f"三角形 {triangle_number}")
        
        # 更新ボタンを有効化
        self.update_triangle_button.setEnabled(True)
        
        # シーン内の三角形を選択状態にする（辺は選択されない）
        for item in self.view.scene().items():
            if isinstance(item, TriangleItem):
                if item.triangle_data.number == triangle_number:
                    # 選択された三角形を強調表示（辺は選択しない）
                    item.setOpacity(1.0)
                    pen = item.pen()
                    pen.setWidth(2)
                    pen.setColor(QColor(255, 0, 0))  # 赤色で強調
                    item.setPen(pen)
                else:
                    # 他の三角形は通常表示
                    item.setOpacity(0.7)
                    pen = item.pen()
                    pen.setWidth(1)
                    pen.setColor(item.triangle_data.color)
                    item.setPen(pen)
        
        # 詳細情報をステータスバーに表示
        self.statusBar().showMessage(f"三角形 {triangle_number} を選択しました（辺は選択されていません）")

    def update_triangle_combo(self):
        """三角形選択コンボボックスを更新"""
        # 現在の選択を保存
        current_selection = self.triangle_combo.currentData()
        
        # コンボボックスをクリア
        self.triangle_combo.blockSignals(True)  # シグナルを一時停止
        self.triangle_combo.clear()
        self.triangle_combo.addItem("---", -1)  # デフォルト選択なし
        
        # 三角形リストを反復処理
        for triangle in sorted(self.triangle_list, key=lambda t: t.number):
            if triangle.number > 0:  # 有効な三角形番号のみ
                self.triangle_combo.addItem(f"三角形 {triangle.number}", triangle.number)
        
        # 前の選択を復元（可能な場合）
        if current_selection != -1:
            index = self.triangle_combo.findData(current_selection)
            if index >= 0:
                self.triangle_combo.setCurrentIndex(index)
            else:
                self.triangle_combo.setCurrentIndex(0)  # デフォルト選択
        
        self.triangle_combo.blockSignals(False)  # シグナルを再開

    def handle_triangle_selected(self, triangle_number):
        """三角形が選択されたときの処理"""
        # 選択情報を更新（辺は選択されていない状態）
        self.selected_parent_number = triangle_number
        self.selected_side_index = -1  # 辺は選択されていない
        
        # 三角形を取得
        triangle = self.get_triangle_by_number(triangle_number)
        if not triangle:
            return
        
        # 三角形の情報をフォームに反映
        self.new_len_a_input.setText(f"{triangle.lengths[0]:.1f}")
        self.new_len_b_input.setText(f"{triangle.lengths[1]:.1f}")
        self.new_len_c_input.setText(f"{triangle.lengths[2]:.1f}")
        
        # 選択情報を表示
        self.selected_info_label.setText(f"三角形 {triangle_number}")
        
        # 更新ボタンを有効化
        self.update_triangle_button.setEnabled(True)
        
        # コンボボックスの選択も更新
        self.triangle_combo.blockSignals(True)  # シグナルを一時停止して再帰呼び出しを防止
        index = self.triangle_combo.findData(triangle_number)
        if index >= 0:
            self.triangle_combo.setCurrentIndex(index)
        self.triangle_combo.blockSignals(False)  # シグナルを再開
        
        # シーン内の三角形を選択状態にする（辺は選択されない）
        for item in self.view.scene().items():
            if isinstance(item, TriangleItem):
                if item.triangle_data.number == triangle_number:
                    # 選択された三角形を強調表示（辺は選択しない）
                    item.setOpacity(1.0)
                    pen = item.pen()
                    pen.setWidth(2)
                    pen.setColor(QColor(255, 0, 0))  # 赤色で強調
                    item.setPen(pen)
                else:
                    # 他の三角形は通常表示
                    item.setOpacity(0.7)
                    pen = item.pen()
                    pen.setWidth(1)
                    pen.setColor(item.triangle_data.color)
                    item.setPen(pen)
        
        # 詳細情報をステータスバーに表示
        self.statusBar().showMessage(f"三角形 {triangle_number} を選択しました")

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    window = TriangleManagerWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 