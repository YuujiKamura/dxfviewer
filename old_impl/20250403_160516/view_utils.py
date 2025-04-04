#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ビュー操作ユーティリティ

QGraphicsViewの操作に関する純粋関数を提供します。
"""

from PySide6.QtWidgets import QGraphicsView, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
import logging

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

def center_view_on_entities(view, items_rect=None, keep_aspect_ratio=True):
    """
    エンティティの範囲の中心を画面中央に表示する純粋関数
    
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
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt, QPointF
        
        logger.debug("===== 強制センタリング処理 =====")
        logger.debug(f"アイテム範囲: {items_rect}")
        item_center = items_rect.center()
        logger.debug(f"アイテム中心点: {item_center}")
        
        # ビューポート情報を取得
        viewport_rect = view.viewport().rect()
        logger.debug(f"ビューポート範囲: {viewport_rect}")
        
        # スクロールバーポリシーを一時的に保存して変更
        h_policy_original = view.horizontalScrollBarPolicy()
        v_policy_original = view.verticalScrollBarPolicy()
        
        # スクロールバーを一時的に有効化（必要に応じて表示）
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # トランスフォームをリセット
        view.setTransformationAnchor(view.ViewportAnchor.AnchorViewCenter)
        view.setResizeAnchor(view.ViewportAnchor.AnchorViewCenter)
        view.resetTransform()
        
        # 表示領域にフィット
        aspect_mode = Qt.AspectRatioMode.KeepAspectRatio if keep_aspect_ratio else Qt.AspectRatioMode.IgnoreAspectRatio
        view.fitInView(items_rect, aspect_mode)
        
        # イベント処理を行ってトランスフォームを確定
        QApplication.processEvents()
        
        # マージン追加（95%）
        view.scale(0.95, 0.95)
        
        # ここが重要: まず通常の方法で中心に配置
        view.centerOn(item_center)
        
        # イベント処理
        QApplication.processEvents()
        
        # 中心座標を確認
        current_center = view.mapToScene(viewport_rect.center())
        error_x = abs(item_center.x() - current_center.x())
        error_y = abs(item_center.y() - current_center.y())
        
        logger.debug(f"centerOn後の中心: {current_center}")
        logger.debug(f"誤差: X={error_x:.2f}, Y={error_y:.2f}")
        
        # 誤差が大きい場合は強制的に視点を中心に移動
        if error_x > 10.0 or error_y > 10.0:
            logger.debug("誤差が大きいため強制的に中心を設定します")
            
            # 現在の変換行列（スケールなど）を保持
            transform = view.transform()
            
            # シーン座標からビュー座標への変換行列を取得
            matrix = view.transform()
            
            # ビューの中央座標
            view_center_x = viewport_rect.width() / 2
            view_center_y = viewport_rect.height() / 2
            
            # スクロールバーを直接操作
            h_scroll = view.horizontalScrollBar()
            v_scroll = view.verticalScrollBar()
            
            # 移動先のスクロール値を計算
            h_value = int(item_center.x() * transform.m11() - view_center_x)
            v_value = int(item_center.y() * transform.m22() - view_center_y)
            
            logger.debug(f"スクロール位置を設定: 水平={h_value}, 垂直={v_value}")
            
            # スクロールバーの位置を設定
            h_scroll.setValue(h_value)
            v_scroll.setValue(v_value)
            
            # 再度確認
            QApplication.processEvents()
            view.viewport().update()
            QApplication.processEvents()
            
            # 中心座標を再確認
            final_center = view.mapToScene(viewport_rect.center())
            logger.debug(f"強制設定後の中心: {final_center}")
        else:
            # 元のスクロールバーポリシーに戻す
            view.setHorizontalScrollBarPolicy(h_policy_original)
            view.setVerticalScrollBarPolicy(v_policy_original)
        
        # 最終的な位置確認
        final_center = view.mapToScene(viewport_rect.center())
        error_x = abs(item_center.x() - final_center.x())
        error_y = abs(item_center.y() - final_center.y())
        
        logger.debug(f"最終中心: {final_center}")
        logger.debug(f"最終誤差: X={error_x:.2f}, Y={error_y:.2f}")
        
        # 元のスクロールバーポリシーに戻す
        view.setHorizontalScrollBarPolicy(h_policy_original)
        view.setVerticalScrollBarPolicy(v_policy_original)
        
        # ビューの更新を強制
        view.viewport().update()
        QApplication.processEvents()
        
        return True
    
    except Exception as e:
        logger.error(f"ビューの中心化中にエラーが発生: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # エラー時には元のスクロールバーポリシーに戻す
        try:
            view.setHorizontalScrollBarPolicy(h_policy_original)
            view.setVerticalScrollBarPolicy(v_policy_original)
        except:
            pass
            
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