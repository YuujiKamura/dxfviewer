#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF Parser - DXFファイル解析モジュール

DXFファイルの読み込み、解析機能を提供します。
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# ezdxfのインポート
try:
    import ezdxf
    from ezdxf import recover
    EZDXF_AVAILABLE = True
except ImportError:
    print("ezdxfモジュールのインポートエラー")
    print("pip install ezdxf を実行してインストールしてください。")
    EZDXF_AVAILABLE = False

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

def parse_dxf_file(file_path: str) -> Dict[str, Any]:
    """
    DXFファイルを解析し、データ構造に変換する
    
    Args:
        file_path: DXFファイルのパス
        
    Returns:
        dict: DXFデータを含む辞書
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    try:
        # ezdxfでDXFファイルを読み込み
        if EZDXF_AVAILABLE:
            try:
                doc = ezdxf.readfile(file_path)
            except ezdxf.DXFError:
                logger.warning(f"ファイルの読み込みに問題があります。復旧モードで再試行: {file_path}")
                doc, auditor = recover.readfile(file_path)
                if auditor.has_errors:
                    logger.warning(f"復旧結果: {len(auditor.errors)}個のエラー")
            
            # DXFデータを辞書に格納
            dxf_data = {
                'entities': list(doc.modelspace()),
                'layers': list(doc.layers),
                'version': doc.dxfversion,
                'file_path': file_path
            }
            
            logger.debug(f"DXFファイルの解析完了: {len(dxf_data['entities'])}個のエンティティ")
            return dxf_data
        else:
            raise ImportError("ezdxfモジュールが利用できません")
            
    except Exception as e:
        logger.exception(f"DXFファイルの解析中にエラーが発生: {e}")
        raise

def get_dxf_info(dxf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    DXFデータから基本情報を抽出
    
    Args:
        dxf_data: DXFデータ辞書
        
    Returns:
        dict: DXFファイルの基本情報
    """
    if not dxf_data:
        return {"error": "DXFデータがありません"}
    
    # エンティティ数をカウント
    entity_count = len(dxf_data.get('entities', []))
    
    # レイヤー情報
    layers = [layer.dxf.name for layer in dxf_data.get('layers', [])]
    
    # バージョン情報
    version = dxf_data.get('version', "不明")
    
    # エンティティタイプの集計
    entity_types = {}
    for entity in dxf_data.get('entities', []):
        entity_type = entity.dxftype()
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    # 情報をまとめる
    info = {
        'entity_count': entity_count,
        'layers': layers,
        'version': version,
        'entity_types': entity_types,
        'file_path': dxf_data.get('file_path', "不明")
    }
    
    return info 