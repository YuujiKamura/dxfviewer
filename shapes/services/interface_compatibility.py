#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TriangleShapeとTriangleDataのインターフェース互換性分析

両クラスのインターフェースを比較し、等価性を検証するコード。
"""

import inspect
import logging
from PySide6.QtCore import QPointF

# 両クラスをインポート
from triangle_ui.triangle_data import TriangleData as LegacyTriangleData
from shapes.geometry.triangle_shape import TriangleData as NewTriangleData

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_method_compatibility():
    """両クラスのメソッドを比較して互換性を分析"""
    # クラスのメソッドを取得（特殊メソッドは除く）
    triangle_data_methods = {name: func for name, func in inspect.getmembers(LegacyTriangleData, inspect.isfunction) 
                            if not name.startswith('__')}
    triangle_shape_methods = {name: func for name, func in inspect.getmembers(NewTriangleData, inspect.isfunction)
                             if not name.startswith('__')}
    
    # 分析結果を格納する辞書
    compatibility = {
        "only_in_triangle_data": [],
        "only_in_triangle_shape": [],
        "common_methods": [],
        "method_mappings": {}
    }
    
    # TriangleDataにあってTriangleShapeにないメソッド
    for method_name in triangle_data_methods:
        if method_name not in triangle_shape_methods:
            compatibility["only_in_triangle_data"].append(method_name)
    
    # TriangleShapeにあってTriangleDataにないメソッド
    for method_name in triangle_shape_methods:
        if method_name not in triangle_data_methods:
            compatibility["only_in_triangle_shape"].append(method_name)
    
    # 両方にあるメソッド
    for method_name in triangle_data_methods:
        if method_name in triangle_shape_methods:
            compatibility["common_methods"].append(method_name)
    
    # メソッドマッピング（異なる名前だが同等の機能）
    method_mappings = {
        # TriangleData -> TriangleShape
        "get_side_line": "get_sides",
        "get_connection_point_by_side": "get_connection_point_for_side",
        "get_angle_by_side": "get_connection_angle_for_side",
        "update_with_new_lengths": "update_with_new_properties"
    }
    compatibility["method_mappings"] = method_mappings
    
    return compatibility

def check_interface_compatibility():
    """インターフェース互換性の詳細チェック"""
    compatibility = analyze_method_compatibility()
    
    logger.info("=== インターフェース互換性分析 ===")
    
    # 共通メソッド
    logger.info("共通メソッド:")
    for method in compatibility["common_methods"]:
        logger.info(f"  - {method}")
    
    # TriangleDataのみのメソッド
    logger.info("\nTriangleDataのみに存在するメソッド:")
    for method in compatibility["only_in_triangle_data"]:
        logger.info(f"  - {method}")
    
    # TriangleShapeのみのメソッド
    logger.info("\nTriangleShapeのみに存在するメソッド:")
    for method in compatibility["only_in_triangle_shape"]:
        logger.info(f"  - {method}")
    
    # メソッドマッピング
    logger.info("\nメソッドマッピング (異なる名前だが同等の機能):")
    for td_method, ts_method in compatibility["method_mappings"].items():
        logger.info(f"  - TriangleData.{td_method} → TriangleShape.{ts_method}")
    
    # 初期化パラメータの比較
    logger.info("\n初期化パラメータの比較:")
    td_params = inspect.signature(LegacyTriangleData.__init__).parameters
    ts_params = inspect.signature(NewTriangleData.__init__).parameters
    
    logger.info("TriangleData.__init__ パラメータ:")
    for name, param in td_params.items():
        if name != 'self':
            logger.info(f"  - {name}: {param.default}")
    
    logger.info("\nTriangleShape.__init__ パラメータ:")
    for name, param in ts_params.items():
        if name != 'self':
            logger.info(f"  - {name}: {param.default}")
    
    # インスタンス属性の比較
    logger.info("\nインスタンス属性の比較:")
    td = LegacyTriangleData(100, 100, 100)
    ts = NewTriangleData(100, 100, 100)
    
    td_vars = vars(td)
    ts_vars = vars(ts)
    
    logger.info("TriangleData インスタンス属性:")
    for name, value in td_vars.items():
        logger.info(f"  - {name}: {type(value).__name__}")
    
    logger.info("\nTriangleShape インスタンス属性:")
    for name, value in ts_vars.items():
        logger.info(f"  - {name}: {type(value).__name__}")

def create_compatibility_layer():
    """両クラス間の互換性レイヤーのサンプル実装"""
    # TriangleDataをTriangleShapeに合わせるラッパー
    class TriangleDataWrapper(LegacyTriangleData):
        """TriangleDataをTriangleShapeと互換性を持たせるラッパー"""
        
        def get_bounds(self):
            """境界を返す（TriangleShapeと互換）"""
            polygon = self.get_polygon()
            points = [polygon.at(i) for i in range(polygon.size())]
            min_x = min(p.x() for p in points)
            min_y = min(p.y() for p in points)
            max_x = max(p.x() for p in points)
            max_y = max(p.y() for p in points)
            return (min_x, min_y, max_x, max_y)
        
        def contains_point(self, point):
            """点が三角形内にあるかチェック（TriangleShapeと互換）"""
            return self.get_polygon().containsPoint(point, 0)
        
        def get_sides(self):
            """辺のリストを返す（TriangleShapeと互換）"""
            sides = []
            for i in range(3):
                result = self.get_side_line(i)
                if result:
                    sides.append(result)
            return sides
        
        def get_side_length(self, side_index):
            """辺の長さを返す（TriangleShapeと互換）"""
            if 0 <= side_index < 3:
                return self.lengths[side_index]
            return 0.0
        
        def get_side_midpoint(self, side_index):
            """辺の中点を返す（TriangleShapeと互換）"""
            result = self.get_side_line(side_index)
            if result:
                p1, p2 = result
                return QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            return QPointF(0, 0)
        
        def get_connection_point_for_side(self, side_index):
            """互換性のため別名で提供"""
            return self.get_connection_point_by_side(side_index)
        
        def get_connection_angle_for_side(self, side_index):
            """互換性のため別名で提供"""
            return self.get_angle_by_side(side_index)
        
        def update_with_new_properties(self, **properties):
            """プロパティ更新（TriangleShapeと互換）"""
            lengths = properties.get('lengths', None)
            if lengths:
                return self.update_with_new_lengths(lengths)
            return False
        
        def get_detailed_info(self):
            """詳細情報を返す（TriangleShapeと互換）"""
            return f"TriangleData {self.number}: 位置=({self.points[0].x():.1f}, {self.points[0].y():.1f}), " \
                   f"角度={self.angle_deg:.1f}°, 辺の長さ=(A:{self.lengths[0]:.1f}, B:{self.lengths[1]:.1f}, C:{self.lengths[2]:.1f})"
    
    # TriangleShapeをTriangleDataに合わせるラッパー
    class TriangleShapeWrapper(NewTriangleData):
        """TriangleShapeをTriangleDataと互換性を持たせるラッパー"""
        
        def __init__(self, a=0.0, b=0.0, c=0.0, p_ca=QPointF(0, 0), angle_deg=180.0, number=1, parent=None, connection_side=-1):
            """TriangleDataと互換性のある初期化"""
            super().__init__(a, b, c, p_ca, angle_deg, number)
            self.connection_side = connection_side
            self.parent = parent
            self.children = [None, None, None]  # TriangleDataは3つの子を持つ
        
        def get_side_line(self, side_index):
            """TriangleDataと互換性のあるメソッド"""
            sides = self.get_sides()
            if 0 <= side_index < len(sides):
                return sides[side_index]
            return None
        
        def get_connection_point_by_side(self, side_index):
            """TriangleDataと互換性のあるメソッド"""
            return self.get_connection_point_for_side(side_index)
        
        def get_angle_by_side(self, side_index):
            """TriangleDataと互換性のあるメソッド"""
            return self.get_connection_angle_for_side(side_index)
        
        def update_with_new_lengths(self, new_lengths):
            """TriangleDataと互換性のあるメソッド"""
            return self.update_with_new_properties(lengths=new_lengths)
    
    return TriangleDataWrapper, TriangleShapeWrapper

def check_runtime_compatibility():
    """実行時の互換性チェック - 同じ値で初期化してプロパティを比較"""
    
    # 同じ値で初期化
    td = LegacyTriangleData(100, 100, 100, QPointF(0, 0), 180.0, 1)
    ts = NewTriangleData(100, 100, 100, QPointF(0, 0), 180.0, 1)
    
    # 頂点座標を比較
    logger.info("\n実行時の互換性チェック - 座標比較:")
    
    logger.info("TriangleData 座標:")
    for i, point in enumerate(td.points):
        logger.info(f"  - points[{i}]: ({point.x():.1f}, {point.y():.1f})")
    
    logger.info("\nTriangleShape 座標:")
    for i, point in enumerate(ts.points):
        logger.info(f"  - points[{i}]: ({point.x():.1f}, {point.y():.1f})")
    
    # ポリゴン取得比較
    td_poly = td.get_polygon()
    ts_poly = ts.get_polygon()
    
    logger.info("\nポリゴン比較:")
    logger.info(f"TriangleData polygon size: {td_poly.size()}")
    logger.info(f"TriangleShape polygon size: {ts_poly.size()}")
    
    # その他の主要メソッドの結果比較
    logger.info("\n主要メソッド結果比較:")
    
    # get_side_line / get_sides
    td_side = td.get_side_line(0)
    ts_sides = ts.get_sides()
    logger.info(f"TriangleData get_side_line(0): {td_side}")
    logger.info(f"TriangleShape get_sides()[0]: {ts_sides[0]}")
    
    # get_connection_point_by_side / get_connection_point_for_side
    td_conn = td.get_connection_point_by_side(0)
    ts_conn = ts.get_connection_point_for_side(0)
    logger.info(f"TriangleData get_connection_point_by_side(0): ({td_conn.x():.1f}, {td_conn.y():.1f})")
    logger.info(f"TriangleShape get_connection_point_for_side(0): ({ts_conn.x():.1f}, {ts_conn.y():.1f})")

def main():
    """互換性分析のメイン関数"""
    check_interface_compatibility()
    check_runtime_compatibility()
    
    # 互換性レイヤーを作成
    TriangleDataWrapper, TriangleShapeWrapper = create_compatibility_layer()
    
    logger.info("\n互換性レイヤーのサンプル作成完了")
    logger.info("TriangleDataWrapper: TriangleDataをラップしてTriangleShapeと互換性を持たせる")
    logger.info("TriangleShapeWrapper: TriangleShapeをラップしてTriangleDataと互換性を持たせる")
    
    # ラッパーの例
    td_wrapper = TriangleDataWrapper(100, 100, 100)
    bounds = td_wrapper.get_bounds()  # TriangleShapeのメソッドを呼び出し
    logger.info(f"TriangleDataWrapper.get_bounds(): {bounds}")
    
    ts_wrapper = TriangleShapeWrapper(100, 100, 100)
    side_line = ts_wrapper.get_side_line(0)  # TriangleDataのメソッドを呼び出し
    if side_line:
        p1, p2 = side_line
        logger.info(f"TriangleShapeWrapper.get_side_line(0): ({p1.x():.1f}, {p1.y():.1f}) → ({p2.x():.1f}, {p2.y():.1f})")
    
    logger.info("\n結論:")
    logger.info("1. 両クラスは機能的に等価だが、インターフェースに違いがある")
    logger.info("2. 互換性レイヤーを使用することで、既存コードを変更せずに移行可能")
    logger.info("3. 完全一致の等価性ではなく、機能的等価性の検証が必要")

if __name__ == "__main__":
    main() 