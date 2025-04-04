#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFViewer レンダリングパフォーマンステスト

レンダリング設定の違いによるパフォーマンスへの影響と、
パン・ズーム操作の応答速度を測定します。
"""

import os
import sys
import time
import unittest
import logging
from pathlib import Path

# 親ディレクトリをパスに追加して本番コードをインポートできるようにする
sys.path.insert(0, str(Path(__file__).parent.parent))

# PySide6関連のインポート
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QTimer, QPoint, Qt, QElapsedTimer
from PySide6.QtTest import QTest
from PySide6.QtGui import QPainter, QTransform

# テスト対象のモジュールをインポート
try:
    import dxf_viewer_pyside6
    from dxf_viewer_pyside6 import DXFViewer, DXFGraphicsView, AppSettings
    from dxf_ui_adapter import configure_graphics_view, request_viewport_update
except ImportError as e:
    print(f"テスト対象モジュールのインポートエラー: {e}")
    print("テストを実行するには本番のdxf_viewer_pyside6.pyが必要です")
    sys.exit(1)

# テスト用ロガーの設定
test_logger = logging.getLogger('PerfTest')
test_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
test_logger.addHandler(handler)

class RenderingPerfTest(unittest.TestCase):
    """レンダリングパフォーマンステスト"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラス実行前の準備"""
        # QApplicationを初期化
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """各テスト実行前の準備"""
        # AppSettingsを初期化
        self.app_settings = AppSettings()
        
        # DXFViewerインスタンスを作成
        self.viewer = DXFViewer(self.app_settings)
        
        # DXFGraphicsViewへの参照を取得
        self.view = self.viewer.dxf_view
        
        # サンプルDXFを読み込む
        sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                 "sample_dxf", "12.25 新規路線.dxf")
        if os.path.exists(sample_path):
            self.viewer.load_and_display_dxf(sample_path)
        
        # テスト実行のためにウィンドウを表示
        self.viewer.show()
        QApplication.processEvents()
    
    def tearDown(self):
        """各テスト実行後のクリーンアップ"""
        # ウィンドウを閉じる
        self.viewer.close()
        QApplication.processEvents()
    
    def test_pan_performance(self):
        """パン操作のパフォーマンスを測定"""
        # タイマーを初期化
        timer = QElapsedTimer()
        
        # パン操作の回数
        pan_count = 10
        total_time = 0
        
        # ビューの中央を取得
        center = self.view.viewport().rect().center()
        
        for i in range(pan_count):
            # パン操作の開始時間を記録
            timer.start()
            
            # マウスプレスをシミュレート
            QTest.mousePress(self.view.viewport(), Qt.MouseButton.LeftButton, 
                            Qt.KeyboardModifier.NoModifier, center)
            
            # ドラッグ操作（右に100px、下に50px）
            drag_to = center + QPoint(100, 50)
            QTest.mouseMove(self.view.viewport(), drag_to)
            QApplication.processEvents()
            
            # マウスリリース
            QTest.mouseRelease(self.view.viewport(), Qt.MouseButton.LeftButton, 
                              Qt.KeyboardModifier.NoModifier, drag_to)
            QApplication.processEvents()
            
            # 経過時間を記録
            elapsed = timer.elapsed()
            total_time += elapsed
            
            test_logger.info(f"パン操作 #{i+1}: {elapsed}ミリ秒")
        
        # 平均時間を計算
        avg_time = total_time / pan_count
        test_logger.info(f"パン操作の平均時間: {avg_time:.2f}ミリ秒")
        
        # 許容される最大時間（適切な値に調整する）
        max_acceptable_time = 50  # ミリ秒
        self.assertLessEqual(avg_time, max_acceptable_time, 
                           f"パン操作が遅すぎます: {avg_time:.2f}ms > {max_acceptable_time}ms")
    
    def test_zoom_performance(self):
        """ズーム操作のパフォーマンスを測定"""
        # タイマーを初期化
        timer = QElapsedTimer()
        
        # ズーム操作の回数
        zoom_count = 10
        total_time = 0
        
        for i in range(zoom_count):
            # ズーム操作の開始時間を記録
            timer.start()
            
            # ズームイン操作
            self.view.scale(self.view.zoom_factor, self.view.zoom_factor)
            QApplication.processEvents()
            
            # 経過時間を記録
            elapsed = timer.elapsed()
            total_time += elapsed
            
            test_logger.info(f"ズーム操作 #{i+1}: {elapsed}ミリ秒")
            
            # 次のテスト用にズームアウト
            if i % 2 == 0:
                self.view.scale(1/self.view.zoom_factor, 1/self.view.zoom_factor)
                QApplication.processEvents()
        
        # 平均時間を計算
        avg_time = total_time / zoom_count
        test_logger.info(f"ズーム操作の平均時間: {avg_time:.2f}ミリ秒")
        
        # 許容される最大時間（適切な値に調整する）
        max_acceptable_time = 30  # ミリ秒
        self.assertLessEqual(avg_time, max_acceptable_time, 
                           f"ズーム操作が遅すぎます: {avg_time:.2f}ms > {max_acceptable_time}ms")
    
    def test_rendering_settings_impact(self):
        """レンダリング設定がパフォーマンスに与える影響を測定"""
        # 異なる設定でのレンダリング時間を比較
        
        # 1. 最適化なし
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.view.setCacheMode(QGraphicsView.CacheModeFlag.CacheNone)
        QApplication.processEvents()
        
        # パン操作の時間を測定
        time_without_optimizations = self._measure_pan_time(5)
        test_logger.info(f"最適化なしのパン平均時間: {time_without_optimizations:.2f}ミリ秒")
        
        # 2. 最適化あり
        configure_graphics_view(self.view)
        QApplication.processEvents()
        
        # パン操作の時間を測定
        time_with_optimizations = self._measure_pan_time(5)
        test_logger.info(f"最適化ありのパン平均時間: {time_with_optimizations:.2f}ミリ秒")
        
        # 最適化の有無による時間の差を計算
        time_diff = time_without_optimizations - time_with_optimizations
        time_improvement = (time_diff / time_without_optimizations) * 100 if time_without_optimizations > 0 else 0
        
        test_logger.info(f"最適化による改善: {time_diff:.2f}ミリ秒 ({time_improvement:.2f}%)")
        
        # 最適化により時間が改善されていることを確認
        # 注意: この比較は環境によっては逆になる可能性もあるため、テスト失敗とはしません
        test_logger.info("時間比較: " + 
                      ("改善あり" if time_with_optimizations <= time_without_optimizations else "改善なし"))
    
    def _measure_pan_time(self, count=5):
        """パン操作の平均時間を測定するヘルパーメソッド"""
        timer = QElapsedTimer()
        total_time = 0
        
        # ビューの中央を取得
        center = self.view.viewport().rect().center()
        
        for i in range(count):
            # パン操作の開始時間を記録
            timer.start()
            
            # マウスプレスをシミュレート
            QTest.mousePress(self.view.viewport(), Qt.MouseButton.LeftButton, 
                            Qt.KeyboardModifier.NoModifier, center)
            
            # ドラッグ操作（右に100px、下に50px）
            drag_to = center + QPoint(100, 50)
            QTest.mouseMove(self.view.viewport(), drag_to)
            QApplication.processEvents()
            
            # マウスリリース
            QTest.mouseRelease(self.view.viewport(), Qt.MouseButton.LeftButton, 
                              Qt.KeyboardModifier.NoModifier, drag_to)
            QApplication.processEvents()
            
            # 経過時間を記録
            elapsed = timer.elapsed()
            total_time += elapsed
        
        # 平均時間を返す
        return total_time / count if count > 0 else 0

def run_interactive_performance_test():
    """インタラクティブなパフォーマンステスト実行"""
    app = QApplication([])
    app_settings = AppSettings()
    viewer = DXFViewer(app_settings)
    
    # サンプルファイルが存在すれば読み込む
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                              "sample_dxf", "12.25 新規路線.dxf")
    if os.path.exists(sample_path):
        test_logger.info(f"サンプルファイルを読み込みます: {sample_path}")
        viewer.load_and_display_dxf(sample_path)
    
    # ビューの参照を取得
    view = viewer.dxf_view
    
    # 設定を最適化
    test_logger.info("描画設定を最適化モードに設定します")
    configure_graphics_view(view)
    
    # ウィンドウを表示
    viewer.show()
    
    # パフォーマンス計測機能
    def toggle_optimization():
        """最適化設定の有効/無効を切り替え"""
        # 現在の設定を確認
        has_antialiasing = bool(view.renderHints() & QPainter.RenderHint.Antialiasing)
        
        if has_antialiasing:
            # 最適化を無効化
            view.setRenderHint(QPainter.RenderHint.Antialiasing, False)
            view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
            view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
            test_logger.info("最適化設定を無効化しました - パン操作のパフォーマンスを確認してください")
        else:
            # 最適化を有効化
            configure_graphics_view(view)
            test_logger.info("最適化設定を有効化しました - パン操作のパフォーマンスを確認してください")
    
    # タイマーを設定して定期的に設定を切り替え
    toggle_timer = QTimer()
    toggle_timer.timeout.connect(toggle_optimization)
    toggle_timer.start(5000)  # 5秒ごとに切り替え
    
    test_logger.info("インタラクティブパフォーマンステスト実行中")
    test_logger.info("5秒ごとに描画設定が切り替わります。パン操作の違いを確認してください。")
    test_logger.info("テストを終了するには、ウィンドウを閉じてください")
    
    return app.exec()

if __name__ == "__main__":
    # コマンドライン引数で実行モードを切り替え
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        sys.exit(run_interactive_performance_test())
    else:
        # 通常のユニットテスト実行
        unittest.main() 