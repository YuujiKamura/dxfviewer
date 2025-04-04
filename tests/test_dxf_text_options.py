#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFテキスト設定オプションのテスト

DXFファイル内のテキスト要素の様々な表示設定を試験するスクリプト
テキストの位置、スタイル、高さ、配置、回転などDXF特有の設定を
視覚的にテストできます
"""

import os
import sys
import math
import tempfile
from pathlib import Path

# パスを追加して親ディレクトリのモジュールを参照できるようにする
sys.path.insert(0, str(Path(__file__).parent.parent))

# ezdxfのインポート
try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    print("ezdxfモジュールをインストールしてください: pip install ezdxf")
    sys.exit(1)

# PySide6のインポート
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QPushButton, QComboBox, QSlider, QDoubleSpinBox,
    QCheckBox, QGroupBox, QFileDialog, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

# 自作モジュールのインポート
from dxf_core.parser import parse_dxf_file
from ui.graphics_view import DxfGraphicsView
from dxf_core.adapter import create_dxf_adapter
from dxf_core.renderer import draw_dxf_entities_with_adapter

class DxfTextOptionsTest(QMainWindow):
    """DXFテキスト設定オプションテスト用ウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("DXFテキスト設定オプションテスト")
        self.resize(1200, 900)
        
        # DXF関連の変数
        self.dxf_doc = None
        self.dxf_data = None
        self.temp_file = None
        self.updating_ui = False  # UIの更新中フラグ
        self.y_offset = 0.0  # Y軸オフセット（ベースラインからの距離調整用）
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # グラフィックスビューの作成
        self.view = DxfGraphicsView()
        main_layout.addWidget(self.view, 1)
        
        # コントロールレイアウト
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)
        
        # テキストコントロール
        text_group = QGroupBox("テキスト")
        text_layout = QVBoxLayout(text_group)
        controls_layout.addWidget(text_group)
        
        # テキスト入力
        text_layout.addWidget(QLabel("テキスト:"))
        self.text_input = QComboBox()
        self.text_input.setEditable(True)
        self.text_input.addItems(["サンプルテキスト", "Hello DXF", "テスト 123", "あいうえお", "Multiple\nLines\nText"])
        self.text_input.currentTextChanged.connect(self.on_ui_changed)
        text_layout.addWidget(self.text_input)
        
        # スタイル
        text_layout.addWidget(QLabel("スタイル:"))
        self.style_combo = QComboBox()
        self.style_combo.addItems(["Standard", "Arial", "Times", "Japanese"])
        self.style_combo.currentIndexChanged.connect(self.on_ui_changed)
        text_layout.addWidget(self.style_combo)
        
        # 位置コントロール
        position_group = QGroupBox("位置")
        position_layout = QVBoxLayout(position_group)
        controls_layout.addWidget(position_group)
        
        # X座標
        position_layout.addWidget(QLabel("X座標:"))
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-100, 100)
        self.x_spin.setValue(0)
        self.x_spin.setSingleStep(5)
        self.x_spin.valueChanged.connect(self.on_ui_changed)
        position_layout.addWidget(self.x_spin)
        
        # Y座標
        position_layout.addWidget(QLabel("Y座標:"))
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-100, 100)
        self.y_spin.setValue(0)
        self.y_spin.setSingleStep(5)
        self.y_spin.valueChanged.connect(self.on_ui_changed)
        position_layout.addWidget(self.y_spin)
        
        # Z座標
        position_layout.addWidget(QLabel("Z座標:"))
        self.z_spin = QDoubleSpinBox()
        self.z_spin.setRange(-100, 100)
        self.z_spin.setValue(0)
        self.z_spin.setSingleStep(5)
        self.z_spin.valueChanged.connect(self.on_ui_changed)
        position_layout.addWidget(self.z_spin)
        
        # サイズと角度
        size_group = QGroupBox("サイズと角度")
        size_layout = QVBoxLayout(size_group)
        controls_layout.addWidget(size_group)
        
        # 高さ
        size_layout.addWidget(QLabel("高さ:"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0.1, 50)
        self.height_spin.setValue(5)
        self.height_spin.setSingleStep(1)
        self.height_spin.valueChanged.connect(self.on_ui_changed)
        size_layout.addWidget(self.height_spin)
        
        # 幅係数
        size_layout.addWidget(QLabel("幅係数:"))
        self.width_factor_spin = QDoubleSpinBox()
        self.width_factor_spin.setRange(0.1, 5)
        self.width_factor_spin.setValue(1)
        self.width_factor_spin.setSingleStep(0.1)
        self.width_factor_spin.valueChanged.connect(self.on_ui_changed)
        size_layout.addWidget(self.width_factor_spin)
        
        # 回転角度
        size_layout.addWidget(QLabel("回転角度:"))
        self.rotation_slider = QSlider(Qt.Orientation.Horizontal)
        self.rotation_slider.setRange(0, 360)
        self.rotation_slider.setValue(0)
        self.rotation_slider.valueChanged.connect(self.on_rotation_changed)
        size_layout.addWidget(self.rotation_slider)
        
        self.rotation_label = QLabel("0°")
        size_layout.addWidget(self.rotation_label)
        
        # Y軸オフセット（ベースラインとの隙間調整）
        size_layout.addWidget(QLabel("Y軸オフセット:"))
        self.y_offset_spin = QDoubleSpinBox()
        self.y_offset_spin.setRange(-5, 5)
        self.y_offset_spin.setValue(0)
        self.y_offset_spin.setSingleStep(0.1)
        self.y_offset_spin.valueChanged.connect(self.on_y_offset_changed)
        size_layout.addWidget(self.y_offset_spin)
        
        # 配置オプション
        alignment_group = QGroupBox("配置")
        alignment_layout = QVBoxLayout(alignment_group)
        controls_layout.addWidget(alignment_group)
        
        # 水平配置
        alignment_layout.addWidget(QLabel("水平配置:"))
        self.halign_combo = QComboBox()
        self.halign_combo.addItems([
            "左揃え", "中央揃え", "右揃え", 
            "整列（左）", "整列（中央）", "整列（右）"
        ])
        self.halign_combo.currentIndexChanged.connect(self.on_ui_changed)
        alignment_layout.addWidget(self.halign_combo)
        
        # 垂直配置
        alignment_layout.addWidget(QLabel("垂直配置:"))
        self.valign_combo = QComboBox()
        self.valign_combo.addItems([
            "ベースライン", "下", "中央", "上"
        ])
        self.valign_combo.currentIndexChanged.connect(self.on_ui_changed)
        alignment_layout.addWidget(self.valign_combo)
        
        # その他のオプション
        options_group = QGroupBox("オプション")
        options_layout = QVBoxLayout(options_group)
        controls_layout.addWidget(options_group)
        
        # バックワード
        self.backward_check = QCheckBox("バックワード")
        self.backward_check.stateChanged.connect(self.on_ui_changed)
        options_layout.addWidget(self.backward_check)
        
        # アップサイドダウン
        self.upside_down_check = QCheckBox("アップサイドダウン")
        self.upside_down_check.stateChanged.connect(self.on_ui_changed)
        options_layout.addWidget(self.upside_down_check)
        
        # 操作ボタン
        buttons_group = QGroupBox("操作")
        buttons_layout = QVBoxLayout(buttons_group)
        controls_layout.addWidget(buttons_group)
        
        # 生成ボタン
        self.generate_button = QPushButton("テキスト生成")
        self.generate_button.clicked.connect(self.generate_test_text)
        buttons_layout.addWidget(self.generate_button)
        
        # リセットビューボタン
        self.reset_view_button = QPushButton("ビューリセット")
        self.reset_view_button.clicked.connect(self.reset_view)
        buttons_layout.addWidget(self.reset_view_button)
        
        # 保存ボタン
        self.save_button = QPushButton("DXF保存...")
        self.save_button.clicked.connect(self.save_dxf)
        buttons_layout.addWidget(self.save_button)
        
        # 初期化
        self.init_dxf_document()
        self.generate_test_text()
    
    def init_dxf_document(self):
        """DXFドキュメントを初期化"""
        # 一時ファイルを作成
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.dxf', delete=False)
        self.temp_file.close()
        
        # 新しいDXFドキュメントを作成
        self.dxf_doc = ezdxf.new('R2010')
        
        # スタイルの作成（シンプルな設定に修正）
        styles = self.dxf_doc.styles
        
        # 基本スタイルのみ追加
        if 'Arial' not in styles:
            styles.new('Arial')
        
        if 'Times' not in styles:
            styles.new('Times')
        
        if 'Japanese' not in styles:
            styles.new('Japanese')
        
        # モデル空間を取得
        self.msp = self.dxf_doc.modelspace()
        
        # 参照グリッドを描画
        self.draw_reference_grid()
    
    def draw_reference_grid(self):
        """参照用グリッドを描画"""
        msp = self.msp
        
        # グリッド線は削除
        
        # 主要な軸のみ残す
        # X軸（赤）
        msp.add_line((-100, 0, 0), (100, 0, 0), dxfattribs={'color': 1, 'lineweight': 1})
        # Y軸（緑）
        msp.add_line((0, -100, 0), (0, 100, 0), dxfattribs={'color': 3, 'lineweight': 1})
        
        # 原点マーカー
        msp.add_circle((0, 0, 0), 2, dxfattribs={'color': 5, 'lineweight': 1})
        
        # 軸ラベル
        msp.add_text('X', dxfattribs={
            'height': 5,
            'color': 1
        }).set_placement((95, 5, 0))
        
        msp.add_text('Y', dxfattribs={
            'height': 5,
            'color': 3
        }).set_placement((5, 95, 0))
    
    def generate_test_text(self):
        """テスト用テキストを生成"""
        try:
            # DXFドキュメントが初期化されていない場合は初期化
            if not self.dxf_doc:
                self.init_dxf_document()
            
            # 既存のテキストをクリアするためにドキュメントを再初期化
            self.init_dxf_document()
            
            # テキスト内容
            text = self.text_input.currentText()
            
            # テキストスタイル
            style = self.style_combo.currentText()
            
            # 位置
            x = self.x_spin.value()
            y = self.y_spin.value() + self.y_offset  # Y軸オフセットを適用
            z = self.z_spin.value()
            position = (x, y, z)
            
            # その他のパラメータ
            height = self.height_spin.value()
            width_factor = self.width_factor_spin.value()
            rotation = self.rotation_slider.value()
            
            # 水平配置の設定のみ使用
            halign_map = {
                "左揃え": TextEntityAlignment.LEFT,
                "中央揃え": TextEntityAlignment.CENTER,
                "右揃え": TextEntityAlignment.RIGHT,
                "整列（左）": TextEntityAlignment.ALIGNED,
                "整列（中央）": TextEntityAlignment.FIT,
                "整列（右）": TextEntityAlignment.RIGHT
            }
            align = halign_map[self.halign_combo.currentText()]
            
            # 垂直配置を考慮して適切なalignを選択
            valign_text = self.valign_combo.currentText()
            if valign_text == "中央":
                if self.halign_combo.currentText() == "左揃え":
                    align = TextEntityAlignment.MIDDLE_LEFT
                elif self.halign_combo.currentText() == "中央揃え":
                    align = TextEntityAlignment.MIDDLE_CENTER
                elif self.halign_combo.currentText() == "右揃え":
                    align = TextEntityAlignment.MIDDLE_RIGHT
            elif valign_text == "上":
                if self.halign_combo.currentText() == "左揃え":
                    align = TextEntityAlignment.TOP_LEFT
                elif self.halign_combo.currentText() == "中央揃え":
                    align = TextEntityAlignment.TOP_CENTER
                elif self.halign_combo.currentText() == "右揃え":
                    align = TextEntityAlignment.TOP_RIGHT
            elif valign_text == "下":
                if self.halign_combo.currentText() == "左揃え":
                    align = TextEntityAlignment.BOTTOM_LEFT
                elif self.halign_combo.currentText() == "中央揃え":
                    align = TextEntityAlignment.BOTTOM_CENTER
                elif self.halign_combo.currentText() == "右揃え":
                    align = TextEntityAlignment.BOTTOM_RIGHT
                
            # バックワードとアップサイドダウンの設定
            backward = self.backward_check.isChecked()
            upside_down = self.upside_down_check.isChecked()
            
            # テキストの追加
            text_attribs = {
                'style': style,
                'height': height,
                'width': width_factor,
                'rotation': rotation,
            }
            
            # テキストを作成
            text_entity = self.msp.add_text(text, dxfattribs=text_attribs)
            
            # バックワードとアップサイドダウンの設定
            if hasattr(text_entity, 'is_backward'):
                text_entity.is_backward = backward
            if hasattr(text_entity, 'is_upside_down'):
                text_entity.is_upside_down = upside_down
            
            # 位置と配置を設定
            text_entity.set_placement(position, align=align)
            
            # DXFを一時ファイルに保存
            self.dxf_doc.saveas(self.temp_file.name)
            
            # 一時ファイルからDXFデータを解析
            self.dxf_data = parse_dxf_file(self.temp_file.name)
            
            # グラフィックスビューに表示
            self.display_dxf()
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "テキスト生成エラー", 
                                f"テキストの生成に失敗しました: {str(e)}\n\n詳細:\n{error_details}")
    
    def display_dxf(self):
        """DXFデータをグラフィックスビューに表示"""
        if not self.dxf_data:
            return
        
        # シーンをクリア
        self.view.scene().clear()
        
        # アダプタを作成
        adapter = create_dxf_adapter(self.view.scene())
        
        # DXFデータを描画
        draw_dxf_entities_with_adapter(adapter, self.dxf_data)
        
        # シーンを初期化
        self.view.initialize_view()
        
        # ビューをリセット
        self.reset_view()
    
    def reset_view(self):
        """ビューをリセット"""
        self.view.reset_view()
    
    def save_dxf(self):
        """DXFファイルを保存"""
        if not self.dxf_doc:
            QMessageBox.warning(self, "警告", "DXFドキュメントが生成されていません。")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "DXFファイルの保存", "", "DXF Files (*.dxf)"
        )
        
        if file_path:
            if not file_path.lower().endswith('.dxf'):
                file_path += '.dxf'
            
            try:
                self.dxf_doc.saveas(file_path)
                QMessageBox.information(self, "保存完了", f"DXFファイルを保存しました: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存エラー", f"DXFファイルの保存に失敗しました: {str(e)}")
    
    def closeEvent(self, event):
        """ウィンドウ終了時の処理"""
        # 一時ファイルを削除
        if self.temp_file:
            try:
                if os.path.exists(self.temp_file.name):
                    os.unlink(self.temp_file.name)
            except Exception:
                pass
        
        super().closeEvent(event)

    def on_rotation_changed(self, value):
        """回転スライダーの値が変わったときの処理"""
        self.rotation_label.setText(f"{value}°")
        self.on_ui_changed()

    def on_y_offset_changed(self, value):
        """Y軸オフセットの変更処理"""
        self.y_offset = value
        self.on_ui_changed()

    def on_ui_changed(self):
        """UI要素が変更されたときの処理"""
        # 再帰呼び出しを防止
        if not hasattr(self, 'updating_ui') or not self.updating_ui:
            self.updating_ui = True
            self.generate_test_text()
            self.updating_ui = False

def main():
    """メイン関数"""
    app = QApplication(sys.argv)
    
    window = DxfTextOptionsTest()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 