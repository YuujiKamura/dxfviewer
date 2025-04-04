#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ハイブリッドテスト：シンプルパンテスト + 本番コードコンポーネント

simple_pan_testの単純な構造を保ちながら、
本番コードのDXFGraphicsViewの設定を適用して動作を比較します。
"""

import os
import sys
from pathlib import Path

# 親ディレクトリをインポートパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout, QLabel, QWidget
from PySide6.QtCore import QPointF, Qt, QRectF, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont

# 現在の実行時ログを記録
LOG_EVENTS = []  # format: [(timestamp, event_type, details), ...]

def log_event(event_type, details=""):
    """イベントをログに記録"""
    import time
    timestamp = time.time()
    LOG_EVENTS.append((timestamp, event_type, details))
    print(f"[{event_type}] {details}")

# 本番コードから設定関数をインポート
try:
    from dxf_ui_adapter import configure_graphics_view
    HAS_PROD_CODE = True
    log_event("IMPORT", "本番コードのdxf_ui_adapterをインポートしました")
except ImportError as e:
    HAS_PROD_CODE = False
    log_event("ERROR", f"本番コードのインポートに失敗: {e}")
    print("本番コードが見つかりません。基本的な設定のみで実行します。")

class SimplePanViewWithProdSettings(QGraphicsView):
    """シンプルパンテスト + 本番設定のハイブリッドビュー"""
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 基本設定
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # 本番コードの設定を適用（可能な場合）
        if HAS_PROD_CODE:
            configure_graphics_view(self)
            log_event("CONFIG", "本番コードの描画設定を適用")
        else:
            # 基本的な描画設定
            self.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
            self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
            self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
            self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
            log_event("CONFIG", "基本的な描画設定を適用")
            
        # ドラッグ追跡用
        self.last_mouse_pos = QPointF(0, 0)
        self.zoom_factor = 1.2
        
        # サンプル描画
        self.draw_coordinate_system()
        self.draw_sample_circles()
        
        # 変換行列情報をログ
        transform = self.transform()
        log_event("TRANSFORM", f"初期変換行列: m11={transform.m11():.3f}, m22={transform.m22():.3f}, dx={transform.dx():.3f}, dy={transform.dy():.3f}")
    
    def draw_coordinate_system(self):
        """座標系を描画"""
        # X軸（赤）
        self.scene.addLine(-500, 0, 500, 0, QPen(QColor(255, 0, 0), 1))
        # Y軸（緑）
        self.scene.addLine(0, -500, 0, 500, QPen(QColor(0, 255, 0), 1))
        # 原点
        self.scene.addEllipse(-5, -5, 10, 10, QPen(QColor(0, 0, 255)), QBrush(QColor(0, 0, 255, 100)))
        
        # 軸ラベル
        x_label = self.scene.addText("X", QFont("Arial", 10))
        x_label.setPos(480, 10)
        x_label.setDefaultTextColor(QColor(255, 0, 0))
        
        y_label = self.scene.addText("Y", QFont("Arial", 10))
        y_label.setPos(10, 480)
        y_label.setDefaultTextColor(QColor(0, 255, 0))
        
        log_event("DRAW", "座標系を描画")
    
    def draw_sample_circles(self):
        """サンプルの円を描画"""
        # 大きい円
        self.scene.addEllipse(-200, -200, 400, 400, QPen(QColor(0, 0, 0), 1))
        
        # 中くらいの円
        self.scene.addEllipse(-100, -100, 200, 200, QPen(QColor(0, 0, 0), 1))
        
        # 小さい円
        self.scene.addEllipse(-50, -50, 100, 100, QPen(QColor(0, 0, 0), 1))
        
        log_event("DRAW", "サンプル円を描画")
    
    def mousePressEvent(self, event):
        """マウスボタンが押されたとき"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.last_mouse_pos = event.position()
            log_event("MOUSE", f"ボタン押下: pos=({event.position().x():.1f}, {event.position().y():.1f})")
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """マウス移動時の処理"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            # マウス移動量を計算
            current_pos = event.position()
            delta = current_pos - self.last_mouse_pos
            
            # 本番コードと同じシンプルなパン処理
            transform = self.transform()
            
            # シンプルに変換行列に移動量を適用
            # ズーム率による調整は不要 - マウスの移動量をそのまま反映
            transform.translate(delta.x(), delta.y())
            self.setTransform(transform)
            
            # 明示的なビューポート更新（本番コードと同じ）
            self.viewport().update()
            
            # 位置を更新
            self.last_mouse_pos = current_pos
            
            # ログ出力
            log_event("PAN", f"dx={delta.x():.1f}, dy={delta.y():.1f}")
    
    def mouseReleaseEvent(self, event):
        """マウスボタンが離されたとき"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            log_event("MOUSE", "ボタン解放")
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """ホイールイベント（ズーム処理）"""
        # ズーム処理
        delta = event.angleDelta().y()
        factor = self.zoom_factor if delta > 0 else 1.0 / self.zoom_factor
        
        # ズーム適用
        self.scale(factor, factor)
        
        # 明示的なビューポート更新
        self.viewport().update()
        
        # 変換行列情報をログ
        transform = self.transform()
        log_event("ZOOM", f"factor={factor:.2f}, 方向={'拡大' if delta > 0 else '縮小'}, " +
                 f"m11={transform.m11():.3f}, m22={transform.m22():.3f}")
        
        event.accept()

class HybridTestWindow(QMainWindow):
    """ハイブリッドテスト用メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ハイブリッドテスト: シンプルパン + 本番設定")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # レイアウト
        layout = QVBoxLayout(central_widget)
        
        # ステータスラベル
        self.status_label = QLabel("左ドラッグでパン、ホイールでズーム")
        layout.addWidget(self.status_label)
        
        # ビュー
        self.view = SimplePanViewWithProdSettings()
        layout.addWidget(self.view)
        
        # ステータスバー
        self.statusBar().showMessage("準備完了 - 操作をお試しください")
        
        # 定期的な状態チェック
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(500)  # 500ms
        
        log_event("INIT", "ウィンドウ初期化完了")
    
    def update_status(self):
        """ステータス更新"""
        transform = self.view.transform()
        self.statusBar().showMessage(
            f"スケール: ({transform.m11():.2f}, {transform.m22():.2f}), " +
            f"移動: ({transform.dx():.1f}, {transform.dy():.1f})"
        )

def main():
    """メイン関数"""
    app = QApplication([])
    
    window = HybridTestWindow()
    window.show()
    
    print("テスト実行中: 左ドラッグでパン、ホイールでズーム操作してください")
    print("このテストでは本番コードと同じ描画設定が適用されています")
    
    # 5秒後に結果を表示するタイマー
    def show_results():
        print("\n===== テスト結果 =====")
        print(f"記録されたイベント数: {len(LOG_EVENTS)}")
        transform = window.view.transform()
        print(f"最終変換行列: m11={transform.m11():.3f}, m22={transform.m22():.3f}, dx={transform.dx():.3f}, dy={transform.dy():.3f}")
        print("本番コードの設定が正しく適用されています" if HAS_PROD_CODE else "警告: 本番コードを使用せず基本設定で実行されました")
    
    result_timer = QTimer()
    result_timer.timeout.connect(show_results)
    result_timer.setSingleShot(True)
    result_timer.start(5000)  # 5秒後
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 