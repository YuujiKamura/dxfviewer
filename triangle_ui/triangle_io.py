#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleIO - 三角形データのJSONシリアライズ・デシリアライズ機能

三角形データをJSONファイルに保存し、読み込む機能を提供します
"""

import json
import logging
from pathlib import Path
from PySide6.QtCore import QPointF

# ロガー設定
logger = logging.getLogger(__name__)

class JsonIO:
    """三角形データのJSON入出力を扱うクラス"""
    
    @staticmethod
    def save_to_json(triangle_list, file_path):
        """三角形データをJSONファイルに保存"""
        if not triangle_list:
            logger.warning("保存する三角形データがありません。")
            return False
            
        # 三角形データをシリアライズ可能な辞書に変換
        triangle_dicts = []
        for triangle in triangle_list:
            # 各三角形を辞書形式に変換
            triangle_dict = {
                'number': triangle.number,
                'name': triangle.name,
                'lengths': triangle.lengths,
                'points': [
                    {'x': p.x(), 'y': p.y()} for p in triangle.points
                ],
                'angle_deg': triangle.angle_deg,
                'internal_angles_deg': triangle.internal_angles_deg,
                'center_point': {'x': triangle.center_point.x(), 'y': triangle.center_point.y()},
                'connection_side': triangle.connection_side,
                'parent_number': triangle.parent.number if triangle.parent else -1,
                'children': [
                    child.number if child else -1 for child in triangle.children
                ],
                'color': {
                    'r': triangle.color.red(),
                    'g': triangle.color.green(),
                    'b': triangle.color.blue(),
                    'a': triangle.color.alpha()
                }
            }
            triangle_dicts.append(triangle_dict)
        
        try:
            # JSONファイルに書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(triangle_dicts, f, indent=2)
            
            logger.info(f"{len(triangle_list)}個の三角形データを{file_path}に保存しました")
            return True
        except Exception as e:
            logger.error(f"JSON保存エラー: {str(e)}")
            return False
    
    @staticmethod
    def load_from_json(file_path, triangle_data_class):
        """JSONファイルから三角形データを読み込む"""
        try:
            # JSONファイルを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                triangle_dicts = json.load(f)
            
            # 辞書の存在チェック
            if not triangle_dicts or not isinstance(triangle_dicts, list):
                logger.error("JSONファイルに有効な三角形データが含まれていません。")
                return []
            
            # 三角形データを作成（最初は接続関係なし）
            triangles = []
            for triangle_dict in triangle_dicts:
                # 点をQPointFに変換
                points = [
                    QPointF(p['x'], p['y']) for p in triangle_dict['points']
                ]
                
                # 中心点を復元
                center_point = QPointF(
                    triangle_dict['center_point']['x'],
                    triangle_dict['center_point']['y']
                )
                
                # 基本的な三角形データの作成
                triangle = triangle_data_class(
                    a=triangle_dict['lengths'][0],
                    b=triangle_dict['lengths'][1],
                    c=triangle_dict['lengths'][2],
                    p_ca=points[0],
                    angle_deg=triangle_dict['angle_deg'],
                    number=triangle_dict['number']
                )
                
                # 頂点位置と中心点を直接設定
                triangle.points = points
                triangle.center_point = center_point
                
                # 追加の属性を復元
                if 'internal_angles_deg' in triangle_dict:
                    triangle.internal_angles_deg = triangle_dict['internal_angles_deg']
                
                if 'name' in triangle_dict:
                    triangle.name = triangle_dict['name']
                
                # 色情報を復元
                if 'color' in triangle_dict:
                    color_dict = triangle_dict['color']
                    from PySide6.QtGui import QColor
                    triangle.color = QColor(
                        color_dict['r'],
                        color_dict['g'],
                        color_dict['b'],
                        color_dict.get('a', 255)  # アルファ値がなければデフォルト値
                    )
                
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
            
            logger.info(f"{len(triangles)}個の三角形データを{file_path}から読み込みました")
            return triangles
        except Exception as e:
            logger.error(f"JSON読込エラー: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return [] 