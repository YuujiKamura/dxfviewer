#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyQt5を使用したパン・ズーム操作のサンプル

Tkinterと比較して、PyQtではパン操作やズーム操作が簡単に実装できることを示します。
"""

import sys
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                            QGraphicsScene, QGraphicsTextItem, 
                            QGraphicsLineItem, QGraphicsEllipseItem, QVBoxLayout,
                            QWidget, QPushButton, QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QColor, QFont, QBrush, QPainter


class DxfGraphicsView(QGraphicsView):
    """
    DXFファイルを表示するためのカスタムQGraphicsView
    パン操作とズーム操作を実装
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        
        # ドラッグによるパン操作を有効化
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        
        # マウストラッキングとフォーカスポリシーを設定
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # アンチエイリアスとスムーズな描画
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | 
                          QPainter.SmoothPixmapTransform)
        
        # スクロールバーを非表示に
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # ズーム機能に必要な変数
        self.zoom_factor = 1.0  # 拡大率
        self.current_zoom = 1.0  # 現在のズーム率
        
        # シーンの設定
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # 原点マーカーを描画
        self._draw_origin_marker()
    
    def wheelEvent(self, event):
        """マウスホイールイベントによるズーム処理"""
        # ズーム係数を計算（ホイールの回転方向による）
        zoom_in = event.angleDelta().y() > 0
        
        # ズームイン/アウトに応じて係数を決定
        if zoom_in:
            factor = self.zoom_factor
        else:
            factor = 1.0 / self.zoom_factor
        
        # ズーム係数が一定範囲内になるように制限
        self.current_zoom *= factor
        
        # 最小・最大ズームを制限
        if self.current_zoom < 0.01:
            self.current_zoom = 0.01
            return
        elif self.current_zoom > 100.0:
            self.current_zoom = 100.0
            return
        
        # マウス位置を中心にしてビューをスケーリング
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(factor, factor)
        
        # ズーム係数をステータスバーに表示（メインウィンドウがあれば）
        if hasattr(self.parent(), 'statusBar'):
            self.parent().statusBar().showMessage(f"ズーム: {self.current_zoom:.2f}x")
    
    def _draw_origin_marker(self):
        """原点（0,0）を示すマーカーを描画"""
        # X軸（赤）
        x_axis = QGraphicsLineItem(-100, 0, 100, 0)
        x_axis.setPen(QPen(Qt.red, 1))
        self.scene.addItem(x_axis)
        
        # Y軸（緑）
        y_axis = QGraphicsLineItem(0, -100, 0, 100)
        y_axis.setPen(QPen(Qt.green, 1))
        self.scene.addItem(y_axis)
        
        # 原点の円（青）
        origin_circle = QGraphicsEllipseItem(-5, -5, 10, 10)
        origin_circle.setPen(QPen(Qt.blue, 1))
        origin_circle.setBrush(QBrush(QColor(0, 0, 255, 100)))
        self.scene.addItem(origin_circle)
        
        # 座標ラベル
        coord_text = QGraphicsTextItem("(0,0)")
        coord_text.setPos(10, 10)
        coord_text.setDefaultTextColor(Qt.blue)
        self.scene.addItem(coord_text)
    
    def reset_view(self):
        """ビューをリセット"""
        self.resetTransform()
        self.current_zoom = 1.0
        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.centerOn(0, 0)
    
    def clear_all(self):
        """すべてのアイテムを削除"""
        self.scene.clear()
        self._draw_origin_marker()


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 パン・ズームサンプル")
        self.resize(800, 600)
        
        # 中央ウィジェットを作成
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # レイアウト設定
        main_layout = QVBoxLayout(central_widget)
        
        # DXF表示用のビュー
        self.graphics_view = DxfGraphicsView(self)
        main_layout.addWidget(self.graphics_view)
        
        # 下部のボタン配置
        button_layout = QHBoxLayout()
        
        # リセットボタン
        reset_button = QPushButton("ビューをリセット")
        reset_button.clicked.connect(self.graphics_view.reset_view)
        button_layout.addWidget(reset_button)
        
        # 説明ラベル
        help_label = QLabel("マウスドラッグ: パン操作 / マウスホイール: ズーム操作")
        button_layout.addWidget(help_label)
        
        main_layout.addLayout(button_layout)
        
        # ステータスバー
        self.statusBar().showMessage("準備完了")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 