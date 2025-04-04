#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
強制黒モードのテスト

強制黒モードが正しく機能するかをテストします。
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# テスト対象のモジュールへのパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
from core.dxf_colors import (
    set_force_black_mode, get_entity_color, convert_dxf_color, 
    aci_to_rgb, color_settings
)


class TestForceBlackMode(unittest.TestCase):
    """強制黒モードのテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # 強制黒モードをリセット
        set_force_black_mode(False)
    
    def tearDown(self):
        """各テスト後の後始末"""
        # 強制黒モードをリセット
        set_force_black_mode(False)
    
    def test_force_black_mode_flag(self):
        """強制黒モードフラグの設定と取得テスト"""
        # デフォルトは無効確認
        self.assertFalse(color_settings.is_force_black_mode)
        
        # 有効化
        set_force_black_mode(True)
        
        # フラグの状態を確認
        self.assertTrue(color_settings.is_force_black_mode, "強制黒モードフラグが有効になっていません")
        
        # 無効化
        set_force_black_mode(False)
        self.assertFalse(color_settings.is_force_black_mode)
    
    def test_convert_dxf_color_with_force_black(self):
        """convert_dxf_color関数が強制黒モードで常に黒を返すかテスト"""
        # 通常モードでは色を返す
        self.assertEqual(convert_dxf_color(1), (255, 0, 0))  # 赤色
        self.assertEqual(convert_dxf_color(2), (255, 255, 0))  # 黄色
        
        # 強制黒モードを有効化
        set_force_black_mode(True)
        
        # 強制黒モードでは常に黒を返す
        self.assertEqual(convert_dxf_color(1), (0, 0, 0))
        self.assertEqual(convert_dxf_color(2), (0, 0, 0))
        self.assertEqual(convert_dxf_color(3), (0, 0, 0))
    
    def test_aci_to_rgb_with_force_black(self):
        """aci_to_rgb関数が強制黒モードで常に黒を返すかテスト"""
        # 通常モードでは色を返す
        self.assertEqual(aci_to_rgb(1), (255, 0, 0))  # 赤色
        self.assertEqual(aci_to_rgb(2), (255, 255, 0))  # 黄色
        
        # 強制黒モードを有効化
        set_force_black_mode(True)
        
        # 強制黒モードでは常に黒を返す
        self.assertEqual(aci_to_rgb(1), (0, 0, 0))
        self.assertEqual(aci_to_rgb(2), (0, 0, 0))
        self.assertEqual(aci_to_rgb(3), (0, 0, 0))
    
    def test_get_entity_color_with_force_black(self):
        """get_entity_color関数が強制黒モードで常に黒を返すかテスト"""
        # エンティティのモックを作成
        mock_entity = MagicMock()
        mock_entity.dxf.color = 1  # 赤色
        
        # 通常モードでは色を返す
        self.assertEqual(get_entity_color(mock_entity), (255, 0, 0))
        
        # 強制黒モードを有効化
        set_force_black_mode(True)
        
        # 強制黒モードでは常に黒を返す
        self.assertEqual(get_entity_color(mock_entity), (0, 0, 0))
    
    def test_integration_with_dxf_reader(self):
        """DXFリーダーとの統合テスト"""
        from core.dxf_reader import convert_entity
        
        # エンティティのモックを作成
        mock_entity = MagicMock()
        mock_entity.dxftype.return_value = 'LINE'
        mock_entity.dxf.start.x = 0
        mock_entity.dxf.start.y = 0
        mock_entity.dxf.end.x = 100
        mock_entity.dxf.end.y = 100
        mock_entity.dxf.color = 1  # 赤色
        
        # 通常モードでは色を返す
        with patch('core.dxf_reader.get_entity_color', return_value=(255, 0, 0)):
            result = convert_entity(mock_entity)
            self.assertEqual(result.color, (255, 0, 0))
        
        # 強制黒モードを有効化
        set_force_black_mode(True)
        
        # 強制黒モードでは常に黒を返す
        with patch('core.dxf_reader.get_entity_color', return_value=(0, 0, 0)):
            result = convert_entity(mock_entity)
            self.assertEqual(result.color, (0, 0, 0))


if __name__ == '__main__':
    unittest.main() 