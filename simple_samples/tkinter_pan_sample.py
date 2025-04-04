#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tkinterを使ったシンプルなパン操作サンプル
"""

import tkinter as tk

class PanCanvas(tk.Canvas):
    """パン操作可能なキャンバス"""
    
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # パン操作の状態変数
        self._is_panning = False
        self._pan_start_x = 0
        self._pan_start_y = 0
        
        # キャンバスの背景色を設定
        self.configure(bg='#f0f0f0')
        
        # キャンバスにコンテンツを追加
        self._create_content()
        
        # イベントバインド
        self.bind("<ButtonPress-1>", self._on_mouse_press)
        self.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.bind("<B1-Motion>", self._on_mouse_move)
        
    def _create_content(self):
        """キャンバスにコンテンツを描画"""
        # キャンバスの中心座標を計算
        canvas_width = self.winfo_reqwidth()
        canvas_height = self.winfo_reqheight()
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # グリッドの描画（薄いグレー）
        for i in range(-500, 501, 50):
            # 水平線
            self.create_line(center_x-500, center_y+i, center_x+500, center_y+i, fill='#dcdcdc')
            # 垂直線
            self.create_line(center_x+i, center_y-500, center_x+i, center_y+500, fill='#dcdcdc')
        
        # X軸（赤）
        self.create_line(center_x-100, center_y, center_x+100, center_y, fill='red', width=1)
        
        # Y軸（緑）
        self.create_line(center_x, center_y-100, center_x, center_y+100, fill='green', width=1)
        
        # 原点円（青）
        self.create_oval(center_x-5, center_y-5, center_x+5, center_y+5, outline='blue', fill='#7878ff')
        
        # 原点座標テキスト
        self.create_text(center_x+10, center_y+10, text="(0,0)", anchor=tk.NW)
        
        # 初期位置の設定は不要
        # self.xview_moveto(0.5)
        # self.yview_moveto(0.5)
    
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

class MainApp:
    """メインアプリケーション"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinterパン操作サンプル")
        self.root.geometry("800x600")
        
        # キャンバスを作成
        self.canvas = PanCanvas(
            root,
            width=800,
            height=600,
            scrollregion=(-1000, -1000, 1000, 1000)
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop() 