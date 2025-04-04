#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PySide6を使用したパン・ズーム操作のサンプル

PyQtとほぼ同等の機能ですが、Qt Companyが提供する公式Python版でLGPLライセンスです。
商用利用の際に適しています。
"""

import sys
import math
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                              QGraphicsScene, QGraphicsItem, QGraphicsTextItem, 
                              QGraphicsLineItem, QGraphicsEllipseItem, QVBoxLayout,
                              QWidget, QPushButton, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QFont, QBrush, QPainter


class DxfGraphicsView(QGraphicsView):
    """
    DXFファイルを表示するためのカスタムQGraphicsView
    パン操作とズーム操作を実装
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # PyQtとの違い: setRenderHintの引数がenumになった
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # ドラッグによるパン操作を有効化
        # PyQtとの違い: enumの使い方が異なる
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # マウストラッキングとフォーカスポリシーを設定
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # アンチエイリアスとスムーズな描画
        # PyQtとの違い: enumの扱いが異なる
        self.setRenderHints(QPainter.RenderHint.Antialiasing | 
                            QPainter.RenderHint.TextAntialiasing | 
                            QPainter.RenderHint.SmoothPixmapTransform)
        
        # スクロールバーを非表示に
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # ズーム機能に必要な変数
        self.zoom_factor = 1.25  # 拡大率
        self.current_zoom = 1.0  # 現在のズーム率
        
        # シーンの設定
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # デバッグ用のシーンレクト情報テキスト
        self.debug_text = None
        
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
        # PyQtとの違い: 列挙型の使い方が異なる
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.scale(factor, factor)
        
        # ズーム係数をステータスバーに表示（メインウィンドウがあれば）
        parent = self.parent()
        if hasattr(parent, 'statusBar') and callable(parent.statusBar):
            parent.statusBar().showMessage(f"ズーム: {self.current_zoom:.2f}x")
    
    def _draw_origin_marker(self):
        """原点（0,0）を示すマーカーを描画"""
        # X軸（赤）
        x_axis = QGraphicsLineItem(-100, 0, 100, 0)
        x_axis.setPen(QPen(Qt.GlobalColor.red, 1))
        self.scene.addItem(x_axis)
        
        # Y軸（緑）
        y_axis = QGraphicsLineItem(0, -100, 0, 100)
        y_axis.setPen(QPen(Qt.GlobalColor.green, 1))
        self.scene.addItem(y_axis)
        
        # 原点の円（青）
        origin_circle = QGraphicsEllipseItem(-5, -5, 10, 10)
        origin_circle.setPen(QPen(Qt.GlobalColor.blue, 1))
        origin_circle.setBrush(QBrush(QColor(0, 0, 255, 100)))
        self.scene.addItem(origin_circle)
        
        # 座標ラベル
        coord_text = QGraphicsTextItem("(0,0)")
        coord_text.setPos(10, 10)
        coord_text.setDefaultTextColor(Qt.GlobalColor.blue)
        self.scene.addItem(coord_text)
    
    def add_text(self, x, y, text, rotation=0, height=10, color=Qt.GlobalColor.black, 
               h_align=Qt.AlignmentFlag.AlignLeft, v_align=Qt.AlignmentFlag.AlignBottom):
        """
        テキストを追加（回転対応）
        
        Args:
            x, y: 座標
            text: テキスト内容
            rotation: 回転角度（度）
            height: フォントサイズ
            color: テキスト色
            h_align: 水平揃え位置
            v_align: 垂直揃え位置
        """
        # テキストアイテムを作成
        text_item = QGraphicsTextItem(text)
        
        # フォント設定
        font = QFont("Yu Gothic UI", height)
        text_item.setFont(font)
        
        # 色設定
        text_item.setDefaultTextColor(color)
        
        # 回転の中心点を設定
        text_item.setTransformOriginPoint(text_item.boundingRect().width() / 2, 
                                         text_item.boundingRect().height() / 2)
        
        # テキストを回転
        text_item.setRotation(rotation)
        
        # アンカーポイントに基づく位置調整
        text_width = text_item.boundingRect().width()
        text_height = text_item.boundingRect().height()
        
        # 水平位置の調整
        x_offset = 0
        if h_align == Qt.AlignmentFlag.AlignHCenter:
            x_offset = -text_width / 2
        elif h_align == Qt.AlignmentFlag.AlignRight:
            x_offset = -text_width
        
        # 垂直位置の調整
        y_offset = 0
        if v_align == Qt.AlignmentFlag.AlignVCenter:
            y_offset = -text_height / 2
        elif v_align == Qt.AlignmentFlag.AlignTop:
            y_offset = 0
        else:  # Bottom
            y_offset = -text_height
        
        # 位置を設定
        text_item.setPos(x + x_offset, y + y_offset)
        
        # シーンに追加
        self.scene.addItem(text_item)
        return text_item
    
    def add_circle(self, x, y, radius, color=Qt.GlobalColor.black):
        """円を追加"""
        circle = QGraphicsEllipseItem(x - radius, y - radius, radius * 2, radius * 2)
        circle.setPen(QPen(color, 1))
        self.scene.addItem(circle)
        return circle
    
    def add_line(self, x1, y1, x2, y2, color=Qt.GlobalColor.black):
        """線を追加"""
        line = QGraphicsLineItem(x1, y1, x2, y2)
        line.setPen(QPen(color, 1))
        self.scene.addItem(line)
        return line
    
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
    
    def calculate_model_bounds(self, entities):
        """
        エンティティのリストからモデル座標の境界を計算
        
        Args:
            entities: エンティティのリスト（x, y, radius などの属性を持つ）
            
        Returns:
            tuple: (min_x, min_y, max_x, max_y)
        """
        if not entities:
            return -100, -100, 100, 100  # デフォルト値
        
        # 初期値
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        # すべてのエンティティを走査して境界を更新
        for entity in entities:
            # QGraphicsItem から位置情報を取得
            if isinstance(entity, QGraphicsEllipseItem):
                rect = entity.rect()
                x = rect.x() + rect.width() / 2  # 円の中心X
                y = rect.y() + rect.height() / 2  # 円の中心Y
                radius = rect.width() / 2  # 円の半径
                
                min_x = min(min_x, x - radius)
                min_y = min(min_y, y - radius)
                max_x = max(max_x, x + radius)
                max_y = max(max_y, y + radius)
                
            elif isinstance(entity, QGraphicsLineItem):
                line = entity.line()
                x1, y1 = line.x1(), line.y1()
                x2, y2 = line.x2(), line.y2()
                
                min_x = min(min_x, x1, x2)
                min_y = min(min_y, y1, y2)
                max_x = max(max_x, x1, x2)
                max_y = max(max_y, y1, y2)
                
            elif isinstance(entity, QGraphicsTextItem):
                pos = entity.pos()
                rect = entity.boundingRect()
                x, y = pos.x(), pos.y()
                width, height = rect.width(), rect.height()
                
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + width)
                max_y = max(max_y, y + height)
        
        # 無効な値の場合（エンティティが座標を持たない場合など）
        if min_x == float('inf') or min_y == float('inf') or max_x == float('-inf') or max_y == float('-inf'):
            return -100, -100, 100, 100
            
        return min_x, min_y, max_x, max_y
    
    def setup_scene_rect(self, entities, margin_factor=5.0):
        """
        エンティティの表示範囲に基づいてシーンレクトを設定
        
        Args:
            entities: エンティティのリスト
            margin_factor: 境界の拡張係数（デフォルトは5倍）
        """
        # エンティティからモデル境界を計算
        min_x, min_y, max_x, max_y = self.calculate_model_bounds(entities)
        
        # 境界のサイズを計算
        width = max(max_x - min_x, 1.0)  # ゼロ除算防止
        height = max(max_y - min_y, 1.0)
        
        # 中心点を計算
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # 指定係数の余裕を持たせた範囲を計算
        scene_width = width * margin_factor
        scene_height = height * margin_factor
        
        # シーンレクトを設定
        rect_x = center_x - scene_width/2
        rect_y = center_y - scene_height/2
        self.scene.setSceneRect(rect_x, rect_y, scene_width, scene_height)
        
        # シーンレクト境界線の描画
        rect = self.scene.sceneRect()
        border_line = QPen(Qt.GlobalColor.darkGray, 1, Qt.PenStyle.DashLine)
        self.scene.addRect(rect, border_line)
        
        # デバッグ情報の更新
        self.update_debug_text()
        
        return rect
    
    def update_debug_text(self):
        """シーンレクト情報のデバッグテキストを更新"""
        rect = self.scene.sceneRect()
        debug_info = (f"SceneRect: ({rect.x():.1f}, {rect.y():.1f})\n"
                     f"Size: {rect.width():.1f} x {rect.height():.1f}")
        
        # 既存のデバッグテキストを削除
        if self.debug_text:
            self.scene.removeItem(self.debug_text)
        
        # 新しいデバッグテキストを作成
        self.debug_text = QGraphicsTextItem(debug_info)
        self.debug_text.setPos(rect.x() + 10, rect.y() + 10)
        self.debug_text.setDefaultTextColor(Qt.GlobalColor.darkBlue)
        self.scene.addItem(self.debug_text)


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 パン・ズームサンプル")
        self.resize(800, 600)
        
        # 中央ウィジェットを作成
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # レイアウト設定
        main_layout = QVBoxLayout(central_widget)
        
        # DXF表示用のビュー
        self.graphics_view = DxfGraphicsView(self)
        main_layout.addWidget(self.graphics_view)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        
        # テストパターン描画ボタン
        test_button = QPushButton("テストパターン描画")
        test_button.clicked.connect(self.draw_test_pattern)
        button_layout.addWidget(test_button)
        
        # リセットボタン
        reset_button = QPushButton("ビューをリセット")
        reset_button.clicked.connect(self.graphics_view.reset_view)
        button_layout.addWidget(reset_button)
        
        # クリアボタン
        clear_button = QPushButton("クリア")
        clear_button.clicked.connect(self.graphics_view.clear_all)
        button_layout.addWidget(clear_button)
        
        # ステータスバー
        self.statusBar().showMessage("準備完了")
        
        # 初期表示としてテストパターンを描画
        self.draw_test_pattern()
    
    def draw_test_pattern(self):
        """テストパターンを描画"""
        self.graphics_view.clear_all()
        
        # テスト用エンティティのリスト
        entities = []
        
        # 原点に十字線を描画
        entities.append(self.graphics_view.add_line(-100, 0, 100, 0, Qt.GlobalColor.red))
        entities.append(self.graphics_view.add_line(0, -100, 0, 100, Qt.GlobalColor.green))
        
        # 原点に円を描画
        entities.append(self.graphics_view.add_circle(0, 0, 10, Qt.GlobalColor.blue))
        
        # 原点にテキストを描画
        entities.append(self.graphics_view.add_text(0, 0, "(0,0)", 0, 10, Qt.GlobalColor.blue))
        
        # 円形に8つのマーカーとテキストを配置
        radius = 200
        for i in range(8):
            angle = math.radians(i * 45)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            # マーカー円
            entities.append(self.graphics_view.add_circle(x, y, 10, Qt.GlobalColor.darkRed))
            
            # テキスト
            rotation = i * 45
            entities.append(self.graphics_view.add_text(
                x, y, f"{rotation}° ({x:.1f}, {y:.1f})", 
                rotation, 10, Qt.GlobalColor.black
            ))
        
        # テストアイテムを追加（広い範囲に配置）
        for i in range(10):
            x = random.uniform(-500, 500)
            y = random.uniform(-500, 500)
            radius = random.uniform(5, 20)
            entities.append(self.graphics_view.add_circle(x, y, radius, Qt.GlobalColor.darkGreen))
        
        # シーンレクトを設定（エンティティの5倍の広さ）
        self.graphics_view.setup_scene_rect(entities, margin_factor=5.0)
        
        # ステータスバー更新
        rect = self.graphics_view.scene.sceneRect()
        self.statusBar().showMessage(
            f"テストパターン描画 - SceneRect: ({rect.x():.1f}, {rect.y():.1f}, {rect.width():.1f}, {rect.height():.1f})"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # PyQtとの違い: exec_はexecに変更
    sys.exit(app.exec()) 