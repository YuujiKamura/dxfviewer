#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleExporters - 三角形データのDXFエクスポート機能

三角形データをDXF形式に出力する機能を提供します
"""

import logging
from pathlib import Path
import math
from shapes.geometry.triangle_shape import TriangleData

# DXF出力用にezdxfをインポート
try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False
    logging.warning("ezdxfモジュールが見つかりません。DXF出力機能は利用できません。")
    logging.warning("インストールには: pip install ezdxf を実行してください。")

# ロガー設定
logger = logging.getLogger(__name__)

class DxfExportSettings:
    """DXFエクスポートの設定を管理するクラス"""
    def __init__(self):
        # テキストサイズ設定
        self.edge_text_scale_factor = 0.05  # 辺の長さテキストのスケール係数
        self.number_text_scale_factor = 0.1  # 三角形番号テキストのスケール係数
        
        # 表示設定
        self.show_edge_lengths = True   # 辺の長さを表示するか
        self.show_triangle_numbers = True  # 三角形番号を表示するか
        
        # テキストの配置設定
        self.auto_rotate_edge_text = True  # 辺のテキストを辺に沿って回転させるか
        self.text_halign = 4  # 4=Middle（水平方向の中央揃え）
        self.text_valign = 2  # 2=Middle（垂直方向の中央揃え）

class DxfExporter:
    """三角形データをDXF形式にエクスポートするクラス"""
    
    # デフォルト設定
    default_settings = DxfExportSettings()
    
    @staticmethod
    def export(triangle_list, file_path, settings=None):
        """三角形データをDXFファイルに出力する
        
        Args:
            triangle_list: 出力する三角形のリスト
            file_path: 出力先ファイルパス
            settings: DxfExportSettings オブジェクト（None の場合はデフォルト設定を使用）
        
        Returns:
            bool: 出力が成功したかどうか
        """
        # 設定が指定されていない場合はデフォルト設定を使用
        settings = settings or DxfExporter.default_settings
        
        if not HAS_EZDXF:
            logger.error("ezdxfモジュールがインストールされていないため、DXF出力機能は利用できません。")
            return False
        
        if not triangle_list:
            logger.warning("出力する三角形データがありません。")
            return False
        
        try:
            # R2010形式のDXFドキュメントを作成
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # 各三角形をポリラインとして追加
            for triangle_data in triangle_list:
                if triangle_data and triangle_data.points:
                    # 三角形の点を取得
                    points = [(p.x(), p.y(), 0) for p in triangle_data.points]
                    # 閉じたポリラインを作成
                    points.append(points[0])  # 最初の点を追加して閉じる
                    
                    # ポリラインをモデルスペースに追加
                    msp.add_lwpolyline(points)
                    
                    # 辺の長さを表示する場合
                    if settings.show_edge_lengths:
                        # 寸法テキストを追加
                        for i, length in enumerate(triangle_data.lengths):
                            # 辺の中点を計算
                            p1, p2 = triangle_data.get_side_line(i)
                            mid_x = (p1.x() + p2.x()) / 2
                            mid_y = (p1.y() + p2.y()) / 2
                            
                            angle_deg = 0  # デフォルト角度
                            
                            # テキストを回転する場合
                            if settings.auto_rotate_edge_text:
                                # 辺の角度を計算
                                angle_rad = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
                                angle_deg = math.degrees(angle_rad)
                                
                                # 可読性のため角度を調整（テキストが上下逆さまにならないように）
                                if 90 < angle_deg <= 270 or -270 <= angle_deg < -90:
                                    angle_deg += 180  # 180度回転させて読みやすく
                            
                            # テキストサイズを計算
                            text_height = length * settings.edge_text_scale_factor
                            
                            # テキスト追加
                            text = msp.add_text(f"{length:.1f}", height=text_height)
                            text.dxf.insert = (mid_x, mid_y)
                            text.dxf.rotation = angle_deg  # 回転角度を設定
                            text.dxf.halign = settings.text_halign
                            text.dxf.valign = settings.text_valign
                    
                    # 三角形番号を表示する場合
                    if settings.show_triangle_numbers:
                        # 三角形番号を中央に追加
                        center_x = triangle_data.center_point.x()
                        center_y = triangle_data.center_point.y()
                        
                        # テキストサイズを計算
                        text_height = max(triangle_data.lengths) * settings.number_text_scale_factor
                        
                        # 三角形番号テキストの追加
                        number_text = msp.add_text(f"{triangle_data.number}", height=text_height)
                        number_text.dxf.insert = (center_x, center_y)
                        number_text.dxf.halign = settings.text_halign  # 中央揃え
                        number_text.dxf.valign = settings.text_valign  # 垂直中央揃え
                        # 番号は回転させない（常に水平に表示）
            
            # DXFファイルを保存
            doc.saveas(file_path)
            logger.info(f"DXFファイルを保存しました: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"DXF出力エラー: {str(e)}")
            return False


# 後方互換性のために元のクラス名を維持するエイリアス
TriangleExporter = DxfExporter 