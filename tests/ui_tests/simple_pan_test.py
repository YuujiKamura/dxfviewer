#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
シンプルなパン操作テスト
円を描画し、パン操作の動作確認を行うための最小限のアプリケーション
すべての状態をターミナルに出力
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, 
    QGraphicsTextItem, QLabel
)
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer
from PySide6.QtGui import QPen, QBrush, QColor, QTransform, QFont, QPainter

class SimplePanView(QGraphicsView):
    """
    シンプルなパン操作テスト用のビュークラス
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # シーンの設定
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # レンダリング品質と更新方式の設定
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        
        # Viewport設定
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 円を描画
        self.draw_sample_circles()
        
        # ズーム率の追跡
        self.current_zoom = 1.0
        
        # マウス位置の追跡
        self.last_mouse_pos = QPointF(0, 0)
        
        # 座標原点の描画
        self.draw_coordinate_system()
        
        # 初期状態の変換行列を出力
        transform = self.transform()
        print("\n===== 初期状態 =====")
        print(f"変換行列: [m11={transform.m11():.3f}, m12={transform.m12():.3f}, m21={transform.m21():.3f}, m22={transform.m22():.3f}]")
        print(f"平行移動: [dx={transform.dx():.3f}, dy={transform.dy():.3f}]")
        print(f"ズーム率: {self.current_zoom:.3f}")
        print("===================\n")
    
    def draw_sample_circles(self):
        """サンプルの円を描画"""
        # 中央に大きな円
        self.scene.addEllipse(QRectF(-50, -50, 100, 100), 
                             QPen(QColor(0, 0, 0)), 
                             QBrush(QColor(255, 0, 0, 100)))
        
        # 四隅に小さな円
        positions = [
            (200, 200, QColor(255, 0, 0), "右下"),
            (200, -200, QColor(0, 255, 0), "右上"),
            (-200, 200, QColor(0, 0, 255), "左下"),
            (-200, -200, QColor(255, 255, 0), "左上")
        ]
        
        for x, y, color, label in positions:
            self.scene.addEllipse(QRectF(x-20, y-20, 40, 40), 
                                 QPen(QColor(0, 0, 0)), 
                                 QBrush(color))
            
            # ラベルテキストを追加
            text = self.scene.addText(label)
            text.setPos(x - 20, y + 20)
            text.setDefaultTextColor(QColor(0, 0, 0))
        
        print(f"図形を描画: 中央に赤い円、四隅に小さな円")
    
    def draw_coordinate_system(self):
        """座標系を描画（XY軸と原点）"""
        # X軸（赤）
        self.scene.addLine(-1000, 0, 1000, 0, QPen(QColor(255, 0, 0), 1))
        # Y軸（緑）
        self.scene.addLine(0, -1000, 0, 1000, QPen(QColor(0, 255, 0), 1))
        # 原点（青い円）
        self.scene.addEllipse(QRectF(-5, -5, 10, 10), 
                             QPen(QColor(0, 0, 0)), 
                             QBrush(QColor(0, 0, 255)))
        
        # 軸のラベル
        x_label = self.scene.addText("X軸")
        x_label.setPos(950, 10)
        x_label.setDefaultTextColor(QColor(255, 0, 0))
        
        y_label = self.scene.addText("Y軸")
        y_label.setPos(10, -980)
        y_label.setDefaultTextColor(QColor(0, 255, 0))
        
        # グリッド線（薄い色で）
        grid_pen = QPen(QColor(200, 200, 200, 100))
        grid_pen.setStyle(Qt.PenStyle.DotLine)
        
        # X軸方向のグリッド線
        for y in range(-1000, 1001, 100):
            if y != 0:  # 0はY軸自体
                self.scene.addLine(-1000, y, 1000, y, grid_pen)
        
        # Y軸方向のグリッド線
        for x in range(-1000, 1001, 100):
            if x != 0:  # 0はX軸自体
                self.scene.addLine(x, -1000, x, 1000, grid_pen)
        
        print(f"座標系を描画: X軸(赤)、Y軸(緑)、原点(青)、100単位のグリッド線")
    
    def mousePressEvent(self, event):
        """マウス押下時の処理"""
        if event.button() == Qt.MouseButton.LeftButton:
            screen_pos = event.position()
            scene_pos = self.mapToScene(screen_pos.toPoint())
            
            self.last_mouse_pos = screen_pos
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
            print("\n===== マウス押下 =====")
            print(f"スクリーン座標: ({screen_pos.x():.1f}, {screen_pos.y():.1f})")
            print(f"シーン座標: ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
            
            transform = self.transform()
            print(f"変換行列: [m11={transform.m11():.3f}, m12={transform.m12():.3f}, m21={transform.m21():.3f}, m22={transform.m22():.3f}]")
            print(f"平行移動: [dx={transform.dx():.3f}, dy={transform.dy():.3f}]")
            print("=====================\n")
    
    def mouseMoveEvent(self, event):
        """マウス移動時の処理（パン操作）"""
        if Qt.MouseButton.LeftButton & event.buttons():
            # 現在のマウス位置と前回位置の差分を計算
            current_pos = event.position()
            scene_pos = self.mapToScene(current_pos.toPoint())
            delta = current_pos - self.last_mouse_pos
            
            # 変換前の行列を保存
            old_transform = self.transform()
            
            # シンプルに変換行列に移動量を適用
            # ズーム率による調整は不要 - マウスの移動量をそのまま反映
            new_transform = QTransform(old_transform)
            new_transform.translate(delta.x(), delta.y())
            self.setTransform(new_transform)
            
            # 明示的に再描画を要求
            self.viewport().update()
            
            # 現在位置を更新
            self.last_mouse_pos = current_pos
            
            # デバッグ情報をターミナルに出力
            print("\n===== パン操作 =====")
            print(f"スクリーン座標: ({current_pos.x():.1f}, {current_pos.y():.1f})")
            print(f"シーン座標: ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
            print(f"マウス移動量: dx={delta.x():.1f}, dy={delta.y():.1f}")
            print(f"変換前行列: [m11={old_transform.m11():.3f}, m22={old_transform.m22():.3f}, dx={old_transform.dx():.3f}, dy={old_transform.dy():.3f}]")
            
            new_transform = self.transform()
            print(f"変換後行列: [m11={new_transform.m11():.3f}, m22={new_transform.m22():.3f}, dx={new_transform.dx():.3f}, dy={new_transform.dy():.3f}]")
            print("===================\n")
    
    def mouseReleaseEvent(self, event):
        """マウスリリース時の処理"""
        if event.button() == Qt.MouseButton.LeftButton:
            screen_pos = event.position()
            scene_pos = self.mapToScene(screen_pos.toPoint())
            
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            print("\n===== マウスリリース =====")
            print(f"スクリーン座標: ({screen_pos.x():.1f}, {screen_pos.y():.1f})")
            print(f"シーン座標: ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
            
            transform = self.transform()
            print(f"最終変換行列: [m11={transform.m11():.3f}, m12={transform.m12():.3f}, m21={transform.m21():.3f}, m22={transform.m22():.3f}]")
            print(f"最終平行移動: [dx={transform.dx():.3f}, dy={transform.dy():.3f}]")
            print("========================\n")
    
    def wheelEvent(self, event):
        """ホイールイベント（ズーム処理）"""
        # ズーム倍率
        zoom_factor = 1.25
        
        # 変換前の情報を保存
        old_transform = self.transform()
        old_zoom = self.current_zoom
        
        # マウス位置を取得
        mouse_pos = event.position()
        scene_pos = self.mapToScene(mouse_pos.toPoint())
        
        # ホイールの回転方向に応じてズームイン/アウト
        if event.angleDelta().y() > 0:
            # ズームイン
            scale_factor = zoom_factor
            self.current_zoom *= zoom_factor
            zoom_direction = "ズームイン"
        else:
            # ズームアウト
            scale_factor = 1 / zoom_factor
            self.current_zoom /= zoom_factor
            zoom_direction = "ズームアウト"
        
        # マウス位置を中心にズーム
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        
        # 変換行列のスケール更新
        self.scale(scale_factor, scale_factor)
        
        # マウス位置が変わらないように調整
        new_pos = self.mapToScene(mouse_pos.toPoint())
        delta = new_pos - scene_pos
        
        # 平行移動を適用
        transform = self.transform()
        self.translate(delta.x(), delta.y())
        
        # 明示的に再描画を要求
        self.viewport().update()
        
        # 最終的な変換行列
        final_transform = self.transform()
        
        # デバッグ情報をターミナルに出力
        print("\n===== ズーム操作 =====")
        print(f"操作: {zoom_direction} (factor: {scale_factor:.3f})")
        print(f"ズーム前: {old_zoom:.3f} → ズーム後: {self.current_zoom:.3f}")
        print(f"マウス位置 (スクリーン): ({mouse_pos.x():.1f}, {mouse_pos.y():.1f})")
        print(f"マウス位置 (シーン): ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
        print(f"ズーム前行列: [m11={old_transform.m11():.3f}, m22={old_transform.m22():.3f}, dx={old_transform.dx():.3f}, dy={old_transform.dy():.3f}]")
        print(f"ズーム後行列: [m11={final_transform.m11():.3f}, m22={final_transform.m22():.3f}, dx={final_transform.dx():.3f}, dy={final_transform.dy():.3f}]")
        print(f"座標補正: dx={delta.x():.3f}, dy={delta.y():.3f}")
        print("=====================\n")

class MainWindow(QMainWindow):
    """メインウィンドウ"""
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("シンプルパン操作テスト - ターミナル出力版")
        self.resize(800, 600)
        
        # ビューを設定
        self.view = SimplePanView(self)
        self.setCentralWidget(self.view)
        
        # 初期表示範囲
        self.view.setSceneRect(-500, -500, 1000, 1000)
        
        # ステータスバーにマウス座標を表示
        self.statusBar().showMessage("起動完了 - 左クリック+ドラッグでパン、ホイールでズーム")
        
        # マウス座標表示用ラベル
        self.position_label = QLabel()
        self.statusBar().addPermanentWidget(self.position_label)
        
        # マウス追跡タイマー
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_mouse_position)
        self.timer.start(100)  # 100msごとに更新
        
        # 表示状態確認用の自動テスト
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.run_auto_test)
        self.test_timer.start(2000)  # 2秒ごとに自動テスト
        self.test_counter = 0
        self.auto_test_active = True
        
        # 更新カウンター - 画面が更新されているか確認するため
        self.update_counter = 0
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_updates)
        self.update_timer.start(500)  # 500msごとに確認
    
    def update_mouse_position(self):
        """マウス位置を更新"""
        pos = self.view.mapFromGlobal(self.cursor().pos())
        if self.view.rect().contains(pos):
            scene_pos = self.view.mapToScene(pos)
            transform = self.view.transform()
            status_text = f"座標: ({scene_pos.x():.1f}, {scene_pos.y():.1f}) | 変換: [{transform.m11():.2f}, {transform.m22():.2f}] | 更新: {self.update_counter}"
            self.position_label.setText(status_text)
            
    def check_updates(self):
        """画面更新を監視"""
        self.update_counter += 1
        # 強制的に画面を更新
        self.view.viewport().update()
    
    def run_auto_test(self):
        """自動テスト - パンとズームを自動で実行して動作確認"""
        if not self.auto_test_active:
            return
            
        self.test_counter += 1
        test_num = self.test_counter % 4
        
        if test_num == 0:
            # 右へパン
            transform = self.view.transform()
            new_transform = QTransform(transform)
            new_transform.translate(50, 0)
            self.view.setTransform(new_transform)
            self.view.viewport().update()
            print("\n===== 自動テスト: 右へパン =====")
            print(f"新しい変換行列: [dx={new_transform.dx():.3f}, dy={new_transform.dy():.3f}]")
            
        elif test_num == 1:
            # 下へパン
            transform = self.view.transform()
            new_transform = QTransform(transform)
            new_transform.translate(0, 50)
            self.view.setTransform(new_transform)
            self.view.viewport().update()
            print("\n===== 自動テスト: 下へパン =====")
            print(f"新しい変換行列: [dx={new_transform.dx():.3f}, dy={new_transform.dy():.3f}]")
            
        elif test_num == 2:
            # ズームイン
            old_zoom = self.view.current_zoom
            scale_factor = 1.25
            self.view.current_zoom *= scale_factor
            center = QPointF(self.view.viewport().width() / 2, self.view.viewport().height() / 2)
            scene_center = self.view.mapToScene(center.toPoint())
            
            self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            self.view.scale(scale_factor, scale_factor)
            
            new_center = self.view.mapToScene(center.toPoint())
            delta = new_center - scene_center
            self.view.translate(delta.x(), delta.y())
            self.view.viewport().update()
            
            print("\n===== 自動テスト: ズームイン =====")
            print(f"ズーム: {old_zoom:.3f} → {self.view.current_zoom:.3f}")
            
        elif test_num == 3:
            # ズームアウト
            old_zoom = self.view.current_zoom
            scale_factor = 0.8
            self.view.current_zoom *= scale_factor
            center = QPointF(self.view.viewport().width() / 2, self.view.viewport().height() / 2)
            scene_center = self.view.mapToScene(center.toPoint())
            
            self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
            self.view.scale(scale_factor, scale_factor)
            
            new_center = self.view.mapToScene(center.toPoint())
            delta = new_center - scene_center
            self.view.translate(delta.x(), delta.y())
            self.view.viewport().update()
            
            print("\n===== 自動テスト: ズームアウト =====")
            print(f"ズーム: {old_zoom:.3f} → {self.view.current_zoom:.3f}")
            
        # 10回のテスト後に自動テストを停止
        if self.test_counter >= 20:
            self.auto_test_active = False
            print("\n===== 自動テスト完了 =====")

if __name__ == "__main__":
    print("\n===== シンプルパン操作テストアプリケーション =====")
    print("目的: Qtのグラフィックスビューのパン・ズーム操作を検証")
    print("操作方法:")
    print(" - 左クリック+ドラッグ: パン操作")
    print(" - マウスホイール: ズーム操作")
    print("=================================================\n")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 