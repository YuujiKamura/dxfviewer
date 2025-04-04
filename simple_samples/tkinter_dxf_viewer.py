#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TkinterベースのDXFビューワー

シンプルな構造で効率的なパン操作を実現
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import logging
import os
import sys
import ezdxf
import math

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("tkinter_dxf_viewer")

class DxfPanCanvas(tk.Canvas):
    """DXF表示用パン操作可能なキャンバス"""
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # パン操作の状態変数
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        
        # DXFデータ
        self.dxf_doc = None
        self.entities = []
        
        # スケールと表示位置
        self.scale_factor = 1.0
        
        # キャンバスの背景色を設定
        self.configure(bg='#f0f0f0')
        
        # デフォルトの原点マーカーを描画
        self._create_origin_marker()
        
        # イベントバインド
        self.bind("<ButtonPress-1>", self._on_mouse_press)
        self.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.bind("<B1-Motion>", self._on_mouse_move)
        self.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows用ホイールイベント
        self.bind("<Button-4>", self._on_mouse_wheel)    # Linuxホイール上
        self.bind("<Button-5>", self._on_mouse_wheel)    # Linuxホイール下
        
        # 最初の更新を呼び出し
        self.after(100, self._update_canvas_size)
    
    def _update_canvas_size(self):
        """キャンバスサイズが決まった後に呼び出され、原点マーカーを中央に配置"""
        self.delete("origin_marker")
        self._create_origin_marker()
    
    def _create_origin_marker(self):
        """原点マーカーを描画"""
        # キャンバスの中心座標を計算
        canvas_width = self.winfo_width() or self.winfo_reqwidth()
        canvas_height = self.winfo_height() or self.winfo_reqheight()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # グリッドの描画（薄いグレー）
        grid_tag = "origin_marker"
        grid_size = 50  # グリッドのサイズ
        grid_count = 20  # グリッドの個数
        
        for i in range(-grid_count, grid_count + 1):
            # 水平線
            self.create_line(
                center_x - grid_size * grid_count, 
                center_y + i * grid_size, 
                center_x + grid_size * grid_count, 
                center_y + i * grid_size, 
                fill='#dcdcdc', 
                tags=grid_tag
            )
            # 垂直線
            self.create_line(
                center_x + i * grid_size, 
                center_y - grid_size * grid_count, 
                center_x + i * grid_size, 
                center_y + grid_size * grid_count, 
                fill='#dcdcdc', 
                tags=grid_tag
            )
        
        # X軸（赤）
        self.create_line(
            center_x - 100, center_y, center_x + 100, center_y, 
            fill='red', width=1, tags=grid_tag
        )
        
        # Y軸（緑）
        self.create_line(
            center_x, center_y - 100, center_x, center_y + 100, 
            fill='green', width=1, tags=grid_tag
        )
        
        # 原点円（青）
        self.create_oval(
            center_x - 5, center_y - 5, center_x + 5, center_y + 5, 
            outline='blue', fill='#7878ff', tags=grid_tag
        )
        
        # 原点座標テキスト
        self.create_text(
            center_x + 10, center_y + 10, 
            text="(0,0)", anchor=tk.NW, tags=grid_tag
        )
    
    def _on_mouse_press(self, event):
        """マウスボタン押下イベント"""
        self._is_panning = True
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self.config(cursor="fleur")  # 手のひらカーソル
    
    def _on_mouse_release(self, event):
        """マウスボタン解放イベント"""
        self._is_panning = False
        self.config(cursor="")  # 通常カーソルに戻す
    
    def _on_mouse_move(self, event):
        """マウス移動イベント"""
        if self._is_panning:
            # マウスの移動量を計算
            dx = event.x - self._pan_start_x
            dy = event.y - self._pan_start_y
            
            # すべてのオブジェクトを移動
            self.move(tk.ALL, dx, dy)
            
            # 新しい位置を記録
            self._pan_start_x = event.x
            self._pan_start_y = event.y
    
    def _on_mouse_wheel(self, event):
        """マウスホイールイベント（ズーム）"""
        # スケール倍率
        scale_delta = 0.1
        
        # イベントによって方向が異なるため調整
        if event.num == 5 or event.delta < 0:  # 下方向スクロール（縮小）
            scale = 1.0 - scale_delta
        else:  # 上方向スクロール（拡大）
            scale = 1.0 + scale_delta
        
        # マウス位置を中心にスケール
        mouse_x = event.x
        mouse_y = event.y
        
        # スケールを適用
        self.scale("all", mouse_x, mouse_y, scale, scale)
        
        # スケール係数を更新
        self.scale_factor *= scale

    def open_dxf_file(self, file_path):
        """
        DXFファイルを開いて表示する
        
        Args:
            file_path: 開くDXFファイルのパス
        """
        try:
            # 既存のDXFエンティティを削除
            self.delete("dxf_entity")
            
            # DXFファイルを読み込み
            logger.info(f"DXFファイルを開きます: {file_path}")
            self.dxf_doc = ezdxf.readfile(file_path)
            
            # モデル空間を取得
            msp = self.dxf_doc.modelspace()
            
            # キャンバスの中心座標を計算
            canvas_width = self.winfo_width() or self.winfo_reqwidth()
            canvas_height = self.winfo_height() or self.winfo_reqheight()
            center_x = canvas_width / 2
            center_y = canvas_height / 2
            
            # DXFエンティティを描画
            for entity in msp:
                self._draw_entity(entity, center_x, center_y)
            
            logger.info(f"DXFファイルの表示が完了しました")
            
            # 表示を中央に調整
            self.center_view()
            
            return True
            
        except Exception as e:
            logger.error(f"DXFファイルの読み込み中にエラーが発生: {str(e)}")
            messagebox.showerror("エラー", f"DXFファイルの読み込みに失敗しました:\n{str(e)}")
            return False
    
    def _draw_entity(self, entity, center_x, center_y):
        """
        DXFエンティティを描画する
        
        Args:
            entity: DXFエンティティ
            center_x: キャンバスの中心X座標
            center_y: キャンバスの中心Y座標
        """
        entity_type = entity.dxftype()
        
        # 色の設定（DXFの色はインデックスベース）
        color = "#000000"  # デフォルト白
        try:
            # エンティティのカラーインデックスを取得
            color_idx = entity.dxf.color
            logger.info(f"エンティティタイプ: {entity_type}, カラーインデックス: {color_idx}")
            
            # 基本的なカラーマッピング
            color_map = {
                1: "#FF0000",  # 赤
                2: "#FFFF00",  # 黄
                3: "#00FF00",  # 緑
                4: "#00FFFF",  # シアン
                5: "#0000FF",  # 青
                6: "#FF00FF",  # マゼンタ
                # インデックス7の特殊処理（背景色のブルー成分で判断）
                # 現在の背景色は '#f0f0f0'なのでブルー成分は0xf0=240>127なので黒になる
                7: "#000000",  # 黒（明るい背景用）
                8: "#808080",  # 灰色
                9: "#C0C0C0",  # 薄い灰色
            }
            
            if color_idx in color_map:
                color = color_map[color_idx]
                logger.info(f"マッピング前の色: {color}")
                
                # カラーインデックス7の特殊処理
                if color_idx == 7:
                    # 背景色を取得
                    bg_color = self.cget('bg')
                    logger.info(f"背景色: {bg_color}")
                    
                    # 16進数文字列からRGB値を取得
                    if bg_color.startswith('#'):
                        r = int(bg_color[1:3], 16) if len(bg_color) >= 3 else 0
                        g = int(bg_color[3:5], 16) if len(bg_color) >= 5 else 0
                        b = int(bg_color[5:7], 16) if len(bg_color) >= 7 else 0
                        logger.info(f"背景色RGB: r={r}, g={g}, b={b}")
                    else:
                        # 名前付き色の場合はデフォルト値を使用
                        b = 240  # デフォルトの背景色 #f0f0f0 のブルー成分
                        logger.info(f"名前付き背景色、デフォルトb値: {b}")
                    
                    # 背景色のブルー成分に基づいて色を設定
                    if b >= 127:
                        color = "#000000"  # 黒
                        logger.info("背景色のブルー成分が127以上なので黒を使用")
                    else:
                        color = "#FFFFFF"  # 白
                        logger.info("背景色のブルー成分が127未満なので白を使用")
            
            logger.info(f"最終決定色: {color}")
        except Exception as e:
            logger.error(f"色の設定中にエラー: {str(e)}")
            pass  # 色情報がない場合はデフォルト
        
        # エンティティのタイプに応じて描画
        if entity_type == "LINE":
            # 線分
            start = entity.dxf.start
            end = entity.dxf.end
            
            # DXF座標をキャンバス座標に変換（Y軸反転、中心オフセット）
            x1 = center_x + start.x
            y1 = center_y - start.y  # Y軸は反転
            x2 = center_x + end.x
            y2 = center_y - end.y    # Y軸は反転
            
            self.create_line(x1, y1, x2, y2, fill=color, tags="dxf_entity")
            
        elif entity_type == "CIRCLE":
            # 円
            center = entity.dxf.center
            radius = entity.dxf.radius
            
            # DXF座標をキャンバス座標に変換
            x = center_x + center.x
            y = center_y - center.y  # Y軸は反転
            
            # 円の左上と右下の座標
            x1 = x - radius
            y1 = y - radius
            x2 = x + radius
            y2 = y + radius
            
            self.create_oval(x1, y1, x2, y2, outline=color, tags="dxf_entity")
            
        elif entity_type == "ARC":
            # 円弧
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            
            # DXF座標をキャンバス座標に変換
            x = center_x + center.x
            y = center_y - center.y  # Y軸は反転
            
            # 円の座標
            x1 = x - radius
            y1 = y - radius
            x2 = x + radius
            y2 = y + radius
            
            # 角度を調整（DXFは反時計回り、Tkinterは反時計回りだが、Y軸反転の影響で調整）
            # Tkinterの角度は度数法で、0度は東（右）から
            start_angle = 90 - start_angle  # Y軸反転による調整
            end_angle = 90 - end_angle      # Y軸反転による調整
            
            # 終了角度が開始角度より小さい場合、360度を加える
            if end_angle < start_angle:
                end_angle += 360
            
            # 円弧を描画
            self.create_arc(
                x1, y1, x2, y2,
                start=start_angle, 
                extent=start_angle - end_angle,
                style=tk.ARC,
                outline=color,
                tags="dxf_entity"
            )
            
        elif entity_type == "POLYLINE" or entity_type == "LWPOLYLINE":
            # ポリライン（複数の連続した線分）
            points = []
            
            if entity_type == "LWPOLYLINE":
                # 軽量ポリラインはpoints属性から直接座標を取得
                for point in entity.get_points():
                    x, y = point[0:2]  # 最初の2つの値はX,Y座標
                    # DXF座標をキャンバス座標に変換
                    canvas_x = center_x + x
                    canvas_y = center_y - y  # Y軸は反転
                    points.append(canvas_x)
                    points.append(canvas_y)
            else:
                # 通常のポリラインは頂点を順に取得
                for vertex in entity.vertices:
                    x = vertex.dxf.location.x
                    y = vertex.dxf.location.y
                    # DXF座標をキャンバス座標に変換
                    canvas_x = center_x + x
                    canvas_y = center_y - y  # Y軸は反転
                    points.append(canvas_x)
                    points.append(canvas_y)
            
            # 閉じたポリラインかどうか
            try:
                is_closed = entity.dxf.flags & 1
                logger.info(f"ポリライン - 頂点数: {len(points)//2}, 閉じている: {is_closed}, 色: {color}")
            except Exception as e:
                is_closed = False
                logger.error(f"ポリラインの閉じフラグ取得エラー: {str(e)}")
            
            if len(points) >= 4:
                # ポリラインを線として描画
                line_id = self.create_line(points, fill=color, tags="dxf_entity")
                logger.info(f"ポリライン描画 - ID: {line_id}, 色: {color}")
                
                # 閉じたポリラインなら閉じる線も追加
                if is_closed:
                    # 最初と最後の点を結ぶ線を追加
                    closing_points = [points[-2], points[-1], points[0], points[1]]
                    close_line_id = self.create_line(closing_points, fill=color, tags="dxf_entity")
                    logger.info(f"閉じポリライン追加線 - ID: {close_line_id}, 色: {color}")
            else:
                logger.warning(f"ポリライン - 頂点数不足: {len(points)//2}")
        
        elif entity_type == "TEXT":
            # テキスト
            try:
                # テキストの情報を取得
                text_value = entity.dxf.text
                position = entity.dxf.insert
                height = entity.dxf.height
                rotation = entity.dxf.rotation
                
                # 水平方向の配置（ezdxfでは文字列またはint）
                h_align_map = {
                    "LEFT": tk.W,
                    "CENTER": tk.CENTER,
                    "RIGHT": tk.E,
                    0: tk.W,        # 左揃え
                    1: tk.CENTER,   # 中央揃え
                    2: tk.E,        # 右揃え
                    3: tk.W,        # 左揃え（ezdxfの内部表現）
                    4: tk.CENTER,   # 中央揃え（ezdxfの内部表現）
                    5: tk.E         # 右揃え（ezdxfの内部表現）
                }
                
                # 垂直方向の配置（ezdxfでは文字列またはint）
                v_align_map = {
                    "BASELINE": tk.S,
                    "BOTTOM": tk.S,
                    "MIDDLE": tk.CENTER,
                    "TOP": tk.N,
                    0: tk.S,        # 下/ベースライン
                    1: tk.S,        # 下揃え
                    2: tk.CENTER,   # 中央揃え
                    3: tk.N         # 上揃え
                }
                
                # デフォルト値
                h_align = tk.W   # 左揃え
                v_align = tk.S   # 下揃え
                
                # 水平方向の配置を取得
                try:
                    if hasattr(entity.dxf, "halign"):
                        h_align = h_align_map.get(entity.dxf.halign, tk.W)
                except:
                    pass
                    
                # 垂直方向の配置を取得
                try:
                    if hasattr(entity.dxf, "valign"):
                        v_align = v_align_map.get(entity.dxf.valign, tk.S)
                except:
                    pass
                
                # アンカーポイントの計算
                anchor = ""
                if v_align == tk.N:
                    if h_align == tk.W:
                        anchor = tk.NW
                    elif h_align == tk.E:
                        anchor = tk.NE
                    else:
                        anchor = tk.N
                elif v_align == tk.S:
                    if h_align == tk.W:
                        anchor = tk.SW
                    elif h_align == tk.E:
                        anchor = tk.SE
                    else:
                        anchor = tk.S
                else:
                    if h_align == tk.W:
                        anchor = tk.W
                    elif h_align == tk.E:
                        anchor = tk.E
                    else:
                        anchor = tk.CENTER
                
                # DXF座標をキャンバス座標に変換
                x = center_x + position.x
                y = center_y - position.y  # Y軸は反転
                
                # テキストサイズをスケール
                font_size = int(height * 0.0005)  # 適切なサイズに調整
                #if font_size < 8:
                 #   font_size = 8  # 最小サイズ
                
                # Tkinterでは直接テキストの回転をサポートしていないため、
                # 回転がある場合はその旨をログに記録
                if rotation != 0:
                    logger.info(f"テキスト回転: {rotation}度 - Tkinterでは直接サポートされていません")
                
                # テキストを描画
                text_id = self.create_text(
                    x, y, 
                    text=text_value, 
                    fill=color, 
                    anchor=anchor, 
                    font=("Arial", font_size), 
                    tags="dxf_entity"
                )
                
                logger.info(f"テキスト描画: \"{text_value}\" at ({x}, {y}), サイズ: {font_size}, 色: {color}")
                
            except Exception as e:
                logger.error(f"テキスト描画中にエラー: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # 他のエンティティタイプは必要に応じて追加
    
    def center_view(self):
        """
        すべてのエンティティが表示されるようにビューを中央に配置
        """
        # エンティティの範囲を取得
        bbox = self.bbox("dxf_entity")
        
        if not bbox:
            logger.warning("表示するエンティティがありません")
            return
        
        # キャンバスのサイズを取得
        canvas_width = self.winfo_width() or self.winfo_reqwidth()
        canvas_height = self.winfo_height() or self.winfo_reqheight()
        
        # エンティティの中心を計算
        entity_center_x = (bbox[0] + bbox[2]) / 2
        entity_center_y = (bbox[1] + bbox[3]) / 2
        
        # キャンバスの中心を計算
        canvas_center_x = canvas_width / 2
        canvas_center_y = canvas_height / 2
        
        # 移動量を計算
        dx = canvas_center_x - entity_center_x
        dy = canvas_center_y - entity_center_y
        
        # すべてのアイテムを中央に移動
        self.move(tk.ALL, dx, dy)
        
        # エンティティのサイズを計算
        entity_width = bbox[2] - bbox[0]
        entity_height = bbox[3] - bbox[1]
        
        # スケール倍率を計算（キャンバスの90%に収まるように）
        scale_x = (canvas_width * 0.9) / entity_width if entity_width > 0 else 1.0
        scale_y = (canvas_height * 0.9) / entity_height if entity_height > 0 else 1.0
        scale = min(scale_x, scale_y)
        
        # 極端なスケールは調整
        if scale < 0.01:
            scale = 0.01
        elif scale > 100:
            scale = 100
        
        # スケールを適用
        self.scale("all", canvas_center_x, canvas_center_y, scale, scale)
        self.scale_factor = scale
        
        logger.info(f"ビューを中央に配置しました（スケール: {scale:.2f}）")


class DxfViewerApp:
    """DXFビューワーアプリケーション"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter DXF Viewer")
        self.root.geometry("1000x700")
        
        # メニューバーの作成
        self._create_menu()
        
        # メインフレーム
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = tk.Label(root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # キャンバスを作成
        self.canvas = DxfPanCanvas(
            main_frame,
            width=1000,
            height=700,
            scrollregion=(-5000, -5000, 5000, 5000)
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 現在開いているファイル
        self.current_file = None
        
        logger.info("アプリケーションを初期化しました")
    
    def _create_menu(self):
        """メニューバーを作成"""
        menubar = tk.Menu(self.root)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="開く...", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        
        # 表示メニュー
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="中央に配置", command=lambda: self.canvas.center_view())
        menubar.add_cascade(label="表示", menu=view_menu)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="バージョン情報", command=self.show_about)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def open_file(self):
        """ファイルを開くダイアログを表示"""
        file_path = filedialog.askopenfilename(
            title="DXFファイルを開く",
            filetypes=[("DXF Files", "*.dxf"), ("All Files", "*.*")]
        )
        
        if file_path:
            self.current_file = file_path
            self.status_var.set(f"ファイルを読み込み中: {os.path.basename(file_path)}")
            self.root.update_idletasks()
            
            # DXFファイルを開く
            if self.canvas.open_dxf_file(file_path):
                self.status_var.set(f"ファイル読み込み完了: {os.path.basename(file_path)}")
                self.root.title(f"Tkinter DXF Viewer - {os.path.basename(file_path)}")
            else:
                self.status_var.set("ファイルの読み込みに失敗しました")
    
    def show_about(self):
        """バージョン情報ダイアログを表示"""
        messagebox.showinfo(
            "バージョン情報",
            "Tkinter DXF Viewer\nVersion 1.0\n\n"
            "シンプルで高速なDXFビューワー\n"
            "Copyright © 2025"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = DxfViewerApp(root)
    root.mainloop() 