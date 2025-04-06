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
    QGraphicsScene, QGraphicsTextItem, QGraphicsSimpleTextItem, QSizePolicy,
    QApplication, QDialog, QFormLayout, QDoubleSpinBox, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QDoubleValidator, QPen
from PySide6.QtCore import Qt, QPointF

# 親ディレクトリをパスに追加
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# 三角形関連モジュールをインポート
from ui.graphics_view import DxfGraphicsView
from shapes.geometry.triangle_shape import TriangleData, TriangleManager
from .triangle_exporters import DxfExporter, DxfExportSettings
from .triangle_io import JsonIO
from .triangle_graphics_item import TriangleItem, add_triangle_item_to_scene
from .triangle_ui_controls import TriangleControlPanel

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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # フォントサイズ
        self.dimension_font_size = 6
        
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
        self.control_panel = TriangleControlPanel()
        self.connect_control_signals()
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
    
    def connect_control_signals(self):
        """コントロールパネルのシグナルを接続"""
        # 自動シグナルマッピングを使用
        self.control_panel.connect_signals_to_handlers(self)
    
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
        length_values = self.control_panel.get_length_values()
        if length_values is None:
            QMessageBox.warning(self, "入力エラー", "辺の長さには有効な数値を入力してください")
            return
        
        len_a, len_b, len_c = length_values
        
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
        length_values = self.control_panel.get_length_values()
        if length_values is None:
            QMessageBox.warning(self, "入力エラー", "辺の長さには有効な数値を入力してください")
            return
        
        len_a, len_b, len_c = length_values
        
        # 三角形を更新
        if self.triangle_manager.update_triangle_and_propagate(triangle, [len_a, len_b, len_c]):
            # 更新成功したら、シーンを再描画
            self.refresh_scene()
            self.view.fit_scene_in_view()
            self.statusBar().showMessage(f"三角形 {triangle.number} を更新しました")
        else:
            QMessageBox.warning(self, "更新エラー", "三角形を更新できませんでした")
    
    def show_dxf_export_settings_dialog(self):
        """DXFエクスポート設定ダイアログを表示する"""
        # 設定ダイアログの作成
        dialog = QDialog(self)
        dialog.setWindowTitle("DXFエクスポート設定")
        dialog.setMinimumWidth(400)
        
        # レイアウト
        layout = QFormLayout(dialog)
        
        # 辺のテキストサイズ
        edge_text_scale = QDoubleSpinBox()
        edge_text_scale.setRange(0.01, 1.0)
        edge_text_scale.setSingleStep(0.01)
        edge_text_scale.setValue(0.05)
        edge_text_scale.setDecimals(3)
        edge_text_scale.setSuffix(" × 辺の長さ")
        layout.addRow("辺の長さテキストサイズ:", edge_text_scale)
        
        # 番号のテキストサイズ
        number_text_scale = QDoubleSpinBox()
        number_text_scale.setRange(0.01, 1.0)
        number_text_scale.setSingleStep(0.01)
        number_text_scale.setValue(0.1)
        number_text_scale.setDecimals(3)
        number_text_scale.setSuffix(" × 最大辺の長さ")
        layout.addRow("三角形番号テキストサイズ:", number_text_scale)
        
        # 表示オプション
        show_edge_lengths = QCheckBox("辺の長さを表示する")
        show_edge_lengths.setChecked(True)
        layout.addRow("", show_edge_lengths)
        
        show_triangle_numbers = QCheckBox("三角形番号を表示する")
        show_triangle_numbers.setChecked(True)
        layout.addRow("", show_triangle_numbers)
        
        auto_rotate_edge_text = QCheckBox("辺のテキストを辺に沿って回転させる")
        auto_rotate_edge_text.setChecked(True)
        layout.addRow("", auto_rotate_edge_text)
        
        # ボタン
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("キャンセル")
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addRow("", button_layout)
        
        # ボタンの接続
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 設定オブジェクト
        settings = DxfExportSettings()
        
        # ダイアログの表示
        if dialog.exec() == QDialog.Accepted:
            # 設定値の取得
            settings.edge_text_scale_factor = edge_text_scale.value()
            settings.number_text_scale_factor = number_text_scale.value()
            settings.show_edge_lengths = show_edge_lengths.isChecked()
            settings.show_triangle_numbers = show_triangle_numbers.isChecked()
            settings.auto_rotate_edge_text = auto_rotate_edge_text.isChecked()
            return settings
        else:
            return None  # キャンセルされた場合
    
    def on_export_dxf(self):
        """DXF出力ボタンがクリックされたとき"""
        # 出力ファイルの選択
        file_path, _ = QFileDialog.getSaveFileName(
            self, "DXFファイルを保存", "", "DXF Files (*.dxf);;All Files (*)"
        )
        
        if not file_path:
            return  # ユーザーがキャンセルした場合
        
        # .dxf拡張子を確保
        if not file_path.lower().endswith('.dxf'):
            file_path += '.dxf'
        
        # DXFエクスポート設定ダイアログを表示
        export_settings = self.show_dxf_export_settings_dialog()
        if export_settings is None:
            return  # ユーザーがキャンセルした場合
        
        # 三角形データを出力
        if DxfExporter.export(self.triangle_manager.triangle_list, file_path, export_settings):
            self.statusBar().showMessage(f"DXFファイルを保存しました: {file_path}")
        else:
            self.statusBar().showMessage("DXFファイルの保存中にエラーが発生しました")
            QMessageBox.warning(self, "エラー", "DXFファイルの保存中にエラーが発生しました。ログを確認してください。")
    
    def on_save_json(self):
        """JSON保存ボタンがクリックされたとき"""
        # 保存ファイル名を取得
        file_path, _ = QFileDialog.getSaveFileName(
            self, "JSONファイルを保存", "", "JSON Files (*.json)"
        )
        
        if not file_path:
            return  # ユーザーがキャンセルした場合
        
        # JSON出力
        if JsonIO.save_to_json(self.triangle_manager.triangle_list, file_path):
            self.statusBar().showMessage(f"JSONファイルを保存しました: {file_path}")
            QMessageBox.information(self, "JSON保存", f"三角形データをJSONファイルに保存しました。\n{file_path}")
        else:
            QMessageBox.critical(self, "JSON保存エラー", "JSONファイルの保存中にエラーが発生しました。")
    
    def on_load_json(self):
        """JSON読み込みボタンがクリックされたとき"""
        # 開くファイル名を取得
        file_path, _ = QFileDialog.getOpenFileName(
            self, "JSONファイルを開く", "", "JSON Files (*.json)"
        )
        
        if not file_path:
            return  # ユーザーがキャンセルした場合
        
        # 確認ダイアログを表示
        reply = QMessageBox.question(
            self,
            "確認",
            "現在の三角形データは削除されます。よろしいですか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # JSON読み込み
        triangles = JsonIO.load_from_json(file_path, TriangleData)
        
        if not triangles:
            QMessageBox.critical(self, "JSON読み込みエラー", "JSONファイルからデータを読み込めませんでした。")
            return
        
        # 現在のシーンをクリア
        self.view.scene().clear()
        
        # 三角形マネージャーを初期化
        self.triangle_manager = TriangleManager()
        
        # 読み込んだ三角形を追加
        for triangle in triangles:
            self.triangle_manager.add_triangle(triangle)
            
            # シーンに表示
            triangle_item = add_triangle_item_to_scene(
                self.view.scene(), 
                triangle, 
                self.dimension_font_size
            )
            
            # 辺クリックシグナルの接続
            triangle_item.signalHelper.sideClicked.connect(self.handle_side_clicked)
        
        # 三角形カウンターを更新
        self.triangle_manager.update_triangle_counter()
        
        # 三角形選択コンボボックスを更新
        self.update_triangle_combo()
        
        # ビューを全体表示に合わせる
        self.view.fit_scene_in_view()
        
        # 選択をクリア
        self.clear_selection()
        
        self.statusBar().showMessage(f"{len(triangles)}個の三角形データを{file_path}から読み込みました")
        QMessageBox.information(self, "JSON読み込み", f"{len(triangles)}個の三角形データを読み込みました。")
    
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
        current_selection = self.control_panel.get_triangle_combo().currentData()
        
        # コンボボックスをクリア
        self.control_panel.get_triangle_combo().blockSignals(True)  # シグナルを一時停止
        self.control_panel.clear_triangle_combo()
        
        # 三角形リストを反復処理
        for triangle in sorted(self.triangle_manager.triangle_list, key=lambda t: t.number):
            if triangle.number > 0:  # 有効な三角形番号のみ
                self.control_panel.add_triangle_to_combo(triangle.number)
        
        # 前の選択を復元（可能な場合）
        if current_selection != -1:
            index = self.control_panel.find_triangle_combo_data(current_selection)
            if index >= 0:
                self.control_panel.set_triangle_combo_index(index)
            else:
                self.control_panel.set_triangle_combo_index(0)  # デフォルト選択
        
        self.control_panel.get_triangle_combo().blockSignals(False)  # シグナルを再開
    
    def on_triangle_selected(self, index):
        """コンボボックスから三角形が選択されたとき"""
        # 選択された三角形番号を取得
        triangle_number = self.control_panel.get_triangle_combo().currentData()
        
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
        self.control_panel.set_length_values(
            triangle.lengths[0],
            triangle.lengths[1],
            triangle.lengths[2]
        )
        
        # 選択情報を表示
        self.control_panel.set_selected_info(f"三角形 {triangle_number}")
        
        # 更新ボタンを有効化
        self.control_panel.enable_update_button(True)
        
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
        self.control_panel.set_selected_info(f"三角形 {triangle_number} の辺 {chr(65 + side_index)}")
        
        # 入力欄に現在の値をセット
        self.control_panel.set_length_values(
            triangle.lengths[0],
            triangle.lengths[1],
            triangle.lengths[2]
        )
        
        # 更新ボタンを有効化
        self.control_panel.enable_update_button(True)
        
        # コンボボックスの選択も更新
        combo_index = self.control_panel.find_triangle_combo_data(triangle_number)
        if combo_index >= 0:
            self.control_panel.set_triangle_combo_index(combo_index, block_signals=True)
        
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
        self.control_panel.set_selected_info("なし")
        self.control_panel.enable_update_button(False)
        
        # コンボボックスの選択をリセット
        self.control_panel.set_triangle_combo_index(0, block_signals=True)
        
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
                        index = self.control_panel.find_triangle_combo_data(triangle_number)
                        if index >= 0:
                            self.control_panel.set_triangle_combo_index(index)  # コンボボックスの選択を変更
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