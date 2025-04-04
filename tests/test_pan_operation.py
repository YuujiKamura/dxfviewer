#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
パン操作テスト - スクロールバー排除後の動作確認

このテストは、CAD的なキャンバス画面のパン操作ロジックが正しく機能していることを確認し、
スクロールバーを使用した擬似的なパン操作が正しく排除されていることを検証します。
"""

import sys
import pytest
import math
from pathlib import Path
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt, QPointF, QPoint, QRectF, QEvent
from PySide6.QtGui import QTransform, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QWidget, QApplication, QScrollBar

# テスト対象のモジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# テスト対象のクラスをインポート
from dxf_viewer_pyside6 import DXFGraphicsView

# QApplicationのグローバルインスタンスを保持
app = None

class TestPanOperation:
    """パン操作テスト - スクロールバー排除の検証"""
    
    @pytest.fixture(scope="session")
    def qapp(self):
        """テスト用のQApplicationインスタンスを作成するフィクスチャ"""
        global app
        if app is None:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
        yield app
    
    @pytest.fixture
    def mock_scene(self):
        """テスト用のシーンを作成するフィクスチャ"""
        scene = QGraphicsScene()
        # シンプルな図形を追加
        scene.addRect(QRectF(-100, -100, 200, 200))
        return scene
    
    @pytest.fixture
    def view(self, qapp, mock_scene):
        """テスト用のビューインスタンスを作成するフィクスチャ"""
        # 親ウィジェットを作成
        parent = QWidget()
        parent.debug_mode = True
        parent.resize(800, 600)
        
        # ビューを作成
        view = DXFGraphicsView(parent)
        view.resize(800, 600)
        view.setScene(mock_scene)
        
        yield view
        parent.close()
    
    def test_scrollbars_are_disabled(self, view):
        """スクロールバーが無効化されていることを確認するテスト"""
        # 水平・垂直スクロールバーが非表示に設定されていることを検証
        assert view.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        assert view.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        
        # スクロールバーが非表示であることを確認
        assert not view.horizontalScrollBar().isVisible()
        assert not view.verticalScrollBar().isVisible()
    
    def test_no_scroll_hand_drag(self, view):
        """ScrollHandDragモードが使用されていないことを確認するテスト"""
        # DragModeがNoDragに設定されていることを確認
        assert view.dragMode() == DXFGraphicsView.DragMode.NoDrag
    
    def test_pan_uses_transform_matrix(self, view):
        """パン操作が変換行列を直接操作していることを確認するテスト"""
        # 元の変換行列を保存
        initial_transform = view.transform()
        
        # マウスプレスイベントをシミュレート
        press_pos = QPointF(100, 100)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            press_pos,
            press_pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mousePressEvent(press_event)
        
        # is_panningフラグがセットされていることを確認
        assert view.is_panning == True
        
        # マウス移動イベントをシミュレート（右に50px、下に30px移動）
        move_pos = QPointF(150, 130)
        move_event = QMouseEvent(
            QEvent.Type.MouseMove,
            move_pos,
            move_pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        
        # panByメソッドをモックして呼び出しを監視
        original_panBy = view.panBy
        mock_panBy = MagicMock()
        view.panBy = mock_panBy
        
        # マウス移動を実行
        view.mouseMoveEvent(move_event)
        
        # panByが呼び出されたことを確認
        mock_panBy.assert_called_once()
        args = mock_panBy.call_args[0]
        
        # 期待される引数：(dx, dy) = (50, 30)
        assert abs(args[0] - 50.0) < 0.001
        assert abs(args[1] - 30.0) < 0.001
        
        # 元のメソッドを復元
        view.panBy = original_panBy
        
        # 実際にpanByを呼び出して変換行列の変化を確認
        view.panBy(50.0, 30.0)
        
        # パン後の変換行列を取得
        post_pan_transform = view.transform()
        
        # 変換行列の移動要素が変化していることを確認
        # 注：m31とm32はQTransformの場合、dxとdyに相当する
        dx = post_pan_transform.dx() - initial_transform.dx()
        dy = post_pan_transform.dy() - initial_transform.dy()
        
        # ズーム率1.0の場合、変換はそのまま反映される
        assert abs(dx - 50.0) < 1.0
        assert abs(dy - 30.0) < 1.0
    
    def test_pan_with_zoom_scale_adjustment(self, view):
        """ズーム状態でもパン操作がスケール調整されないことを確認するテスト"""
        # ズーム操作を実行（2倍に拡大）
        view.scale(2.0, 2.0)
        
        # 元の変換行列を保存
        initial_transform = view.transform()
        
        # パン操作をシミュレート（50pxの移動）
        view.panBy(50.0, 50.0)
        
        # パン後の変換行列を取得
        post_pan_transform = view.transform()
        
        # 変換行列の移動要素を確認
        dx = post_pan_transform.dx() - initial_transform.dx()
        dy = post_pan_transform.dy() - initial_transform.dy()
        
        # ズーム率に関わらず、指定した移動量（50px）がそのまま適用されることを確認
        assert abs(dx - 50.0) < 1.0
        assert abs(dy - 50.0) < 1.0
    
    def test_viewport_update_after_pan(self, view):
        """パン操作後にビューポートが更新されることを確認するテスト"""
        # ビューポート更新のモックを作成
        with patch.object(view.viewport(), 'update') as mock_update:
            # パン操作を実行
            view.panBy(50.0, 50.0)
            
            # ビューポート更新が呼び出されたことを確認
            mock_update.assert_called_once()
    
    def test_mouse_release_ends_panning(self, view):
        """マウスリリースでパン操作が終了することを確認するテスト"""
        # マウスプレスでパン開始
        press_pos = QPointF(100, 100)
        press_event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            press_pos,
            press_pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mousePressEvent(press_event)
        
        # is_panningフラグがセットされていることを確認
        assert view.is_panning == True
        
        # マウスリリースイベント
        release_pos = QPointF(150, 150)
        release_event = QMouseEvent(
            QEvent.Type.MouseButtonRelease,
            release_pos,
            release_pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseReleaseEvent(release_event)
        
        # is_panningフラグがクリアされていることを確認
        assert view.is_panning == False
        
        # カーソルが元の状態に戻っていることを確認
        assert view.cursor().shape() == Qt.CursorShape.ArrowCursor

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 