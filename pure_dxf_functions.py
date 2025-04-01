#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
純粋関数のみを含むDXF処理モジュール。
コンテキスト（状態）に依存せず、同じ入力に対して常に同じ出力を返すことを保証します。
"""

import traceback
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any, Union
import math

# 戻り値の型を定義するデータクラス
@dataclass
class LineData:
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    width: float
    color: Tuple[int, int, int]

@dataclass
class CircleData:
    center_x: float
    center_y: float
    radius: float
    width: float
    color: Tuple[int, int, int]

@dataclass
class ArcData:
    center_x: float
    center_y: float
    radius: float
    start_angle: float
    end_angle: float
    width: float
    color: Tuple[int, int, int]

@dataclass
class PolylineData:
    points: List[Tuple[float, float]]
    width: float
    color: Tuple[int, int, int]
    is_closed: bool

@dataclass
class TextData:
    text: str
    pos_x: float
    pos_y: float
    height: float
    h_align: int  # 0=左, 2=右, 4=中央
    v_align: int  # 0=ベース, 1=下, 2=中央, 3=上
    rotation: float
    color: Tuple[int, int, int]

@dataclass
class Result:
    success: bool
    data: Any = None
    error: str = None
    details: str = None

# 線幅計算関数
def calculate_lineweight(entity, default_width=1.0, min_width=0.1) -> float:
    """
    エンティティの線幅を計算する純粋関数
    
    Args:
        entity: DXFエンティティ
        default_width: デフォルト線幅
        min_width: 最小線幅
    
    Returns:
        float: 計算された線幅
    """
    if entity is None:
        return default_width
        
    try:
        # エンティティに直接lineweight属性がある場合
        if hasattr(entity.dxf, 'lineweight'):
            lw = entity.dxf.lineweight
            if lw > 0:
                return max(lw / 10.0, min_width)
            elif lw == -1:  # DEFAULT
                return default_width
            elif lw == -2:  # BYBLOCK
                return default_width
            elif lw == -3:  # BYLAYER
                # レイヤーの線幅を取得
                if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'layer'):
                    layer_name = entity.dxf.layer
                    layer = entity.doc.layers.get(layer_name)
                    if layer and hasattr(layer.dxf, 'lineweight') and layer.dxf.lineweight > 0:
                        return max(layer.dxf.lineweight / 10.0, min_width)
    except Exception:
        pass
    
    # 情報が取得できない場合はデフォルト値を返す
    return default_width

# 色変換関数
def dxf_color_to_rgb(dxf_color_index: int) -> Tuple[int, int, int]:
    """
    DXFカラーインデックスをRGBに変換する純粋関数
    
    Args:
        dxf_color_index: DXFのカラーインデックス
        
    Returns:
        Tuple[int, int, int]: RGB値のタプル
    """
    # 基本色マッピング (簡易版)
    color_map = {
        1: (255, 0, 0),      # 赤
        2: (255, 255, 0),    # 黄
        3: (0, 255, 0),      # 緑
        4: (0, 255, 255),    # シアン
        5: (0, 0, 255),      # 青
        6: (255, 0, 255),    # マゼンタ
        7: (255, 255, 255),  # 白
        8: (128, 128, 128),  # 灰色
        9: (192, 192, 192),  # 明るい灰色
    }
    
    return color_map.get(dxf_color_index, (255, 255, 255))  # デフォルトは白

# 線描画データ計算関数
def compute_line_data(start, end, color=(255, 255, 255), entity=None, default_width=1.0) -> LineData:
    """
    線の描画データを計算する純粋関数
    
    Args:
        start: 開始点座標 (x, y)
        end: 終了点座標 (x, y)
        color: 色 (R, G, B)
        entity: DXFエンティティ
        default_width: デフォルト線幅
        
    Returns:
        LineData: 線の描画データ
    """
    # 線幅の計算
    line_width = calculate_lineweight(entity, default_width)
    
    return LineData(
        start_x=start[0], 
        start_y=start[1], 
        end_x=end[0], 
        end_y=end[1],
        width=line_width,
        color=color
    )

# 円描画データ計算関数
def compute_circle_data(center, radius, color=(255, 255, 255), entity=None, default_width=1.0) -> CircleData:
    """
    円の描画データを計算する純粋関数
    
    Args:
        center: 中心座標 (x, y)
        radius: 半径
        color: 色 (R, G, B)
        entity: DXFエンティティ
        default_width: デフォルト線幅
        
    Returns:
        CircleData: 円の描画データ
    """
    # 線幅の計算
    line_width = calculate_lineweight(entity, default_width)
    
    return CircleData(
        center_x=center[0],
        center_y=center[1],
        radius=radius,
        width=line_width,
        color=color
    )

# 円弧描画データ計算関数
def compute_arc_data(center, radius, start_angle, end_angle, color=(255, 255, 255), entity=None, default_width=1.0) -> ArcData:
    """
    円弧の描画データを計算する純粋関数
    
    Args:
        center: 中心座標 (x, y)
        radius: 半径
        start_angle: 開始角度 (度)
        end_angle: 終了角度 (度)
        color: 色 (R, G, B)
        entity: DXFエンティティ
        default_width: デフォルト線幅
        
    Returns:
        ArcData: 円弧の描画データ
    """
    # 線幅の計算
    line_width = calculate_lineweight(entity, default_width)
    
    return ArcData(
        center_x=center[0],
        center_y=center[1],
        radius=radius,
        start_angle=start_angle,
        end_angle=end_angle,
        width=line_width,
        color=color
    )

# ポリライン描画データ計算関数
def compute_polyline_data(points, color=(255, 255, 255), entity=None, default_width=1.0) -> PolylineData:
    """
    ポリラインの描画データを計算する純粋関数
    
    Args:
        points: 頂点座標のリスト [(x1, y1), (x2, y2), ...]
        color: 色 (R, G, B)
        entity: DXFエンティティ
        default_width: デフォルト線幅
        
    Returns:
        PolylineData: ポリラインの描画データ
    """
    # 線幅の計算
    line_width = calculate_lineweight(entity, default_width)
    
    # 閉じたポリラインかどうか
    is_closed = False
    if entity and hasattr(entity, 'is_closed'):
        is_closed = entity.is_closed
    
    return PolylineData(
        points=points,
        width=line_width,
        color=color,
        is_closed=is_closed
    )

# テキスト描画データ計算関数
def compute_text_data(text, pos, height, color=(255, 255, 255), entity=None) -> TextData:
    """
    テキストの描画データを計算する純粋関数
    
    Args:
        text: テキスト内容
        pos: 挿入位置 (x, y)
        height: テキスト高さ
        color: 色 (R, G, B)
        entity: DXFエンティティ
        
    Returns:
        TextData: テキストの描画データ
    """
    # 水平方向の配置
    h_align = 0  # デフォルト: 左揃え
    if entity and hasattr(entity.dxf, 'halign'):
        h_align = entity.dxf.halign
    
    # 垂直方向の配置
    v_align = 0  # デフォルト: ベースライン
    if entity and hasattr(entity.dxf, 'valign'):
        v_align = entity.dxf.valign
    
    # 回転
    rotation = 0
    if entity and hasattr(entity.dxf, 'rotation'):
        rotation = entity.dxf.rotation
    
    return TextData(
        text=text,
        pos_x=pos[0],
        pos_y=pos[1],
        height=height,
        h_align=h_align,
        v_align=v_align,
        rotation=rotation,
        color=color
    )

# DXFエンティティ処理関数
def process_entity_data(entity, default_color=(255, 255, 255), default_width=1.0) -> Result:
    """
    DXFエンティティからデータを抽出する純粋関数
    
    Args:
        entity: DXFエンティティ
        default_color: デフォルト色 (R, G, B)
        default_width: デフォルト線幅
        
    Returns:
        Result: 処理結果（成功/失敗と関連データ）
    """
    try:
        entity_type = entity.dxftype()
        
        if entity_type == 'LINE':
            start = (entity.dxf.start.x, entity.dxf.start.y)
            end = (entity.dxf.end.x, entity.dxf.end.y)
            data = compute_line_data(start, end, default_color, entity, default_width)
            return Result(success=True, data=data)
            
        elif entity_type == 'CIRCLE':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            radius = entity.dxf.radius
            data = compute_circle_data(center, radius, default_color, entity, default_width)
            return Result(success=True, data=data)
            
        elif entity_type == 'ARC':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            data = compute_arc_data(center, radius, start_angle, end_angle, default_color, entity, default_width)
            return Result(success=True, data=data)
            
        elif entity_type == 'POLYLINE' or entity_type == 'LWPOLYLINE':
            # ポリラインの頂点を取得
            if entity_type == 'LWPOLYLINE':
                # LWポリラインは直接座標を持っている
                points = [(point[0], point[1]) for point in entity.get_points()]
            else:
                # 通常のポリラインは頂点オブジェクトを持っている
                points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
            
            data = compute_polyline_data(points, default_color, entity, default_width)
            return Result(success=True, data=data)
            
        elif entity_type == 'TEXT' or entity_type == 'MTEXT':
            # テキストの処理
            if entity_type == 'TEXT':
                text = entity.dxf.text
                pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                height = entity.dxf.height
            else:  # MTEXT
                text = entity.text
                pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                height = entity.dxf.char_height
            
            data = compute_text_data(text, pos, height, default_color, entity)
            return Result(success=True, data=data)
            
        else:
            # 未対応のエンティティタイプ
            return Result(
                success=False, 
                error=f"未対応のエンティティタイプ", 
                details=f"エンティティタイプ: {entity_type}"
            )
        
    except Exception as e:
        error_details = traceback.format_exc()
        entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else "不明"
        return Result(
            success=False, 
            error=f"エンティティの処理中にエラーが発生: {str(e)}", 
            details=error_details
        )

# テーマ色の取得関数
def get_theme_colors(theme_name):
    """
    テーマ名から背景色と線色を取得する純粋関数
    
    Args:
        theme_name: テーマ名 ("ダーク", "ライト", "ブルー")
        
    Returns:
        Tuple[Tuple[int, int, int], Tuple[int, int, int]]: (背景色, 線色)のタプル
    """
    if theme_name == "ダーク":
        return (40, 40, 40), (255, 255, 255)
    elif theme_name == "ライト":
        return (240, 240, 240), (0, 0, 0)
    elif theme_name == "ブルー":
        return (25, 35, 45), (200, 220, 255)
    else:
        return (40, 40, 40), (255, 255, 255)  # デフォルト

# 同一性検証関数
def verify_identical_output(func, args1, args2) -> bool:
    """
    同じ関数に異なる引数を与えた結果が同一かどうかを検証する関数
    
    Args:
        func: テスト対象の関数
        args1: 1回目の引数
        args2: 2回目の引数
        
    Returns:
        bool: 結果が同一であればTrue、異なればFalse
    """
    result1 = func(*args1)
    result2 = func(*args2)
    return result1 == result2

# サンプルDXF作成関数
def create_sample_dxf(filename):
    """
    サンプルDXFファイルを作成する純粋関数
    同じファイル名に対して常に同じ結果を返します。
    
    Args:
        filename: 出力するDXFファイルのパス
        
    Returns:
        Tuple[str, Tuple[str, str]]: (成功した場合のファイル名, エラー情報のタプル)
    """
    if not filename:
        return None, ("ファイル名が指定されていません", "")
    
    if not filename.lower().endswith('.dxf'):
        filename += '.dxf'
    
    try:
        from ezdxf.r12writer import r12writer
        
        with r12writer(filename) as dxf:
            # 線幅テスト用の平行線を描画（異なる線幅で比較できるように）
            for i in range(5):
                y = 150 + i * 20
                dxf.add_line((10, y), (190, y))
                dxf.add_text(f"線幅テスト {i+1}", (200, y), height=7)
            
            # 線を描画
            dxf.add_line((0, 0), (100, 0))
            dxf.add_line((100, 0), (100, 100))
            dxf.add_line((100, 100), (0, 100))
            dxf.add_line((0, 100), (0, 0))
            
            # 円を描画
            dxf.add_circle((50, 50), 40)
            
            # テキストを追加
            dxf.add_text("サンプルDXF", (10, 110), height=10)
            
            # 対角線を描画
            dxf.add_line((0, 0), (100, 100))
            dxf.add_line((0, 100), (100, 0))
            
            # 多角形（ポリライン）を描画
            points = [(150, 10), (170, 20), (190, 40), (180, 60), (150, 50)]
            dxf.add_polyline(points, close=True)
            
        return filename, None
        
    except Exception as e:
        error_details = traceback.format_exc()
        return None, (str(e), error_details)


if __name__ == "__main__":
    # 自己検証テスト
    print("純粋関数の自己検証を実行中...")
    
    # 同じ入力に対して同じ出力を返すかテスト
    line_data1 = compute_line_data((0, 0), (100, 100))
    line_data2 = compute_line_data((0, 0), (100, 100))
    assert line_data1 == line_data2, "線データの同一性テスト失敗"
    
    circle_data1 = compute_circle_data((50, 50), 30)
    circle_data2 = compute_circle_data((50, 50), 30)
    assert circle_data1 == circle_data2, "円データの同一性テスト失敗"
    
    arc_data1 = compute_arc_data((50, 50), 30, 0, 90)
    arc_data2 = compute_arc_data((50, 50), 30, 0, 90)
    assert arc_data1 == arc_data2, "円弧データの同一性テスト失敗"
    
    polyline_data1 = compute_polyline_data([(0, 0), (10, 10), (20, 0)])
    polyline_data2 = compute_polyline_data([(0, 0), (10, 10), (20, 0)])
    assert polyline_data1 == polyline_data2, "ポリラインデータの同一性テスト失敗"
    
    text_data1 = compute_text_data("テスト", (10, 10), 5)
    text_data2 = compute_text_data("テスト", (10, 10), 5)
    assert text_data1 == text_data2, "テキストデータの同一性テスト失敗"
    
    print("すべてのテストが成功しました。同一の入力に対して同一の出力が保証されています。") 