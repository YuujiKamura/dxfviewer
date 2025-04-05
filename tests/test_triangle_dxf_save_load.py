#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
三角形データの保存と読み込みの同一性をテストするユニットテスト
"""

import unittest
import sys
import os
import math
import logging
import tempfile
import json
from pathlib import Path

# 親ディレクトリをパスに追加して、必要なモジュールをインポートできるようにする
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 必要なモジュールをインポート
from PySide6.QtCore import QPointF

# TriangleDataクラスのインポート
from triangle_ui.triangle_manager import TriangleData

# ロガーのセットアップ
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class TestTriangleSaveLoad(unittest.TestCase):
    """三角形データの保存と読み込みをテストするクラス"""
    
    def test_save_load_triangle_data(self):
        """三角形データの保存と読み込みの同一性テスト"""
        # テスト用の三角形データを作成
        triangle1 = TriangleData(100.0, 100.0, 100.0, QPointF(0, 0), 180.0, 1)
        
        # 二つ目の三角形を作成して接続
        connection_point = triangle1.get_connection_point_by_side(0)  # 辺Aに接続
        connection_angle = triangle1.get_angle_by_side(0)
        
        triangle2 = TriangleData(
            a=100.0, b=80.0, c=80.0,
            p_ca=connection_point,
            angle_deg=connection_angle,
            number=2
        )
        
        # 親子関係を設定
        triangle1.set_child(triangle2, 0)
        
        # テスト用の三角形リスト
        triangles = [triangle1, triangle2]
        
        # 一時ファイルを作成してJSONに出力
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
            json_path = tmp_file.name
        
        try:
            # JSONファイルに出力
            self._save_triangles_to_json(triangles, json_path)
            
            # JSONファイルから読み込み
            loaded_triangles = self._load_triangles_from_json(json_path)
            
            # 同一性の検証
            self._verify_triangles_equality(triangles, loaded_triangles)
            
        finally:
            # テスト後に一時ファイルを削除
            if os.path.exists(json_path):
                os.unlink(json_path)
    
    def _save_triangles_to_json(self, triangles, file_path):
        """三角形データをJSONファイルに出力する"""
        # 三角形データをシリアライズ可能な辞書に変換
        triangle_dicts = []
        for triangle in triangles:
            triangle_dict = {
                'number': triangle.number,
                'lengths': triangle.lengths,
                'points': [
                    {'x': p.x(), 'y': p.y()} for p in triangle.points
                ],
                'angle_deg': triangle.angle_deg,
                'connection_side': triangle.connection_side,
                'parent_number': triangle.parent.number if triangle.parent else -1,
                'children': [
                    child.number if child else -1 for child in triangle.children
                ]
            }
            triangle_dicts.append(triangle_dict)
        
        # JSONファイルに書き込み
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(triangle_dicts, f, indent=2)
        
        logger.info(f"{len(triangles)}個の三角形データを{file_path}に保存しました")
    
    def _load_triangles_from_json(self, file_path):
        """JSONファイルから三角形データを読み込む"""
        # JSONファイルを読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            triangle_dicts = json.load(f)
        
        # 三角形データを作成（最初は接続関係なし）
        triangles = []
        for triangle_dict in triangle_dicts:
            # 点をQPointFに変換
            points = [
                QPointF(p['x'], p['y']) for p in triangle_dict['points']
            ]
            
            # 三角形データの作成
            triangle = TriangleData(
                a=triangle_dict['lengths'][0],
                b=triangle_dict['lengths'][1],
                c=triangle_dict['lengths'][2],
                p_ca=points[0],
                angle_deg=triangle_dict['angle_deg'],
                number=triangle_dict['number']
            )
            
            # 頂点位置を直接設定
            triangle.points = points
            
            triangles.append(triangle)
        
        # 親子関係を設定
        for i, triangle_dict in enumerate(triangle_dicts):
            # 親の設定
            parent_number = triangle_dict['parent_number']
            if parent_number != -1:
                # 親三角形を探す
                parent = next((t for t in triangles if t.number == parent_number), None)
                if parent:
                    triangles[i].parent = parent
                    # 親の子として設定
                    connection_side = triangle_dict['connection_side']
                    triangles[i].connection_side = connection_side  # 接続辺を設定
                    if 0 <= connection_side < 3:
                        parent.children[connection_side] = triangles[i]
        
        # 三角形番号でソート
        triangles.sort(key=lambda t: t.number)
        
        logger.info(f"{len(triangles)}個の三角形データを{file_path}から読み込みました")
        return triangles
    
    def _verify_triangles_equality(self, original_triangles, loaded_triangles):
        """元の三角形データと読み込んだデータの同一性を検証"""
        # 三角形の数が同じことを確認
        self.assertEqual(len(original_triangles), len(loaded_triangles),
                         f"三角形の数が一致しません: 元={len(original_triangles)}, 読込={len(loaded_triangles)}")
        
        # 各三角形の同一性を検証
        for orig, loaded in zip(original_triangles, loaded_triangles):
            # 番号が同じことを確認
            self.assertEqual(orig.number, loaded.number,
                           f"三角形番号が一致しません: 元={orig.number}, 読込={loaded.number}")
            
            # 辺の長さが同じことを確認（許容誤差あり）
            for i in range(3):
                self.assertAlmostEqual(
                    orig.lengths[i], 
                    loaded.lengths[i], 
                    delta=0.1,
                    msg=f"三角形{orig.number}の辺{i}の長さが一致しません: "
                        f"元={orig.lengths[i]}, 読込={loaded.lengths[i]}"
                )
            
            # 頂点座標が同じことを確認（許容誤差あり）
            for i in range(3):
                self.assertAlmostEqual(
                    orig.points[i].x(), 
                    loaded.points[i].x(), 
                    delta=0.1,
                    msg=f"三角形{orig.number}の頂点{i}のX座標が一致しません"
                )
                self.assertAlmostEqual(
                    orig.points[i].y(), 
                    loaded.points[i].y(), 
                    delta=0.1,
                    msg=f"三角形{orig.number}の頂点{i}のY座標が一致しません"
                )
            
            # 親子関係が同じことを確認
            if orig.parent:
                self.assertIsNotNone(loaded.parent, f"三角形{orig.number}の親が欠落しています")
                self.assertEqual(orig.parent.number, loaded.parent.number, 
                               f"三角形{orig.number}の親番号が一致しません: "
                               f"元={orig.parent.number}, 読込={loaded.parent.number}")
            else:
                self.assertIsNone(loaded.parent, f"三角形{orig.number}に不正な親があります")
            
            # 接続辺が同じことを確認
            self.assertEqual(orig.connection_side, loaded.connection_side,
                           f"三角形{orig.number}の接続辺が一致しません: "
                           f"元={orig.connection_side}, 読込={loaded.connection_side}")
            
            # 子三角形が同じことを確認
            for i in range(3):
                orig_child = orig.children[i]
                loaded_child = loaded.children[i]
                
                if orig_child:
                    self.assertIsNotNone(loaded_child, 
                                       f"三角形{orig.number}の辺{i}の子が欠落しています")
                    self.assertEqual(orig_child.number, loaded_child.number,
                                   f"三角形{orig.number}の辺{i}の子番号が一致しません: "
                                   f"元={orig_child.number}, 読込={loaded_child.number}")
                else:
                    self.assertIsNone(loaded_child, 
                                    f"三角形{orig.number}の辺{i}に不正な子があります")

if __name__ == '__main__':
    unittest.main() 