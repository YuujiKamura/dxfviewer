#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleData - 三角形データクラス

三角形の寸法、頂点座標、接続関係を管理するクラス
"""

import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPolygonF
import logging

# 幾何学計算モジュールをインポート
from .triangle_geometry import (
    is_valid_triangle,
    calculate_internal_angles,
    calculate_triangle_points,
    get_side_points,
    get_connection_point,
    get_connection_angle
)

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

# 元のTriangleExporterクラスの代わりに、triangle_exporters.pyからインポート
# 後方互換性のために、同じ名前で提供
from .triangle_exporters import DxfExporter as TriangleExporter

class TriangleData:
    """三角形のデータと計算ロジックを保持するクラス"""
    def __init__(self, a=0.0, b=0.0, c=0.0, p_ca=QPointF(0, 0), angle_deg=180.0, number=1, parent=None, connection_side=-1):
        self.number = number
        self.name = f"Tri_{number}"
        self.lengths = [float(a), float(b), float(c)]
        self.points = [QPointF(p_ca), QPointF(0, 0), QPointF(0, 0)]
        self.angle_deg = float(angle_deg)
        self.internal_angles_deg = [0.0, 0.0, 0.0]
        self.center_point = QPointF(0, 0)
        self.parent = parent
        self.connection_side = connection_side
        self.children = [None, None, None]
        self.color = QColor(0, 100, 200)
        
        if a > 0 and b > 0 and c > 0:
            if self.is_valid_lengths():
                self.calculate_points()
    
    def is_valid_lengths(self, a=None, b=None, c=None):
        """三角形の成立条件を確認"""
        a = a if a is not None else self.lengths[0]
        b = b if b is not None else self.lengths[1]
        c = c if c is not None else self.lengths[2]
        return is_valid_triangle(a, b, c)
    
    def calculate_points(self):
        """三角形の頂点座標を計算"""
        # 幾何学計算モジュールを使用して頂点を計算
        self.points, self.center_point = calculate_triangle_points(
            self.points[0],
            self.lengths[0],
            self.lengths[1],
            self.lengths[2],
            self.angle_deg
        )
        
        # 内角を計算
        self.internal_angles_deg = calculate_internal_angles(
            self.lengths[0],
            self.lengths[1],
            self.lengths[2]
        )
    
    def get_polygon(self) -> QPolygonF:
        """描画用のQPolygonFを返す"""
        return QPolygonF(self.points)
    
    def get_side_line(self, side_index: int) -> tuple:
        """指定された辺の両端点を返す (0:A, 1:B, 2:C)"""
        # 幾何学計算モジュールを使用
        result = get_side_points(self.points, side_index)
        if result:
            p1, p2 = result
            logger.debug(f"Triangle {self.number}: 辺{chr(65 + side_index)}({side_index})の両端点: {p1} → {p2}")
            return p1, p2
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return None
    
    def get_connection_point_by_side(self, side_index: int) -> QPointF:
        """指定された接続辺の次の三角形の基準点を返す"""
        # 幾何学計算モジュールを使用
        connection_point = get_connection_point(self.points, side_index)
        if connection_point:
            logger.debug(f"Triangle {self.number}: 辺{chr(65 + side_index)}({side_index})の接続点は{connection_point}")
            return connection_point
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
            return self.points[0]  # デフォルトは点CA
    
    def get_angle_by_side(self, side_index: int) -> float:
        """指定された辺に接続する次の三角形の回転角度を返す"""
        # 幾何学計算モジュールを使用
        return get_connection_angle(self.points, side_index, self.angle_deg)
    
    def set_child(self, child_triangle, side_index):
        """指定した辺に接続する子三角形を設定"""
        if 0 <= side_index < 3:
            self.children[side_index] = child_triangle
            child_triangle.parent = self
            child_triangle.connection_side = side_index
            logger.debug(f"Triangle {self.number}の辺{side_index}に子三角形{child_triangle.number}を接続しました")
        else:
            logger.warning(f"Triangle {self.number}: 無効な辺インデックス {side_index}")
    
    def update_with_new_lengths(self, new_lengths):
        """三角形の寸法を更新する"""
        if not self.is_valid_lengths(new_lengths[0], new_lengths[1], new_lengths[2]):
            logger.warning(f"Triangle {self.number}: 無効な辺の長さ {new_lengths}")
            return False
        
        # 寸法を更新
        self.lengths = new_lengths.copy()
        # 座標を再計算
        self.calculate_points()
        return True

    @staticmethod
    def get_detailed_edge_info(triangle, side_index):
        """三角形の辺の詳細情報を文字列として返す（純粋関数）"""
        if not triangle:
            return "選択なし"
        
        # 辺の表示名マッピング（インデックスから名前へ）
        edge_name_mapping = {
            0: "A",  # インデックス0 → 辺A (CA→AB)
            1: "B",  # インデックス1 → 辺B (AB→BC)
            2: "C"   # インデックス2 → 辺C (BC→CA)
        }
        edge_name = edge_name_mapping[side_index]
        
        # 辺の両端点を取得
        side_points = get_side_points(triangle.points, side_index)
        if not side_points:
            return "選択なし"
            
        p1, p2 = side_points
        edge_length = triangle.lengths[side_index]
        
        # 頂点名マッピング（辺のインデックスから頂点の名前ペアへ）
        edge_vertices_mapping = {
            0: ("CA", "AB"),  # 辺A
            1: ("AB", "BC"),  # 辺B
            2: ("BC", "CA")   # 辺C
        }
        start_vertex, end_vertex = edge_vertices_mapping[side_index]
        
        # 詳細情報を文字列として返す
        return (
            f"三角形 {triangle.number} の辺 {edge_name}: "
            f"{start_vertex}({p1.x():.1f}, {p1.y():.1f}) → "
            f"{end_vertex}({p2.x():.1f}, {p2.y():.1f}), "
            f"長さ: {edge_length:.1f}"
        )


class TriangleManager:
    """三角形の集合を管理するクラス"""
    
    def __init__(self):
        """三角形マネージャーの初期化"""
        self.triangle_list = []
        self.next_triangle_number = 1
    
    def get_triangle_by_number(self, number):
        """番号から三角形を取得"""
        return next((t for t in self.triangle_list if t.number == number), None)
    
    def add_triangle(self, triangle_data):
        """三角形をリストに追加し、次の番号を更新"""
        self.triangle_list.append(triangle_data)
        
        # 次の三角形番号を更新
        if triangle_data.number >= self.next_triangle_number:
            self.next_triangle_number = triangle_data.number + 1
    
    def update_triangle_counter(self):
        """三角形の番号カウンターを更新"""
        # 最大の三角形番号を見つけて次の番号を設定
        max_num = 0
        for tri in self.triangle_list:
            if tri.number > max_num:
                max_num = tri.number
        self.next_triangle_number = max_num + 1
        logger.debug(f"三角形カウンター更新: 次の番号 = {self.next_triangle_number}")
    
    def create_triangle_at_side(self, parent_number, side_index, lengths):
        """親三角形の指定された辺に新しい三角形を作成して追加"""
        if not self.triangle_list:
            logger.warning("三角形リストが空です")
            return None
        
        # 親三角形の取得
        parent_triangle = self.get_triangle_by_number(parent_number)
        if not parent_triangle:
            logger.warning(f"親三角形 {parent_number} が見つかりません")
            return None
        
        # 既に接続されているかチェック
        if parent_triangle.children[side_index] is not None:
            logger.warning(f"三角形 {parent_number} の辺 {side_index} には既に三角形が接続されています")
            return None
        
        # 三角形の成立条件をチェック
        if not is_valid_triangle(lengths[0], lengths[1], lengths[2]):
            logger.warning(f"指定された辺の長さ ({lengths[0]:.1f}, {lengths[1]:.1f}, {lengths[2]:.1f}) では三角形が成立しません")
            return None
        
        # 接続点（次の三角形の基準点）
        connection_point = parent_triangle.get_connection_point_by_side(side_index)
        
        # 接続角度
        connection_angle = parent_triangle.get_angle_by_side(side_index)
        
        # 新しい三角形を作成
        new_triangle = TriangleData(
            a=lengths[0], b=lengths[1], c=lengths[2],
            p_ca=connection_point,
            angle_deg=connection_angle,
            number=self.next_triangle_number
        )
        
        # 親子関係の設定
        parent_triangle.set_child(new_triangle, side_index)
        
        # 三角形リストに追加
        self.add_triangle(new_triangle)
        
        return new_triangle
    
    def update_triangle_and_propagate(self, triangle, new_lengths):
        """三角形の寸法を更新し、子三角形の座標も再計算する"""
        if not triangle:
            logger.warning("更新する三角形が指定されていません")
            return False
            
        # 更新前の子三角形の接続情報を保存
        children_info = []
        for i, child in enumerate(triangle.children):
            if child:
                children_info.append({
                    'index': i,
                    'child': child,
                    'old_point': QPointF(child.points[0]),
                    'old_angle': child.angle_deg
                })
        
        # 1. 三角形の寸法と座標を更新
        if not triangle.update_with_new_lengths(new_lengths):
            return False
        
        # 2. 子三角形の座標を更新
        for info in children_info:
            child = info['child']
            side_index = info['index']
            
            # 新しい接続点と角度
            new_p_ca = triangle.get_connection_point_by_side(side_index)
            new_angle = triangle.get_angle_by_side(side_index)
            
            # 子三角形の更新前情報をログ出力
            logger.debug(f"子三角形 {child.number} 更新前: 基準点=({info['old_point'].x():.1f}, {info['old_point'].y():.1f}), "
                       f"角度={info['old_angle']:.1f}")
            
            # 子三角形の基準点と角度を更新
            child.points[0] = new_p_ca
            child.angle_deg = new_angle
            
            # 子三角形の座標を再計算
            child.calculate_points()
            
            # 更新後情報をログ出力
            logger.debug(f"子三角形 {child.number} 更新後: 基準点=({child.points[0].x():.1f}, {child.points[0].y():.1f}), "
                       f"角度={child.angle_deg:.1f}")
            
            # 3. 孫三角形があれば再帰的に更新
            if any(child.children):
                self.update_child_triangles_recursive(child)
        
        return True
    
    def update_child_triangles_recursive(self, parent):
        """子三角形を再帰的に更新する"""
        for side_index, child in enumerate(parent.children):
            if not child:
                continue
                
            # 新しい接続点と角度
            new_p_ca = parent.get_connection_point_by_side(side_index)
            new_angle = parent.get_angle_by_side(side_index)
            
            # 接続点の更新前後をログ出力
            logger.debug(f"孫三角形 {child.number} 更新前: 基準点=({child.points[0].x():.1f}, {child.points[0].y():.1f})")
            
            # 子三角形の基準点と角度を更新
            child.points[0] = new_p_ca
            child.angle_deg = new_angle
            
            # 座標を再計算
            child.calculate_points()
            
            logger.debug(f"孫三角形 {child.number} 更新後: 基準点=({child.points[0].x():.1f}, {child.points[0].y():.1f})")
            
            # さらに子がいれば再帰的に更新
            if any(child.children):
                self.update_child_triangles_recursive(child) 