#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
2D CADアプリケーション
DXFファイルの表示と編集が可能な2D CADビューア
"""

import os
import sys
import time
import argparse
import logging
import platform
from pathlib import Path

# PySide6のインポート
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFileDialog, QPushButton, QLabel, QMessageBox, QGraphicsView, 
    QGraphicsScene, QGraphicsItem, QStatusBar, QComboBox, QDialog, 
    QCheckBox, QSlider, QGroupBox, QSpinBox, QSizePolicy, QToolBar,
    QInputDialog, QDoubleSpinBox, QRadioButton, QButtonGroup, QColorDialog,
    QMenu
)
from PySide6.QtGui import (
    QIcon, QColor, QPen, QBrush, QTransform, QPainterPath, 
    QPolygonF, QFont, QFontMetricsF, QImage, QPainter, QClipboard,
    QPixmap, QKeySequence, QAction
)
from PySide6.QtCore import (
    QPointF, QRectF, QLineF, Qt, QTimer, QFileSystemWatcher, QSize,
    QSettings, Signal, Slot
)

# ezdxfのインポート
try:
    import ezdxf
    from ezdxf import recover
    EZDXF_AVAILABLE = True
except ImportError as e:
    print(f"ezdxfモジュールのインポートエラー: {e}")
    print("pip install ezdxf を実行してインストールしてください。")
    EZDXF_AVAILABLE = False

# 純粋関数モジュールをインポート
import pure_dxf_functions as pdf
from dxf_ui_adapter import DXFSceneAdapter

# 基本設定
APP_NAME = "2D CAD (PySide6版)"
APP_VERSION = "1.0"
DEFAULT_LINE_WIDTH = 1.0
DEFAULT_GRID_SPACING = 10.0

# ロガーの設定
logger = logging.getLogger('CAD2D')
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

# 描画モード列挙型
class DrawingMode:
    SELECT = 0
    LINE = 1
    RECTANGLE = 2
    CIRCLE = 3
    ARC = 4
    POLYLINE = 5
    TEXT = 6

# CAD用のグラフィックスビュー
class CADGraphicsView(QGraphicsView):
    mouse_moved = Signal(float, float)  # マウス移動シグナル (x, y)
    mouse_pressed = Signal(float, float, Qt.MouseButton)  # マウス押下シグナル (x, y, button)
    mouse_released = Signal(float, float, Qt.MouseButton)  # マウスリリースシグナル (x, y, button)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 座標系は標準のまま（Y軸下向き正）
        
        # グリッド設定
        self.grid_visible = True
        self.grid_spacing = DEFAULT_GRID_SPACING
        self.grid_color = QColor(200, 200, 200)
        
        # スナップ設定
        self.snap_enabled = True
        
        # 一時的な描画アイテム
        self.temp_items = []
        
        # ドラッグ関連
        self.panning = False
        self.last_pan_point = None
        
    def drawBackground(self, painter, rect):
        """背景にグリッドを描画"""
        super().drawBackground(painter, rect)
        
        if not self.grid_visible:
            return
            
        # グリッドの表示
        left = int(rect.left()) - (int(rect.left()) % self.grid_spacing)
        top = int(rect.top()) - (int(rect.top()) % self.grid_spacing)
        
        # グリッド線を描画
        grid_pen = QPen(self.grid_color)
        grid_pen.setStyle(Qt.DotLine)
        painter.setPen(grid_pen)
        
        # 縦線
        for x in range(int(left), int(rect.right()), int(self.grid_spacing)):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        
        # 横線
        for y in range(int(top), int(rect.bottom()), int(self.grid_spacing)):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
    
    def mousePressEvent(self, event):
        """マウス押下イベント"""
        if event.button() == Qt.MiddleButton:
            # 中クリックでパン開始
            self.panning = True
            self.last_pan_point = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            # マウス座標をシーン座標に変換
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # スナップ処理
            if self.snap_enabled:
                snapped_pos = self.snapToGrid(QPointF(scene_pos.x(), scene_pos.y()))
                # 信号を発行（ボタン情報も含める）
                self.mouse_pressed.emit(snapped_pos.x(), snapped_pos.y(), event.button())
            else:
                # 信号を発行
                self.mouse_pressed.emit(scene_pos.x(), scene_pos.y(), event.button())
                
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """マウス移動イベント"""
        if self.panning and self.last_pan_point:
            # パン処理
            delta = event.position().toPoint() - self.last_pan_point
            self.last_pan_point = event.position().toPoint()
            
            # ビューのスクロール
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            
            event.accept()
        else:
            # マウス座標をシーン座標に変換
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # スナップ処理
            if self.snap_enabled:
                snapped_pos = self.snapToGrid(QPointF(scene_pos.x(), scene_pos.y()))
                # 信号を発行
                self.mouse_moved.emit(snapped_pos.x(), snapped_pos.y())
            else:
                # 信号を発行
                self.mouse_moved.emit(scene_pos.x(), scene_pos.y())
                
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """マウスリリースイベント"""
        if event.button() == Qt.MiddleButton:
            # パン終了
            self.panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            # マウス座標をシーン座標に変換
            scene_pos = self.mapToScene(event.position().toPoint())
            
            # スナップ処理
            if self.snap_enabled:
                snapped_pos = self.snapToGrid(QPointF(scene_pos.x(), scene_pos.y()))
                # 信号を発行
                self.mouse_released.emit(snapped_pos.x(), snapped_pos.y(), event.button())
            else:
                # 信号を発行
                self.mouse_released.emit(scene_pos.x(), scene_pos.y(), event.button())
                
            super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """ホイールイベントでズーム"""
        zoom_factor = 1.2
        
        if event.angleDelta().y() > 0:
            # ズームイン
            self.scale(zoom_factor, zoom_factor)
        else:
            # ズームアウト
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)
    
    def snapToGrid(self, pos):
        """グリッドにスナップした座標を返す"""
        x = round(pos.x() / self.grid_spacing) * self.grid_spacing
        y = round(pos.y() / self.grid_spacing) * self.grid_spacing
        return QPointF(x, y)
    
    def setGridVisible(self, visible):
        """グリッド表示設定"""
        self.grid_visible = visible
        self.viewport().update()
    
    def setGridSpacing(self, spacing):
        """グリッド間隔設定"""
        self.grid_spacing = spacing
        self.viewport().update()
    
    def setSnapEnabled(self, enabled):
        """スナップ有効/無効設定"""
        self.snap_enabled = enabled
    
    def clearTempItems(self):
        """一時的な描画アイテムをクリア"""
        for item in self.temp_items:
            if item in self.scene().items():
                self.scene().removeItem(item)
        self.temp_items = []
    
    def addTempItem(self, item):
        """一時的な描画アイテムを追加"""
        self.temp_items.append(item)
        return item

# メインウィンドウ
class CAD2DMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
        # 現在の描画モード
        self.current_mode = DrawingMode.SELECT
        
        # 描画データ
        self.drawing_start_point = None
        self.current_item = None
        
        # 選択されたアイテム
        self.selected_items = []
        
        # 現在のファイル
        self.current_file = None
        self.file_modified = False
        
        # カラーとラインスタイル
        self.current_color = QColor(0, 0, 0)
        self.current_line_width = DEFAULT_LINE_WIDTH
        
        # ステータスバー更新
        self.updateStatusBar()
        
        # マウスイベントに対する描画処理の設定
        self.view.mouse_pressed.connect(self.handleMousePressed)
        self.view.mouse_moved.connect(self.handleMouseMoved)
        self.view.mouse_released.connect(self.handleMouseReleased)
        
        logger.info(f"{APP_NAME}が起動しました")
    
    def initUI(self):
        """UIの初期化"""
        self.setWindowTitle(APP_NAME)
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央ウィジェットとレイアウト
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # シーンとビューの作成
        self.scene = QGraphicsScene()
        self.view = CADGraphicsView(self.scene)
        self.view.setScene(self.scene)
        
        # アダプターの設定
        self.adapter = DXFSceneAdapter(self.scene)
        
        # ツールバー
        self.toolbar = self.addToolBar("メインツール")
        
        # ファイルを開くボタン
        self.open_action = self.toolbar.addAction("ファイルを開く")
        self.open_action.triggered.connect(self.openFile)
        
        # 背景色変更ボタン
        self.bg_color_action = self.toolbar.addAction("背景色変更")
        self.bg_color_action.triggered.connect(self.change_background_color)
        
        # 線の色変更ボタン
        self.line_color_action = self.toolbar.addAction("線の色変更")
        self.line_color_action.triggered.connect(self.change_line_color)
        
        # テーマ選択用のコンボボックス
        self.toolbar.addSeparator()
        self.theme_label = QLabel("テーマ:")
        self.toolbar.addWidget(self.theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["明るいテーマ", "暗いテーマ"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        self.toolbar.addWidget(self.theme_combo)
        
        # 描画モード選択
        self.toolbar.addSeparator()
        
        # ツールバーの作成
        self.createToolbars()
        
        # ビューをレイアウトに追加
        self.main_layout.addWidget(self.view)
        
        # ステータスバーの設定
        self.statusBar = self.statusBar()
        self.coords_label = QLabel("X: 0.00  Y: 0.00")
        self.statusBar.addPermanentWidget(self.coords_label)
        
        # マウス移動時の座標表示
        self.view.mouse_moved.connect(self.updateCoordinates)
        
        # メニューの作成
        self.createMenus()
    
    def createToolbars(self):
        """ツールバーの作成"""
        # メインツールバー
        self.main_toolbar = QToolBar("描画ツール")
        self.addToolBar(self.main_toolbar)
        
        # 描画モード用のアクションを格納するリスト
        self.mode_actions = []
        
        # 選択ツール
        select_action = QAction("選択", self)
        select_action.setCheckable(True)
        select_action.setChecked(True)
        select_action.triggered.connect(lambda: self.setDrawingMode(DrawingMode.SELECT))
        self.main_toolbar.addAction(select_action)
        self.mode_actions.append(select_action)
        
        # 線描画
        line_action = QAction("線", self)
        line_action.setCheckable(True)
        line_action.triggered.connect(lambda: self.setDrawingMode(DrawingMode.LINE))
        self.main_toolbar.addAction(line_action)
        self.mode_actions.append(line_action)
        
        # 長方形
        rect_action = QAction("長方形", self)
        rect_action.setCheckable(True)
        rect_action.triggered.connect(lambda: self.setDrawingMode(DrawingMode.RECTANGLE))
        self.main_toolbar.addAction(rect_action)
        self.mode_actions.append(rect_action)
        
        # 円
        circle_action = QAction("円", self)
        circle_action.setCheckable(True)
        circle_action.triggered.connect(lambda: self.setDrawingMode(DrawingMode.CIRCLE))
        self.main_toolbar.addAction(circle_action)
        self.mode_actions.append(circle_action)
        
        # 円弧
        arc_action = QAction("円弧", self)
        arc_action.setCheckable(True)
        arc_action.triggered.connect(lambda: self.setDrawingMode(DrawingMode.ARC))
        self.main_toolbar.addAction(arc_action)
        self.mode_actions.append(arc_action)
        
        # ポリライン
        polyline_action = QAction("ポリライン", self)
        polyline_action.setCheckable(True)
        polyline_action.triggered.connect(lambda: self.setDrawingMode(DrawingMode.POLYLINE))
        self.main_toolbar.addAction(polyline_action)
        self.mode_actions.append(polyline_action)
        
        # テキスト
        text_action = QAction("テキスト", self)
        text_action.setCheckable(True)
        text_action.triggered.connect(lambda: self.setDrawingMode(DrawingMode.TEXT))
        self.main_toolbar.addAction(text_action)
        self.mode_actions.append(text_action)
        
        self.main_toolbar.addSeparator()
        
        # 編集ツールバー
        self.edit_toolbar = QToolBar("編集ツール")
        self.addToolBar(self.edit_toolbar)
        
        # 削除
        delete_action = QAction("削除", self)
        delete_action.triggered.connect(self.deleteSelectedItems)
        self.edit_toolbar.addAction(delete_action)
        
        # 複製
        duplicate_action = QAction("複製", self)
        duplicate_action.triggered.connect(self.duplicateSelectedItems)
        self.edit_toolbar.addAction(duplicate_action)
        
        # グリッド設定
        self.edit_toolbar.addSeparator()
        
        # グリッド表示切替
        grid_action = QAction("グリッド表示", self)
        grid_action.setCheckable(True)
        grid_action.setChecked(True)
        grid_action.triggered.connect(self.toggleGrid)
        self.edit_toolbar.addAction(grid_action)
        
        # スナップ切替
        snap_action = QAction("スナップ", self)
        snap_action.setCheckable(True)
        snap_action.setChecked(True)
        snap_action.triggered.connect(self.toggleSnap)
        self.edit_toolbar.addAction(snap_action)
        
        # グリッド間隔
        self.edit_toolbar.addWidget(QLabel("グリッド間隔:"))
        grid_spacing = QDoubleSpinBox()
        grid_spacing.setRange(1, 100)
        grid_spacing.setValue(DEFAULT_GRID_SPACING)
        grid_spacing.valueChanged.connect(self.setGridSpacing)
        self.edit_toolbar.addWidget(grid_spacing)
    
    def createMenus(self):
        """メニューの作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル")
        
        new_action = QAction("新規作成", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.newFile)
        file_menu.addAction(new_action)
        
        open_action = QAction("開く...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.openFile)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.saveFile)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("名前を付けて保存...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.saveFileAs)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("終了", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 編集メニュー
        edit_menu = menubar.addMenu("編集")
        
        delete_action = QAction("削除", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self.deleteSelectedItems)
        edit_menu.addAction(delete_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu("表示")
        
        zoom_in_action = QAction("ズームイン", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self.zoomIn)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("ズームアウト", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self.zoomOut)
        view_menu.addAction(zoom_out_action)
        
        zoom_fit_action = QAction("全体表示", self)
        zoom_fit_action.triggered.connect(self.zoomFit)
        view_menu.addAction(zoom_fit_action)
    
    def updateCoordinates(self, x, y):
        """座標表示の更新"""
        self.coords_label.setText(f"X: {x:.2f}  Y: {y:.2f}")
    
    def updateStatusBar(self):
        """ステータスバーの更新"""
        mode_text = ""
        if self.current_mode == DrawingMode.SELECT:
            mode_text = "選択モード"
        elif self.current_mode == DrawingMode.LINE:
            mode_text = "線描画モード"
        elif self.current_mode == DrawingMode.RECTANGLE:
            mode_text = "長方形描画モード"
        elif self.current_mode == DrawingMode.CIRCLE:
            mode_text = "円描画モード"
        elif self.current_mode == DrawingMode.ARC:
            mode_text = "円弧描画モード"
        elif self.current_mode == DrawingMode.POLYLINE:
            mode_text = "ポリライン描画モード"
        elif self.current_mode == DrawingMode.TEXT:
            mode_text = "テキスト入力モード"
        
        self.statusBar.showMessage(mode_text)
    
    def setDrawingMode(self, mode):
        """描画モードの設定"""
        self.current_mode = mode
        self.updateStatusBar()
        
        # 描画開始点をリセット
        self.drawing_start_point = None
        self.view.clearTempItems()
        
        # アクションの状態を更新
        for action in self.mode_actions:
            action.setChecked(False)
        self.mode_actions[mode].setChecked(True)
        
        # 選択モード以外ではビューの選択モードを無効化
        if mode == DrawingMode.SELECT:
            self.view.setDragMode(QGraphicsView.RubberBandDrag)
        else:
            self.view.setDragMode(QGraphicsView.NoDrag)
    
    def toggleGrid(self, checked):
        """グリッド表示の切り替え"""
        self.view.setGridVisible(checked)
    
    def toggleSnap(self, checked):
        """スナップの切り替え"""
        self.view.setSnapEnabled(checked)
    
    def setGridSpacing(self, spacing):
        """グリッド間隔の設定"""
        self.view.setGridSpacing(spacing)
    
    def deleteSelectedItems(self):
        """選択されたアイテムの削除"""
        for item in self.scene.selectedItems():
            self.scene.removeItem(item)
        self.file_modified = True
    
    def duplicateSelectedItems(self):
        """選択されたアイテムの複製"""
        # 実装予定
        pass
    
    def zoomIn(self):
        """ズームイン"""
        self.view.scale(1.2, 1.2)
    
    def zoomOut(self):
        """ズームアウト"""
        self.view.scale(1/1.2, 1/1.2)
    
    def zoomFit(self):
        """全体表示"""
        # シーンの領域を取得
        scene_rect = self.scene.itemsBoundingRect()
        # 余白を追加
        scene_rect.adjust(-50, -50, 50, 50)
        # ビューにフィット
        self.view.fitInView(scene_rect, Qt.KeepAspectRatio)
    
    def newFile(self):
        """新規ファイル作成"""
        # 変更があれば保存確認
        if self.file_modified:
            reply = QMessageBox.question(
                self, "確認", "変更を保存しますか？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.saveFile()
            elif reply == QMessageBox.Cancel:
                return
        
        # シーンをクリア
        self.scene.clear()
        self.current_file = None
        self.file_modified = False
        self.setWindowTitle(f"{APP_NAME} - 新規ファイル")
    
    def openFile(self):
        """ファイルを開く"""
        # 変更があれば保存確認
        if self.file_modified:
            reply = QMessageBox.question(
                self, "確認", "変更を保存しますか？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.saveFile()
            elif reply == QMessageBox.Cancel:
                return
        
        # ファイル選択ダイアログ
        file_path, _ = QFileDialog.getOpenFileName(
            self, "ファイルを開く", "",
            "DXFファイル (*.dxf);;すべてのファイル (*.*)"
        )
        
        if file_path:
            self.loadFile(file_path)
    
    def loadFile(self, file_path):
        """ファイルの読み込み"""
        try:
            # DXFファイルをロード
            doc = ezdxf.readfile(file_path)
            
            # シーンをクリア
            self.scene.clear()
            
            # モデルスペースを取得
            msp = doc.modelspace()
            
            # エンティティを処理
            for entity in msp:
                entity_type = entity.dxftype()
                
                # 色の処理
                if hasattr(entity.dxf, 'color'):
                    color_index = entity.dxf.color
                    rgb = pdf.dxf_color_to_rgb(color_index)
                    color = QColor(rgb[0], rgb[1], rgb[2])
                else:
                    color = QColor(0, 0, 0)  # デフォルト黒
                
                # エンティティデータの計算
                entity_data = pdf.process_entity_data(
                    entity, 
                    (color.red(), color.green(), color.blue()),
                    self.current_line_width
                )
                
                if entity_data.success:
                    # 描画データのタイプに応じて処理
                    if isinstance(entity_data.data, pdf.LineData):
                        self.adapter.draw_line(entity_data.data)
                    elif isinstance(entity_data.data, pdf.CircleData):
                        self.adapter.draw_circle(entity_data.data)
                    elif isinstance(entity_data.data, pdf.ArcData):
                        self.adapter.draw_arc(entity_data.data)
                    elif isinstance(entity_data.data, pdf.PolylineData):
                        self.adapter.draw_polyline(entity_data.data)
                    elif isinstance(entity_data.data, pdf.TextData):
                        self.adapter.draw_text(entity_data.data)
            
            # 現在のファイルパスを設定
            self.current_file = file_path
            self.file_modified = False
            self.setWindowTitle(f"{APP_NAME} - {os.path.basename(file_path)}")
            
            # 全体表示
            self.zoomFit()
            
            logger.info(f"ファイルを読み込みました: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", 
                f"ファイルの読み込みに失敗しました: {str(e)}"
            )
            logger.error(f"ファイル読み込みエラー: {str(e)}")
    
    def saveFile(self):
        """ファイルの保存"""
        if self.current_file:
            self.saveFileToPath(self.current_file)
        else:
            self.saveFileAs()
    
    def saveFileAs(self):
        """名前を付けて保存"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "名前を付けて保存", "",
            "DXFファイル (*.dxf);;すべてのファイル (*.*)"
        )
        
        if file_path:
            self.saveFileToPath(file_path)
    
    def saveFileToPath(self, file_path):
        """指定パスにファイルを保存"""
        try:
            # 新しいDXFドキュメントを作成
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # シーン内のアイテムをDXFエンティティに変換
            # (実装予定)
            
            # ファイルに保存
            doc.saveas(file_path)
            
            # 現在のファイルパスを更新
            self.current_file = file_path
            self.file_modified = False
            self.setWindowTitle(f"{APP_NAME} - {os.path.basename(file_path)}")
            
            logger.info(f"ファイルを保存しました: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(
                self, "エラー", 
                f"ファイルの保存に失敗しました: {str(e)}"
            )
            logger.error(f"ファイル保存エラー: {str(e)}")

    def handleMousePressed(self, x, y, button):
        """マウス押下イベントの処理"""
        # 左ボタンのみ処理
        if button != Qt.LeftButton:
            return
            
        if self.current_mode == DrawingMode.SELECT:
            # 選択モードでは何もしない（Qtの標準選択処理に任せる）
            pass
        elif self.current_mode == DrawingMode.LINE:
            # 線の開始点を記録
            self.drawing_start_point = QPointF(x, y)
            # 仮の線を描画
            pen = QPen(self.current_color)
            pen.setWidthF(self.current_line_width)
            self.current_item = self.view.addTempItem(
                self.scene.addLine(QLineF(x, y, x, y), pen))
        elif self.current_mode == DrawingMode.RECTANGLE:
            # 長方形の開始点を記録
            self.drawing_start_point = QPointF(x, y)
            # 仮の長方形を描画
            pen = QPen(self.current_color)
            pen.setWidthF(self.current_line_width)
            self.current_item = self.view.addTempItem(
                self.scene.addRect(QRectF(x, y, 0, 0), pen))
        elif self.current_mode == DrawingMode.CIRCLE:
            # 円の中心点を記録
            self.drawing_start_point = QPointF(x, y)
            # 仮の円を描画
            pen = QPen(self.current_color)
            pen.setWidthF(self.current_line_width)
            self.current_item = self.view.addTempItem(
                self.scene.addEllipse(QRectF(x-0.1, y-0.1, 0.2, 0.2), pen))
        elif self.current_mode == DrawingMode.ARC:
            # 円弧の処理は後で実装
            pass
        elif self.current_mode == DrawingMode.POLYLINE:
            # ポリラインの処理は後で実装
            pass
        elif self.current_mode == DrawingMode.TEXT:
            # テキスト入力ダイアログを表示
            text, ok = QInputDialog.getText(self, "テキスト入力", "テキスト:")
            if ok and text:
                # テキストアイテムを追加
                text_item = self.scene.addText(text)
                text_item.setDefaultTextColor(self.current_color)
                text_item.setPos(x, y)
                text_item.setFlag(QGraphicsItem.ItemIsSelectable)
                text_item.setFlag(QGraphicsItem.ItemIsMovable)
                self.file_modified = True
    
    def handleMouseMoved(self, x, y):
        """マウス移動イベントの処理"""
        # 座標表示の更新
        self.updateCoordinates(x, y)
        
        # 描画中のアイテムの更新
        if self.drawing_start_point is not None and self.current_item is not None:
            if self.current_mode == DrawingMode.LINE:
                # 線の更新
                line = QLineF(
                    self.drawing_start_point.x(), self.drawing_start_point.y(),
                    x, y
                )
                self.current_item.setLine(line)
            elif self.current_mode == DrawingMode.RECTANGLE:
                # 長方形の更新
                rect = QRectF(
                    self.drawing_start_point.x(),
                    self.drawing_start_point.y(),
                    x - self.drawing_start_point.x(),
                    y - self.drawing_start_point.y()
                )
                self.current_item.setRect(rect.normalized())
            elif self.current_mode == DrawingMode.CIRCLE:
                # 円の更新
                dx = x - self.drawing_start_point.x()
                dy = y - self.drawing_start_point.y()
                radius = (dx**2 + dy**2)**0.5
                
                rect = QRectF(
                    self.drawing_start_point.x() - radius,
                    self.drawing_start_point.y() - radius,
                    radius * 2,
                    radius * 2
                )
                self.current_item.setRect(rect)
    
    def handleMouseReleased(self, x, y, button):
        """マウスリリースイベントの処理"""
        # 左ボタンのみ処理
        if button != Qt.LeftButton:
            return
            
        if self.drawing_start_point is not None:
            if self.current_mode == DrawingMode.LINE:
                # 線の確定
                if (self.drawing_start_point.x() != x or self.drawing_start_point.y() != y):
                    # 一時的なアイテムを削除
                    self.view.clearTempItems()
                    
                    # 実際の線を追加
                    pen = QPen(self.current_color)
                    pen.setWidthF(self.current_line_width)
                    line = self.scene.addLine(
                        QLineF(
                            self.drawing_start_point.x(), self.drawing_start_point.y(),
                            x, y
                        ),
                        pen
                    )
                    line.setFlag(QGraphicsItem.ItemIsSelectable)
                    line.setFlag(QGraphicsItem.ItemIsMovable)
                    self.file_modified = True
            elif self.current_mode == DrawingMode.RECTANGLE:
                # 長方形の確定
                if (self.drawing_start_point.x() != x or self.drawing_start_point.y() != y):
                    # 一時的なアイテムを削除
                    self.view.clearTempItems()
                    
                    # 実際の長方形を追加
                    pen = QPen(self.current_color)
                    pen.setWidthF(self.current_line_width)
                    rect = QRectF(
                        self.drawing_start_point.x(),
                        self.drawing_start_point.y(),
                        x - self.drawing_start_point.x(),
                        y - self.drawing_start_point.y()
                    ).normalized()
                    
                    rectangle = self.scene.addRect(rect, pen)
                    rectangle.setFlag(QGraphicsItem.ItemIsSelectable)
                    rectangle.setFlag(QGraphicsItem.ItemIsMovable)
                    self.file_modified = True
            elif self.current_mode == DrawingMode.CIRCLE:
                # 円の確定
                dx = x - self.drawing_start_point.x()
                dy = y - self.drawing_start_point.y()
                radius = (dx**2 + dy**2)**0.5
                
                if radius > 0:
                    # 一時的なアイテムを削除
                    self.view.clearTempItems()
                    
                    # 実際の円を追加
                    pen = QPen(self.current_color)
                    pen.setWidthF(self.current_line_width)
                    rect = QRectF(
                        self.drawing_start_point.x() - radius,
                        self.drawing_start_point.y() - radius,
                        radius * 2,
                        radius * 2
                    )
                    
                    circle = self.scene.addEllipse(rect, pen)
                    circle.setFlag(QGraphicsItem.ItemIsSelectable)
                    circle.setFlag(QGraphicsItem.ItemIsMovable)
                    self.file_modified = True
            
            # 描画データをリセット
            self.drawing_start_point = None
            self.current_item = None

    def change_background_color(self):
        """背景色を変更する"""
        color = QColorDialog.getColor()
        if color.isValid():
            bg_color = (color.red(), color.green(), color.blue())
            self.adapter.set_background_color(bg_color)
            self.statusBar.showMessage(f"背景色を変更しました: RGB{bg_color}")
    
    def change_line_color(self):
        """線の色を変更する"""
        color = QColorDialog.getColor()
        if color.isValid():
            line_color = (color.red(), color.green(), color.blue())
            # 線の色を変更する処理を追加
            self.adapter.apply_color_to_all_items(line_color)
            self.statusBar.showMessage(f"線の色を変更しました: RGB{line_color}")
    
    def change_theme(self, index):
        """テーマを変更する"""
        if index == 0:  # 明るいテーマ
            # 白背景、黒線
            self.adapter.set_theme((255, 255, 255), (0, 0, 0))
            theme_name = "明るいテーマ"
        else:  # 暗いテーマ
            # 黒背景、白線
            self.adapter.set_theme((0, 0, 0), (255, 255, 255))
            theme_name = "暗いテーマ"
        
        self.statusBar.showMessage(f"テーマを{theme_name}に変更しました")

# メイン関数
def main():
    app = QApplication(sys.argv)
    main_window = CAD2DMainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 