#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
テキスト配置のテスト

DXFファイル上のテキスト表示に関する様々な設定を試験するスクリプト
フォント、サイズ、配置、回転などの設定をテストします
"""

import os
import sys
import math
from pathlib import Path

# パスを追加して親ディレクトリのモジュールを参照できるようにする
sys.path.insert(0, str(Path(__file__).parent.parent))

# PySide6のインポート
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QPushButton, QComboBox, QSlider, QDoubleSpinBox,
    QGraphicsTextItem, QColorDialog, QFontDialog, QGraphicsView
)
from PySide6.QtGui import (
    QFont, QColor, QPen, QBrush, QTransform, QPainter
)
from PySide6.QtCore import (
    Qt, QPointF, QRectF
)

class TextPlacementTest(QMainWindow):
    """テキスト配置テスト用ウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("テキスト配置テスト")
        self.resize(1000, 800)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # シーンとビュー
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        main_layout.addWidget(self.view, 1)
        
        # コントロールレイアウト
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)
        
        # テキスト入力
        text_layout = QVBoxLayout()
        controls_layout.addLayout(text_layout)
        
        text_layout.addWidget(QLabel("テキスト:"))
        self.text_input = QComboBox()
        self.text_input.setEditable(True)
        self.text_input.addItems(["サンプルテキスト", "Hello World", "テスト 123", "あいうえお", "漢字も表示"])
        self.text_input.currentTextChanged.connect(self.update_text)
        text_layout.addWidget(self.text_input)
        
        # フォント設定
        font_layout = QVBoxLayout()
        controls_layout.addLayout(font_layout)
        
        self.font_button = QPushButton("フォント選択")
        self.font_button.clicked.connect(self.select_font)
        font_layout.addWidget(self.font_button)
        
        self.current_font = QFont("Arial", 12)
        self.font_label = QLabel("Arial, 12pt")
        font_layout.addWidget(self.font_label)
        
        # 色設定
        color_layout = QVBoxLayout()
        controls_layout.addLayout(color_layout)
        
        self.color_button = QPushButton("色選択")
        self.color_button.clicked.connect(self.select_color)
        color_layout.addWidget(self.color_button)
        
        self.current_color = QColor(0, 0, 0)  # 黒
        self.color_label = QLabel("RGB: 0,0,0")
        color_layout.addWidget(self.color_label)
        
        # 回転設定
        rotation_layout = QVBoxLayout()
        controls_layout.addLayout(rotation_layout)
        
        rotation_layout.addWidget(QLabel("回転角度:"))
        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.update_rotation)
        rotation_layout.addWidget(self.rotation_slider)
        
        self.rotation_label = QLabel("0°")
        rotation_layout.addWidget(self.rotation_label)
        
        # 位置設定
        position_layout = QVBoxLayout()
        controls_layout.addLayout(position_layout)
        
        position_layout.addWidget(QLabel("X位置:"))
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-500, 500)
        self.x_spin.setValue(0)
        self.x_spin.setSingleStep(10)
        self.x_spin.valueChanged.connect(self.update_position)
        position_layout.addWidget(self.x_spin)
        
        position_layout.addWidget(QLabel("Y位置:"))
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-500, 500)
        self.y_spin.setValue(0)
        self.y_spin.setSingleStep(10)
        self.y_spin.valueChanged.connect(self.update_position)
        position_layout.addWidget(self.y_spin)
        
        # 配置基準点設定
        anchor_layout = QVBoxLayout()
        controls_layout.addLayout(anchor_layout)
        
        anchor_layout.addWidget(QLabel("配置基準点:"))
        self.anchor_combo = QComboBox()
        self.anchor_combo.addItems([
            "左上", "上", "右上", 
            "左", "中央", "右", 
            "左下", "下", "右下"
        ])
        self.anchor_combo.setCurrentIndex(4)  # デフォルトは中央
        self.anchor_combo.currentIndexChanged.connect(self.update_anchor)
        anchor_layout.addWidget(self.anchor_combo)
        
        # リセットボタン
        reset_layout = QVBoxLayout()
        controls_layout.addLayout(reset_layout)
        
        self.reset_button = QPushButton("リセット")
        self.reset_button.clicked.connect(self.reset_view)
        reset_layout.addWidget(self.reset_button)
        
        self.create_reference_grid()
        self.create_text_item()
        self.reset_view()
    
    def create_reference_grid(self):
        """参照用グリッドを作成"""
        # グリッドの線
        grid_pen = QPen(QColor(200, 200, 200), 1)
        grid_pen.setCosmetic(True)
        
        # 細かいグリッド
        for i in range(-500, 501, 50):
            self.scene.addLine(-500, i, 500, i, grid_pen)
            self.scene.addLine(i, -500, i, 500, grid_pen)
        
        # 主要な軸
        axis_pen = QPen(QColor(100, 100, 100), 2)
        axis_pen.setCosmetic(True)
        
        # X軸
        self.scene.addLine(-500, 0, 500, 0, axis_pen)
        # Y軸
        self.scene.addLine(0, -500, 0, 500, axis_pen)
        
        # 原点マーカー
        origin_pen = QPen(QColor(255, 0, 0), 2)
        origin_pen.setCosmetic(True)
        self.scene.addEllipse(-5, -5, 10, 10, origin_pen)
        
        # 軸ラベル
        axis_font = QFont()
        axis_font.setPointSize(10)
        
        x_label = self.scene.addText("X")
        x_label.setFont(axis_font)
        x_label.setPos(480, 10)
        
        y_label = self.scene.addText("Y")
        y_label.setFont(axis_font)
        y_label.setPos(10, -480)
    
    def create_text_item(self):
        """テキストアイテムを作成"""
        self.text_item = QGraphicsTextItem("サンプルテキスト")
        self.text_item.setFont(self.current_font)
        self.text_item.setDefaultTextColor(self.current_color)
        self.scene.addItem(self.text_item)
        
        # テキストの位置をデフォルト値でセット
        self.update_position()
    
    def update_text(self):
        """テキストを更新"""
        self.text_item.setPlainText(self.text_input.currentText())
        self.update_anchor()  # アンカーポイントに応じて位置を再調整
    
    def select_font(self):
        """フォント選択ダイアログ"""
        font_dialog = QFontDialog(self.current_font, self)
        if font_dialog.exec():
            self.current_font = font_dialog.selectedFont()
            self.text_item.setFont(self.current_font)
            self.font_label.setText(f"{self.current_font.family()}, {self.current_font.pointSize()}pt")
            self.update_anchor()  # テキストサイズが変わったのでアンカーポイントを再調整
    
    def select_color(self):
        """色選択ダイアログ"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.text_item.setDefaultTextColor(self.current_color)
            self.color_label.setText(f"RGB: {color.red()},{color.green()},{color.blue()}")
    
    def update_rotation(self):
        """回転角度を更新"""
        angle = self.rotation_slider.value()
        self.rotation_label.setText(f"{angle}°")
        
        # テキストアイテムの回転を更新
        # QGraphicsTextItemは回転をサポートしていないため、トランスフォームを使用
        transform = QTransform()
        
        # テキストのバウンディングレクトを取得して中心を見つける
        rect = self.text_item.boundingRect()
        center = rect.center()
        
        # 中心を原点とした回転を設定
        transform.translate(center.x(), center.y())
        transform.rotate(angle)
        transform.translate(-center.x(), -center.y())
        
        self.text_item.setTransform(transform)
        
        # 位置が回転で変わるため、アンカーポイント位置を再調整
        self.update_anchor()
    
    def update_position(self):
        """位置を更新"""
        x = self.x_spin.value()
        y = self.y_spin.value()
        
        # 単純な位置設定（アンカーポイントは別途処理）
        self.text_item.setPos(x, y)
        
        # アンカーポイントに基づいて調整
        self.update_anchor()
    
    def update_anchor(self):
        """アンカーポイント（基準点）に応じてテキスト位置を調整"""
        # 現在の表示位置を取得
        pos = QPointF(self.x_spin.value(), self.y_spin.value())
        
        # テキストのバウンディングレクトを取得
        rect = self.text_item.boundingRect()
        width = rect.width()
        height = rect.height()
        
        # アンカーポイントのインデックス（0-8）
        anchor_idx = self.anchor_combo.currentIndex()
        
        # X方向のオフセット（0:左, 1:中央, 2:右）
        x_offset = (anchor_idx % 3) / 2.0
        
        # Y方向のオフセット（0:上, 1:中央, 2:下）
        y_offset = (anchor_idx // 3) / 2.0
        
        # オフセットを適用
        offset_x = -width * x_offset
        offset_y = -height * y_offset
        
        # 位置を調整（元の指定位置 + オフセット）
        self.text_item.setPos(pos.x() + offset_x, pos.y() + offset_y)
    
    def reset_view(self):
        """ビューをリセット（全体表示）"""
        self.view.resetTransform()
        self.view.setSceneRect(self.scene.itemsBoundingRect())
        self.view.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.view.scale(0.9, 0.9)  # 少し余白を持たせる

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    window = TextPlacementTest()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 