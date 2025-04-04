#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFエンティティのデータクラス

DXFエンティティを表す中間表現のデータクラスを定義します。
これらのクラスはUI依存の情報を持たない純粋なデータ構造です。
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional

# 基本カラータイプ定義
RGBColor = Tuple[int, int, int]

@dataclass
class DxfEntity:
    """全DXFエンティティの基本クラス"""
    color: RGBColor = (255, 255, 255)  # 白をデフォルト色に
    width: float = 1.0  # デフォルト線幅

@dataclass
class DxfLine(DxfEntity):
    """線エンティティ"""
    start_x: float = 0.0
    start_y: float = 0.0
    end_x: float = 0.0
    end_y: float = 0.0

@dataclass
class DxfCircle(DxfEntity):
    """円エンティティ"""
    center_x: float = 0.0
    center_y: float = 0.0
    radius: float = 0.0

@dataclass
class DxfArc(DxfEntity):
    """円弧エンティティ"""
    center_x: float = 0.0
    center_y: float = 0.0
    radius: float = 0.0
    start_angle: float = 0.0
    end_angle: float = 360.0

@dataclass
class DxfPolyline(DxfEntity):
    """ポリラインエンティティ"""
    points: List[Tuple[float, float]] = None
    is_closed: bool = False
    
    def __post_init__(self):
        if self.points is None:
            self.points = []

@dataclass
class DxfText(DxfEntity):
    """テキストエンティティ"""
    text: str = ""
    pos_x: float = 0.0
    pos_y: float = 0.0
    height: float = 1.0
    h_align: int = 0  # 0=左, 2=右, 4=中央
    v_align: int = 0  # 0=ベース, 1=下, 2=中央, 3=上
    rotation: float = 0.0 