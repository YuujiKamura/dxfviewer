#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFビューアのメインウィンドウ

アプリケーションのメインウィンドウとUIコンポーネントを提供します。
"""

import os
import logging
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QFileDialog, QMessageBox,
    QToolBar, QStatusBar, QGraphicsScene
)
from PySide6.QtGui import QIcon, QKeySequence, QAction, QColor, QBrush, QPen
from PySide6.QtCore import Qt, Slot, QSize, QPointF

from ui_new.graphics_view import DxfGraphicsView
from renderer_new.renderer import DxfRenderer

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

class MainWindow(QMainWindow):
    """
    DXFビューアのメインウィンドウ
    
    アプリケーションのメインウィンドウを提供します。
    """
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        メインウィンドウの初期化
        
        Args:
            settings: アプリケーション設定（オプション）
        """
        super().__init__()
        
        # 設定の適用
        self.settings = settings or {}
        self.file_path = self.settings.get('file_path')
        
        # ウィンドウ設定
        self.setWindowTitle("DXFビューア")
        self.resize(1024, 768)
        
        # 中央ウィジェット
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # メインレイアウト
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # グラフィックスシーン
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QBrush(QColor(255, 255, 255)))  # 白背景
        
        # グラフィックスビュー
        self.view = DxfGraphicsView(self.scene)
        self.layout.addWidget(self.view)
        
        # レンダラーの初期化
        self.renderer = DxfRenderer(self.scene)
        
        # ステータスバー設定
        self.statusBar().showMessage("準備完了")
        self.zoom_label = QLabel("ズーム: 100%")
        self.statusBar().addPermanentWidget(self.zoom_label)
        
        # シグナル接続
        self.view.zoom_changed.connect(self._on_zoom_changed)
        
        # UIの作成
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        
        # 原点マーカーを描画
        self._draw_origin_marker()
        
        logger.debug("メインウィンドウを初期化しました")
    
    def _create_actions(self):
        """アクションの作成"""
        # ファイルを開く
        self.open_action = QAction("開く...", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.triggered.connect(self.open_file)
        
        # 全体表示
        self.fit_action = QAction("全体表示", self)
        self.fit_action.setShortcut("F")
        self.fit_action.triggered.connect(self.fit_view)
        
        # ズームイン
        self.zoom_in_action = QAction("拡大", self)
        self.zoom_in_action.setShortcut("+")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        
        # ズームアウト
        self.zoom_out_action = QAction("縮小", self)
        self.zoom_out_action.setShortcut("-")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        
        # 終了
        self.exit_action = QAction("終了", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.triggered.connect(self.close)
    
    def _create_menus(self):
        """メニューの作成"""
        # ファイルメニュー
        file_menu = self.menuBar().addMenu("ファイル")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # 表示メニュー
        view_menu = self.menuBar().addMenu("表示")
        view_menu.addAction(self.fit_action)
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
    
    def _create_toolbars(self):
        """ツールバーの作成"""
        # メインツールバー
        toolbar = QToolBar("メインツールバー")
        toolbar.setMovable(False)
        toolbar.addAction(self.open_action)
        toolbar.addSeparator()
        toolbar.addAction(self.fit_action)
        toolbar.addAction(self.zoom_in_action)
        toolbar.addAction(self.zoom_out_action)
        self.addToolBar(toolbar)
    
    def _draw_origin_marker(self):
        """原点にマーカーを描画"""
        # 十字マーカー
        marker_size = 30.0
        
        # 赤色の横線（X軸）
        pen_x = QPen(QColor(255, 0, 0))
        pen_x.setWidth(2)
        self.scene.addLine(-marker_size/2, 0, marker_size/2, 0, pen_x)
        
        # 緑色の縦線（Y軸）
        pen_y = QPen(QColor(0, 255, 0))
        pen_y.setWidth(2)
        self.scene.addLine(0, -marker_size/2, 0, marker_size/2, pen_y)
        
        # 中心点に青い丸
        center_radius = 3.0
        pen_circle = QPen(QColor(0, 0, 255))
        pen_circle.setWidth(2)
        brush = QBrush(QColor(0, 0, 255, 128))  # 半透明の青
        self.scene.addEllipse(
            -center_radius, -center_radius, 
            center_radius * 2, center_radius * 2, 
            pen_circle, brush
        )
        
        # X軸ラベル - 旧版のテキスト回転ポリシーを使用
        self.renderer.render_text(
            "X軸", marker_size/2 + 5, 0, 
            height=5.0, 
            color=(255, 0, 0),  # 赤
            h_align=0,  # 左揃え
            v_align=2,  # 中央揃え
            rotation=0.0
        )
        
        # Y軸ラベル - 旧版のテキスト回転ポリシーを使用
        self.renderer.render_text(
            "Y軸", 0, marker_size/2 + 5, 
            height=5.0, 
            color=(0, 255, 0),  # 緑
            h_align=1,  # 中央揃え
            v_align=0,  # ベースライン
            rotation=90.0  # 縦向き
        )
        
        # 原点座標ラベル - 旧版のテキスト回転ポリシーを使用
        self.renderer.render_text(
            "(0,0)", 5, 5, 
            height=5.0, 
            color=(0, 0, 0),  # 黒
            h_align=0,  # 左揃え
            v_align=1,  # 下揃え
            rotation=0.0
        )
        
        logger.debug("原点マーカーを描画しました")
    
    def _on_zoom_changed(self, zoom_factor):
        """ズーム率変更時の処理"""
        self.zoom_label.setText(f"ズーム: {int(zoom_factor * 100)}%")
    
    def open_file(self):
        """ファイルを開くダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "DXFファイルを開く", "", "DXF Files (*.dxf);;All Files (*.*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.setWindowTitle(f"DXFビューア - {os.path.basename(file_path)}")
            self.statusBar().showMessage(f"ファイル {os.path.basename(file_path)} を開きました")
    
    def fit_view(self):
        """ビューをコンテンツに合わせる"""
        self.view.fit_in_view()
        self.statusBar().showMessage("表示を調整しました")
    
    def zoom_in(self):
        """ズームイン"""
        self.view.zoom_in()
        self.statusBar().showMessage("拡大しました")
    
    def zoom_out(self):
        """ズームアウト"""
        self.view.zoom_out()
        self.statusBar().showMessage("縮小しました") 