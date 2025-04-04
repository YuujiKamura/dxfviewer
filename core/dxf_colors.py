#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFカラー処理モジュール

AutoCADカラーインデックス(ACI)からRGBへの変換や、エンティティの色を取得する機能を提供します。
"""

import logging
from typing import Tuple, Any, Dict, Optional

# 型定義
RGBColor = Tuple[int, int, int]

# ロガーの設定
logger = logging.getLogger("dxf_viewer")

# 設定クラス（シングルトン）
class ColorSettings:
    """色設定を保持するシングルトンクラス"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ColorSettings, cls).__new__(cls)
            cls._instance.force_black_mode = False
        return cls._instance
    
    @property
    def is_force_black_mode(self) -> bool:
        """強制黒モードが有効かどうか"""
        return self.force_black_mode
    
    @is_force_black_mode.setter
    def is_force_black_mode(self, value: bool) -> None:
        """強制黒モードの設定"""
        self.force_black_mode = value

# シングルトンインスタンス
color_settings = ColorSettings()

# 「すべて黒」モードのフラグ（下位互換性のため）
FORCE_BLACK_MODE = False

# AutoCADカラーインデックス(ACI)からRGB値へのマッピング
# 基本的な色（インデックス1-9）のマッピング
ACI_COLOR_MAP: Dict[int, RGBColor] = {
    0: (0, 0, 0),        # 0: ByBlock (デフォルトは黒)
    1: (255, 0, 0),      # 赤
    2: (255, 255, 0),    # 黄
    3: (0, 255, 0),      # 緑
    4: (0, 255, 255),    # シアン
    5: (0, 0, 255),      # 青
    6: (255, 0, 255),    # マゼンタ
    7: (255, 255, 255),  # 白 (特殊処理: 背景色に応じて反転)
    8: (128, 128, 128),  # 灰色
    9: (192, 192, 192),  # 薄い灰色
    # 以下、代表的なACIカラーをいくつか追加
    # 完全な実装では256色すべてをマッピング
    10: (255, 0, 0),     # 赤 (明るい)
    20: (255, 128, 0),   # オレンジ
    30: (255, 255, 0),   # 黄 (明るい)
    40: (0, 255, 0),     # 緑 (明るい)
    50: (0, 255, 255),   # シアン (明るい)
    60: (0, 0, 255),     # 青 (明るい)
    70: (255, 0, 255),   # マゼンタ (明るい)
    90: (128, 0, 0),     # 暗い赤
    110: (128, 128, 0),  # 暗い黄
    130: (0, 128, 0),    # 暗い緑
    150: (0, 128, 128),  # 暗いシアン
    170: (0, 0, 128),    # 暗い青
    190: (128, 0, 128),  # 暗いマゼンタ
    210: (128, 128, 128) # 中間の灰色
}

# テーマに基づくカラーセット
THEME_COLORS = {
    "ライト": {
        "background": (255, 255, 255),  # 白
        "foreground": (0, 0, 0),        # 黒
        "grid": (220, 220, 220),        # 薄いグレー
        "highlight": (255, 0, 0)        # 赤
    },
    "ダーク": {
        "background": (53, 53, 53),     # 暗いグレー
        "foreground": (220, 220, 220),  # 明るいグレー
        "grid": (80, 80, 80),           # 中間のグレー
        "highlight": (255, 127, 0)      # オレンジ
    },
    "ブルー": {
        "background": (30, 30, 50),     # 暗い青
        "foreground": (200, 220, 255),  # 明るい青白
        "grid": (60, 70, 100),          # 青みがかったグレー
        "highlight": (255, 200, 0)      # 金色
    }
}

def get_theme_colors(theme_name: str = "ライト") -> Dict[str, RGBColor]:
    """
    テーマ名に基づいた色設定を取得
    
    Args:
        theme_name: テーマ名 ("ライト", "ダーク", "ブルー")
        
    Returns:
        Dict[str, RGBColor]: テーマカラーのマッピング
    """
    return THEME_COLORS.get(theme_name, THEME_COLORS["ライト"])

def set_force_black_mode(enabled: bool) -> None:
    """
    すべてのエンティティを黒で描画するモードを設定
    
    Args:
        enabled: モードを有効にする場合はTrue、無効にする場合はFalse
    """
    global FORCE_BLACK_MODE
    FORCE_BLACK_MODE = enabled
    # シングルトンにも設定
    color_settings.is_force_black_mode = enabled
    logger.info(f"強制黒モード: {'有効' if enabled else '無効'}")

def invert_color(color: RGBColor) -> RGBColor:
    """
    色を反転する純粋関数
    
    Args:
        color: 元のRGB色
        
    Returns:
        RGBColor: 反転したRGB色
    """
    return (255 - color[0], 255 - color[1], 255 - color[2])

def convert_dxf_color(color_index: int, background_color: RGBColor = (255, 255, 255)) -> RGBColor:
    """
    DXFカラーインデックスをRGBに変換する純粋関数
    カラーインデックス7は背景色に対して反転した色を返す特殊処理あり
    
    Args:
        color_index: DXFカラーインデックス
        background_color: 背景色のRGB値 (デフォルト: 白)
        
    Returns:
        RGBColor: 変換されたRGB値
    """
    # 強制黒モードが有効な場合は常に黒を返す
    if color_settings.is_force_black_mode:
        return (0, 0, 0)
        
    # デフォルト色（黒）
    default_color = (0, 0, 0)
    
    # ネガティブな値や範囲外の値を処理
    if color_index < 0 or color_index > 255:
        return default_color
    
    # カラーインデックス7の特殊処理 - 背景色に対して反転
    if color_index == 7:
        return invert_color(background_color)
    
    # 通常のカラーマッピング
    return ACI_COLOR_MAP.get(color_index, default_color)

def aci_to_rgb(color_index: int) -> RGBColor:
    """
    AutoCADカラーインデックス(ACI)からRGB値に変換
    
    Args:
        color_index: ACIカラーインデックス (0-255)
        
    Returns:
        RGBColor: RGB値のタプル (r, g, b)
    """
    # 白背景に対する変換（従来の互換性のため）
    return convert_dxf_color(color_index)

def get_entity_color(entity: Any) -> RGBColor:
    """
    DXFエンティティから色を取得
    
    エンティティ自体の色属性を確認し、なければレイヤーの色を使用。
    両方ない場合はデフォルト色（黒）を返す。
    
    Args:
        entity: DXFエンティティオブジェクト
        
    Returns:
        RGBColor: RGB値のタプル (r, g, b)
    """
    # 強制黒モードが有効な場合は常に黒を返す
    if color_settings.is_force_black_mode:
        return (0, 0, 0)
        
    # デフォルト色（黒）- 白背景に適切
    default_color = (0, 0, 0)
    
    try:
        # エンティティの色属性をチェック
        if hasattr(entity.dxf, 'color'):
            color_index = entity.dxf.color
            # 正の値ならそのインデックスの色を使用
            if color_index > 0:
                return convert_dxf_color(color_index)
            # 0 (ByBlock) または 256 (ByLayer) の場合はレイヤーの色を使用
            elif color_index == 0 or color_index == 256:
                # レイヤーの色を探す
                if hasattr(entity.dxf, 'layer') and hasattr(entity, 'doc'):
                    if entity.doc:
                        layer = entity.doc.layers.get(entity.dxf.layer)
                        if layer and hasattr(layer.dxf, 'color'):
                            layer_color = layer.dxf.color
                            if layer_color > 0:
                                return convert_dxf_color(layer_color)
        
        # レイヤーの色を直接探す
        if hasattr(entity.dxf, 'layer') and hasattr(entity, 'doc'):
            if entity.doc:
                layer = entity.doc.layers.get(entity.dxf.layer)
                if layer and hasattr(layer.dxf, 'color'):
                    layer_color = layer.dxf.color
                    if layer_color > 0:
                        return convert_dxf_color(layer_color)
        
        return default_color
        
    except Exception as e:
        logger.debug(f"色の取得中にエラー: {str(e)}")
        return default_color

def apply_color_theme(scene: Any, theme_name: str = "ライト") -> None:
    """
    グラフィックスシーンにテーマカラーを適用
    
    Args:
        scene: QGraphicsSceneオブジェクト
        theme_name: テーマ名
    """
    from PySide6.QtGui import QColor, QBrush, QPen
    
    # 強制黒モードが有効な場合はテーマ色を適用しない
    if color_settings.is_force_black_mode:
        return
    
    # テーマカラーの取得
    theme = get_theme_colors(theme_name)
    
    # 背景色の設定
    bg_color = QColor(*theme["background"])
    scene.setBackgroundBrush(QBrush(bg_color))
    
    # アイテムの色を設定
    fg_color = QColor(*theme["foreground"])
    for item in scene.items():
        # ペンを持つアイテム
        if hasattr(item, 'pen') and callable(item.pen):
            pen = item.pen()
            pen.setColor(fg_color)
            item.setPen(pen)
        
        # ブラシを持つアイテム
        if hasattr(item, 'brush') and callable(item.brush):
            brush = item.brush()
            brush.setColor(fg_color)
            item.setBrush(brush)
        
        # テキストアイテム
        if hasattr(item, 'setDefaultTextColor'):
            item.setDefaultTextColor(fg_color) 