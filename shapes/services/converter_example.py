#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
使用例: 既存のTriangleDataと新しいTriangleShapeの変換

このモジュールは、アダプターを使用して既存のTriangleDataと
新しいTriangleShapeの間で変換を行う方法を示します。
"""

import sys
import logging
from PySide6.QtCore import QPointF
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView

# 既存のクラス
from triangle_ui.triangle_data import TriangleData
from triangle_ui.triangle_graphics_item import add_triangle_item_to_scene

# 新しいクラス
from shapes.geometry.triangle_shape import TriangleData as ShapeTriangleData
from shapes.services.shape_adapter import TriangleAdapter

# ロガー設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_sample_triangle_data():
    """サンプルTriangleDataを作成"""
    return TriangleData(
        a=100.0,
        b=120.0,
        c=150.0,
        p_ca=QPointF(100, 100),
        angle_deg=0.0,
        number=1
    )

def create_sample_triangle_shape():
    """サンプルTriangleShapeを作成"""
    return TriangleShape(
        a=100.0,
        b=120.0,
        c=150.0,
        position=QPointF(300, 100),
        angle_deg=0.0,
        number=2
    )

def print_triangle_info(triangle, name):
    """三角形の情報を表示（TriangleDataかTriangleShapeかに関わらず）"""
    logger.info(f"{name} - 番号: {triangle.number}")
    logger.info(f"{name} - 辺の長さ: A={triangle.lengths[0]}, B={triangle.lengths[1]}, C={triangle.lengths[2]}")
    logger.info(f"{name} - 基準点: ({triangle.points[0].x()}, {triangle.points[0].y()})")
    logger.info(f"{name} - 角度: {triangle.angle_deg}")

def main():
    """アダプターの使用例"""
    app = QApplication(sys.argv)
    
    # メインウィンドウとシーンの作成
    window = QMainWindow()
    window.setWindowTitle("三角形変換デモ")
    window.resize(800, 600)
    
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    window.setCentralWidget(view)
    
    # サンプルTriangleData作成
    tri_data = create_sample_triangle_data()
    print_triangle_info(tri_data, "TriangleData")
    
    # TriangleDataをシーンに追加
    logger.info("TriangleDataをシーンに追加")
    add_triangle_item_to_scene(scene, tri_data)
    
    # TriangleDataからTriangleShapeに変換
    logger.info("TriangleDataからTriangleShapeに変換")
    tri_shape = TriangleAdapter.triangle_data_to_shape(tri_data)
    print_triangle_info(tri_shape, "変換されたTriangleShape")
    
    # TriangleShapeから新しいTriangleDataに変換
    logger.info("TriangleShapeから新しいTriangleDataに変換")
    new_tri_data = TriangleAdapter.triangle_shape_to_data(tri_shape, TriangleData)
    new_tri_data.points[0] = QPointF(new_tri_data.points[0].x() + 200, new_tri_data.points[0].y() + 100)
    new_tri_data.calculate_points()
    print_triangle_info(new_tri_data, "変換されたTriangleData")
    
    # 変換された新しいTriangleDataをシーンに追加
    logger.info("変換された新しいTriangleDataをシーンに追加")
    add_triangle_item_to_scene(scene, new_tri_data)
    
    # シーンをフィットさせる
    view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
    
    # ウィンドウを表示
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 