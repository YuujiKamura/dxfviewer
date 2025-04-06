#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Triangle Manager UI - 三角形管理ユーザーインターフェース

三角形データを管理・編集するためのUIコンポーネント
"""

import sys
import logging
from pathlib import Path

# PySide6のインポート
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox, 
    QComboBox, QFileDialog, QFrame, QStatusBar,
    QGraphicsScene, QGraphicsTextItem, QGraphicsSimpleTextItem
)
from PySide6.QtGui import QPainter, QColor, QDoubleValidator
from PySide6.QtCore import Qt, QPointF

# 親ディレクトリをパスに追加
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# 三角形関連モジュールをインポート
from ui.graphics_view import DxfGraphicsView
from triangle_ui.triangle_data import TriangleData, TriangleManager, TriangleExporter
from triangle_ui.triangle_ui_item import TriangleItem, add_triangle_item_to_scene

# ロガー設定
logger = logging.getLogger(__name__)

# UIデザイン定数
class UIConstants:
    # ウィンドウサイズ
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # コントロールサイズ
    CONTROL_HEIGHT = 36      # 標準コントロールの高さ
    BUTTON_HEIGHT = 36       # ボタンの高さ
    BUTTON_WIDTH = 120       # ボタンの幅
    INPUT_HEIGHT = 36        # 入力フィールドの高さ
    INPUT_WIDTH = 80         # 入力フィールドの幅
    
    # フォントサイズ
    DEFAULT_FONT_SIZE = 10   # 基本フォントサイズ
    BUTTON_FONT_SIZE = 20    # ボタン用フォントサイズ（標準の2倍）
    LABEL_FONT_SIZE = 12     # ラベル用フォントサイズ
    INPUT_FONT_SIZE = 15     # 入力フィールド用フォントサイズ（基本の1.5倍）
    DIMENSION_FONT_SIZE = 6  # 三角形の寸法表示サイズ
    
    # 色の定義
    BACKGROUND_COLOR = "#f0f0f0"
    BUTTON_COLOR = "#e0e0e0"
    HIGHLIGHT_COLOR = "#d0d0d0"
    FORM_BACKGROUND = "#f8f8f8"
    
    # スタイルシート
    CONTROL_STYLE = f"""
        QWidget {{ background-color: {BACKGROUND_COLOR}; }}
        QPushButton {{ 
            min-height: {BUTTON_HEIGHT}px; 
            min-width: {BUTTON_WIDTH}px;
            background-color: {BUTTON_COLOR};
            padding: 5px;
            border: 1px solid #a0a0a0;
            border-radius: 4px;
            font-size: {BUTTON_FONT_SIZE}pt;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {HIGHLIGHT_COLOR}; }}
        QLineEdit {{ 
            min-height: {INPUT_HEIGHT}px; 
            min-width: {INPUT_WIDTH}px;
            padding: 3px;
            border: 1px solid #a0a0a0;
            border-radius: 4px;
            font-size: {INPUT_FONT_SIZE}pt;
            font-weight: bold;
        }}
        QLabel {{ 
            font-size: {LABEL_FONT_SIZE}pt; 
            min-height: {CONTROL_HEIGHT // 2}px;
        }}
    """

# TriangleManagerウィンドウ
class TriangleManagerWindow(QMainWindow):
    """三角形管理UIのメインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # UIデザイン定数を適用
        self.dimension_font_size = UIConstants.DIMENSION_FONT_SIZE
        
        # ウィンドウの設定
        self.setWindowTitle("Triangle Manager")
        self.resize(UIConstants.WINDOW_WIDTH, UIConstants.WINDOW_HEIGHT)
        
        # メインウィジェットとレイアウト
        main_widget = QWidget()
        main_widget.setStyleSheet(UIConstants.CONTROL_STYLE)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # ビューとシーンの設定
        self.view = DxfGraphicsView()
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        main_layout.addWidget(self.view, 1)
        
        # 背景クリック時のハンドラを設定
        self.view.scene().mouseReleaseEvent = self.scene_mouse_release_event
        
        # コントロールパネルの作成
        self.control_panel = self.create_control_panel()
        main_layout.addWidget(self.control_panel)
        
        # ステータスバーの設定
        self.statusBar().showMessage("準備完了")
        
        # 三角形マネージャーの初期化
        self.triangle_manager = TriangleManager()
        
        # 選択状態の初期化
        self.selected_parent_number = -1
        self.selected_side_index = -1
        
        # 最初の三角形を作成
        initial_triangle = TriangleData(100.0, 100.0, 100.0, QPointF(0, 0), 180.0, 1)
        self.add_triangle(initial_triangle)
        
        # 三角形選択コンボボックスを更新
        self.update_triangle_combo()
    
    def create_control_panel(self):
        """コントロールパネルを作成"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 情報表示部分
        info_group = QWidget()
        info_layout = QVBoxLayout(info_group)
        
        # 選択情報
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("選択中:"))
        self.selected_info_label = QLabel("なし")
        selection_layout.addWidget(self.selected_info_label)
        info_layout.addLayout(selection_layout)
        
        layout.addWidget(info_group)
        
        # 入力部分
        input_group = QWidget()
        input_layout = QVBoxLayout(input_group)
        
        # 辺の長さ入力 - 3つの入力欄を並べるように変更
        lengths_layout = QHBoxLayout()
        
        # 三角形選択コンボボックス（左側に配置）
        lengths_layout.addWidget(QLabel("三角形選択:"))
        self.triangle_combo = QComboBox()
        self.triangle_combo.setMinimumWidth(100)
        self.triangle_combo.addItem("---", -1)  # デフォルト選択なし
        self.triangle_combo.currentIndexChanged.connect(self.on_triangle_selected)
        
        # フォントサイズを設定
        font = self.triangle_combo.font()
        font.setPointSize(15)  # UIConstants.INPUT_FONT_SIZEの値
        self.triangle_combo.setFont(font)
        
        lengths_layout.addWidget(self.triangle_combo)
        
        # 横方向のスペーサーを追加（縦の区切り線を追加）
        vertical_line = QFrame()
        vertical_line.setFrameShape(QFrame.VLine)
        vertical_line.setFrameShadow(QFrame.Sunken)
        lengths_layout.addWidget(vertical_line)
        
        # 辺A
        lengths_layout.addWidget(QLabel("辺A:"))
        self.new_len_a_input = QLineEdit()
        self.new_len_a_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        self.new_len_a_input.setText("100.0")
        lengths_layout.addWidget(self.new_len_a_input)
        
        # 辺B
        lengths_layout.addWidget(QLabel("辺B:"))
        self.new_len_b_input = QLineEdit()
        self.new_len_b_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        self.new_len_b_input.setText("80.0")
        lengths_layout.addWidget(self.new_len_b_input)
        
        # 辺C
        lengths_layout.addWidget(QLabel("辺C:"))
        self.new_len_c_input = QLineEdit()
        self.new_len_c_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        self.new_len_c_input.setText("80.0")
        lengths_layout.addWidget(self.new_len_c_input)
        
        input_layout.addLayout(lengths_layout)
        
        # ボタン
        buttons_layout = QHBoxLayout()
        
        # 追加ボタン
        self.add_button = QPushButton("三角形を追加")
        self.add_button.clicked.connect(self.on_add_triangle)
        buttons_layout.addWidget(self.add_button)
        
        # 更新ボタン
        self.update_triangle_button = QPushButton("三角形を更新")
        self.update_triangle_button.clicked.connect(self.on_update_triangle)
        self.update_triangle_button.setEnabled(False)  # 初期状態は無効
        buttons_layout.addWidget(self.update_triangle_button)
        
        # DXF出力ボタン
        self.export_dxf_button = QPushButton("DXF出力")
        self.export_dxf_button.clicked.connect(self.on_export_dxf)
        buttons_layout.addWidget(self.export_dxf_button)
        
        input_layout.addLayout(buttons_layout)
        
        layout.addWidget(input_group)
        
        return panel
    
    def add_triangle(self, triangle_data):
        """三角形を追加してUIに表示"""
        # 三角形マネージャーに追加
        self.triangle_manager.add_triangle(triangle_data)
        
        # シーンに表示
        triangle_item = add_triangle_item_to_scene(
            self.view.scene(), 
            triangle_data, 
            self.dimension_font_size
        )
        
        # 辺クリックシグナルの接続
        triangle_item.signalHelper.sideClicked.connect(self.handle_side_clicked)
        
        # ビューを更新
        self.view.initialize_view()
        
        # 三角形選択コンボボックスを更新
        self.update_triangle_combo()
    
    def on_add_triangle(self):
        """三角形追加ボタンがクリックされたとき"""
        # 選択チェック
        if self.selected_parent_number < 0 or self.selected_side_index < 0:
            QMessageBox.warning(self, "選択エラー", "三角形の辺が選択されていません")
            return
        
        # 新しい辺の長さを取得
        try:
            len_a = float(self.new_len_a_input.text())
            len_b = float(self.new_len_b_input.text())
            len_c = float(self.new_len_c_input.text())
        except ValueError:
            QMessageBox.warning(self, "入力エラー", "辺の長さには有効な数値を入力してください")
            return
        
        # 三角形マネージャーを使って新しい三角形を作成
        new_triangle = self.triangle_manager.create_triangle_at_side(
            self.selected_parent_number,
            self.selected_side_index,
            [len_a, len_b, len_c]
        )
        
        if not new_triangle:
            QMessageBox.warning(self, "作成エラー", "三角形を作成できませんでした")
            return
        
        # 三角形をUIに表示
        triangle_item = add_triangle_item_to_scene(
            self.view.scene(), 
            new_triangle, 
            self.dimension_font_size
        )
        
        # 辺クリックシグナルの接続
        triangle_item.signalHelper.sideClicked.connect(self.handle_side_clicked)
        
        # ビューを更新
        self.view.fit_scene_in_view()
        
        # 三角形選択コンボボックスを更新
        self.update_triangle_combo()
        
        # 選択をクリア
        self.clear_selection()
        
        self.statusBar().showMessage(f"三角形 {new_triangle.number} を追加しました")
    
    def on_update_triangle(self):
        """三角形更新ボタンがクリックされたとき"""
        # 選択チェック
        if self.selected_parent_number < 0:
            QMessageBox.warning(self, "選択エラー", "三角形が選択されていません")
            return
        
        # 三角形を取得
        triangle = self.triangle_manager.get_triangle_by_number(self.selected_parent_number)
        if not triangle:
            QMessageBox.warning(self, "エラー", "選択された三角形が見つかりません")
            return
        
        # 新しい辺の長さを取得
        try:
            len_a = float(self.new_len_a_input.text())
            len_b = float(self.new_len_b_input.text())
            len_c = float(self.new_len_c_input.text())
        except ValueError:
            QMessageBox.warning(self, "入力エラー", "辺の長さには有効な数値を入力してください")
            return
        
        # 三角形を更新
        if self.triangle_manager.update_triangle_and_propagate(triangle, [len_a, len_b, len_c]):
            # 更新成功したら、シーンを再描画
            self.refresh_scene()
            self.view.fit_scene_in_view()
            self.statusBar().showMessage(f"三角形 {triangle.number} を更新しました")
        else:
            QMessageBox.warning(self, "更新エラー", "三角形を更新できませんでした")
    
    def on_export_dxf(self):
        """DXF出力ボタンがクリックされたとき"""
        # 保存ファイル名を取得
        file_path, _ = QFileDialog.getSaveFileName(
            self, "DXFファイルを保存", "", "DXF Files (*.dxf)"
        )
        
        if not file_path:
            return  # ユーザーがキャンセルした場合
        
        # DXF出力
        if TriangleExporter.export_to_dxf(self.triangle_manager.triangle_list, file_path):
            self.statusBar().showMessage(f"DXFファイルを保存しました: {file_path}")
            QMessageBox.information(self, "DXF出力", f"三角形データをDXFファイルに出力しました。\n{file_path}")
        else:
            QMessageBox.critical(self, "DXF出力エラー", "DXFファイルの出力中にエラーが発生しました。")
    
    def refresh_scene(self):
        """シーンを再描画する"""
        # シーンをクリア
        self.view.scene().clear()
        
        # 三角形アイテムを再作成
        for triangle in self.triangle_manager.triangle_list:
            triangle_item = add_triangle_item_to_scene(
                self.view.scene(), 
                triangle, 
                self.dimension_font_size
            )
            
            # 辺クリックシグナルの接続
            triangle_item.signalHelper.sideClicked.connect(self.handle_side_clicked)
    
    def update_triangle_combo(self):
        """三角形選択コンボボックスを更新"""
        # 現在の選択を保存
        current_selection = self.triangle_combo.currentData()
        
        # コンボボックスをクリア
        self.triangle_combo.blockSignals(True)  # シグナルを一時停止
        self.triangle_combo.clear()
        self.triangle_combo.addItem("---", -1)  # デフォルト選択なし
        
        # 三角形リストを反復処理
        for triangle in sorted(self.triangle_manager.triangle_list, key=lambda t: t.number):
            if triangle.number > 0:  # 有効な三角形番号のみ
                self.triangle_combo.addItem(f"三角形 {triangle.number}", triangle.number)
        
        # 前の選択を復元（可能な場合）
        if current_selection != -1:
            index = self.triangle_combo.findData(current_selection)
            if index >= 0:
                self.triangle_combo.setCurrentIndex(index)
            else:
                self.triangle_combo.setCurrentIndex(0)  # デフォルト選択
        
        self.triangle_combo.blockSignals(False)  # シグナルを再開
    
    def on_triangle_selected(self, index):
        """コンボボックスから三角形が選択されたとき"""
        # 選択された三角形番号を取得
        triangle_number = self.triangle_combo.currentData()
        
        # 無効な選択の場合は何もしない
        if triangle_number == -1:
            return
        
        # 三角形を取得
        triangle = self.triangle_manager.get_triangle_by_number(triangle_number)
        if not triangle:
            return
        
        # 選択情報を更新（辺は選択されていない状態）
        self.selected_parent_number = triangle_number
        self.selected_side_index = -1  # 辺は選択されていない
        
        # 三角形の情報をフォームに反映
        self.new_len_a_input.setText(f"{triangle.lengths[0]:.1f}")
        self.new_len_b_input.setText(f"{triangle.lengths[1]:.1f}")
        self.new_len_c_input.setText(f"{triangle.lengths[2]:.1f}")
        
        # 選択情報を表示
        self.selected_info_label.setText(f"三角形 {triangle_number}")
        
        # 更新ボタンを有効化
        self.update_triangle_button.setEnabled(True)
        
        # シーン内の三角形の表示を更新
        self.highlight_triangle(triangle_number)
        
        # 詳細情報をステータスバーに表示
        self.statusBar().showMessage(f"三角形 {triangle_number} を選択しました")
    
    def highlight_triangle(self, triangle_number):
        """三角形を強調表示する"""
        for item in self.view.scene().items():
            if isinstance(item, TriangleItem):
                if item.triangle_data.number == triangle_number:
                    # 選択された三角形を強調表示
                    item.setOpacity(1.0)
                    pen = item.pen()
                    pen.setWidth(2)
                    pen.setColor(QColor(255, 0, 0))  # 赤色で強調
                    item.setPen(pen)
                else:
                    # 他の三角形は通常表示
                    item.setOpacity(0.7)
                    pen = item.pen()
                    pen.setWidth(1)
                    pen.setColor(item.triangle_data.color)
                    item.setPen(pen)
    
    def handle_side_clicked(self, triangle_number, side_index):
        """三角形の辺がクリックされたときの処理"""
        # 選択情報を保存
        self.selected_parent_number = triangle_number
        self.selected_side_index = side_index
        
        # 選択された三角形を取得
        triangle = self.triangle_manager.get_triangle_by_number(triangle_number)
        if not triangle:
            return
        
        # 選択情報を表示
        self.selected_info_label.setText(f"三角形 {triangle_number} の辺 {chr(65 + side_index)}")
        
        # 入力欄に現在の値をセット
        self.new_len_a_input.setText(f"{triangle.lengths[0]:.1f}")
        self.new_len_b_input.setText(f"{triangle.lengths[1]:.1f}")
        self.new_len_c_input.setText(f"{triangle.lengths[2]:.1f}")
        
        # 更新ボタンを有効化
        self.update_triangle_button.setEnabled(True)
        
        # コンボボックスの選択も更新
        self.triangle_combo.blockSignals(True)
        index = self.triangle_combo.findData(triangle_number)
        if index >= 0:
            self.triangle_combo.setCurrentIndex(index)
        self.triangle_combo.blockSignals(False)
        
        # 選択された辺をハイライト
        for item in self.view.scene().items():
            if isinstance(item, TriangleItem):
                if item.triangle_data.number == triangle_number:
                    # 選択された三角形の辺をハイライト
                    item.highlight_selected_side(side_index)
                else:
                    # 他の三角形の選択をクリア
                    item.highlight_selected_side(None)
        
        # 詳細情報をステータスバーに表示
        detailed_info = TriangleData.get_detailed_edge_info(triangle, side_index)
        self.statusBar().showMessage(detailed_info)
    
    def clear_selection(self):
        """選択をクリア"""
        # すべての三角形の選択状態をクリア
        for item in self.view.scene().items():
            if isinstance(item, TriangleItem):
                item.highlight_selected_side(None)
                item.setOpacity(1.0)  # 透明度をリセット
                pen = item.pen()
                pen.setWidth(1)  # 線の太さをリセット
                pen.setColor(item.triangle_data.color)  # 色をリセット
                item.setPen(pen)
        
        # 内部の選択状態をリセット
        self.selected_parent_number = -1
        self.selected_side_index = -1
        self.selected_info_label.setText("なし")
        self.update_triangle_button.setEnabled(False)
        
        # コンボボックスの選択をリセット
        self.triangle_combo.blockSignals(True)
        self.triangle_combo.setCurrentIndex(0)  # "---" を選択
        self.triangle_combo.blockSignals(False)
        
        # ステータスバーをクリア
        self.statusBar().showMessage("選択をクリアしました")
    
    def scene_mouse_release_event(self, event):
        """シーンのマウスリリースイベント処理"""
        # クリックされたアイテムを取得
        clicked_items = self.view.scene().items(event.scenePos())
        
        if clicked_items:
            # テキストアイテムのクリックを処理
            for item in clicked_items:
                # 三角形番号クリック
                if hasattr(item, 'data') and item.data(0) is not None and isinstance(item.data(0), int):
                    triangle_number = item.data(0)
                    
                    # 三角形番号のテキストアイテム
                    if isinstance(item, QGraphicsTextItem):
                        logging.debug(f"三角形番号 {triangle_number} をクリック")
                        index = self.triangle_combo.findData(triangle_number)
                        if index >= 0:
                            self.triangle_combo.setCurrentIndex(index)  # コンボボックスの選択を変更
                        return
                
                # 寸法テキストのクリック
                if hasattr(item, 'data') and item.data(0) is not None and item.data(1) is not None:
                    # 三角形番号と辺インデックス
                    triangle_number = item.data(1)
                    side_index = item.data(0)
                    
                    if isinstance(side_index, int) and 0 <= side_index <= 2:
                        logging.debug(f"寸法テキストのクリック: 三角形={triangle_number}, 辺={side_index}")
                        self.handle_side_clicked(triangle_number, side_index)
                        return
        else:
            # 背景クリック - すべての選択をクリア
            logging.debug("背景クリック: すべての選択をクリア")
            self.clear_selection()
        
        # 親クラスの処理を呼び出す
        from PySide6.QtWidgets import QGraphicsScene
        QGraphicsScene.mouseReleaseEvent(self.view.scene(), event) 