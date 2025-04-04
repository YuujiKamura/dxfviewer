#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFファイル読み込みモジュール

DXFファイルを読み込み、内部データ構造に変換します。
"""

import os
import logging
from typing import Optional, List, Dict, Any, Tuple

from core.dxf_entities import (
    DxfEntity, DxfLine, DxfCircle, DxfArc, DxfPolyline, DxfText
)
from core.dxf_colors import get_entity_color, RGBColor

# ezdxfのインポート
try:
    import ezdxf
except ImportError:
    ezdxf = None
    logging.warning("ezdxfがインストールされていません。DXF読み込み機能は使用できません。")

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

def load_dxf_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    DXFファイルを読み込んで内部形式に変換
    
    Args:
        file_path: DXFファイルのパス
        
    Returns:
        Dict: メタデータとエンティティリストを含む辞書
        エラー時はNone
    """
    if not ezdxf:
        logger.error("ezdxfがインストールされていないため、DXFファイルを読み込めません")
        return None
        
    # ファイルの存在確認
    if not os.path.exists(file_path):
        logger.error(f"ファイルが存在しません: {file_path}")
        return None
        
    try:
        # DXFファイルを読み込み
        logger.info(f"DXFファイル読み込み: {file_path}")
        doc = ezdxf.readfile(file_path)
        
        # 結果格納用の辞書
        result = {
            "metadata": {
                "filename": os.path.basename(file_path),
                "filepath": file_path,
                "version": doc.dxfversion,
                "layers": [layer.dxf.name for layer in doc.layers]
            },
            "entities": []
        }
        
        # モデル空間のエンティティを取得
        msp = doc.modelspace()
        
        # エンティティの変換
        for entity in msp:
            converted_entity = convert_entity(entity)
            if converted_entity:
                result["entities"].append(converted_entity)
        
        logger.info(f"DXFファイル読み込み完了: {len(result['entities'])}個のエンティティ")
        return result
    
    except Exception as e:
        logger.error(f"DXFファイル読み込みエラー: {str(e)}", exc_info=True)
        return None

def convert_entity(entity: Any) -> Optional[DxfEntity]:
    """
    ezdxfエンティティを内部エンティティに変換
    
    Args:
        entity: ezdxfエンティティ
        
    Returns:
        DxfEntity: 変換された内部エンティティ、変換失敗時はNone
    """
    try:
        entity_type = entity.dxftype()
        
        # エンティティの色と線幅を取得
        color = get_entity_color(entity)
        width = get_entity_width(entity)
        
        # LINE - 線分
        if entity_type == 'LINE':
            return DxfLine(
                start_x=entity.dxf.start.x,
                start_y=entity.dxf.start.y,
                end_x=entity.dxf.end.x,
                end_y=entity.dxf.end.y,
                color=color,
                width=width
            )
        
        # CIRCLE - 円
        elif entity_type == 'CIRCLE':
            return DxfCircle(
                center_x=entity.dxf.center.x,
                center_y=entity.dxf.center.y,
                radius=entity.dxf.radius,
                color=color,
                width=width
            )
        
        # ARC - 円弧
        elif entity_type == 'ARC':
            return DxfArc(
                center_x=entity.dxf.center.x,
                center_y=entity.dxf.center.y,
                radius=entity.dxf.radius,
                start_angle=entity.dxf.start_angle,
                end_angle=entity.dxf.end_angle,
                color=color,
                width=width
            )
        
        # LWPOLYLINE - 軽量ポリライン
        elif entity_type == 'LWPOLYLINE':
            points = [(point[0], point[1]) for point in entity.get_points()]
            return DxfPolyline(
                points=points,
                color=color,
                width=width,
                is_closed=entity.is_closed
            )
        
        # POLYLINE - ポリライン
        elif entity_type == 'POLYLINE':
            points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
            return DxfPolyline(
                points=points,
                color=color,
                width=width,
                is_closed=entity.is_closed
            )
        
        # TEXT - テキスト
        elif entity_type == 'TEXT':
            return DxfText(
                text=entity.dxf.text,
                pos_x=entity.dxf.insert.x,
                pos_y=entity.dxf.insert.y,
                height=entity.dxf.height,
                rotation=entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0,
                h_align=entity.dxf.halign if hasattr(entity.dxf, 'halign') else 0,
                v_align=entity.dxf.valign if hasattr(entity.dxf, 'valign') else 0,
                color=color
            )
        
        # MTEXT - 複数行テキスト
        elif entity_type == 'MTEXT':
            # MTEXTの配置をTEXTの形式に変換
            h_align = 0  # デフォルト: 左揃え
            v_align = 0  # デフォルト: ベースライン
            
            if hasattr(entity.dxf, 'attachment_point'):
                attachment = entity.dxf.attachment_point
                # 水平方向: 0=左, 1=中央, 2=右
                h_value = attachment % 3
                if h_value == 1:  # 中央
                    h_align = 4
                elif h_value == 2:  # 右
                    h_align = 2
                
                # 垂直方向: 0=上, 1=中央, 2=下
                v_value = attachment // 3
                if v_value == 0:  # 上
                    v_align = 3
                elif v_value == 1:  # 中央
                    v_align = 2
                elif v_value == 2:  # 下
                    v_align = 1
            
            return DxfText(
                text=entity.text,
                pos_x=entity.dxf.insert.x,
                pos_y=entity.dxf.insert.y,
                height=entity.dxf.char_height,
                rotation=entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0.0,
                h_align=h_align,
                v_align=v_align,
                color=color
            )
        
        # サポートされていないエンティティタイプ
        else:
            logger.debug(f"サポートされていないエンティティタイプ: {entity_type}")
            return None
            
    except Exception as e:
        logger.warning(f"エンティティの変換中にエラー: {str(e)}")
        return None

def get_entity_width(entity: Any) -> float:
    """エンティティの線幅を取得"""
    # デフォルト線幅
    default_width = 1.0
    
    try:
        # lineweight属性がある場合
        if hasattr(entity.dxf, 'lineweight'):
            lw = entity.dxf.lineweight
            
            # 正の値の場合（100分の1 mm単位）
            if lw > 0:
                return max(lw / 10.0, 0.1)  # ピクセル単位に変換
                
            # BYLAYERの場合
            elif lw == -3 and hasattr(entity.dxf, 'layer') and hasattr(entity, 'doc'):
                if entity.doc:
                    layer = entity.doc.layers.get(entity.dxf.layer)
                    if layer and hasattr(layer.dxf, 'lineweight') and layer.dxf.lineweight > 0:
                        return max(layer.dxf.lineweight / 10.0, 0.1)
        
        return default_width
        
    except Exception as e:
        logger.debug(f"線幅の取得中にエラー: {str(e)}")
        return default_width 