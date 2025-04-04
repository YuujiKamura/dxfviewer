#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF表示用のカスタムグラフィックスビュー

ズーム、パン、その他の操作機能を持つカスタムグラフィックスビューを提供します。
"""

import logging
from typing import Optional, Tuple

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent
from PySide6.QtCore import Qt, QPoint, QPointF, Signal

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

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
        
        # ドラッグモード設定
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # 座標変換の設定
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        
        # スクロールバーポリシー
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # 内部状態
        self._zoom_factor = 1.0
        self._pan_start_point = None
        self._is_panning = False
        
        # ビューをリセット
        self.reset_view()
    
    def reset_view(self):
        """ビューをリセットして全体表示"""
        self.resetTransform()
        self._zoom_factor = 1.0
        self.zoom_changed.emit(self._zoom_factor)
        
        # シーンの内容に合わせてビューを調整
        if not self.scene().items():
            # アイテムがない場合はデフォルトのビュー範囲を設定
            self.setSceneRect(-500, -500, 1000, 1000)
        else:
            # アイテムがある場合はそれに合わせる
            self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)
            # 少し余裕を持たせる
            self.scale(0.9, 0.9)
            self._zoom_factor = 0.9
            self.zoom_changed.emit(self._zoom_factor)
    
    def zoom_in(self, factor: float = 1.2):
        """
        ズームイン
        
        Args:
            factor: ズーム倍率（デフォルト1.2倍）
        """
        self.scale(factor, factor)
        self._zoom_factor *= factor
        self.zoom_changed.emit(self._zoom_factor)
    
    def zoom_out(self, factor: float = 1.2):
        """
        ズームアウト
        
        Args:
            factor: ズーム倍率（デフォルト1.2倍）
        """
        factor_inv = 1.0 / factor
        self.scale(factor_inv, factor_inv)
        self._zoom_factor *= factor_inv
        self.zoom_changed.emit(self._zoom_factor)
    
    def set_zoom(self, factor: float):
        """
        ズーム倍率を直接設定
        
        Args:
            factor: 設定するズーム倍率
        """
        self.resetTransform()
        self.scale(factor, factor)
        self._zoom_factor = factor
        self.zoom_changed.emit(self._zoom_factor)
    
    def get_zoom(self) -> float:
        """現在のズーム倍率を取得"""
        return self._zoom_factor
    
    def wheelEvent(self, event: QWheelEvent):
        """
        マウスホイールイベントの処理
        
        Args:
            event: ホイールイベント
        """
        # Ctrlキーが押されている場合はデフォルトの動作（スクロール）
        if event.modifiers() & Qt.ControlModifier:
            super().wheelEvent(event)
            return
        
        # ホイールの回転に応じてズーム
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        
        event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        """
        マウスボタン押下イベントの処理
        
        Args:
            event: マウスイベント
        """
        # 左ボタンでパン開始
        if event.button() == Qt.LeftButton:
            self._pan_start_point = event.pos()
            self._is_panning = True
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """
        マウス移動イベントの処理
        
        Args:
            event: マウスイベント
        """
        # パン中の場合
        if self._is_panning and self._pan_start_point:
            # 移動量を計算
            delta = event.pos() - self._pan_start_point
            self._pan_start_point = event.pos()
            
            # ビューをスクロール
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            
            self.view_panned.emit()
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        マウスボタン解放イベントの処理
        
        Args:
            event: マウスイベント
        """
        # パン終了
        if self._is_panning and event.button() == Qt.LeftButton:
            self._is_panning = False
            self._pan_start_point = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        キー押下イベントの処理
        
        Args:
            event: キーイベント
        """
        # ESCキーで選択解除
        if event.key() == Qt.Key_Escape:
            self.scene().clearSelection()
            event.accept()
            return
        
        # F キーでビューをリセット（全体表示）
        if event.key() == Qt.Key_F:
            self.reset_view()
            event.accept()
            return
        
        # + キーでズームイン
        if event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoom_in()
            event.accept()
            return
        
        # - キーでズームアウト
        if event.key() == Qt.Key_Minus:
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
        """シーンのクリア"""
        self.scene().clear()
    
    def fit_scene_in_view(self):
        """シーンの内容に合わせてビューを調整"""
        if not self.scene().items():
            return
        
        self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)
        # 現在のズーム倍率を更新
        transform = self.transform()
        self._zoom_factor = (transform.m11() + transform.m22()) / 2.0
        self.zoom_changed.emit(self._zoom_factor)
