#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleExporters - 三角形データのDXFエクスポート機能

三角形データをDXF形式に出力する機能を提供します
"""

import logging
from pathlib import Path

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

class DxfExporter:
    """三角形データをDXF形式にエクスポートするクラス"""
    
    @staticmethod
    def export(triangle_list, file_path):
        """三角形データをDXFファイルに出力する"""
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
                    
                    # 寸法テキストを追加
                    for i, length in enumerate(triangle_data.lengths):
                        # 辺の中点を計算
                        p1, p2 = triangle_data.get_side_line(i)
                        mid_x = (p1.x() + p2.x()) / 2
                        mid_y = (p1.y() + p2.y()) / 2
                        
                        # テキスト追加
                        text = msp.add_text(f"{length:.1f}", height=length * 0.05)
                        text.dxf.insert = (mid_x, mid_y)
                        text.dxf.halign = 4  # 4=Middle
                        text.dxf.valign = 2  # 2=Middle
            
            # DXFファイルを保存
            doc.saveas(file_path)
            logger.info(f"DXFファイルを保存しました: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"DXF出力エラー: {str(e)}")
            return False


# 後方互換性のために元のクラス名を維持するエイリアス
TriangleExporter = DxfExporter 