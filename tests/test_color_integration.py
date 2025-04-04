#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF色処理の統合テスト

DXFファイルの読み込みからシーン描画までの流れで、カラーインデックス7の特殊処理が
正しく機能しているかを確認します。
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import MagicMock, patch

# テスト対象のモジュールをインポートできるようにパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# PySide6のインポート
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtGui import QColor

# テスト対象のモジュールをインポート
from core.dxf_colors import convert_dxf_color, get_entity_color
from core.dxf_reader import convert_entity
from core.dxf_entities import DxfLine

# インテグレーションテスト用のテストDXFファイルを作成する関数
def create_test_dxf_file():
    """テスト用のDXFファイルを作成して、そのパスを返す"""
    try:
        import ezdxf
        # 一時ファイルを作成
        fd, temp_path = tempfile.mkstemp(suffix='.dxf')
        os.close(fd)
        
        # 新しいDXFファイルを作成
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # カラーインデックス7（白/特殊）の線を追加
        msp.add_line((0, 0), (10, 10), dxfattribs={'color': 7})
        
        # カラーインデックス1（赤）の線を追加
        msp.add_line((0, 5), (10, 5), dxfattribs={'color': 1})
        
        # DXFファイルを保存
        doc.saveas(temp_path)
        return temp_path
        
    except ImportError:
        # ezdxfがない場合はテストをスキップするためにNoneを返す
        return None

class MockDxfEntity:
    """モックDXFエンティティクラス"""
    def __init__(self, entity_type='LINE', color=7):
        self.dxf = MagicMock()
        self.dxf.color = color
        self._entity_type = entity_type
        
        # LINE用の属性
        if entity_type == 'LINE':
            self.dxf.start = MagicMock()
            self.dxf.start.x = 0
            self.dxf.start.y = 0
            self.dxf.end = MagicMock()
            self.dxf.end.x = 10
            self.dxf.end.y = 10
        
        # レイヤー情報
        self.dxf.layer = 'Default'
        self.doc = MagicMock()
        self.doc.layers.get.return_value = None
        
    def dxftype(self):
        """エンティティタイプを返す"""
        return self._entity_type

class TestColorIntegration(unittest.TestCase):
    """色処理の統合テスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化"""
        # QApplicationの初期化（GUIテスト用）
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])
    
    def setUp(self):
        """各テストの前処理"""
        # テスト用のシーン作成
        self.scene = QGraphicsScene()
    
    def test_mock_entity_color_conversion(self):
        """モックエンティティの色変換をテスト"""
        # カラーインデックス7のモックエンティティ
        entity_7 = MockDxfEntity(color=7)
        
        # 色変換
        color_7_rgb = get_entity_color(entity_7)
        
        # 白背景の場合、インデックス7は黒(0,0,0)になるはず
        self.assertEqual(color_7_rgb, (0, 0, 0), "インデックス7は白背景では黒になるはず")
        
        # 比較対象として、カラーインデックス1（赤）のエンティティもテスト
        entity_1 = MockDxfEntity(color=1)
        color_1_rgb = get_entity_color(entity_1)
        self.assertEqual(color_1_rgb, (255, 0, 0), "インデックス1は赤になるはず")
    
    def test_convert_entity_with_mock(self):
        """モックエンティティを使ったconvert_entity関数のテスト"""
        # カラーインデックス7のモックエンティティ
        entity_7 = MockDxfEntity(color=7)
        
        # convert_entity関数での変換
        with patch('core.dxf_reader.get_entity_color', return_value=(0, 0, 0)):
            result = convert_entity(entity_7)
            
            # 変換結果の検証
            self.assertIsInstance(result, DxfLine, "LINE型のエンティティに変換されるはず")
            self.assertEqual(result.color, (0, 0, 0), "変換後のエンティティの色が黒であるべき")
    
    def test_integration_with_real_scene(self):
        """実際のシーンへの描画時に色が正しく適用されるかテスト"""
        # シーンの背景色を白に設定
        self.scene.setBackgroundBrush(QColor(255, 255, 255))
        
        # モックのDXFエンティティ（カラーインデックス7）を作成
        mock_entity = MockDxfEntity(color=7)
        
        # 実際のPySide6シーンにエンティティを描画するモック関数
        def mock_draw_line_on_scene(entity, color):
            from PySide6.QtGui import QPen
            from PySide6.QtCore import QLineF, QPointF
            pen = QPen(QColor(*color))
            line = self.scene.addLine(QLineF(
                QPointF(entity.dxf.start.x, entity.dxf.start.y),
                QPointF(entity.dxf.end.x, entity.dxf.end.y)
            ), pen)
            return line
        
        # エンティティの色を取得
        color = get_entity_color(mock_entity)
        
        # シーンに描画
        line_item = mock_draw_line_on_scene(mock_entity, color)
        
        # 描画された線の色をチェック
        self.assertEqual(line_item.pen().color().getRgb()[:3], (0, 0, 0), 
                          "インデックス7のエンティティは白背景で黒く描画されるべき")

if __name__ == '__main__':
    unittest.main() 