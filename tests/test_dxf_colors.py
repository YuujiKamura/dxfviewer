#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFカラー処理モジュールのユニットテスト
"""

import unittest
import sys
import os
from unittest.mock import MagicMock

# テスト対象のモジュールをインポートできるようにパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.dxf_colors import (
    invert_color, 
    convert_dxf_color, 
    aci_to_rgb, 
    get_entity_color
)

class TestDxfColors(unittest.TestCase):
    """DXFカラー処理モジュールのテスト"""

    def test_invert_color(self):
        """色反転関数のテスト"""
        self.assertEqual(invert_color((0, 0, 0)), (255, 255, 255), "黒を反転すると白になるはず")
        self.assertEqual(invert_color((255, 255, 255)), (0, 0, 0), "白を反転すると黒になるはず")
        self.assertEqual(invert_color((255, 0, 0)), (0, 255, 255), "赤を反転するとシアンになるはず")
        self.assertEqual(invert_color((0, 255, 0)), (255, 0, 255), "緑を反転するとマゼンタになるはず")
        self.assertEqual(invert_color((0, 0, 255)), (255, 255, 0), "青を反転すると黄色になるはず")
        self.assertEqual(invert_color((128, 128, 128)), (127, 127, 127), "グレーを反転するとグレーになるはず")

    def test_convert_dxf_color_regular_indices(self):
        """通常のカラーインデックスの変換テスト"""
        # 白背景の場合
        self.assertEqual(convert_dxf_color(1), (255, 0, 0), "インデックス1は赤になるはず")
        self.assertEqual(convert_dxf_color(2), (255, 255, 0), "インデックス2は黄色になるはず")
        self.assertEqual(convert_dxf_color(3), (0, 255, 0), "インデックス3は緑になるはず")
        self.assertEqual(convert_dxf_color(4), (0, 255, 255), "インデックス4はシアンになるはず")
        self.assertEqual(convert_dxf_color(5), (0, 0, 255), "インデックス5は青になるはず")
        self.assertEqual(convert_dxf_color(6), (255, 0, 255), "インデックス6はマゼンタになるはず")
        
        # 存在しないインデックスはデフォルト色（黒）になる
        self.assertEqual(convert_dxf_color(999), (0, 0, 0), "存在しないインデックスはデフォルト色になるはず")
        self.assertEqual(convert_dxf_color(-1), (0, 0, 0), "負のインデックスはデフォルト色になるはず")

    def test_convert_dxf_color_index_7_special_handling(self):
        """カラーインデックス7の特殊処理テスト（背景色に応じた反転）"""
        # 白背景の場合（デフォルト）
        white_bg = (255, 255, 255)
        self.assertEqual(convert_dxf_color(7), (0, 0, 0), "白背景の場合、インデックス7は黒になるはず")
        self.assertEqual(convert_dxf_color(7, white_bg), (0, 0, 0), "白背景の場合、インデックス7は黒になるはず")
        
        # 黒背景の場合
        black_bg = (0, 0, 0)
        self.assertEqual(convert_dxf_color(7, black_bg), (255, 255, 255), "黒背景の場合、インデックス7は白になるはず")
        
        # グレー背景の場合
        grey_bg = (128, 128, 128)
        self.assertEqual(convert_dxf_color(7, grey_bg), (127, 127, 127), "グレー背景の場合、インデックス7は反転グレーになるはず")
        
        # 色付き背景の場合
        red_bg = (255, 0, 0)
        self.assertEqual(convert_dxf_color(7, red_bg), (0, 255, 255), "赤背景の場合、インデックス7はシアンになるはず")

    def test_aci_to_rgb(self):
        """aci_to_rgb関数が正しく変換されているかテスト"""
        self.assertEqual(aci_to_rgb(1), convert_dxf_color(1), "aci_to_rgbはconvert_dxf_colorに委譲するはず")
        self.assertEqual(aci_to_rgb(7), convert_dxf_color(7), "インデックス7も正しく処理されるはず")

    def test_get_entity_color(self):
        """エンティティから色を取得する関数のテスト"""
        # モックエンティティの作成
        entity = MagicMock()
        
        # ケース1: 色属性を直接持つエンティティ
        entity.dxf.color = 1  # 赤
        self.assertEqual(get_entity_color(entity), (255, 0, 0), "エンティティの色が直接指定されている場合は、その色を返すはず")
        
        # ケース2: カラーインデックス7を持つエンティティ（特殊処理）
        entity.dxf.color = 7
        self.assertEqual(get_entity_color(entity), (0, 0, 0), "インデックス7は白背景に対して黒になるはず")
        
        # ケース3: 色属性がない場合はデフォルト色
        entity = MagicMock()
        entity.dxf = MagicMock(spec=[])  # 色属性なし
        self.assertEqual(get_entity_color(entity), (0, 0, 0), "色属性がない場合はデフォルト色（黒）になるはず")

if __name__ == '__main__':
    unittest.main() 