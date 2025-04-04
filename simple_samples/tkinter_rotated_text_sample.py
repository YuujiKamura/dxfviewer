#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TkinterとPILを使用してテキスト回転を実現するサンプル

DXFファイル内のTEXTエンティティを適切に回転させて表示します。
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import math
from PIL import Image, ImageDraw, ImageFont, ImageTk
import ezdxf
from enum import Enum, auto

# ロガーの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("rotated_text_sample")

# エンティティタイプの列挙型
class EntityType(Enum):
    LINE = auto()
    CIRCLE = auto()
    TEXT = auto()
    OTHER = auto()

# 色マッピングクラス
class ColorMapping:
    """DXFの色インデックスをRGB色に変換するクラス"""
    
    def __init__(self, bg_color="#FFFFFF"):
        self.bg_color = bg_color
        
        # 基本色マッピング（ACI色インデックス → RGB）
        self.color_map = {
            1: "#FF0000",  # 赤
            2: "#FFFF00",  # 黄
            3: "#00FF00",  # 緑
            4: "#00FFFF",  # シアン
            5: "#0000FF",  # 青
            6: "#FF00FF",  # マゼンタ
            7: "#000000",  # 黒 (白背景) または "#FFFFFF" (黒背景)
            8: "#808080",  # グレー
            9: "#C0C0C0",  # 明るいグレー
        }
        
        # 背景が白なら7番は黒、背景が黒なら7番は白
        if bg_color.upper() == "#FFFFFF":
            self.color_map[7] = "#000000"
        else:
            self.color_map[7] = "#FFFFFF"
    
    def get_color(self, color_index):
        """
        色インデックスからRGB色を取得
        
        Args:
            color_index: DXFの色インデックス
            
        Returns:
            str: RGB色（#RRGGBB形式）
        """
        if color_index is None:
            return self.color_map[7]  # デフォルトは7番
        
        if color_index in self.color_map:
            return self.color_map[color_index]
        
        # 上記以外の色インデックスの場合はデフォルト
        return self.color_map[7]

# DXFパーサークラス
class DxfParser:
    """DXFファイルを解析して単純なエンティティリストに変換するクラス"""
    
    def __init__(self):
        self.doc = None
    
    def parse(self, file_path):
        """
        DXFファイルを解析してエンティティのリストを返す
        
        Args:
            file_path: 解析するDXFファイルのパス
            
        Returns:
            list: エンティティオブジェクトのリスト
        """
        entities = []
        
        try:
            # DXFファイルを読み込み
            self.doc = ezdxf.readfile(file_path)
            
            # モデル空間を取得
            msp = self.doc.modelspace()
            
            # エンティティの処理
            for entity in msp:
                parsed_entity = self._parse_entity(entity)
                if parsed_entity is not None:
                    entities.append(parsed_entity)
            
            logger.info(f"{len(entities)}個のエンティティをパースしました")
            return entities
            
        except Exception as e:
            logger.error(f"DXFファイルのパース中にエラー: {str(e)}")
            raise
    
    def _parse_entity(self, entity):
        """
        DXFエンティティをパースして単純なオブジェクトに変換
        
        Args:
            entity: DXFエンティティ
            
        Returns:
            object: エンティティオブジェクト
        """
        dxftype = entity.dxftype()
        
        # 線分の処理
        if dxftype == "LINE":
            line = type('Line', (), {})
            line.type = EntityType.LINE
            line.start = (entity.dxf.start.x, entity.dxf.start.y)
            line.end = (entity.dxf.end.x, entity.dxf.end.y)
            line.color_index = entity.dxf.color
            return line
        
        # 円の処理
        elif dxftype == "CIRCLE":
            circle = type('Circle', (), {})
            circle.type = EntityType.CIRCLE
            circle.x = entity.dxf.center.x
            circle.y = entity.dxf.center.y
            circle.radius = entity.dxf.radius
            circle.color_index = entity.dxf.color
            return circle
        
        # テキストの処理
        elif dxftype == "TEXT" or dxftype == "MTEXT":
            text = type('Text', (), {})
            text.type = EntityType.TEXT
            
            if dxftype == "TEXT":
                text.x = entity.dxf.insert.x
                text.y = entity.dxf.insert.y
                text.text = entity.dxf.text
                text.height = entity.dxf.height
                text.rotation = entity.dxf.rotation
            else:  # MTEXT
                text.x = entity.dxf.insert.x
                text.y = entity.dxf.insert.y
                text.text = entity.text
                text.height = entity.dxf.char_height
                text.rotation = entity.dxf.rotation
            
            text.color_index = entity.dxf.color
            return text
        
        # その他のエンティティ
        return None

class DxfPanCanvas(tk.Canvas):
    """
    パン操作が可能なキャンバス
    """
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg='white')
        
        # 初期設定
        self.scale_factor = 1.0  # 表示スケール（名前変更）
        self.origin_x = 0       # 原点のX座標
        self.origin_y = 0       # 原点のY座標
        self.panning = False    # パン操作中フラグ
        self.pan_start_x = 0    # パン開始時のX座標
        self.pan_start_y = 0    # パン開始時のY座標
        
        # フォントキャッシュの初期化
        self.font_cache = {}
        
        # モデル座標系とビュー座標系の変換パラメータ
        self.min_model_coord = (-1000, -1000)  # モデル座標の最小値 (x, y)
        self.max_model_coord = (1000, 1000)    # モデル座標の最大値 (x, y)
        
        # パン操作の感度係数（ズームレベルに応じて自動調整）
        self.pan_sensitivity = 1.0
        
        # イベントバインド
        self.bind("<ButtonPress-1>", self.on_pan_start)
        self.bind("<B1-Motion>", self.on_pan_move)
        self.bind("<ButtonRelease-1>", self.on_pan_end)
        self.bind("<MouseWheel>", self.on_zoom)  # Windowsのマウスホイール
        self.bind("<Button-4>", self.on_zoom)    # Linuxのマウスホイール上
        self.bind("<Button-5>", self.on_zoom)    # Linuxのマウスホイール下
        
        # キャンバスサイズの変更を監視
        self.bind("<Configure>", self.on_resize)
        
        # 原点マーカーの描画
        self._create_origin_marker()
    
    def on_resize(self, event):
        """キャンバスのリサイズ時に呼ばれる"""
        # キャンバスの中心を原点にする（初期設定）
        if self.origin_x == 0 and self.origin_y == 0:
            self.origin_x = event.width / 2
            self.origin_y = event.height / 2
        
        # モデル表示範囲からズームレベルを計算
        self.calculate_initial_zoom(event.width, event.height)
        
        # パン感度を再計算
        self.calculate_pan_sensitivity()
    
    def calculate_initial_zoom(self, width, height):
        """モデルサイズに基づいて適切な初期ズームを計算"""
        if not hasattr(self, 'initial_zoom_calculated') or not self.initial_zoom_calculated:
            # モデル座標系の幅と高さ
            model_width = self.max_model_coord[0] - self.min_model_coord[0]
            model_height = self.max_model_coord[1] - self.min_model_coord[1]
            
            if model_width <= 0 or model_height <= 0:
                return  # モデルサイズが無効
            
            # キャンバスサイズとモデルサイズから適切なスケールを計算
            # （余白を10%程度確保）
            scale_x = (width * 0.9) / model_width
            scale_y = (height * 0.9) / model_height
            
            # 小さい方のスケールを採用（全体が表示されるように）
            new_scale = min(scale_x, scale_y)
            
            # スケールが極端に小さい/大きい場合は調整
            if new_scale < 0.01:
                new_scale = 0.01
            elif new_scale > 100:
                new_scale = 100
            
            # 初期スケールの設定
            if new_scale != self.scale_factor:
                old_scale = self.scale_factor
                self.scale_factor = new_scale
                
                # 原点位置の調整（スケール変更に合わせて）
                center_x = width / 2
                center_y = height / 2
                self.origin_x = center_x
                self.origin_y = center_y
                
                logger.info(f"初期ズーム設定: {self.scale_factor:.3f}倍")
            
            self.initial_zoom_calculated = True
    
    def calculate_pan_sensitivity(self):
        """
        パン操作の感度を計算
        ズームレベルに応じてパン感度を調整し、一貫した操作感を提供
        """
        # ズームレベルが小さいほど、パン感度は大きく
        # 基本的には逆比例の関係
        base_sensitivity = 2.0  # 基準感度（ズーム1.0xでの値）
        self.pan_sensitivity = base_sensitivity / max(0.1, self.scale_factor)
        
        # 感度の範囲制限
        self.pan_sensitivity = max(0.5, min(10.0, self.pan_sensitivity))
        logger.debug(f"パン感度: {self.pan_sensitivity:.2f} (ズーム: {self.scale_factor:.2f}x)")
        
        return self.pan_sensitivity
    
    def model_to_view(self, model_x, model_y):
        """モデル座標をビュー座標に変換"""
        view_x = self.origin_x + model_x * self.scale_factor
        view_y = self.origin_y - model_y * self.scale_factor  # Y軸は反転
        return view_x, view_y
    
    def view_to_model(self, view_x, view_y):
        """ビュー座標をモデル座標に変換"""
        model_x = (view_x - self.origin_x) / self.scale_factor
        model_y = (self.origin_y - view_y) / self.scale_factor  # Y軸は反転
        return model_x, model_y
    
    def on_pan_start(self, event):
        """パン操作開始時の処理"""
        self.panning = True
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # カーソルを手の形に変更
        self.config(cursor="fleur")  # 4方向の矢印カーソル
    
    def on_pan_move(self, event):
        """パン操作中の処理"""
        if not self.panning:
            return
        
        # ビュー座標系での移動量
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        # パン感度を適用（小さなズームレベルでも操作しやすくする）
        dx = dx * self.pan_sensitivity
        dy = dy * self.pan_sensitivity
        
        # 原点を移動
        self.origin_x += dx
        self.origin_y += dy
        
        # すべてのオブジェクトを移動
        self.move("all", dx, dy)
        
        # パン開始点を更新
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        # 現在のモデル座標（中心位置）をログ出力
        center_x, center_y = self.view_to_model(self.winfo_width()/2, self.winfo_height()/2)
        logger.debug(f"中心位置: ({center_x:.2f}, {center_y:.2f}), ズーム: {self.scale_factor:.2f}x")
    
    def on_pan_end(self, event):
        """パン操作終了時の処理"""
        self.panning = False
        
        # カーソルを元に戻す
        self.config(cursor="")
    
    def on_zoom(self, event):
        """ズーム操作の処理"""
        # ズーム前の中心位置を保存
        center_x, center_y = self.view_to_model(self.winfo_width()/2, self.winfo_height()/2)
        
        # マウスホイールの方向に応じたズーム係数
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            # ズームイン
            factor = 1.25
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            # ズームアウト
            factor = 0.8
        else:
            return
        
        # 新しいスケールが極端に小さい/大きい場合は制限
        new_scale = self.scale_factor * factor
        if new_scale < 0.01:
            factor = 0.01 / self.scale_factor
            new_scale = 0.01
        elif new_scale > 100:
            factor = 100 / self.scale_factor
            new_scale = 100
        
        # スケールが変わらない場合は何もしない
        if factor == 1.0:
            return
        
        # キャンバスの中心を基準にスケール変更
        self.origin_x = self.winfo_width() / 2 + (self.origin_x - self.winfo_width() / 2) * factor
        self.origin_y = self.winfo_height() / 2 + (self.origin_y - self.winfo_height() / 2) * factor
        
        # すべてのオブジェクトをスケーリング
        super().scale("all", self.origin_x, self.origin_y, factor, factor)
        
        # 内部スケール値を更新
        self.scale_factor = new_scale
        
        # パン感度を再計算
        self.calculate_pan_sensitivity()
        
        # ズーム後の中心位置をログ出力
        new_center_x, new_center_y = self.view_to_model(self.winfo_width()/2, self.winfo_height()/2)
        logger.debug(f"ズーム変更: {self.scale_factor:.2f}x, 中心位置: ({new_center_x:.2f}, {new_center_y:.2f})")
        
        # 原点マーカーのサイズを調整
        self._resize_origin_marker()
    
    def _resize_origin_marker(self):
        """原点マーカーのサイズをズームレベルに合わせて調整"""
        # 既存のマーカーを削除
        self.delete("origin_marker")
        
        # 新しいマーカーを作成
        self._create_origin_marker()
    
    def _create_origin_marker(self):
        """原点（0,0）を示すマーカーを描画"""
        # X軸（赤）
        self.create_line(
            self.origin_x - 100, self.origin_y, 
            self.origin_x + 100, self.origin_y,
            fill="red", width=1, tags=("origin_marker", "x_axis")
        )
        
        # Y軸（緑）
        self.create_line(
            self.origin_x, self.origin_y - 100, 
            self.origin_x, self.origin_y + 100,
            fill="green", width=1, tags=("origin_marker", "y_axis")
        )
        
        # 原点のマーカー（青い円）
        radius = 5
        self.create_oval(
            self.origin_x - radius, self.origin_y - radius,
            self.origin_x + radius, self.origin_y + radius,
            outline="blue", fill="#0000FF", width=1,
            tags=("origin_marker", "origin_point")
        )
        
        # 座標ラベル
        self.create_text(
            self.origin_x + 10, self.origin_y + 10,
            text="(0,0)", fill="blue",
            tags=("origin_marker", "origin_label")
        )
    
    def update_model_bounds(self, entities):
        """エンティティのリストから適切なモデル境界を計算"""
        if not entities:
            return
        
        # 初期値
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        for entity in entities:
            # エンティティタイプに応じて座標を取得
            coords = []
            if hasattr(entity, 'type'):
                if entity.type == EntityType.LINE:
                    coords = [entity.start[0], entity.start[1], entity.end[0], entity.end[1]]
                elif entity.type == EntityType.CIRCLE:
                    coords = [
                        entity.x - entity.radius, entity.y - entity.radius,
                        entity.x + entity.radius, entity.y + entity.radius
                    ]
                elif entity.type == EntityType.TEXT:
                    # テキストはポイント座標のみ
                    coords = [entity.x, entity.y]
            
            # 座標範囲の更新
            if coords:
                min_x = min(min_x, min(coords[0::2]))
                max_x = max(max_x, max(coords[0::2]))
                min_y = min(min_y, min(coords[1::2]))
                max_y = max(max_y, max(coords[1::2]))
        
        # 無効な値のチェック
        if min_x == float('inf') or min_y == float('inf') or max_x == float('-inf') or max_y == float('-inf'):
            return
        
        # 境界に余裕を持たせる（10%マージン）
        width = max_x - min_x
        height = max_y - min_y
        min_x -= width * 0.1
        max_x += width * 0.1
        min_y -= height * 0.1
        max_y += height * 0.1
        
        # 最小サイズの保証（点のみのモデルの場合）
        if width < 10:
            min_x -= 5
            max_x += 5
        if height < 10:
            min_y -= 5
            max_y += 5
        
        # モデル座標系の範囲を更新
        self.min_model_coord = (min_x, min_y)
        self.max_model_coord = (max_x, max_y)
        
        logger.info(f"モデル座標範囲: ({min_x:.2f}, {min_y:.2f}) - ({max_x:.2f}, {max_y:.2f})")
        
        # 初期ズームを再計算するためのフラグをリセット
        self.initial_zoom_calculated = False
    
    def draw_rotated_text(self, x, y, text, rotation=0, height=10, color="black", h_align=None, v_align=None):
        """
        PIL/Pillowを使用して回転テキストを描画
        
        Args:
            x, y: 描画位置（DXF座標）
            text: 描画するテキスト
            rotation: 回転角度（度）
            height: フォントサイズ
            color: テキスト色
            h_align: 水平方向の揃え位置（左揃え=0, 中央揃え=1, 右揃え=2）
            v_align: 垂直方向の揃え位置（下揃え=0, 中央揃え=1, 上揃え=2）
        """
        # DXF座標をキャンバス座標に変換
        canvas_x = self.origin_x + x * self.scale_factor
        canvas_y = self.origin_y - y * self.scale_factor  # Y軸は反転
        
        # フォントサイズをスケーリング
        font_size = int(height * self.scale_factor)
        if font_size < 8:  # 最小サイズ
            font_size = 8
        
        # 多言語文字コード対応：様々なエンコーディングを試す
        text_to_draw, encoding_used = self._try_encodings(text)
        logger.debug(f"テキスト '{text}' の処理に {encoding_used} を使用")
        
        # フォントの取得（キャッシュ利用）
        if font_size not in self.font_cache:
            try:
                # 日本語対応フォントを使用する（Windows環境用）
                font_path = None
                font_candidates = [
                    "Yu Gothic UI", "Yu Gothic", "MS Gothic", "Meiryo UI", "Meiryo", "MS Mincho",  # 日本語フォント
                    "Arial", "Tahoma", "Verdana"  # 英語フォント（フォールバック用）
                ]
                
                # 事前に使えるフォントを確認
                available_fonts = []
                for candidate in font_candidates:
                    try:
                        # フォントのパスを特定
                        if os.name == 'nt':  # Windows環境
                            # Windowsフォントディレクトリから検索
                            windows_font_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
                            possible_files = [
                                f"{candidate}.ttf",
                                f"{candidate}.ttc",
                                f"{candidate}Regular.ttf",
                                f"{candidate}-Regular.ttf",
                                f"{candidate}Bold.ttf",
                                f"{candidate}-Bold.ttf",
                            ]
                            for font_file in possible_files:
                                full_path = os.path.join(windows_font_dir, font_file)
                                if os.path.exists(full_path):
                                    font_path = full_path
                                    available_fonts.append((candidate, full_path))
                                    logger.debug(f"フォントファイル '{full_path}' が見つかりました")
                                    break
                    except Exception as e:
                        logger.debug(f"フォント '{candidate}' の検索中にエラー: {e}")
                
                # 利用可能なフォント一覧をログに出力
                if available_fonts:
                    logger.info(f"利用可能な日本語フォント: {[name for name, _ in available_fonts]}")
                else:
                    logger.warning("利用可能な日本語フォントが見つかりませんでした")
                
                # 直接パスを指定してフォントをロード
                for font_name, path in available_fonts:
                    try:
                        self.font_cache[font_size] = ImageFont.truetype(path, font_size)
                        logger.info(f"フォント '{font_name}' をパス '{path}' から読み込みました")
                        break
                    except Exception as e:
                        logger.debug(f"フォント '{font_name}' のロード中にエラー: {e}")
                
                # 名前でのフォント指定も試してみる
                if font_size not in self.font_cache:
                    for font_name in font_candidates:
                        try:
                            self.font_cache[font_size] = ImageFont.truetype(font_name, font_size)
                            logger.info(f"フォント '{font_name}' を名前で読み込みました")
                            break
                        except Exception:
                            continue
                
                # フォントが見つからなかった場合はデフォルトを使用
                if font_size not in self.font_cache:
                    # 最終手段: デフォルトモノスペースフォントを使用
                    try:
                        from PIL import features
                        if features.check('raqm'):  # Pillowでraqmサポートがあるか確認
                            logger.info("Pillowのraqmサポートが有効です（多言語テキストレイアウト）")
                        
                        # Pillowのデフォルトフォントを使用
                        self.font_cache[font_size] = ImageFont.load_default()
                        logger.warning("日本語対応フォントが見つからないため、デフォルトフォントを使用します")
                    except Exception as e:
                        logger.error(f"デフォルトフォントのロード中にエラー: {e}")
                        # 最低限のフォールバック
                        self.font_cache[font_size] = ImageFont.load_default()
            except Exception as e:
                # フォールバック
                logger.warning(f"フォント読み込みエラー: {e}")
                self.font_cache[font_size] = ImageFont.load_default()
        
        font = self.font_cache[font_size]
        
        # テキストサイズの計算
        text_width, text_height = font.getsize(text_to_draw) if hasattr(font, 'getsize') else font.getbbox(text_to_draw)[2:]
        
        # 余白を追加
        pad = 5
        img_width = text_width + 2 * pad
        img_height = text_height + 2 * pad
        
        # 透明な背景の画像を作成
        img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # アンカーポイントに基づいてテキスト位置を調整（デフォルトは左下）
        h_align = 0 if h_align is None else h_align  # デフォルトは左揃え
        v_align = 0 if v_align is None else v_align  # デフォルトは下揃え
        
        # 水平方向の位置調整
        if h_align == 1:  # 中央揃え
            x_pos = pad + (img_width - 2 * pad - text_width) / 2
        elif h_align == 2:  # 右揃え
            x_pos = img_width - pad - text_width
        else:  # 左揃え
            x_pos = pad
        
        # 垂直方向の位置調整（改善版）
        # フォントによって異なるベースラインオフセットを考慮
        baseline_offset = text_height * 0.2  # およそのベースラインオフセット（フォントによる）
        
        if v_align == 1:  # 中央揃え
            # より正確な垂直中央揃え
            y_pos = (img_height - text_height) / 2
        elif v_align == 2:  # 上揃え
            # 上端に合わせる（パディングのみ）
            y_pos = pad
        else:  # 下揃え
            # ベースラインを考慮して下端に合わせる
            y_pos = img_height - pad - text_height
        
        # テキストを描画
        draw.text((x_pos, y_pos), text_to_draw, font=font, fill=color)
        
        # 画像を回転
        rotated = img.rotate(rotation, expand=True, resample=Image.BICUBIC)
        
        # PhotoImageに変換
        photo = ImageTk.PhotoImage(rotated)
        
        # アンカーポイントに基づいて配置位置を調整
        anchor_offset_x = 0
        anchor_offset_y = 0
        
        # 回転後の画像の中心点
        img_center_x = rotated.width / 2
        img_center_y = rotated.height / 2
        
        # 回転によるオフセットを考慮しつつ、アンカーポイントに対応
        if h_align == 0:  # 左揃え
            anchor_offset_x = img_center_x
        elif h_align == 2:  # 右揃え
            anchor_offset_x = -img_center_x
        
        if v_align == 0:  # 下揃え
            anchor_offset_y = -img_center_y
        elif v_align == 2:  # 上揃え
            anchor_offset_y = img_center_y
            
        # 垂直方向の微調整（上下揃えの位置をより正確に）
        if v_align == 2:  # 上揃え
            # 少し下方向に調整（テキストの上端を基準点に近づける）
            anchor_offset_y += text_height * 0.1  # 下方向に調整
        elif v_align == 1:  # 中央揃え
            # 中央揃えも若干調整
            anchor_offset_y -= text_height * 0.1  # 上方向に調整
        
        # キャンバスに配置
        item_id = self.create_image(
            canvas_x + anchor_offset_x, 
            canvas_y + anchor_offset_y,
            image=photo, 
            anchor=tk.CENTER, 
            tags=("entity", "text")
        )
        
        # 参照を保持（ガベージコレクション対策）
        setattr(self, f"_photo_{item_id}", photo)
        
        return item_id
    
    def _try_encodings(self, text):
        """
        様々なエンコーディングでテキストの処理を試みる
        
        Args:
            text: 処理するテキスト
            
        Returns:
            tuple: (処理後のテキスト, 使用したエンコーディング)
        """
        if not isinstance(text, str):
            return text, "raw"
        
        # 文字化けしていないかチェックする文字
        mojibake_chars = {'', '?', '\ufffd'}
        
        # 試すエンコーディング一覧
        encodings = [
            'utf-8',
            'shift_jis', 'cp932',  # 日本語Windows
            'euc_jp',              # 日本語UNIX
            'iso2022_jp',          # JIS
            'latin1'               # 西欧
        ]
        
        best_text = text
        best_encoding = 'utf-8'  # デフォルト
        best_score = self._count_mojibake(text, mojibake_chars)
        
        # 各エンコーディングを試す
        for encoding in encodings:
            try:
                # 一度バイト列に変換してから戻す
                encoded = text.encode(encoding, errors='ignore')
                decoded = encoded.decode(encoding, errors='ignore')
                
                # 文字化けしている文字の数をカウント
                score = self._count_mojibake(decoded, mojibake_chars)
                
                # より良い結果なら更新
                if score < best_score or (score == best_score and len(decoded) > len(best_text)):
                    best_text = decoded
                    best_encoding = encoding
                    best_score = score
                    
                    # 完全に文字化けがなければ終了
                    if score == 0:
                        break
                        
            except Exception:
                continue
        
        return best_text, best_encoding
    
    def _count_mojibake(self, text, mojibake_chars):
        """文字化けしている文字の数をカウント"""
        count = 0
        for char in text:
            if char in mojibake_chars:
                count += 1
        return count
    
    def clear_entities(self):
        """エンティティをクリア"""
        self.delete("entity")
        self._create_origin_marker()

class MainApp:
    """メインアプリケーションクラス"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DXF回転テキストサンプル")
        
        # ウィンドウサイズ設定
        self.root.geometry("1000x700")
        
        # メインフレーム
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # コントロールフレーム（上部）
        self.control_frame = tk.Frame(self.main_frame, height=40)
        self.control_frame.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        # キャンバス（中央）
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # DXFパンキャンバスの作成
        self.canvas = DxfPanCanvas(self.canvas_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # ステータスバー（下部）
        self.status_frame = tk.Frame(self.main_frame, height=20)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.status_label = tk.Label(self.status_frame, text="準備完了", anchor=tk.W)
        self.status_label.pack(fill=tk.X)
        
        # コントロールボタンの追加
        self.test_btn = tk.Button(self.control_frame, text="テストパターン描画", command=self.draw_test_pattern)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(self.control_frame, text="クリア", command=self.clear_canvas)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.center_btn = tk.Button(self.control_frame, text="中央表示", command=self.center_view)
        self.center_btn.pack(side=tk.LEFT, padx=5)
        
        # DXFパーサー
        self.parser = DxfParser()
        self.color_mapping = ColorMapping()
        
        # 初期テストパターンの描画
        self.root.after(500, self.draw_test_pattern)
    
    def clear_canvas(self):
        """キャンバスをクリア"""
        self.canvas.clear_entities()
        self.status_label.config(text="クリアしました")
    
    def center_view(self):
        """ビューを中央に表示"""
        # キャンバスのサイズを取得
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # 原点をキャンバスの中央に設定
        self.canvas.origin_x = width / 2
        self.canvas.origin_y = height / 2
        
        # すべてを再描画
        self.canvas.delete("all")
        self._create_origin_marker()
        
        # テストパターンを再描画
        self.draw_test_pattern()
        
        self.status_label.config(text="ビューを中央に移動しました")
    
    def draw_test_pattern(self):
        """テストパターンを描画"""
        # キャンバスをクリア
        self.canvas.clear_entities()
        
        # テストのためのダミーエンティティリストを作成
        entities = []
        
        # 原点に十字とマーカー
        x_line = type('Line', (), {
            'type': EntityType.LINE,
            'start': (-100, 0),
            'end': (100, 0),
            'color_index': 1  # 赤
        })
        entities.append(x_line)
        
        y_line = type('Line', (), {
            'type': EntityType.LINE,
            'start': (0, -100),
            'end': (0, 100),
            'color_index': 3  # 緑
        })
        entities.append(y_line)
        
        origin_circle = type('Circle', (), {
            'type': EntityType.CIRCLE,
            'x': 0,
            'y': 0,
            'radius': 10,
            'color_index': 5  # 青
        })
        entities.append(origin_circle)
        
        # 原点テキスト
        origin_text = type('Text', (), {
            'type': EntityType.TEXT,
            'x': 0,
            'y': 0,
            'text': '(0,0)',
            'height': 10,
            'rotation': 0,
            'color_index': 7
        })
        entities.append(origin_text)
        
        # 回転テキストのテストパターン
        rotations = [0, 45, 90, 135, 180, 225, 270, 315]
        for i, rotation in enumerate(rotations):
            radius = 200
            angle = math.radians(i * 45)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            # 日本語混在テキスト
            text_content = f"{rotation}° 回転テキスト ABC123"
            if i % 2 == 0:
                text_content = f"英語 {rotation}° English"
            
            # テスト用にいくつかのテキストには特殊文字や長い文字列を設定
            if i == 2:
                text_content = "←→↑↓★☆○●◎◆◇□■※＊☆★アイウエオ"
            elif i == 6:
                text_content = "長い文字列テスト ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789 あいうえお"
            
            text_entity = type('Text', (), {
                'type': EntityType.TEXT,
                'x': x,
                'y': y,
                'text': text_content,
                'height': 15,
                'rotation': rotation,
                'color_index': i + 1
            })
            entities.append(text_entity)
            
            # テキスト位置マーカー
            marker = type('Circle', (), {
                'type': EntityType.CIRCLE,
                'x': x,
                'y': y,
                'radius': 3,
                'color_index': i + 1
            })
            entities.append(marker)
        
        # 追加のテスト: 水平・垂直方向の配置テスト
        alignments = [
            # h_align, v_align, 説明
            (0, 0, "左下揃え"),
            (1, 0, "中央下揃え"),
            (2, 0, "右下揃え"),
            (0, 1, "左中央揃え"),
            (1, 1, "中央揃え"),
            (2, 1, "右中央揃え"),
            (0, 2, "左上揃え"),
            (1, 2, "中央上揃え"),
            (2, 2, "右上揃え"),
        ]
        
        for i, (h_align, v_align, desc) in enumerate(alignments):
            # 格子状に配置
            x = -300 + (i % 3) * 150
            y = 300 - (i // 3) * 150
            
            # アンカーテキスト
            text_entity = type('Text', (), {
                'type': EntityType.TEXT,
                'x': x,
                'y': y,
                'text': desc,
                'height': 12,
                'rotation': 0,
                'color_index': 7,
                'h_align': h_align,
                'v_align': v_align
            })
            entities.append(text_entity)
            
            # マーカー
            marker = type('Circle', (), {
                'type': EntityType.CIRCLE,
                'x': x,
                'y': y,
                'radius': 5,
                'color_index': 1
            })
            entities.append(marker)
        
        # モデル境界の計算とキャンバスの初期設定
        self.canvas.update_model_bounds(entities)
        
        # 各エンティティの描画
        for entity in entities:
            self._draw_entity(entity)
        
        # ビューを中央に
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.canvas.calculate_initial_zoom(width, height)
        
        self.status_label.config(text=f"テストパターンを描画しました")
    
    def _draw_entity(self, entity):
        """エンティティを描画"""
        if entity.type == EntityType.LINE:
            # 線の描画
            x1, y1 = self.canvas.model_to_view(entity.start[0], entity.start[1])
            x2, y2 = self.canvas.model_to_view(entity.end[0], entity.end[1])
            color = self.color_mapping.get_color(entity.color_index)
            line_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=1, tags=("entity", "line"))
            
        elif entity.type == EntityType.CIRCLE:
            # 円の描画
            x, y = self.canvas.model_to_view(entity.x, entity.y)
            radius = entity.radius * self.canvas.scale_factor
            color = self.color_mapping.get_color(entity.color_index)
            circle_id = self.canvas.create_oval(
                x - radius, y - radius, 
                x + radius, y + radius,
                outline=color, width=1, tags=("entity", "circle")
            )
            
        elif entity.type == EntityType.TEXT:
            # テキストの描画
            color = self.color_mapping.get_color(entity.color_index)
            
            # アンカーポイント設定（デフォルトは左下）
            h_align = getattr(entity, 'h_align', 0)
            v_align = getattr(entity, 'v_align', 0)
            
            # ログ出力
            logger.debug(f"テキスト描画: '{entity.text}' @ ({entity.x}, {entity.y}) 回転={entity.rotation}° サイズ={entity.height} 色={color} h_align={h_align} v_align={v_align}")
            
            text_id = self.canvas.draw_rotated_text(
                entity.x, entity.y, 
                entity.text, 
                rotation=entity.rotation, 
                height=entity.height,
                color=color,
                h_align=h_align,
                v_align=v_align
            )

# メイン実行部
if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop() 