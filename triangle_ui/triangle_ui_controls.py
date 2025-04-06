#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleControlPanel - 三角形UIのコントロールパネル

三角形の作成・編集・保存のためのUI要素を含むコントロールパネルを提供します
"""

import logging
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QSizePolicy, QFrame
)
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QDoubleValidator

# ロガー設定
logger = logging.getLogger(__name__)

class TriangleControlSignals(QObject):
    """コントロールパネルからのシグナルを中継するクラス"""
    # 三角形追加ボタンがクリックされたシグナル
    addTriangleClicked = Signal()
    # 三角形更新ボタンがクリックされたシグナル
    updateTriangleClicked = Signal()
    # DXF出力ボタンがクリックされたシグナル
    exportDxfClicked = Signal()
    # JSON保存ボタンがクリックされたシグナル
    saveJsonClicked = Signal()
    # JSON読み込みボタンがクリックされたシグナル
    loadJsonClicked = Signal()
    # 三角形選択が変更されたシグナル (コンボボックスのインデックス)
    triangleSelected = Signal(int)

class TriangleControlPanel(QWidget):
    """三角形UIのコントロールパネルを提供するクラス"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # シグナルオブジェクトの作成
        self.signals = TriangleControlSignals()
        
        # UI要素の参照を保持する辞書
        self.ui_elements = {}
        
        # レイアウトの作成
        self.init_ui()
    
    def init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        
        # 情報表示部分
        info_group = QWidget()
        info_layout = QVBoxLayout(info_group)
        
        # 選択情報
        selection_layout = QHBoxLayout()
        # 選択中ラベルを作成し、固定幅を設定
        selection_label = QLabel("選択中:")
        selection_label.setFixedWidth(70)  # 固定幅を設定
        selection_layout.addWidget(selection_label)
        
        selected_info_label = QLabel("なし")
        # 水平方向のポリシーを設定
        selected_info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        selection_layout.addWidget(selected_info_label)
        # 余分なスペースを追加しない
        selection_layout.setStretch(0, 0)  # 選択中ラベルは固定
        selection_layout.setStretch(1, 1)  # 内容ラベルは拡張可能
        info_layout.addLayout(selection_layout)
        
        # UI要素の参照を保存
        self.ui_elements['selected_info_label'] = selected_info_label
        
        layout.addWidget(info_group)
        
        # 入力部分
        input_group = QWidget()
        input_layout = QVBoxLayout(input_group)
        
        # 辺の長さ入力 - 3つの入力欄を並べる
        lengths_layout = QHBoxLayout()
        
        # 三角形選択コンボボックス（左側に配置）
        lengths_layout.addWidget(QLabel("三角形選択:"))
        triangle_combo = QComboBox()
        triangle_combo.setMinimumWidth(100)
        triangle_combo.addItem("---", -1)  # デフォルト選択なし
        triangle_combo.currentIndexChanged.connect(self._on_triangle_selected)
        
        # フォントサイズを設定
        font = triangle_combo.font()
        font.setPointSize(15)
        triangle_combo.setFont(font)
        
        lengths_layout.addWidget(triangle_combo)
        
        # UI要素の参照を保存
        self.ui_elements['triangle_combo'] = triangle_combo
        
        # 横方向のスペーサーを追加（縦の区切り線を追加）
        vertical_line = QFrame()
        vertical_line.setFrameShape(QFrame.VLine)
        vertical_line.setFrameShadow(QFrame.Sunken)
        lengths_layout.addWidget(vertical_line)
        
        # 辺A
        lengths_layout.addWidget(QLabel("辺A:"))
        new_len_a_input = QLineEdit()
        new_len_a_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        new_len_a_input.setText("100.0")
        lengths_layout.addWidget(new_len_a_input)
        
        # 辺B
        lengths_layout.addWidget(QLabel("辺B:"))
        new_len_b_input = QLineEdit()
        new_len_b_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        new_len_b_input.setText("80.0")
        lengths_layout.addWidget(new_len_b_input)
        
        # 辺C
        lengths_layout.addWidget(QLabel("辺C:"))
        new_len_c_input = QLineEdit()
        new_len_c_input.setValidator(QDoubleValidator(0.1, 9999.9, 1))
        new_len_c_input.setText("80.0")
        lengths_layout.addWidget(new_len_c_input)
        
        # UI要素の参照を保存
        self.ui_elements['new_len_a_input'] = new_len_a_input
        self.ui_elements['new_len_b_input'] = new_len_b_input
        self.ui_elements['new_len_c_input'] = new_len_c_input
        
        input_layout.addLayout(lengths_layout)
        
        # ボタン
        buttons_layout = QHBoxLayout()
        
        # 追加ボタン
        add_button = QPushButton("三角形を追加")
        add_button.clicked.connect(self._on_add_triangle)
        buttons_layout.addWidget(add_button)
        
        # 更新ボタン
        update_triangle_button = QPushButton("三角形を更新")
        update_triangle_button.clicked.connect(self._on_update_triangle)
        update_triangle_button.setEnabled(False)  # 初期状態は無効
        buttons_layout.addWidget(update_triangle_button)
        
        # DXF出力ボタン
        export_dxf_button = QPushButton("DXF出力")
        export_dxf_button.clicked.connect(self._on_export_dxf)
        buttons_layout.addWidget(export_dxf_button)
        
        # UI要素の参照を保存
        self.ui_elements['add_button'] = add_button
        self.ui_elements['update_triangle_button'] = update_triangle_button
        self.ui_elements['export_dxf_button'] = export_dxf_button
        
        input_layout.addLayout(buttons_layout)
        
        # JSON保存/読み込みボタンを追加
        json_buttons_layout = QHBoxLayout()
        
        # JSON保存ボタン
        save_json_button = QPushButton("JSON保存")
        save_json_button.clicked.connect(self._on_save_json)
        json_buttons_layout.addWidget(save_json_button)
        
        # JSON読み込みボタン
        load_json_button = QPushButton("JSON読み込み")
        load_json_button.clicked.connect(self._on_load_json)
        json_buttons_layout.addWidget(load_json_button)
        
        # UI要素の参照を保存
        self.ui_elements['save_json_button'] = save_json_button
        self.ui_elements['load_json_button'] = load_json_button
        
        input_layout.addLayout(json_buttons_layout)
        
        layout.addWidget(input_group)
    
    def connect_signals_to_handlers(self, handler_object):
        """シグナルをハンドラーに自動接続する
        
        シグナル名からハンドラー名を自動生成して接続します。
        例: addTriangleClicked → on_add_triangle
             triangleSelected → on_triangle_selected
        """
        signals = self.signals
        
        # シグナル名とハンドラー名のマッピング
        signal_handler_map = {
            'addTriangleClicked': 'on_add_triangle',
            'updateTriangleClicked': 'on_update_triangle',
            'exportDxfClicked': 'on_export_dxf',
            'saveJsonClicked': 'on_save_json',
            'loadJsonClicked': 'on_load_json',
            'triangleSelected': 'on_triangle_selected'
        }
        
        # シグナル名に基づいて自動的にハンドラーを見つけて接続
        for signal_name in dir(signals):
            # シグナルオブジェクトのみを処理（アンダースコアで始まる属性は除外）
            if not signal_name.startswith('_') and isinstance(getattr(signals, signal_name), Signal):
                # マッピングからハンドラー名を取得
                if signal_name in signal_handler_map:
                    handler_name = signal_handler_map[signal_name]
                    
                    if hasattr(handler_object, handler_name):
                        # ハンドラーが存在する場合は接続
                        logger.debug(f"シグナル {signal_name} を {handler_name} に接続します")
                        getattr(signals, signal_name).connect(getattr(handler_object, handler_name))
                    else:
                        logger.warning(f"ハンドラー {handler_name} が見つかりません")
    
    def _on_triangle_selected(self, index):
        """コンボボックスで三角形が選択されたときの内部処理"""
        self.signals.triangleSelected.emit(index)
    
    def _on_add_triangle(self):
        """三角形追加ボタンがクリックされたときの内部処理"""
        self.signals.addTriangleClicked.emit()
    
    def _on_update_triangle(self):
        """三角形更新ボタンがクリックされたときの内部処理"""
        self.signals.updateTriangleClicked.emit()
    
    def _on_export_dxf(self):
        """DXF出力ボタンがクリックされたときの内部処理"""
        self.signals.exportDxfClicked.emit()
    
    def _on_save_json(self):
        """JSON保存ボタンがクリックされたときの内部処理"""
        self.signals.saveJsonClicked.emit()
    
    def _on_load_json(self):
        """JSON読み込みボタンがクリックされたときの内部処理"""
        self.signals.loadJsonClicked.emit()
    
    # アクセサメソッド
    def get_selected_info_label(self):
        """選択情報ラベルを取得"""
        return self.ui_elements['selected_info_label']
    
    def get_triangle_combo(self):
        """三角形選択コンボボックスを取得"""
        return self.ui_elements['triangle_combo']
    
    def get_length_inputs(self):
        """辺の長さ入力欄のタプルを取得 (a, b, c)"""
        return (
            self.ui_elements['new_len_a_input'],
            self.ui_elements['new_len_b_input'],
            self.ui_elements['new_len_c_input']
        )
    
    def get_update_button(self):
        """三角形更新ボタンを取得"""
        return self.ui_elements['update_triangle_button']
    
    def clear_triangle_combo(self):
        """三角形選択コンボボックスをクリア"""
        self.ui_elements['triangle_combo'].clear()
        self.ui_elements['triangle_combo'].addItem("---", -1)  # デフォルト選択なし
    
    def add_triangle_to_combo(self, number, text=None):
        """三角形選択コンボボックスに項目を追加"""
        if text is None:
            text = f"三角形 {number}"
        self.ui_elements['triangle_combo'].addItem(text, number)
    
    def set_triangle_combo_index(self, index, block_signals=False):
        """三角形選択コンボボックスのインデックスを設定"""
        if block_signals:
            self.ui_elements['triangle_combo'].blockSignals(True)
        self.ui_elements['triangle_combo'].setCurrentIndex(index)
        if block_signals:
            self.ui_elements['triangle_combo'].blockSignals(False)
    
    def set_selected_info(self, text):
        """選択情報ラベルのテキストを設定"""
        self.ui_elements['selected_info_label'].setText(text)
    
    def set_length_values(self, a, b, c):
        """辺の長さ入力欄の値を設定"""
        self.ui_elements['new_len_a_input'].setText(f"{a:.1f}")
        self.ui_elements['new_len_b_input'].setText(f"{b:.1f}")
        self.ui_elements['new_len_c_input'].setText(f"{c:.1f}")
    
    def get_length_values(self):
        """辺の長さ入力欄の値を取得"""
        try:
            a = float(self.ui_elements['new_len_a_input'].text())
            b = float(self.ui_elements['new_len_b_input'].text())
            c = float(self.ui_elements['new_len_c_input'].text())
            return a, b, c
        except ValueError:
            return None
    
    def enable_update_button(self, enable=True):
        """三角形更新ボタンの有効/無効を切り替え"""
        self.ui_elements['update_triangle_button'].setEnabled(enable)
    
    def find_triangle_combo_data(self, triangle_number):
        """指定された三角形番号に対応するコンボボックスのインデックスを取得"""
        combo = self.ui_elements['triangle_combo']
        for i in range(combo.count()):
            if combo.itemData(i) == triangle_number:
                return i
        return -1 