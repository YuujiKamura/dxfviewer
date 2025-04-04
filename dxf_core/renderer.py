#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF Renderer - DXFエンティティのレンダリングモジュール

DXFエンティティをグラフィックスシーンに描画する機能を提供します。
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtGui import QColor

# 自作モジュール
from dxf_core.adapter import create_dxf_adapter

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

def draw_dxf_entities(scene: QGraphicsScene, dxf_data: Dict[str, Any]) -> int:
    """
    DXFエンティティをシーンに描画する
    
    Args:
        scene: 描画先のQGraphicsScene
        dxf_data: DXFデータを含む辞書
        
    Returns:
        int: 描画されたエンティティの数
    """
    if not dxf_data or 'entities' not in dxf_data:
        logger.warning("描画するDXFデータがありません")
        return 0
    
    # DXF用アダプターを作成
    adapter = create_dxf_adapter(scene)
    
    # アダプターを使って描画
    return draw_dxf_entities_with_adapter(adapter, dxf_data)

def draw_dxf_entities_with_adapter(adapter, dxf_data: Dict[str, Any]) -> int:
    """
    アダプターを使用してDXFエンティティをシーンに描画する
    
    Args:
        adapter: DXFSceneAdapterインスタンス
        dxf_data: DXFデータを含む辞書
        
    Returns:
        int: 描画されたエンティティの数
    """
    if not dxf_data or 'entities' not in dxf_data:
        logger.warning("描画するDXFデータがありません")
        return 0
    
    # エンティティ数のカウント
    total_entities = len(dxf_data['entities'])
    processed_entities = 0
    
    # 進捗状況を10%ごとに表示
    progress_interval = max(1, total_entities // 10)
    
    # すべてのエンティティを処理
    for entity in dxf_data['entities']:
        try:
            # デフォルト色（白）
            color = (0, 0, 0)  # 黒
            
            # エンティティごとの色を取得（実装例、必要に応じて変更）
            if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'color'):
                # カラーコードからRGB値に変換（簡易的な実装）
                color_code = entity.dxf.color
                if 1 <= color_code <= 255:
                    # カラーコードに応じた色を設定（詳細なカラーテーブルは省略）
                    if color_code == 1:  # 赤
                        color = (255, 0, 0)
                    elif color_code == 2:  # 黄
                        color = (255, 255, 0)
                    elif color_code == 3:  # 緑
                        color = (0, 255, 0)
                    elif color_code == 4:  # シアン
                        color = (0, 255, 255)
                    elif color_code == 5:  # 青
                        color = (0, 0, 255)
                    elif color_code == 6:  # マゼンタ
                        color = (255, 0, 255)
                    elif color_code == 7:  # 白/黒
                        color = (0, 0, 0)  # 黒に固定
                    else:
                        # その他の色は黒（シンプル実装）
                        color = (0, 0, 0)
            
            # アダプターを使用してエンティティを描画
            item, result = adapter.process_entity(entity, color)
            
            # 処理カウントを更新
            processed_entities += 1
            
            # 進捗状況を表示
            if processed_entities % progress_interval == 0:
                progress = int(processed_entities / total_entities * 100)
                logger.debug(f"描画進捗: {progress}% ({processed_entities}/{total_entities})")
                
        except Exception as e:
            logger.error(f"エンティティの描画中にエラーが発生: {str(e)}")
    
    logger.info(f"描画完了: {processed_entities}/{total_entities}エンティティを処理")
    return processed_entities

def get_entity_color(entity) -> Tuple[int, int, int]:
    """
    エンティティの色を取得する
    
    Args:
        entity: DXFエンティティ
        
    Returns:
        tuple: (R, G, B)の色情報
    """
    # デフォルト色（黒）
    default_color = (0, 0, 0)
    
    # エンティティに色情報がなければデフォルト色を返す
    if not hasattr(entity, 'dxf') or not hasattr(entity.dxf, 'color'):
        return default_color
    
    # カラーコードからRGB値に変換（簡易実装）
    color_code = entity.dxf.color
    if 0 <= color_code <= 256:
        # 0と256は特殊なコード、それ以外はカラーテーブルを使用
        if color_code == 0 or color_code == 256:
            return default_color
            
        # 以下は簡易的なカラーテーブル実装、本来は完全なACIカラーテーブルが必要
        if color_code == 1:  # 赤
            return (255, 0, 0)
        elif color_code == 2:  # 黄
            return (255, 255, 0)
        elif color_code == 3:  # 緑
            return (0, 255, 0)
        elif color_code == 4:  # シアン
            return (0, 255, 255)
        elif color_code == 5:  # 青
            return (0, 0, 255)
        elif color_code == 6:  # マゼンタ
            return (255, 0, 255)
        elif color_code == 7:  # 白/黒
            return (0, 0, 0)  # 黒に固定
        else:
            # その他の色は黒（シンプル実装）
            return default_color
    
    # 範囲外のコードはデフォルト色
    return default_color 