#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleGeometry - 三角形の幾何学計算

三角形の頂点座標計算、角度計算、成立条件などの純粋な計算ロジックを提供
"""

import math
from PySide6.QtCore import QPointF
import logging

# ロガー設定
logger = logging.getLogger(__name__)

def is_valid_triangle(a, b, c):
    """三角形の成立条件を確認する純粋関数"""
    if a <= 0 or b <= 0 or c <= 0:
        return False
    return (a + b > c) and (b + c > a) and (c + a > b)

def calculate_internal_angles(a, b, c):
    """三辺から内角を計算する純粋関数
    
    戻り値: [角A, 角B, 角C] (度数法)
    """
    angles = [0.0, 0.0, 0.0]
    
    # 角A（辺BCの対角）
    if b * c > 0:
        cos_angle_a = (b**2 + c**2 - a**2) / (2 * b * c)
        cos_angle_a = max(-1.0, min(1.0, cos_angle_a))  # 数値誤差対策
        angles[0] = math.degrees(math.acos(cos_angle_a))
    
    # 角B（辺CAの対角）
    if a * c > 0:
        cos_angle_b = (a**2 + c**2 - b**2) / (2 * a * c)
        cos_angle_b = max(-1.0, min(1.0, cos_angle_b))
        angles[1] = math.degrees(math.acos(cos_angle_b))
    
    # 角C（辺ABの対角）
    if a * b > 0:
        cos_angle_c = (a**2 + b**2 - c**2) / (2 * a * b)
        cos_angle_c = max(-1.0, min(1.0, cos_angle_c))
        angles[2] = math.degrees(math.acos(cos_angle_c))
    
    return angles

def calculate_triangle_area(a, b, c):
    """三角形の面積をヘロンの公式で計算する純粋関数"""
    # 半周長
    s = (a + b + c) / 2
    # 面積
    try:
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        return area
    except ValueError:
        logger.warning(f"面積計算エラー: 三角形が成立しない ({a}, {b}, {c})")
        return 0.0

def calculate_triangle_height(a, b, c, base_side=0):
    """三角形の高さを計算する純粋関数
    
    base_side: どの辺を底辺とするか (0=辺A, 1=辺B, 2=辺C)
    """
    area = calculate_triangle_area(a, b, c)
    
    # 指定された辺に対する高さを計算
    base_length = [a, b, c][base_side]
    if base_length > 0:
        return 2 * area / base_length
    return 0.0

def calculate_triangle_points(p_ca, len_a, len_b, len_c, angle_deg):
    """三角形の頂点座標を計算する純粋関数
    
    p_ca: CA点の座標 (原点)
    len_a: 辺Aの長さ
    len_b: 辺Bの長さ
    len_c: 辺Cの長さ
    angle_deg: CA→AB方向の角度 (度数法)
    
    戻り値: [CA点, AB点, BC点], 重心
    """
    # 各点の座標と重心を格納するリスト
    points = [QPointF(p_ca), QPointF(), QPointF()]
    
    # 角度をラジアンに変換
    angle_rad = math.radians(angle_deg)
    
    # 点ABの計算 (CAからlen_a分、angle_deg方向に移動)
    p_ab = QPointF(
        p_ca.x() + len_a * math.cos(angle_rad),
        p_ca.y() + len_a * math.sin(angle_rad)
    )
    points[1] = p_ab
    
    # CAからABへのベクトル
    vec_ca_to_ab = QPointF(p_ab.x() - p_ca.x(), p_ab.y() - p_ca.y())
    
    # 三角形の面積と高さを計算
    area = calculate_triangle_area(len_a, len_b, len_c)
    height = 2 * area / len_a if len_a > 0 else 0  # 辺Aに対する高さ
    
    # 点ABからの垂線の足からBCまでの距離
    try:
        base_to_bc = math.sqrt(len_c**2 - height**2)
    except ValueError:
        # 数値誤差などによるエラー時は0とする
        logger.warning(f"数値計算エラー: len_c={len_c}, height={height}")
        base_to_bc = 0
    
    # 点BCの計算
    # 垂線の方向ベクトル (CA→ABを90度回転)
    perp_vec = QPointF(-vec_ca_to_ab.y(), vec_ca_to_ab.x())
    perp_vec_length = math.sqrt(perp_vec.x()**2 + perp_vec.y()**2)
    
    if perp_vec_length > 0:
        # 単位ベクトル化して高さを掛ける
        norm_perp_vec = QPointF(
            perp_vec.x() / perp_vec_length,
            perp_vec.y() / perp_vec_length
        )
        height_vec = QPointF(
            norm_perp_vec.x() * height,
            norm_perp_vec.y() * height
        )
        
        # ABからbase_to_bc分進んだ点
        if len_a > 0:
            base_vec = QPointF(
                vec_ca_to_ab.x() / len_a * (len_a - base_to_bc),
                vec_ca_to_ab.y() / len_a * (len_a - base_to_bc)
            )
            base_point = QPointF(
                p_ab.x() - base_vec.x(),
                p_ab.y() - base_vec.y()
            )
            
            # 高さ方向に移動して点BCを求める
            points[2] = QPointF(
                base_point.x() + height_vec.x(),
                base_point.y() + height_vec.y()
            )
        else:
            points[2] = p_ab  # エラー時の回避策
    else:
        points[2] = p_ab  # エラー時の回避策
    
    # 重心計算
    center_point = QPointF(
        (points[0].x() + points[1].x() + points[2].x()) / 3.0,
        (points[0].y() + points[1].y() + points[2].y()) / 3.0
    )
    
    return points, center_point

def get_side_points(points, side_index):
    """指定された辺の両端点を返す純粋関数
    
    side_index: 0=辺A(CA→AB), 1=辺B(AB→BC), 2=辺C(BC→CA)
    """
    if len(points) != 3:
        return None
    
    # 辺のインデックスマッピング
    side_indices = [
        (0, 1),  # 辺A: CA→AB
        (1, 2),  # 辺B: AB→BC
        (2, 0)   # 辺C: BC→CA
    ]
    
    if 0 <= side_index < 3:
        start_idx, end_idx = side_indices[side_index]
        return points[start_idx], points[end_idx]
    
    return None

def get_connection_point(points, side_index):
    """指定された辺の接続点（次の三角形の基準点）を返す純粋関数"""
    if len(points) != 3:
        return None
    
    # 辺の接続点インデックス (辺の終点が次の三角形の始点)
    connection_indices = [1, 2, 0]  # 各辺の終点インデックス
    
    if 0 <= side_index < 3:
        return points[connection_indices[side_index]]
    
    return None

def get_connection_angle(points, side_index, current_angle):
    """辺の接続角度を計算する純粋関数
    
    points: 三角形の頂点座標リスト [CA, AB, BC]
    side_index: 辺のインデックス (0=A, 1=B, 2=C)
    current_angle: 現在の三角形のCA→AB方向の角度 (度数法)
    
    戻り値: 次の三角形のCA→AB方向の角度 (度数法)
    """
    if len(points) != 3:
        return 0
    
    if side_index == 0:  # 辺A: CA→AB
        # AB方向から180度逆向き
        return (current_angle + 180) % 360
    
    elif side_index == 1:  # 辺B: AB→BC
        # AB→BC向きの角度を計算
        start, end = get_side_points(points, side_index)
        vec_x = end.x() - start.x()
        vec_y = end.y() - start.y()
        angle_rad = math.atan2(vec_y, vec_x)
        # 180度回転（逆向き）
        return (math.degrees(angle_rad) + 180) % 360
    
    elif side_index == 2:  # 辺C: BC→CA
        # BC→CA向きの角度を計算
        start, end = get_side_points(points, side_index)
        vec_x = end.x() - start.x()
        vec_y = end.y() - start.y()
        angle_rad = math.atan2(vec_y, vec_x)
        # 180度回転（逆向き）
        return (math.degrees(angle_rad) + 180) % 360
    
    return 0 