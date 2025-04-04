#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFビューアのメインウィンドウ

アプリケーションのメインウィンドウとUIコンポーネントを提供します。
"""

import os
import logging
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QMessageBox,
    QToolBar, QStatusBar, QGraphicsScene
)
from PySide6.QtGui import QIcon, QKeySequence, QAction, QColor, QBrush, QPen
from PySide6.QtCore import Qt, Slot, QSize

from ui.graphics_view import DxfGraphicsView
from ui.view_utils import center_view_on_entities, configure_view_for_cad
from renderer.renderer import DxfRenderer
from core.dxf_reader import load_dxf_file
from core.dxf_entities import DxfEntity

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

class MainWindow(QMainWindow):
    """
    DXFビューアのメインウィンドウ
    
    アプリケーションのメインウィンドウを提供し、
    DXFファイルの読み込みと表示を管理します。
    """
    
    def __init__(self, settings: Dict[str, Any] = None):
        """
        メインウィンドウの初期化
        
        Args:
            settings: アプリケーション設定
        """
        super().__init__()
        
        # 設定値を取得
        self.settings = settings or {}
        self.file_path = self.settings.get('file_path')
        self.debug_mode = self.settings.get('debug_mode', False)
        
        # ウィンドウのタイトルと初期サイズ
        self.setWindowTitle("DXFビューア")
        self.resize(1024, 768)
        
        # 中央ウィジェット
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # グラフィックスシーン
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor(255, 255, 255)))  # 白背景
        
        # グラフィックスビュー
        self.view = DxfGraphicsView(self.scene)
        self.layout.addWidget(self.view)
        
        # CAD表示用にビューを最適化
        configure_view_for_cad(self.view)
        
        # 原点にマーカーを描画
        self._draw_origin_marker()
        
        # レンダラー
        self.renderer = DxfRenderer(self.scene)
        
        # ステータスバーの設定
        self.status_bar = self.statusBar()
        self.zoom_label = QLabel("ズーム: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)
        
        # ビューからのシグナル接続
        self.view.zoom_changed.connect(self._on_zoom_changed)
        
        # UIの構築
        self._setup_ui()
        
        # 初期状態での表示を更新
        self._update_ui_state()
        
        # ファイルが指定されていたら開く
        if self.file_path:
            self.load_dxf_file(self.file_path)
            
        logger.info("メインウィンドウを初期化しました")
    
    def _setup_ui(self):
        """UIコンポーネントのセットアップ"""
        # メニューバーの作成
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu('ファイル')
        
        # ファイルを開く
        open_action = QAction('開く...', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        
        # 終了
        exit_action = QAction('終了', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu('表示')
        
        # 全体表示
        fit_action = QAction('全体表示', self)
        fit_action.setShortcut('F')
        fit_action.triggered.connect(self.fit_to_view)
        view_menu.addAction(fit_action)
        
        # ズームイン
        zoom_in_action = QAction('拡大', self)
        zoom_in_action.setShortcut('+')
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        # ズームアウト
        zoom_out_action = QAction('縮小', self)
        zoom_out_action.setShortcut('-')
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # ツールバーの作成
        toolbar = QToolBar("メインツールバー")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # ツールバーにアクションを追加
        toolbar.addAction(open_action)
        toolbar.addSeparator()
        toolbar.addAction(fit_action)
        toolbar.addAction(zoom_in_action)
        toolbar.addAction(zoom_out_action)
    
    def _update_ui_state(self):
        """UI状態の更新"""
        # ファイルが開かれているかどうかでUI要素の有効・無効を切り替える
        has_items = len(self.scene.items()) > 0
        logger.debug(f"UI状態更新: アイテム数 = {len(self.scene.items())}")
    
    def _on_zoom_changed(self, zoom_factor):
        """ズーム率変更時の処理"""
        self.zoom_label.setText(f"ズーム: {int(zoom_factor * 100)}%")
    
    def open_file_dialog(self):
        """ファイル選択ダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "DXFファイルを開く", "", "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.setWindowTitle(f"DXFビューア - {os.path.basename(file_path)}")
            self.load_dxf_file(file_path)
    
    def _draw_origin_marker(self):
        """原点（0,0）にマーカーを描画"""
        # 十字マーカー（赤色）
        marker_size = 50.0
        pen = QPen(QColor(255, 0, 0))  # 赤色
        pen.setWidth(2)
        
        # 水平線
        self.scene.addLine(-marker_size/2, 0, marker_size/2, 0, pen)
        # 垂直線
        self.scene.addLine(0, -marker_size/2, 0, marker_size/2, pen)
        
        # 円マーカー（赤色、半透明）
        marker_radius = 10.0
        circle_pen = QPen(QColor(255, 0, 0))
        circle_pen.setWidth(2)
        brush = QBrush(QColor(255, 0, 0, 128))  # 半透明の赤
        self.scene.addEllipse(-marker_radius, -marker_radius, marker_radius*2, marker_radius*2, circle_pen, brush)
        
        logger.debug("原点マーカーを描画しました")
    
    def load_dxf_file(self, file_path):
        """DXFファイルを読み込み表示"""
        try:
            # 状態バーに読み込み中メッセージ
            self.statusBar().showMessage(f"ファイルを読み込み中: {os.path.basename(file_path)}")
            
            # シーンをクリア
            self.scene.clear()
            
            # シーンの背景色を再設定（クリア時に消えることがあるため）
            self.scene.setBackgroundBrush(QBrush(QColor(255, 255, 255)))  # 白背景
            
            # 原点にマーカーを描画
            self._draw_origin_marker()
            
            # DXFファイル読み込み
            dxf_data = load_dxf_file(file_path)
            
            if not dxf_data or not dxf_data.get("entities"):
                logger.error("DXFファイルの読み込みに失敗しました")
                QMessageBox.critical(
                    self, 
                    "エラー", 
                    "DXFファイルの読み込みに失敗しました。形式が正しくないか、サポートされていない形式です。"
                )
                self.statusBar().showMessage("ファイルの読み込みに失敗しました")
                return
            
            # DXFデータをシーンに描画
            entities_count = self.renderer.render_entities(dxf_data["entities"])
            logger.info(f"{entities_count}個のエンティティを描画しました")
            
            # イベント処理を確実に行ってから範囲を取得
            self.view.viewport().update()
            
            # バウンディングボックスの情報を取得
            bbox = self.scene.itemsBoundingRect()
            logger.debug(f"シーンのバウンディングボックス: {bbox}")
            
            if bbox.isEmpty():
                logger.warning("シーンが空です。有効なエンティティが含まれていません。")
                self.statusBar().showMessage(f"ファイルは読み込まれましたが、表示可能なエンティティがありません")
                return
            
            # 表示範囲調整
            logger.debug("エンティティの中心配置を開始...")
            if center_view_on_entities(self.view, bbox):
                logger.debug("エンティティの中心配置に成功しました")
                self.statusBar().showMessage(f"ファイルを読み込みました: {os.path.basename(file_path)}")
                self._on_zoom_changed(self.view.get_zoom())
            else:
                logger.warning("エンティティの中心配置に失敗しました")
                self.statusBar().showMessage(f"ファイルを読み込みましたが、表示範囲の調整に失敗しました")
            
            # UI状態を更新
            self._update_ui_state()
        
        except Exception as e:
            logger.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # エラーメッセージを表示
            QMessageBox.critical(
                self, 
                "エラー", 
                f"ファイルの読み込み中にエラーが発生しました:\n{str(e)}"
            )
            self.statusBar().showMessage("ファイルの読み込みに失敗しました")
    
    def fit_to_view(self):
        """コンテンツを表示範囲に合わせる"""
        if center_view_on_entities(self.view):
            self.statusBar().showMessage("表示範囲を調整しました")
            self._on_zoom_changed(self.view.get_zoom())
        else:
            self.statusBar().showMessage("表示範囲の調整に失敗しました")
    
    def zoom_in(self):
        """拡大"""
        self.view.zoom_in()
        self._on_zoom_changed(self.view.get_zoom())
    
    def zoom_out(self):
        """縮小"""
        self.view.zoom_out()
        self._on_zoom_changed(self.view.get_zoom()) 