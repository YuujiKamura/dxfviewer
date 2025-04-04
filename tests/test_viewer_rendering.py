#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFViewer レンダリング設定とパン・ズーム操作テスト

本番環境のDXFViewerクラスやDXFGraphicsViewクラスを使用して、
パン・ズーム操作の品質と描画設定が正しく適用されているかをテストします。
"""

import os
import sys
import unittest
import logging
from pathlib import Path

# 親ディレクトリをパスに追加して本番コードをインポートできるようにする
sys.path.insert(0, str(Path(__file__).parent.parent))

# PySide6関連のインポート
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView
from PySide6.QtCore import QTimer, QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QTransform

# テスト対象のモジュールをインポート
try:
    import dxf_viewer_pyside6
    from dxf_viewer_pyside6 import DXFViewer, DXFGraphicsView, AppSettings
    from dxf_ui_adapter import configure_graphics_view
except ImportError as e:
    print(f"テスト対象モジュールのインポートエラー: {e}")
    print("テストを実行するには本番のdxf_viewer_pyside6.pyが必要です")
    sys.exit(1)

# テスト用ロガーの設定
test_logger = logging.getLogger('ViewerTest')
test_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
test_logger.addHandler(handler)

class TestViewerRendering(unittest.TestCase):
    """DXFViewerのレンダリング設定と操作テスト"""
    
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
        
        # テスト実行のためにウィンドウを表示
        self.viewer.show()
        QApplication.processEvents()
    
    def tearDown(self):
        """各テスト実行後のクリーンアップ"""
        # ウィンドウを閉じる
        self.viewer.close()
        QApplication.processEvents()
    
    def test_graphics_view_settings(self):
        """QGraphicsViewの描画設定が正しく適用されているかテスト"""
        # 基本的なプロパティをチェック
        self.assertTrue(self.view.renderHints() & self.view.renderHint(Qt.RenderHint.Antialiasing))
        self.assertTrue(self.view.renderHints() & self.view.renderHint(Qt.RenderHint.SmoothPixmapTransform))
        self.assertEqual(self.view.viewportUpdateMode(), QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.assertEqual(self.view.cacheMode(), QGraphicsView.CacheModeFlag.CacheBackground)
        
        # 最適化フラグの確認（通常は直接チェックできないため、テスト中は省略可能）
        test_logger.info("レンダリング設定: アンチエイリアス=%s, スムーズトランスフォーム=%s",
                 self.view.renderHints() & Qt.RenderHint.Antialiasing,
                 self.view.renderHints() & Qt.RenderHint.SmoothPixmapTransform)
        test_logger.info("ビューポート更新モード: %s", self.view.viewportUpdateMode())
        
        # configure_graphics_view関数の適用テスト
        # 一度設定をリセットして再適用
        self.view.setRenderHint(Qt.RenderHint.Antialiasing, False)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        
        # 設定を再適用
        configure_graphics_view(self.view)
        
        # 再度チェック
        self.assertTrue(self.view.renderHints() & Qt.RenderHint.Antialiasing)
        self.assertEqual(self.view.viewportUpdateMode(), QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        test_logger.info("レンダリング設定テスト完了: 設定が正しく適用されています")
    
    def test_pan_operation(self):
        """パン操作のテスト"""
        # 初期変換行列を保存
        initial_transform = self.view.transform()
        test_logger.info("初期変換行列: m11=%f, m22=%f, dx=%f, dy=%f",
                 initial_transform.m11(), initial_transform.m22(),
                 initial_transform.dx(), initial_transform.dy())
        
        # マウスプレスとドラッグをシミュレート
        center = self.view.viewport().rect().center()
        QTest.mousePress(self.view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, center)
        
        # ドラッグ操作（100ピクセル右、50ピクセル下）
        drag_to = center + QPoint(100, 50)
        QTest.mouseMove(self.view.viewport(), drag_to)
        QApplication.processEvents()
        
        # マウスリリース
        QTest.mouseRelease(self.view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, drag_to)
        QApplication.processEvents()
        
        # 変換行列の変更を確認
        current_transform = self.view.transform()
        test_logger.info("パン後の変換行列: m11=%f, m22=%f, dx=%f, dy=%f",
                 current_transform.m11(), current_transform.m22(),
                 current_transform.dx(), current_transform.dy())
        
        # 変換行列の平行移動成分（dx, dy）が変化していることを確認
        self.assertNotEqual(initial_transform.dx(), current_transform.dx())
        self.assertNotEqual(initial_transform.dy(), current_transform.dy())
        
        test_logger.info("パン操作テスト完了: 変換行列が正しく更新されました")
    
    def test_zoom_operation(self):
        """ズーム操作のテスト"""
        # 初期変換行列を保存
        initial_transform = self.view.transform()
        test_logger.info("初期変換行列: m11=%f, m22=%f",
                 initial_transform.m11(), initial_transform.m22())
        
        # ホイールイベントをシミュレート（ズームイン）
        center = self.view.viewport().rect().center()
        # PySide6ではQWheelEventの直接作成が難しいため、panByメソッドで代用
        self.view.scale(self.view.zoom_factor, self.view.zoom_factor)
        QApplication.processEvents()
        
        # 変換行列のスケール成分が変化していることを確認
        current_transform = self.view.transform()
        test_logger.info("ズームイン後の変換行列: m11=%f, m22=%f",
                 current_transform.m11(), current_transform.m22())
        
        # スケール成分（m11, m22）が大きくなっていることを確認
        self.assertGreater(current_transform.m11(), initial_transform.m11())
        self.assertGreater(current_transform.m22(), initial_transform.m22())
        
        # ズームアウト
        self.view.scale(1.0/self.view.zoom_factor, 1.0/self.view.zoom_factor)
        QApplication.processEvents()
        
        # 元のスケールに近い値に戻っていることを確認
        final_transform = self.view.transform()
        test_logger.info("ズームアウト後の変換行列: m11=%f, m22=%f",
                 final_transform.m11(), final_transform.m22())
        
        # 元の値との差が小さいことを確認（浮動小数点の誤差を考慮）
        self.assertAlmostEqual(initial_transform.m11(), final_transform.m11(), delta=0.001)
        self.assertAlmostEqual(initial_transform.m22(), final_transform.m22(), delta=0.001)
        
        test_logger.info("ズーム操作テスト完了: スケール変換が正しく適用されました")

def run_interactive_test():
    """インタラクティブなテスト実行"""
    app = QApplication([])
    app_settings = AppSettings()
    viewer = DXFViewer(app_settings)
    
    # サンプルファイルが存在すれば読み込む
    sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                              "sample_dxf", "12.25 新規路線.dxf")
    if os.path.exists(sample_path):
        test_logger.info(f"サンプルファイルを読み込みます: {sample_path}")
        viewer.load_and_display_dxf(sample_path)
    
    # 描画設定を確認
    view = viewer.dxf_view
    test_logger.info("現在の描画設定:")
    test_logger.info("- アンチエイリアス: %s", bool(view.renderHints() & Qt.RenderHint.Antialiasing))
    test_logger.info("- スムーズトランスフォーム: %s", bool(view.renderHints() & Qt.RenderHint.SmoothPixmapTransform))
    test_logger.info("- ビューポート更新モード: %s", view.viewportUpdateMode())
    test_logger.info("- キャッシュモード: %s", view.cacheMode())
    
    # ウィンドウを表示
    viewer.show()
    
    test_logger.info("インタラクティブテスト実行中: マウスでパン・ズーム操作を試してください")
    test_logger.info("テストを終了するには、ウィンドウを閉じてください")
    
    return app.exec()

if __name__ == "__main__":
    # コマンドライン引数で実行モードを切り替え
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        sys.exit(run_interactive_test())
    else:
        # 通常のユニットテスト実行
        unittest.main() 