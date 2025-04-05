#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
三角形データのDXF出力および読み込みの同一性をテストするユニットテスト
"""

import unittest
import sys
import os
import math
import logging
import tempfile
from pathlib import Path

# 親ディレクトリをパスに追加して、必要なモジュールをインポートできるようにする
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# 必要なモジュールをインポート
from PySide6.QtCore import QPointF

# TriangleDataとDXF関連のインポート
from triangle_ui.triangle_manager import TriangleData, HAS_EZDXF

# ezdxfが利用可能な場合のみテストを実行
try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError:
    print("ezdxfモジュールが見つかりません。DXF出力テストはスキップされます。")
    print("インストールには: pip install ezdxf を実行してください。")
    HAS_EZDXF = False

# ロガーのセットアップ
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class TestTriangleDXFExport(unittest.TestCase):
    """三角形データのDXF出力と読み込みをテストするクラス"""
    
    @unittest.skipIf(not HAS_EZDXF, "ezdxfモジュールがインストールされていません")
    def test_export_import_dxf(self):
        """三角形データのDXF出力と読み込みの同一性テスト"""
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
        
        # 一時ファイルを作成してDXFに出力
        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp_file:
            dxf_path = tmp_file.name
        
        try:
            # DXFファイルに出力
            self._export_triangles_to_dxf(triangles, dxf_path)
            
            # DXFファイルから読み込み
            imported_triangles = self._import_triangles_from_dxf(dxf_path)
            
            # 同一性の検証
            self._verify_triangles_equality(triangles, imported_triangles)
            
        finally:
            # テスト後に一時ファイルを削除
            if os.path.exists(dxf_path):
                os.unlink(dxf_path)
    
    def _export_triangles_to_dxf(self, triangles, file_path):
        """三角形データをDXFファイルに出力する"""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # 各三角形をポリラインとして追加
        for triangle_data in triangles:
            if triangle_data and triangle_data.points:
                # 三角形の点を取得
                points = [(p.x(), p.y(), 0) for p in triangle_data.points]
                # 閉じたポリラインを作成
                points.append(points[0])  # 最初の点を追加して閉じる
                
                # ポリラインをモデルスペースに追加
                polyline = msp.add_lwpolyline(points)
                # 三角形番号をユーザーデータとして保存
                polyline.dxf.layer = f"Triangle_{triangle_data.number}"
                
                # 寸法テキストを追加
                for i, length in enumerate(triangle_data.lengths):
                    # 辺の中点を計算
                    p1, p2 = triangle_data.get_side_line(i)
                    mid_x = (p1.x() + p2.x()) / 2
                    mid_y = (p1.y() + p2.y()) / 2
                    
                    # テキスト追加
                    text = msp.add_text(f"{length:.1f}", height=length * 0.05)
                    text.dxf.insert = (mid_x, mid_y)
                    # TextEntityAlignment.MIDDLE_CENTERをhalignとvalignに変換
                    text.dxf.halign = 4  # 4=Middle
                    text.dxf.valign = 2  # 2=Middle
                    text.dxf.layer = f"Dimension_Tri{triangle_data.number}_Edge{i}"
        
        # DXFファイルを保存
        doc.saveas(file_path)
        logger.info(f"三角形データを{file_path}にDXF出力しました")
    
    def _import_triangles_from_dxf(self, file_path):
        """DXFファイルから三角形データを読み込む"""
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        # 三角形データを格納するリスト
        imported_triangles = []
        
        # レイヤー名から三角形番号を取得する正規表現
        import re
        triangle_pattern = re.compile(r'Triangle_(\d+)')
        
        # ポリライン（三角形）を検索
        for entity in msp:
            if entity.dxftype() == 'LWPOLYLINE':
                # レイヤー名から三角形番号を取得
                layer_name = entity.dxf.layer
                match = triangle_pattern.match(layer_name)
                
                if match:
                    # 三角形番号を取得
                    triangle_number = int(match.group(1))
                    
                    # ポリラインの頂点を取得
                    points = list(entity.get_points())
                    
                    # 閉じたポリラインなので最後の点は最初の点と同じなので除外
                    if len(points) > 3 and (points[0][0] == points[-1][0] and points[0][1] == points[-1][1]):
                        points = points[:-1]
                    
                    # 点をQPointFに変換
                    qt_points = [QPointF(point[0], point[1]) for point in points]
                    
                    # 三角形を作成する際に必要な情報を収集
                    if len(qt_points) == 3:
                        # 辺の長さを計算
                        lengths = []
                        for i in range(3):
                            p1 = qt_points[i]
                            p2 = qt_points[(i + 1) % 3]
                            length = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
                            lengths.append(length)
                        
                        # 三角形データを作成
                        triangle = TriangleData(
                            a=lengths[0],
                            b=lengths[1],
                            c=lengths[2],
                            p_ca=qt_points[0],  # 最初の点をCA点とする
                            number=triangle_number
                        )
                        
                        # 三角形の頂点を直接設定
                        triangle.points = qt_points
                        
                        # リストに追加
                        imported_triangles.append(triangle)
        
        # 三角形番号でソート
        imported_triangles.sort(key=lambda t: t.number)
        
        logger.info(f"{len(imported_triangles)}個の三角形データをDXFから読み込みました")
        return imported_triangles
    
    def _verify_triangles_equality(self, original_triangles, imported_triangles):
        """元の三角形データと読み込んだデータの同一性を検証"""
        # 三角形の数が同じことを確認
        self.assertEqual(len(original_triangles), len(imported_triangles),
                         f"三角形の数が一致しません: 元={len(original_triangles)}, 読込={len(imported_triangles)}")
        
        # 各三角形の同一性を検証
        for orig, imp in zip(original_triangles, imported_triangles):
            # 番号が同じことを確認
            self.assertEqual(orig.number, imp.number,
                           f"三角形番号が一致しません: 元={orig.number}, 読込={imp.number}")
            
            # 辺の長さが同じことを確認（許容誤差あり）
            for i in range(3):
                self.assertAlmostEqual(
                    orig.lengths[i], 
                    imp.lengths[i], 
                    delta=0.1,
                    msg=f"三角形{orig.number}の辺{i}の長さが一致しません: "
                        f"元={orig.lengths[i]}, 読込={imp.lengths[i]}"
                )
            
            # 頂点座標が同じことを確認（許容誤差あり）
            for i in range(3):
                self.assertAlmostEqual(
                    orig.points[i].x(), 
                    imp.points[i].x(), 
                    delta=0.1,
                    msg=f"三角形{orig.number}の頂点{i}のX座標が一致しません"
                )
                self.assertAlmostEqual(
                    orig.points[i].y(), 
                    imp.points[i].y(), 
                    delta=0.1,
                    msg=f"三角形{orig.number}の頂点{i}のY座標が一致しません"
                )

if __name__ == '__main__':
    unittest.main() 