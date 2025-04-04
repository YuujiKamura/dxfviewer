#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ビュー操作ユーティリティ

QGraphicsViewの操作に関する純粋関数を提供します。
"""

from PySide6.QtWidgets import QGraphicsView, QApplication
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter
import logging

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

def center_view_on_entities(view, items_rect=None, keep_aspect_ratio=True):
    """
    エンティティの範囲の中心を画面中央に表示する純粋関数（シンプル版）
    
    Args:
        view: 対象のQGraphicsViewインスタンス
        items_rect: エンティティの範囲（Noneの場合はscene().itemsBoundingRect()を使用）
        keep_aspect_ratio: アスペクト比を維持するかどうか
        
    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse
    """
    # シーンがなければ失敗
    if not view.scene():
        logger.warning("シーンがないためビューの中心化ができません")
        return False
    
    # エンティティの範囲を取得
    if items_rect is None:
        items_rect = view.scene().itemsBoundingRect()
    
    # 範囲が空であれば失敗
    if items_rect.isEmpty():
        logger.warning("エンティティがないためビューの中心化ができません")
        return False
    
    try:
        # デバッグログ
        logger.debug("===== シンプル中心化処理 =====")
        logger.debug(f"アイテム範囲: {items_rect}")
        item_center = items_rect.center()
        logger.debug(f"アイテム中心点: {item_center}")
        
        # トランスフォームをリセット
        view.resetTransform()
        
        # ビューポートのサイズを記録
        viewport_size = view.viewport().size()
        logger.debug(f"ビューポートサイズ: {viewport_size}")
        
        # アンカーを設定
        view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        # アスペクト比の設定
        aspect_mode = Qt.AspectRatioMode.KeepAspectRatio if keep_aspect_ratio else Qt.AspectRatioMode.IgnoreAspectRatio
        
        # 表示を全体に合わせる
        view.fitInView(items_rect, aspect_mode)
        
        # マージンを追加（95%）
        view.scale(0.95, 0.95)
        
        # 中央に配置
        view.centerOn(item_center)
        
        # イベント処理を行って表示を更新
        QApplication.processEvents()
        view.viewport().update()
        QApplication.processEvents()
        
        # 中心位置の確認
        viewport_rect = view.viewport().rect()
        final_center = view.mapToScene(viewport_rect.center())
        error_x = abs(item_center.x() - final_center.x())
        error_y = abs(item_center.y() - final_center.y())
        
        logger.debug(f"最終中心: {final_center}")
        logger.debug(f"中心誤差: X={error_x:.2f}, Y={error_y:.2f}")
        
        if error_x > 10.0 or error_y > 10.0:
            logger.warning(f"中心化誤差が大きいです: X={error_x:.2f}, Y={error_y:.2f}")
        else:
            logger.debug("中心化成功: 誤差は許容範囲内です")
        
        return True
    
    except Exception as e:
        logger.error(f"ビューの中心化中にエラーが発生: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def configure_view_for_cad(view):
    """
    QGraphicsViewをCAD表示に最適化する純粋関数
    
    Args:
        view: 対象のQGraphicsViewインスタンス
        
    Returns:
        None
    """
    # スクロールバーを非表示（CAD的な操作のため）
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    # パン操作用の設定
    view.setDragMode(QGraphicsView.DragMode.NoDrag)  # 独自パン処理のため標準ドラッグは無効化
    view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
    
    # 描画品質と最適化設定
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    # より効率的な描画モード（必要な部分だけの更新）
    view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
    
    # パフォーマンス向上のための設定
    view.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
    view.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
    view.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
    
    logger.debug("ビューをCAD表示用に設定しました")

def request_viewport_update(view):
    """
    ビューポートの更新を明示的に要求する純粋関数
    
    パン・ズーム操作後に呼び出すことで、表示の更新を確実に行う
    
    Args:
        view: 更新を要求するQGraphicsViewインスタンス
        
    Returns:
        None
    """
    if view and view.viewport():
        view.viewport().update()
        logger.debug("ビューポートの更新を要求しました") 