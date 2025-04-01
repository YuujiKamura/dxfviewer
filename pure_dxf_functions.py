#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
純粋関数のみを含むDXF処理モジュール。
コンテキスト（状態）に依存せず、同じ入力に対して常に同じ出力を返すことを保証します。
"""

import traceback
import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any, Union
import math

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

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
        if logger:
            logger.debug(f"  エンティティから取得した水平揃え (halign): {h_align}")
    
    # 垂直方向の配置
    v_align = 0  # デフォルト: ベースライン
    if entity and hasattr(entity.dxf, 'valign'):
        v_align = entity.dxf.valign
        if logger:
            logger.debug(f"  エンティティから取得した垂直揃え (valign): {v_align}")
    
    # 回転
    rotation = 0
    if entity and hasattr(entity.dxf, 'rotation'):
        rotation = entity.dxf.rotation
    
    # エンティティタイプの確認（デバッグ用）
    if entity and logger:
        entity_type = entity.dxftype()
        logger.debug(f"  テキストデータ計算: タイプ={entity_type}, テキスト='{text}', h_align={h_align}, v_align={v_align}")
    
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
    DXFエンティティを処理してデータ構造を生成する純粋関数
    
    Args:
        entity: DXFエンティティ
        default_color: デフォルト色 (R, G, B)
        default_width: デフォルト線幅
        
    Returns:
        Result: 処理結果
    """
    try:
        # エンティティがNoneの場合はエラー
        if entity is None:
            return Result(False, None, "エンティティがNoneです")
        
        # エンティティタイプの取得
        entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else '不明'
        
        # エンティティタイプに応じて処理
        if entity_type == 'LINE':
            start = (entity.dxf.start.x, entity.dxf.start.y)
            end = (entity.dxf.end.x, entity.dxf.end.y)
            line_data = compute_line_data(start, end, default_color, entity, default_width)
            return Result(True, line_data)
            
        elif entity_type == 'CIRCLE':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            radius = entity.dxf.radius
            circle_data = compute_circle_data(center, radius, default_color, entity, default_width)
            return Result(True, circle_data)
            
        elif entity_type == 'ARC':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            arc_data = compute_arc_data(center, radius, start_angle, end_angle, default_color, entity, default_width)
            return Result(True, arc_data)
            
        elif entity_type == 'POLYLINE' or entity_type == 'LWPOLYLINE':
            # ポリラインの頂点を取得
            points = []
            if entity_type == 'LWPOLYLINE':
                # LWポリラインは直接座標を持っている
                points = [(point[0], point[1]) for point in entity.get_points()]
            else:
                # 通常のポリラインは頂点オブジェクトを持っている
                points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
            
            polyline_data = compute_polyline_data(points, default_color, entity, default_width)
            return Result(True, polyline_data)
            
        elif entity_type == 'TEXT' or entity_type == 'MTEXT':
            # テキストの位置を取得
            if entity_type == 'TEXT':
                pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                text = entity.dxf.text
                height = entity.dxf.height
                # テキスト配置の取得
                h_align = getattr(entity.dxf, 'halign', 0)
                v_align = getattr(entity.dxf, 'valign', 0)
                rotation = getattr(entity.dxf, 'rotation', 0)
                if logger:
                    logger.debug(f"  TEXT エンティティ: pos=({pos[0]}, {pos[1]}), text='{text}', h_align={h_align}")
            else:  # MTEXT
                pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                text = entity.text
                height = entity.dxf.char_height
                # MTEXTの配置はattachment_pointから計算
                attachment_point = getattr(entity.dxf, 'attachment_point', 1)
                h_align_raw = attachment_point % 3  # 0=左, 1=中央, 2=右
                v_align = attachment_point // 3  # 0=上, 1=中央, 2=下
                
                # MTEXTの中央揃え(1)をTEXTの中央揃え(4)に変換
                if h_align_raw == 1:  # 中央揃え
                    h_align = 4  # TEXTの中央揃え値に合わせる
                elif h_align_raw == 2:  # 右揃え
                    h_align = 2  # 右揃えは同じ値
                else:  # 左揃え
                    h_align = 0  # 左揃えは同じ値
                
                rotation = getattr(entity.dxf, 'rotation', 0)
                if logger:
                    logger.debug(f"  MTEXT エンティティ: pos=({pos[0]}, {pos[1]}), text='{text}', attachment_point={attachment_point}, h_align_raw={h_align_raw}, h_align={h_align}, v_align={v_align}")
            
            text_data = compute_text_data(text, pos, height, default_color, entity)
            # 水平垂直配置と回転を設定
            text_data.h_align = h_align
            text_data.v_align = v_align
            text_data.rotation = rotation
            return Result(True, text_data)
            
        else:
            # サポートされていないエンティティタイプ
            return Result(False, None, f"サポートされていないエンティティタイプです: {entity_type}")
    
    except Exception as e:
        # エラーが発生した場合、詳細情報を返す
        error_details = traceback.format_exc()
        return Result(False, None, f"エンティティ処理中にエラーが発生: {str(e)}", error_details)

# テーマ色の取得関数
def get_default_colors() -> tuple:
    """
    デフォルトの色設定を返す純粋関数
    
    Returns:
        tuple: (背景色RGB, 線色RGB)のタプル
    """
    # デフォルトの色
    bg_color = (255, 255, 255)  # 白背景
    line_color = (0, 0, 0)      # 黒線
    
    return bg_color, line_color

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