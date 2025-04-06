#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleLabels - 三角形ラベル関連ユーティリティ

三角形の頂点ラベル、辺ラベル、寸法テキスト、番号ラベルなどの
作成・配置を行うユーティリティ関数を提供します。
"""

import math
import logging
from PySide6.QtWidgets import (
    QGraphicsTextItem, QGraphicsSimpleTextItem, QGraphicsRectItem,
    QGraphicsEllipseItem
)
from PySide6.QtGui import QPen, QColor, QBrush, QTransform
from PySide6.QtCore import Qt, QPointF

# ロガー設定
logger = logging.getLogger(__name__)

def create_vertex_labels(triangle_item, triangle_data):
    """三角形の頂点ラベルを作成"""
    vertices = triangle_data.points
    vertex_names = ["CA", "AB", "BC"]
    
    # 頂点位置のログ出力（デバッグ用）
    logger.debug(f"三角形 {triangle_data.number} の頂点: CA={vertices[0]}, AB={vertices[1]}, BC={vertices[2]}")
    
    for i, name in enumerate(vertex_names):
        vertex = vertices[i]
        # 頂点ラベルを追加
        text_item = QGraphicsTextItem(name, triangle_item)
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
    
    return vertex_names

def create_edge_labels(triangle_item, triangle_data, edge_definition):
    """辺の名前ラベルを作成"""
    for edge in edge_definition:
        edge_index = edge["index"]
        edge_name = edge["name"]
        
        # 直接頂点インデックスから両端点を取得
        start_idx, end_idx = edge["points_index"]
        p1 = triangle_data.points[start_idx]
        p2 = triangle_data.points[end_idx]
        
        # 辺の中点を計算
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2
        
        # 辺名ラベルを追加
        label_item = QGraphicsTextItem(edge_name, triangle_item)
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

def create_dimension_labels(triangle_item, triangle_data, edge_definition):
    """辺の寸法ラベルを作成し情報を返す"""
    dimension_items = []
    
    for edge in edge_definition:
        edge_index = edge["index"]
        edge_name = edge["name"]
        
        # 直接頂点インデックスから両端点を取得
        start_idx, end_idx = edge["points_index"]
        p1 = triangle_data.points[start_idx]
        p2 = triangle_data.points[end_idx]
        
        # 辺の中点を計算
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2
        
        # 辺の方向ベクトル
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        
        # 辺の角度を計算
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 辺の長さ
        edge_length = triangle_data.lengths[edge_index]
        
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
        dimension_items.append(dimension_info)
        
        # アイテムにデータを設定（クリック時の辺の特定用）
        dimension_text.setData(0, edge_index)  # 辺インデックスを保存
        dimension_text.setData(1, triangle_data.number)  # 三角形番号を保存
        bg_rect.setData(0, edge_index)  # 辺インデックスを保存
        bg_rect.setData(1, triangle_data.number)  # 三角形番号を保存
    
    return dimension_items

def create_triangle_number_label(scene, triangle_data):
    """三角形番号ラベルを作成してシーンに追加"""
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
    return label

def add_dimension_labels_to_scene(scene, dimension_items, dimension_font_size=6):
    """寸法ラベルをシーンに追加"""
    for dim_info in dimension_items:
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