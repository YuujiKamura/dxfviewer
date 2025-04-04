#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF表示用のカスタムグラフィックスビュー

ズーム、パン、その他の操作機能を持つカスタムグラフィックスビューを提供します。
"""

import logging
from typing import Optional, Tuple

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QApplication
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent, QKeyEvent
from PySide6.QtCore import Qt, QPoint, QPointF, Signal

# ユーティリティのインポート
from ui_new.view_utils import center_view_on_entities, configure_view_for_cad, request_viewport_update

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
        
        # CAD表示用の設定を適用
        configure_view_for_cad(self)
        
        # 内部状態
        self._zoom_factor = 1.0  # 初期ズーム率
        self._pan_start_point = None  # パン開始位置
        self._is_panning = False  # パン中かどうか
        
        logger.debug("DxfGraphicsViewを初期化しました")
    
    def wheelEvent(self, event: QWheelEvent):
        """
        マウスホイールイベント - ズーム処理
        
        Args:
            event: ホイールイベント
        """
        # ホイールの回転方向を取得
        delta = event.angleDelta().y()
        
        # ズーム率を変更
        zoom_factor = 1.2  # ズーム倍率
        if delta > 0:
            # ズームイン
            self.scale(zoom_factor, zoom_factor)
            self._zoom_factor *= zoom_factor
        else:
            # ズームアウト
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)
            self._zoom_factor /= zoom_factor
        
        # ズーム率変更シグナルを発行
        self.zoom_changed.emit(self._zoom_factor)
        
        # ビューポートの更新を要求
        request_viewport_update(self)
        
        # イベントを消費
        event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        """
        マウスボタン押下イベント - パン開始
        
        Args:
            event: マウスイベント
        """
        # 左ボタンでパン開始
        if event.button() == Qt.LeftButton:
            self._pan_start_point = event.pos()
            self._is_panning = True
            self.setCursor(Qt.ClosedHandCursor)  # 手のひらカーソルに変更
            event.accept()
            return
        
        # それ以外は親クラスの処理を呼び出す
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """
        マウス移動イベント - パン処理
        
        Args:
            event: マウスイベント
        """
        # パン中の場合のみ処理
        if self._is_panning and self._pan_start_point:
            # 単純なマウス移動量を計算
            delta = event.pos() - self._pan_start_point
            
            # 新しい位置を記録
            self._pan_start_point = event.pos()
            
            # ビューを単純に移動 - QGraphicsViewの独自変換なしで直接移動
            self.translate(delta.x(), delta.y())
            
            # パンシグナルを発行
            self.view_panned.emit()
            
            event.accept()
            return
        
        # それ以外は親クラスの処理を呼び出す
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        マウスボタン解放イベント - パン終了
        
        Args:
            event: マウスイベント
        """
        # パン終了
        if self._is_panning and event.button() == Qt.LeftButton:
            self._is_panning = False
            self._pan_start_point = None
            self.setCursor(Qt.ArrowCursor)  # 標準カーソルに戻す
            
            # ビューポートの更新を要求
            request_viewport_update(self)
            
            event.accept()
            return
        
        # それ以外は親クラスの処理を呼び出す
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event: QKeyEvent):
        """
        キープレスイベント - ショートカットキー処理
        
        Args:
            event: キーイベント
        """
        # F キーで全体表示
        if event.key() == Qt.Key_F:
            self.fit_in_view()
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
        
        # Esc キーで選択解除
        if event.key() == Qt.Key_Escape:
            self.scene().clearSelection()
            event.accept()
            return
        
        # それ以外は親クラスの処理を呼び出す
        super().keyPressEvent(event)
    
    def fit_in_view(self):
        """シーンの内容に合わせてビューを調整"""
        if not self.scene():
            return
        
        rect = self.scene().itemsBoundingRect()
        if rect.isEmpty():
            return
        
        # ユーティリティ関数を使用してビューを中央に配置
        success = center_view_on_entities(self, rect)
        
        if success:
            # ズーム率を更新
            transform = self.transform()
            self._zoom_factor = (transform.m11() + transform.m22()) / 2.0
            
            # ズーム率変更シグナルを発行
            self.zoom_changed.emit(self._zoom_factor)
            
            logger.debug(f"ビューをシーンに合わせました: ズーム率 {self._zoom_factor:.2f}")
        else:
            logger.warning("ビューの調整に失敗しました")
    
    def zoom_in(self, factor: float = 1.2):
        """
        ズームイン
        
        Args:
            factor: ズーム倍率（デフォルト1.2倍）
        """
        self.scale(factor, factor)
        self._zoom_factor *= factor
        self.zoom_changed.emit(self._zoom_factor)
        
        # ビューポートの更新を要求
        request_viewport_update(self)
    
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
        
        # ビューポートの更新を要求
        request_viewport_update(self)
    
    def get_zoom_factor(self):
        """現在のズーム率を取得"""
        return self._zoom_factor 