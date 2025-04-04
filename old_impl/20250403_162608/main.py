#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFビューアのメインプログラム

PySide6を使用したDXFファイルビューアの実行スクリプトです。
"""

import sys
import os
import logging
import argparse
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFileDialog, QMessageBox,
    QToolBar, QStatusBar, QLabel
)
from PySide6.QtGui import QAction, QKeySequence, QColor, QBrush
from PySide6.QtCore import Qt, Slot, QSize

# 旧実装からの必要な関数とクラスをインポート
from old_implementation.dxf_viewer_pyside6 import parse_dxf_file, draw_dxf_entities
from old_implementation.dxf_ui_adapter import configure_graphics_view
from ui.graphics_view import DxfGraphicsView

# 強制黒モードの設定をインポート
from core.dxf_colors import set_force_black_mode

# ビュー操作ユーティリティをインポート
from ui.view_utils import center_view_on_entities, configure_view_for_cad

def setup_logging():
    """ロギングの設定"""
    logger = logging.getLogger("dxf_viewer")
    logger.setLevel(logging.DEBUG)  # 常にDEBUGレベルに設定
    
    # コンソールハンドラ
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # ハンドラもDEBUGレベルに設定
    
    # フォーマッタ
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    
    # ハンドラを追加
    logger.addHandler(ch)
    
    return logger

class MainWindow(QMainWindow):
    """
    DXFビューアのメインウィンドウ
    """
    def __init__(self, settings: Dict[str, Any]):
        super().__init__()
        
        # ロガー設定
        self.logger = logging.getLogger("dxf_viewer")
        
        # 設定値を取得
        self.file_path = settings.get('file_path')
        self.debug_mode = settings.get('debug_mode', False)
        
        # ウィンドウの基本設定
        self.setWindowTitle("DXFビューア")
        self.resize(1200, 800)
        
        # 中央ウィジェット
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # グラフィックビューの作成
        self.view = DxfGraphicsView()
        self.layout.addWidget(self.view)
        
        # ビューの設定を最適化
        configure_view_for_cad(self.view)
        
        # シーンを作成して背景色を設定
        self.view.scene().setBackgroundBrush(QBrush(QColor(255, 255, 255)))  # 白背景
        
        # ステータスバーの設定
        self.status_bar = self.statusBar()
        self.zoom_label = QLabel("ズーム: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)
        
        # UIの構築
        self._setup_ui()
        
        # ファイルが指定されていたら開く
        if self.file_path:
            self.load_dxf_file(self.file_path)
    
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
    
    def open_file_dialog(self):
        """ファイル選択ダイアログを表示"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "DXFファイルを開く", "", "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.setWindowTitle(f"DXFビューア - {os.path.basename(file_path)}")
            self.load_dxf_file(file_path)
    
    def load_dxf_file(self, file_path):
        """DXFファイルを読み込み表示"""
        try:
            # 状態バーに読み込み中メッセージ
            self.statusBar().showMessage(f"ファイルを読み込み中: {os.path.basename(file_path)}")
            
            # シーンをクリア
            self.view.scene().clear()
            
            # シーンの背景色を再設定（クリア時に消えることがあるため）
            self.view.scene().setBackgroundBrush(QBrush(QColor(255, 255, 255)))  # 白背景
            
            # DXFファイル読み込み（旧実装関数を使用）
            dxf_data = parse_dxf_file(file_path)
            
            # DXFデータをシーンに描画（旧実装関数を使用）
            draw_dxf_entities(self.view.scene(), dxf_data)
            
            # イベント処理を確実に行ってから範囲を取得
            QApplication.processEvents()
            
            # バウンディングボックスの情報を取得
            bbox = self.view.scene().itemsBoundingRect()
            self.logger.debug(f"シーンのバウンディングボックス: {bbox}")
            
            if bbox.isEmpty():
                self.logger.warning("シーンが空です。有効なエンティティが含まれていません。")
                self.statusBar().showMessage(f"ファイルは読み込まれましたが、表示可能なエンティティがありません")
                return
            
            # バウンディングボックスの中心を取得
            center = bbox.center()
            self.logger.debug(f"バウンディングボックスの中心: {center}")
            
            # 表示範囲調整（改良した関数を使用し、明示的にバウンディングボックスを渡す）
            self.logger.debug("エンティティの中心配置を開始...")
            if center_view_on_entities(self.view, bbox):
                self.logger.debug("エンティティの中心配置に成功しました")
                
                # ビューの強制更新
                self.view.viewport().update()
                QApplication.processEvents()
                
                # 中心配置後のビュー状態を確認
                viewport_rect = self.view.viewport().rect()
                view_center_scene = self.view.mapToScene(viewport_rect.center())
                scene_center = bbox.center()
                error_x = abs(scene_center.x() - view_center_scene.x())
                error_y = abs(scene_center.y() - view_center_scene.y())
                
                self.logger.debug(f"中心配置後の誤差: X={error_x:.2f}, Y={error_y:.2f}")
                
                if error_x > 5.0 or error_y > 5.0:
                    self.logger.warning(f"中心配置の誤差が大きすぎます：X={error_x:.2f}, Y={error_y:.2f}")
                    # 再試行
                    self.logger.debug("中心配置を再試行します...")
                    center_view_on_entities(self.view, bbox)
                    self.view.viewport().update()
                    QApplication.processEvents()
                
                self.statusBar().showMessage(f"ファイルを読み込みました: {os.path.basename(file_path)}")
                self._update_zoom_info()
            else:
                self.logger.warning("エンティティの中心配置に失敗しました")
                self.statusBar().showMessage(f"ファイルを読み込みましたが、表示範囲の調整に失敗しました")
        
        except Exception as e:
            self.logger.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # エラーメッセージを表示
            QMessageBox.critical(
                self, 
                "エラー", 
                f"ファイルの読み込み中にエラーが発生しました:\n{str(e)}"
            )
            self.statusBar().showMessage("ファイルの読み込みに失敗しました")
    
    def fit_to_view(self):
        """コンテンツを表示範囲に合わせる"""
        # 新しい純粋関数を使用してビューを中心化
        if center_view_on_entities(self.view):
            # 成功した場合
            self.statusBar().showMessage("表示範囲を調整しました")
            # ズーム情報更新
            self._update_zoom_info()
        else:
            # 失敗した場合
            self.statusBar().showMessage("表示範囲の調整に失敗しました")
    
    def zoom_in(self):
        """拡大"""
        self.view.scale(1.2, 1.2)
        self._update_zoom_info()
    
    def zoom_out(self):
        """縮小"""
        self.view.scale(1/1.2, 1/1.2)
        self._update_zoom_info()
    
    def _update_zoom_info(self):
        """ズーム情報を更新"""
        transform = self.view.transform()
        zoom_level = (transform.m11() + transform.m22()) / 2.0
        self.zoom_label.setText(f"ズーム: {int(zoom_level * 100)}%")

def main():
    """メインプログラム"""
    # ロギングのセットアップ
    logger = setup_logging()
    logger.info("アプリケーション開始")
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='DXF Viewerアプリケーション')
    parser.add_argument('--file', help='開くDXFファイルのパス')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効にする')
    args = parser.parse_args()
    
    # アプリケーション設定
    app_settings = {
        'file_path': args.file,
        'debug_mode': args.debug
    }
    
    # Qtアプリケーション作成
    app = QApplication(sys.argv)
    app.setApplicationName("DXFビューア")
    
    # ハイDPIスケーリングを有効化
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # メインウィンドウ作成
    main_window = MainWindow(app_settings)
    main_window.show()
    
    # アプリケーション実行
    exit_code = app.exec()
    
    logger.info(f"アプリケーション終了 (コード: {exit_code})")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
