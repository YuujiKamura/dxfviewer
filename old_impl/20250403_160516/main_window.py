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
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import Qt, Slot, QSize

from ui.graphics_view import DxfGraphicsView
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
    
    def __init__(self):
        """メインウィンドウの初期化"""
        super().__init__()
        
        # ウィンドウのタイトルと初期サイズ
        self.setWindowTitle("DXFビューア")
        self.resize(1024, 768)
        
        # 内部状態
        self.current_file = None
        self.dxf_data = None
        
        # UIの初期化
        self._setup_ui()
        self._create_actions()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
        
        # 初期状態での表示を更新
        self._update_ui_state()
        
        logger.info("メインウィンドウを初期化しました")
    
    def _setup_ui(self):
        """UIコンポーネントの初期化"""
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # グラフィックスシーン
        self.scene = QGraphicsScene()
        
        # グラフィックスビュー
        self.graphics_view = DxfGraphicsView(self.scene)
        main_layout.addWidget(self.graphics_view)
        
        # レンダラー
        self.renderer = DxfRenderer(self.scene)
        
        # ズーム情報の表示用ラベル
        self.zoom_label = QLabel("ズーム: 100%")
        
        # ビューからのシグナル接続
        self.graphics_view.zoom_changed.connect(self._on_zoom_changed)
    
    def _create_actions(self):
        """アクションの作成"""
        # ファイルを開く
        self.open_action = QAction("開く", self)
        self.open_action.setShortcut(QKeySequence.Open)
        self.open_action.setStatusTip("DXFファイルを開きます")
        self.open_action.triggered.connect(self.open_file)
        
        # 終了
        self.exit_action = QAction("終了", self)
        self.exit_action.setShortcut(QKeySequence.Quit)
        self.exit_action.setStatusTip("アプリケーションを終了します")
        self.exit_action.triggered.connect(self.close)
        
        # 表示をリセット
        self.reset_view_action = QAction("表示をリセット", self)
        self.reset_view_action.setShortcut("F")
        self.reset_view_action.setStatusTip("表示をリセットし、全体を表示します")
        self.reset_view_action.triggered.connect(self.graphics_view.reset_view)
        
        # ズームイン
        self.zoom_in_action = QAction("拡大", self)
        self.zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        self.zoom_in_action.setStatusTip("表示を拡大します")
        self.zoom_in_action.triggered.connect(self.graphics_view.zoom_in)
        
        # ズームアウト
        self.zoom_out_action = QAction("縮小", self)
        self.zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        self.zoom_out_action.setStatusTip("表示を縮小します")
        self.zoom_out_action.triggered.connect(self.graphics_view.zoom_out)
    
    def _create_menu(self):
        """メニューの作成"""
        # ファイルメニュー
        file_menu = self.menuBar().addMenu("ファイル")
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # 表示メニュー
        view_menu = self.menuBar().addMenu("表示")
        view_menu.addAction(self.reset_view_action)
        view_menu.addAction(self.zoom_in_action)
        view_menu.addAction(self.zoom_out_action)
    
    def _create_toolbar(self):
        """ツールバーの作成"""
        toolbar = QToolBar("メインツールバー")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # アクションの追加
        toolbar.addAction(self.open_action)
        toolbar.addSeparator()
        toolbar.addAction(self.reset_view_action)
        toolbar.addAction(self.zoom_in_action)
        toolbar.addAction(self.zoom_out_action)
    
    def _create_statusbar(self):
        """ステータスバーの作成"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)
        
        # ズーム情報ラベルをステータスバーに追加
        statusbar.addPermanentWidget(self.zoom_label)
        
        # 初期メッセージ
        statusbar.showMessage("準備完了")
    
    def _update_ui_state(self):
        """UI状態の更新"""
        # ファイルが開かれているかどうかに応じた状態更新
        file_loaded = self.current_file is not None
        
        # ズーム関連アクションの有効/無効
        self.reset_view_action.setEnabled(file_loaded)
        self.zoom_in_action.setEnabled(file_loaded)
        self.zoom_out_action.setEnabled(file_loaded)
        
        # ウィンドウタイトルの更新
        if file_loaded:
            filename = os.path.basename(self.current_file)
            self.setWindowTitle(f"DXFビューア - {filename}")
        else:
            self.setWindowTitle("DXFビューア")
    
    @Slot(float)
    def _on_zoom_changed(self, zoom_factor: float):
        """
        ズーム倍率変更時の処理
        
        Args:
            zoom_factor: 新しいズーム倍率
        """
        # ズーム倍率をパーセント表示に変換
        zoom_percent = int(zoom_factor * 100)
        self.zoom_label.setText(f"ズーム: {zoom_percent}%")
    
    @Slot()
    def open_file(self):
        """DXFファイルを開くダイアログを表示し、選択されたファイルを読み込む"""
        # ファイル選択ダイアログ
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "DXFファイルを開く",
            "",
            "DXFファイル (*.dxf);;すべてのファイル (*.*)"
        )
        
        if not file_path:
            return  # キャンセルされた場合
        
        self.load_dxf_file(file_path)
    
    def load_dxf_file(self, file_path: str):
        """
        DXFファイルを読み込む
        
        Args:
            file_path: DXFファイルのパス
        """
        try:
            # カーソル形状を変更（処理中）
            self.setCursor(Qt.WaitCursor)
            
            # 前回のデータをクリア
            self.graphics_view.clear_scene()
            
            # ファイル読み込み
            self.statusBar().showMessage(f"ファイルを読み込んでいます: {file_path}")
            dxf_data = load_dxf_file(file_path)
            
            if not dxf_data:
                QMessageBox.critical(
                    self,
                    "エラー",
                    f"ファイルの読み込みに失敗しました: {file_path}"
                )
                self.statusBar().showMessage("読み込み失敗")
                return
            
            # データ保存
            self.current_file = file_path
            self.dxf_data = dxf_data
            
            # エンティティ描画
            entities = dxf_data.get("entities", [])
            count = len(entities)
            success_count = self.renderer.render_entities(entities)
            
            # 表示調整
            self.graphics_view.fit_scene_in_view()
            
            # 状態更新
            self._update_ui_state()
            
            # ステータスバー更新
            self.statusBar().showMessage(
                f"読み込み完了: {count}エンティティ中{success_count}個を描画"
            )
            
            logger.info(f"ファイルを読み込みました: {file_path}")
            logger.info(f"エンティティ数: {count}、描画成功: {success_count}")
            
        except Exception as e:
            logger.error(f"ファイル読み込み中にエラー: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "エラー",
                f"ファイルの処理中にエラーが発生しました: {str(e)}"
            )
            self.statusBar().showMessage("読み込み失敗")
        
        finally:
            # カーソルを元に戻す
            self.unsetCursor() 