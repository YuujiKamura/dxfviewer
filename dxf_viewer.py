#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF Viewer - シンプルなDXFファイルビューア

PySide6を使用したDXFファイルビューアアプリケーション
ズーム・パン操作、DXFファイル読み込み機能を提供します。
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# PySide6のインポート
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFileDialog, QPushButton, QLabel, QMessageBox, QStatusBar,
    QComboBox
)
from PySide6.QtGui import (
    QAction, QColor, QPen, QFont, QPainter, QSurfaceFormat
)
from PySide6.QtCore import (
    Qt, QPointF, QSize
)

# 自作モジュール
from ui.graphics_view import DxfGraphicsView
from dxf_core.parser import parse_dxf_file, get_dxf_info
from dxf_core.renderer import draw_dxf_entities
from dxf_core.adapter import create_dxf_adapter

# ezdxfのインポート（エラー処理用）
try:
    import ezdxf
    EZDXF_AVAILABLE = True
except ImportError:
    print("ezdxfモジュールのインポートエラー")
    print("pip install ezdxf を実行してインストールしてください。")
    EZDXF_AVAILABLE = False

# 基本設定
APP_NAME = "DXF Viewer"
APP_VERSION = "1.0"

# ロガーの設定
logger = None

def setup_logger(debug_mode=False):
    """ロガーの設定をセットアップ"""
    global logger
    
    # ロガーの作成
    logger = logging.getLogger('DXFViewer')
    
    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # デバッグモードならDEBUG、そうでなければINFOレベル
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # ログのフォーマット設定
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    
    # コンソールへの出力設定
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    logger.addHandler(console_handler)
    
    return logger

class DXFViewerMainWindow(QMainWindow):
    """DXFファイルビューアのメインウィンドウクラス"""
    
    def __init__(self, file_path=None, debug_mode=False):
        super().__init__()
        
        self.file_path = file_path
        self.debug_mode = debug_mode
        self.current_line_width = 1.0  # デフォルトの線幅を倍率として扱う
        self.dxf_data = None  # DXFデータを保持
        
        # ウィンドウ設定
        self.setWindowTitle(f"{APP_NAME} - {os.path.basename(self.file_path) if self.file_path else 'No File'}")
        self.resize(1200, 800)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # グラフィックスビューの作成
        self.view = DxfGraphicsView()
        # すべてのレンダリングヒントを一度に設定
        self.view.setRenderHints(
            QPainter.Antialiasing | 
            QPainter.TextAntialiasing | 
            QPainter.SmoothPixmapTransform |
            QPainter.LosslessImageRendering
        )
        layout.addWidget(self.view)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # ファイルを開くボタン
        open_button = QPushButton("ファイルを開く")
        open_button.clicked.connect(self.open_file_dialog)
        button_layout.addWidget(open_button)
        
        # リセットボタン
        reset_button = QPushButton("ビューをリセット")
        reset_button.clicked.connect(self.view.reset_view)
        button_layout.addWidget(reset_button)
        
        # 原点表示ボタン
        origin_button = QPushButton("原点表示")
        origin_button.clicked.connect(self.draw_origin)
        button_layout.addWidget(origin_button)
        
        # 線幅設定のラベル
        line_width_label = QLabel("線幅倍率:")
        button_layout.addWidget(line_width_label)
        
        # 線幅設定のコンボボックス
        self.line_width_combo = QComboBox()
        # 0.2単位で0.2から3.0までの値を追加
        for width in [round(i * 0.2, 1) for i in range(1, 16)]:
            self.line_width_combo.addItem(f"{width:.1f}x", width)
        # デフォルト値を1.0に設定
        self.line_width_combo.setCurrentText("1.0x")
        self.line_width_combo.currentIndexChanged.connect(self.on_line_width_changed)
        button_layout.addWidget(self.line_width_combo)
        
        # ファイル情報ラベル
        self.info_label = QLabel("ファイル情報: なし")
        button_layout.addWidget(self.info_label)
        
        # ステータスバーの設定
        self.statusBar().showMessage("Ready")
        
        # ユーザーインターフェースのセットアップ
        self.setup_ui()
        
        # 原点表示
        self.draw_origin()
        
        # DXFファイルが指定されている場合は読み込む
        if self.file_path:
            self.load_dxf_file(self.file_path)
        
        # ログ初期化
        logger.info(f"DXF Viewerを初期化しました。ファイル: {self.file_path}")

    def on_line_width_changed(self, index):
        """線幅倍率が変更されたときの処理"""
        # コンボボックスから選択された値を取得
        # currentData()の代わりにテキストから数値を取得
        text = self.line_width_combo.currentText()
        try:
            # "1.0x"のような形式から数値部分を取得
            self.current_line_width = float(text.replace('x', ''))
            logger.debug(f"線幅倍率を変更: {self.current_line_width}")
            
            # ステータスバーに表示
            self.statusBar().showMessage(f"線幅倍率を {self.current_line_width}x に変更しました")
            
            # 現在のDXFデータが読み込まれている場合は再描画
            if self.dxf_data:
                self.redraw_dxf_data()
            else:
                # DXFデータがなくても原点を再描画する
                self.view.scene().clear()
                self.draw_origin()
        except ValueError as e:
            logger.error(f"線幅倍率の変換エラー: {e}")
            self.statusBar().showMessage(f"線幅倍率の設定に失敗しました: {text}")
    
    def redraw_dxf_data(self):
        """DXFデータを現在の線幅設定で再描画"""
        try:
            # シーンをクリア
            self.view.scene().clear()
            
            # 原点を再描画
            self.draw_origin()
            
            # アダプターを作成し、線幅倍率を設定
            adapter = create_dxf_adapter(self.view.scene())
            adapter.line_width_scale = self.current_line_width  # default_line_width ではなく line_width_scale を設定
            
            # DXFエンティティを描画（アダプターを直接使用）
            from dxf_core.renderer import draw_dxf_entities_with_adapter
            draw_dxf_entities_with_adapter(adapter, self.dxf_data)
            
            # 表示範囲を調整
            self.view.setup_scene_rect(margin_factor=5.0)
            self.view.fit_scene_in_view()
            
            logger.debug(f"DXFデータを線幅倍率 {self.current_line_width}x で再描画しました")
            
        except Exception as e:
            error_msg = f"DXFデータの再描画に失敗しました: {str(e)}"
            self.statusBar().showMessage(error_msg)
            logger.error(error_msg)
            logger.exception(e)

    def setup_ui(self):
        """ユーザーインターフェースのセットアップ"""
        # メニューバーの作成
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu('ファイル')
        
        # ファイルを開く
        open_action = QAction('開く...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        
        # 終了
        exit_action = QAction('終了', self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu('表示')
        
        # 全体表示
        fit_action = QAction('全体表示', self)
        fit_action.setShortcut('F')
        fit_action.triggered.connect(self.view.reset_view)
        view_menu.addAction(fit_action)
        
        # ズームインボタン
        zoom_in_action = QAction('拡大', self)
        zoom_in_action.setShortcut('+')
        zoom_in_action.triggered.connect(lambda: self.view.zoom_in())
        view_menu.addAction(zoom_in_action)
        
        # ズームアウトボタン
        zoom_out_action = QAction('縮小', self)
        zoom_out_action.setShortcut('-')
        zoom_out_action.triggered.connect(lambda: self.view.zoom_out())
        view_menu.addAction(zoom_out_action)
        
        # 原点表示
        origin_action = QAction('原点表示', self)
        origin_action.triggered.connect(self.draw_origin)
        view_menu.addAction(origin_action)
        
        # ツールバーの作成
        toolbar = self.addToolBar('メインツールバー')
        toolbar.addAction(open_action)
        toolbar.addAction(fit_action)
        toolbar.addAction(zoom_in_action)
        toolbar.addAction(zoom_out_action)
        toolbar.addAction(origin_action)

    def draw_origin(self):
        """原点にクロスラインと円を描画"""
        scene = self.view.scene()
        
        # 基本線幅
        baseline_width = 1.0
        # 現在の線幅倍率を適用
        scaled_width = baseline_width * self.current_line_width
        
        # ペンの設定
        x_pen = QPen(QColor(255, 0, 0))
        x_pen.setWidthF(scaled_width)
        x_pen.setCosmetic(False)  # CAD表示のためコスメティックペンを無効化
        
        y_pen = QPen(QColor(0, 255, 0))
        y_pen.setWidthF(scaled_width)
        y_pen.setCosmetic(False)  # CAD表示のためコスメティックペンを無効化
        
        circle_pen = QPen(QColor(0, 0, 255))
        circle_pen.setWidthF(scaled_width)
        circle_pen.setCosmetic(False)  # CAD表示のためコスメティックペンを無効化
        
        # 原点マーカーを描画
        # X軸（赤）
        x_axis = scene.addLine(-100, 0, 100, 0, x_pen)
        
        # Y軸（緑）
        y_axis = scene.addLine(0, -100, 0, 100, y_pen)
        
        # 原点の円（青）
        origin_circle = scene.addEllipse(-10, -10, 20, 20, circle_pen)
        
        # 座標ラベル
        coord_text = scene.addText("(0,0)")
        coord_text.setPos(15, 15)
        coord_text.setDefaultTextColor(QColor(0, 0, 255))
        
        # シーンレクトの設定
        self.view.setup_scene_rect(margin_factor=5.0)
        
        # 表示範囲を調整
        self.view.fit_scene_in_view()
        
        self.statusBar().showMessage(f"原点を表示しました (線幅倍率: {self.current_line_width}x)")

    def open_file_dialog(self):
        """ファイル選択ダイアログを開く"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "DXFファイルを開く", "", "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.setWindowTitle(f"{APP_NAME} - {os.path.basename(file_path)}")
            self.load_dxf_file(file_path)
    
    def load_dxf_file(self, file_path):
        """DXFファイルを読み込み、シーンに描画する"""
        if not EZDXF_AVAILABLE:
            QMessageBox.critical(self, "エラー", "ezdxfモジュールがインストールされていません。")
            return
            
        try:
            logger.info(f"DXFファイル読み込み開始: {file_path}")
            
            # DXFファイルを解析（dxf_coreモジュールを使用）
            self.dxf_data = parse_dxf_file(file_path)
            
            # シーンをクリア
            self.view.scene().clear()
            
            # 原点を再描画
            self.draw_origin()
            
            # アダプターを作成し、線幅倍率を設定
            adapter = create_dxf_adapter(self.view.scene())
            adapter.line_width_scale = self.current_line_width  # default_line_width ではなく line_width_scale を設定
            
            # DXFエンティティを描画（アダプターを直接使用）
            from dxf_core.renderer import draw_dxf_entities_with_adapter
            draw_dxf_entities_with_adapter(adapter, self.dxf_data)
            
            # 表示範囲を調整
            self.view.setup_scene_rect(margin_factor=5.0)
            self.view.fit_scene_in_view()
            
            # ファイル情報の更新
            self.update_file_info(self.dxf_data)
            
            # 成功メッセージ
            self.statusBar().showMessage(f"DXFファイルを読み込みました: {os.path.basename(file_path)}")
            logger.info(f"DXFファイル読み込み成功: {file_path}")
            
        except Exception as e:
            # エラーメッセージ
            error_msg = f"DXFファイルの読み込みに失敗しました: {str(e)}"
            self.statusBar().showMessage(error_msg)
            logger.error(error_msg)
            logger.exception(e)
            
            # エラーダイアログ表示
            QMessageBox.critical(self, "読み込みエラー", error_msg)
    
    def update_file_info(self, dxf_data):
        """ファイル情報ラベルを更新"""
        if not dxf_data:
            self.info_label.setText("ファイル情報なし")
            return
        
        # dxf_coreモジュールのget_dxf_info関数を使用
        info = get_dxf_info(dxf_data)
        
        # エンティティ数
        entity_count = info.get('entity_count', 0)
        
        # 情報テキスト
        info_text = f"エンティティ数: {entity_count}"
        self.info_label.setText(info_text)

def parse_arguments():
    """コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(description=f'{APP_NAME} - DXFファイルビューア')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効化')
    parser.add_argument('--file', type=str, help='起動時に開くDXFファイル')
    return parser.parse_args()

def main():
    """メイン関数"""
    # コマンドライン引数のパース
    args = parse_arguments()
    
    # ロガーの設定
    global logger
    logger = setup_logger(debug_mode=args.debug)
    
    # QPainterの警告を完全に抑制するための環境変数を設定
    os.environ["QT_LOGGING_RULES"] = "*=false"
    
    # QSurfaceFormatの設定（OpenGLレンダリングの最適化）
    try:
        surface_format = QSurfaceFormat()
        surface_format.setRenderableType(QSurfaceFormat.OpenGL)
        surface_format.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
        QSurfaceFormat.setDefaultFormat(surface_format)
    except ImportError:
        logger.warning("QSurfaceFormatのインポートに失敗しました。一部の描画最適化が無効です。")
    
    # アプリケーション作成
    app = QApplication(sys.argv)
    
    # メインウィンドウ作成
    window = DXFViewerMainWindow(file_path=args.file, debug_mode=args.debug)
    window.show()
    
    # アプリケーション実行
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
