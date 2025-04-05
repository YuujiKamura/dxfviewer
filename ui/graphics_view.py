#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF表示用のカスタムグラフィックスビュー

ズーム、パン、その他の操作機能を持つカスタムグラフィックスビューを提供します。
simple_samples/pyside_pan_zoom_sample.pyと同様のロジックで実装。
"""

import math
import logging
from typing import Optional, Tuple, List

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QRubberBand
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent, QPen, QColor, QBrush, QFont, QTransform
from PySide6.QtCore import Qt, QPoint, QPointF, Signal, QRectF, QLineF

# ロガーの取得
logger = logging.getLogger('DXFViewer')

class DxfGraphicsView(QGraphicsView):
    """
    DXF表示用のカスタムグラフィックスビュー
    
    ズーム、パン、選択などの機能を提供します。
    """
    
    # シグナル定義
    zoom_changed = Signal(float)  # ズーム率が変更された時に発行
    view_panned = Signal()  # ビューがパンされた時に発行
    
    def __init__(self, scene: Optional[QGraphicsScene] = None):
        """
        グラフィックスビューの初期化
        
        Args:
            scene: 表示するグラフィックスシーン（省略可能）
        """
        if scene:
            super().__init__(scene)
        else:
            super().__init__()
            self.setScene(QGraphicsScene())
        
        # ビューの設定
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # ドラッグモード設定 - パン操作を有効にする
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # マウストラッキングとフォーカスポリシーを設定
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # ビューポート更新モード - パン操作をスムーズにする
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        
        # 座標変換の設定
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        # スクロールバーポリシー - スクロールバーを完全に非表示に
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 内部状態
        self.zoom_factor = 1.25  # 拡大率
        self.current_zoom = 1.0  # 現在のズーム率
        
        # デバッグ用のシーンレクト情報テキスト
        self.debug_text = None
        
        # キャッシュモードの設定 - キャッシュを無効化して描画エラーを防止
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        
        # ビューをリセット
        self.reset_view()
    
    def paintEvent(self, event):
        """
        ペイントイベントの処理
        
        QPainterを正しく初期化してQGraphicsViewの描画を実行
        """
        # ウィジェットが表示されていることを確認
        if not self.isVisible():
            return
        
        try:
            # キャッシュの一時的な無効化
            cache_mode = self.cacheMode()
            self.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
            
            # 親クラスのpaintEventを呼び出す
            super().paintEvent(event)
            
            # キャッシュを元に戻す
            self.setCacheMode(cache_mode)
        except Exception as e:
            # 描画エラーが発生した場合、ログに記録するだけで処理を続行
            logger.debug(f"描画中にエラーが発生: {str(e)}")
            
            # エラー発生時は最小限の処理で描画
            super().paintEvent(event)
    
    def reset_view(self):
        """ビューをリセットして全体表示"""
        self.resetTransform()
        self.current_zoom = 1.0
        self.zoom_changed.emit(self.current_zoom)
        
        # シーンの内容に合わせてビューを調整（シーンレクトは変更しない）
        self.fit_scene_in_view()
        
        # 画面の更新を要求
        self.viewport().update()
    
    def zoom_in(self, factor: float = 1.25):
        """
        ズームイン
        
        Args:
            factor: ズーム倍率（デフォルト1.25倍）
        """
        # ズーム係数が一定範囲内になるように制限
        self.current_zoom *= factor
        
        # 最小・最大ズームを制限
        if self.current_zoom < 0.01:
            factor = 0.01 / (self.current_zoom / factor)
            self.current_zoom = 0.01
        elif self.current_zoom > 100.0:
            factor = 100.0 / (self.current_zoom / factor)
            self.current_zoom = 100.0
            
        # マウス位置を中心にしてビューをスケーリング
        self.scale(factor, factor)
        self.zoom_changed.emit(self.current_zoom)
        
        # 画面の更新を要求
        self.viewport().update()
    
    def zoom_out(self, factor: float = 1.25):
        """
        ズームアウト
        
        Args:
            factor: ズーム倍率（デフォルト1.25倍）
        """
        self.zoom_in(1.0 / factor)
    
    def set_zoom(self, factor: float):
        """
        ズーム倍率を直接設定
        
        Args:
            factor: 設定するズーム倍率
        """
        self.resetTransform()
        self.scale(factor, factor)
        self.current_zoom = factor
        self.zoom_changed.emit(self.current_zoom)
        
        # 画面の更新を要求
        self.viewport().update()
    
    def get_zoom(self) -> float:
        """現在のズーム倍率を取得"""
        return self.current_zoom
    
    def wheelEvent(self, event: QWheelEvent):
        """
        マウスホイールイベントの処理
        
        Args:
            event: ホイールイベント
        """
        # ズーム係数を計算（ホイールの回転方向による）
        zoom_in = event.angleDelta().y() > 0
        
        # ズームイン/アウトに応じて処理
        if zoom_in:
            self.zoom_in()
        else:
            self.zoom_out()
        
        event.accept()
        
        # ズーム係数をステータスバーに表示（メインウィンドウがあれば）
        parent = self.parent()
        if hasattr(parent, 'statusBar') and callable(parent.statusBar):
            parent.statusBar().showMessage(f"ズーム: {self.current_zoom:.2f}x")
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        キー押下イベントの処理
        
        Args:
            event: キーイベント
        """
        # ESCキーで選択解除
        if event.key() == Qt.Key.Key_Escape:
            self.scene().clearSelection()
            event.accept()
            return
        
        # F キーでビューをリセット（全体表示）
        if event.key() == Qt.Key.Key_F:
            self.reset_view()
            event.accept()
            return
        
        # + キーでズームイン
        if event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
            event.accept()
            return
        
        # - キーでズームアウト
        if event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
            event.accept()
            return
        
        super().keyPressEvent(event)
    
    def scene_pos_from_mouse(self, mouse_pos: QPoint) -> QPointF:
        """
        マウス座標からシーン座標に変換
        
        Args:
            mouse_pos: マウス座標（ビュー上の位置）
            
        Returns:
            QPointF: シーン上の座標
        """
        return self.mapToScene(mouse_pos)
    
    def clear_scene(self):
        """シーンをクリア"""
        if self.scene():
            self.scene().clear()
        
        # 画面の更新を要求
        self.viewport().update()
    
    def initialize_view(self, items=None):
        """
        シーンを初期化し、大きな固定のシーンレクトを設定
        
        Args:
            items: アイテムのリスト（Noneの場合は全アイテム）
        """
        # 十分に大きなシーンレクトを設定（事実上無制限のパン）
        large_rect = QRectF(-100000, -100000, 200000, 200000)
        self.scene().setSceneRect(large_rect)
        
        # 現在のアイテムに合わせてビューをフィット
        self.fit_scene_in_view()
        
        logger.debug(f"ビュー初期化: シーンレクト {large_rect}, 現在のズーム {self.current_zoom:.2f}x")

    def fit_scene_in_view(self, extra_scale=0.8):
        """
        シーンの内容に合わせてビューを調整（シーンレクトは変更しない）
        
        Args:
            extra_scale: フィット後に適用する追加スケール係数（デフォルトは0.8 = ズームアウト）
        """
        if self.scene() and not self.scene().itemsBoundingRect().isEmpty():
            # アイテムの境界にフィット
            self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
            # スケールを調整して、より広い範囲を表示（ズームアウト）
            if extra_scale != 1.0:
                self.scale(extra_scale, extra_scale)
                self.current_zoom *= extra_scale
                self.zoom_changed.emit(self.current_zoom)
            
        # 画面の更新を要求
        self.viewport().update()
    
    def calculate_model_bounds(self, items: List[QGraphicsItem]):
        """
        アイテムのリストからモデル座標の境界を計算
        
        Args:
            items: アイテムのリスト
            
        Returns:
            tuple: (min_x, min_y, max_x, max_y)
        """
        if not items:
            return -100, -100, 100, 100  # デフォルト値
        
        # 初期値
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        
        # すべてのアイテムを走査して境界を更新
        for item in items:
            rect = item.sceneBoundingRect()
            min_x = min(min_x, rect.left())
            min_y = min(min_y, rect.top())
            max_x = max(max_x, rect.right())
            max_y = max(max_y, rect.bottom())
        
        # 無効な値の場合（アイテムが座標を持たない場合など）
        if min_x == float('inf') or min_y == float('inf') or max_x == float('-inf') or max_y == float('-inf'):
            return -100, -100, 100, 100
            
        return min_x, min_y, max_x, max_y
    
    def setup_scene_rect(self, items=None, margin_factor=5.0):
        """
        アイテムの表示範囲に基づいてシーンレクトを設定
        
        Args:
            items: アイテムのリスト（Noneの場合は全アイテム）
            margin_factor: 境界の拡張係数（デフォルトは5倍）
        """
        # アイテムリストの取得
        if items is None:
            items = self.scene().items()
        
        # アイテムからモデル境界を計算
        min_x, min_y, max_x, max_y = self.calculate_model_bounds(items)
        
        # 境界のサイズを計算
        width = max(max_x - min_x, 1.0)  # ゼロ除算防止
        height = max(max_y - min_y, 1.0)
        
        # 中心点を計算
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # 指定係数の余裕を持たせた範囲を計算
        scene_width = max(width * margin_factor, 1000)  # 最小幅
        scene_height = max(height * margin_factor, 1000)  # 最小高さ
        
        # シーンレクトを設定
        rect_x = center_x - scene_width/2
        rect_y = center_y - scene_height/2
        self.scene().setSceneRect(rect_x, rect_y, scene_width, scene_height)
        
        # シーンレクト境界線の描画（デバッグモード時）
        debug_mode = logger.getEffectiveLevel() <= logging.DEBUG
        if debug_mode:
            rect = self.scene().sceneRect()
            border_line = QPen(QColor(128, 128, 128), 1, Qt.PenStyle.DashLine)
            self.scene().addRect(rect, border_line)
            self.update_debug_text()
        
        # ログ出力
        logger.debug(f"シーンレクト設定: x={rect_x:.1f}, y={rect_y:.1f}, w={scene_width:.1f}, h={scene_height:.1f}")
        
        # 画面の更新を要求
        self.viewport().update()
        
        return self.scene().sceneRect()
    
    def update_debug_text(self):
        """シーンレクト情報のデバッグテキストを更新"""
        rect = self.scene().sceneRect()
        debug_info = (f"SceneRect: ({rect.x():.1f}, {rect.y():.1f})\n"
                     f"Size: {rect.width():.1f} x {rect.height():.1f}")
        
        # 既存のデバッグテキストを削除
        if self.debug_text:
            self.scene().removeItem(self.debug_text)
        
        # 新しいデバッグテキストを作成
        self.debug_text = QGraphicsTextItem(debug_info)
        self.debug_text.setPos(rect.x() + 10, rect.y() + 10)
        self.debug_text.setDefaultTextColor(QColor(0, 0, 128))
        self.scene().addItem(self.debug_text)
        
        # 画面の更新を要求
        self.viewport().update()
    
    # マウスイベント処理（パンのためのオーバーライド）
    def mouseMoveEvent(self, event: QMouseEvent):
        """
        マウス移動イベント処理
        
        パン操作を追跡し、シグナルを発行します。
        """
        # 親クラスのイベント処理を呼び出す
        super().mouseMoveEvent(event)
        
        # ドラッグモードがScrollHandDragで、マウスの左ボタンが押されている場合
        if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag and event.buttons() & Qt.MouseButton.LeftButton:
            # パン操作シグナルを発行
            self.view_panned.emit()
            
            # デバッグログ
            center = self.mapToScene(self.viewport().rect().center())
            viewport_rect = self.mapToScene(self.viewport().rect()).boundingRect()
            scene_rect = self.scene().sceneRect()
            
            # ビューポートがシーンレクトからはみ出ているか確認
            is_viewport_inside_x = (viewport_rect.left() >= scene_rect.left() and 
                                   viewport_rect.right() <= scene_rect.right())
            is_viewport_inside_y = (viewport_rect.top() >= scene_rect.top() and 
                                   viewport_rect.bottom() <= scene_rect.bottom())
            
            logger.debug(f"パン操作: 中心位置=({center.x():.1f}, {center.y():.1f})") 
            logger.debug(f"ビューポート境界: ({viewport_rect.left():.1f}, {viewport_rect.top():.1f}, {viewport_rect.width():.1f}, {viewport_rect.height():.1f})")
            logger.debug(f"シーンレクト境界: ({scene_rect.left():.1f}, {scene_rect.top():.1f}, {scene_rect.width():.1f}, {scene_rect.height():.1f})")
            logger.debug(f"ビューポート位置: X方向内={is_viewport_inside_x}, Y方向内={is_viewport_inside_y}") 