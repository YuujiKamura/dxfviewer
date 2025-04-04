#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pytest
import math
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from PySide6.QtCore import Qt, QPointF, QPoint, QRectF, QEvent
from PySide6.QtGui import QTransform, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QWidget, QGraphicsItem, QApplication

# テスト対象のモジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# テスト対象のクラスをインポート
from dxf_viewer_pyside6 import DXFGraphicsView

# QApplicationのグローバルインスタンスを保持
app = None

class TestBasicOperations:
    """基本操作のテスト - 標準的なノーマルケース"""
    
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
        scene.addLine(0, 0, 100, 100)  # シンプルな線を追加
        return scene
    
    @pytest.fixture
    def view(self, qapp, mock_scene):
        """テスト用のビューインスタンスを作成するフィクスチャ"""
        # 親ウィジェットを作成
        parent = QWidget()
        parent.debug_mode = True
        parent.resize(800, 600)  # サイズを設定
        parent.show()  # ウィジェットを表示（画面に表示しなくても内部的には必要）
        
        # 親ウィジェットを持つビューを作成
        view = DXFGraphicsView(parent)
        view.resize(800, 600)
        
        # シーンを設定
        view.setScene(mock_scene)
        
        # テスト終了後にビューと親ウィジェットをクリーンアップ
        yield view
        
        parent.close()
    
    def test_initial_state(self, view):
        """初期状態の検証"""
        # 現在のズームレベルが1.0（初期値）であることを確認
        assert view.current_zoom == 1.0
        
        # デフォルトの変換行列が単位行列であることを確認
        transform = view.transform()
        assert transform.m11() == 1.0  # X方向のスケール
        assert transform.m22() == 1.0  # Y方向のスケール
        assert transform.m31() == 0.0  # X方向の移動
        assert transform.m32() == 0.0  # Y方向の移動
    
    def test_basic_zoom_in(self, view):
        """基本的なズームイン操作のテスト"""
        # ズームイン前の状態を保存
        initial_transform = view.transform()
        
        # ズームインをシミュレート（マウスホイールを前方に回転）
        mock_wheel_event = QWheelEvent(
            QPointF(100, 100),  # ポジション
            QPointF(100, 100),  # グローバルポジション
            QPoint(0, 120),     # ピクセルデルタ（Y軸の正の値でズームイン）
            QPoint(0, 120),     # 角度デルタ
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        view.wheelEvent(mock_wheel_event)
        
        # ズーム後の変換行列を取得
        post_zoom_transform = view.transform()
        
        # ズームレベルが増加していることを確認
        assert view.current_zoom > 1.0
        
        # 変換行列のスケール要素が増加していることを確認
        assert post_zoom_transform.m11() > initial_transform.m11()
        assert post_zoom_transform.m22() > initial_transform.m22()
        
        # ズームの中心が指定したマウス位置になっていることを確認
        # (これは間接的にしか確認できないので、変換後の座標でテスト)
        test_point = QPoint(100, 100)
        world_point = view.mapToScene(test_point)
        screen_point = view.mapFromScene(world_point)
        
        # 変換前後で座標が一致することを確認
        assert abs(screen_point.x() - test_point.x()) < 1.0
        assert abs(screen_point.y() - test_point.y()) < 1.0
    
    def test_basic_zoom_out(self, view):
        """基本的なズームアウト操作のテスト"""
        # ズームアウト前の状態を保存
        initial_transform = view.transform()
        
        # ズームアウトをシミュレート（マウスホイールを後方に回転）
        mock_wheel_event = QWheelEvent(
            QPointF(100, 100),  # ポジション
            QPointF(100, 100),  # グローバルポジション
            QPoint(0, -120),    # ピクセルデルタ（Y軸の負の値でズームアウト）
            QPoint(0, -120),    # 角度デルタ
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        view.wheelEvent(mock_wheel_event)
        
        # ズーム後の変換行列を取得
        post_zoom_transform = view.transform()
        
        # ズームレベルが減少していることを確認
        assert view.current_zoom < 1.0
        
        # 変換行列のスケール要素が減少していることを確認
        assert post_zoom_transform.m11() < initial_transform.m11()
        assert post_zoom_transform.m22() < initial_transform.m22()
    
    def test_basic_pan(self, view):
        """基本的なパン操作のテスト"""
        # パン前の状態を保存
        initial_transform = view.transform()
        
        # パンをシミュレート（マウスドラッグ）
        # マウス押下
        mock_press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(100, 100),  # ポジション
            QPointF(100, 100),  # グローバルポジション
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mousePressEvent(mock_press_event)
        
        # マウス移動
        mock_move_event = QMouseEvent(
            QEvent.MouseMove,
            QPointF(150, 150),  # 新しいポジション（右下に50px移動）
            QPointF(150, 150),  # グローバルポジション
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseMoveEvent(mock_move_event)
        
        # マウスリリース
        mock_release_event = QMouseEvent(
            QEvent.MouseButtonRelease,
            QPointF(150, 150),  # ポジション
            QPointF(150, 150),  # グローバルポジション
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseReleaseEvent(mock_release_event)
        
        # パン後の変換行列を取得
        post_pan_transform = view.transform()
        
        # 変換行列の移動要素が変化していることを確認
        assert post_pan_transform.m31() != initial_transform.m31()
        assert post_pan_transform.m32() != initial_transform.m32()
        
        # パンの方向が正しいことを確認（右下に移動したので、シーンは左上に移動する）
        translation_x = post_pan_transform.m31() - initial_transform.m31()
        translation_y = post_pan_transform.m32() - initial_transform.m32()
        assert translation_x > 0  # 左上に移動するのでX方向は正
        assert translation_y > 0  # 左上に移動するのでY方向は正
    
    def test_reset_view(self, view):
        """ビューリセット操作のテスト"""
        # 初期状態を変更するためにズームとパンを実行
        # ズーム操作
        mock_wheel_event = QWheelEvent(
            QPointF(100, 100),
            QPointF(100, 100),
            QPoint(0, 120),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        view.wheelEvent(mock_wheel_event)
        
        # パン操作（マウスドラッグ）
        mock_press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(100, 100),
            QPointF(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mousePressEvent(mock_press_event)
        
        mock_move_event = QMouseEvent(
            QEvent.MouseMove,
            QPointF(150, 150),
            QPointF(150, 150),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseMoveEvent(mock_move_event)
        
        mock_release_event = QMouseEvent(
            QEvent.MouseButtonRelease,
            QPointF(150, 150),
            QPointF(150, 150),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseReleaseEvent(mock_release_event)
        
        # 変更後の状態を保存
        modified_transform = view.transform()
        modified_zoom = view.current_zoom
        
        # 実際に変更が加えられたことを確認
        assert modified_zoom != 1.0
        
        # モック設定
        # fitInViewとcreateCoordinateSystemをモック化
        original_fitInView = view.fitInView
        original_createCoordinateSystem = view.createCoordinateSystem
        
        view.fitInView = MagicMock()
        view.createCoordinateSystem = MagicMock()
        
        # リセット操作を実行
        view.reset_view()
        
        # fitInViewが呼ばれたことを確認
        view.fitInView.assert_called_once()
        
        # createCoordinateSystemが呼ばれたことを確認
        view.createCoordinateSystem.assert_called_once()
        
        # モックを元に戻す
        view.fitInView = original_fitInView
        view.createCoordinateSystem = original_createCoordinateSystem
    
    def test_screen_to_world_conversion(self, view):
        """スクリーン座標からワールド座標への変換テスト"""
        # 画面中央の座標
        test_point = QPoint(100, 100)
        
        # スクリーン→ワールド変換
        world_point = view.mapToScene(test_point)
        
        # Y座標が反転していることを確認（スクリーン座標系はY軸が下向き、ワールド座標系はY軸が上向き）
        # 正確な値はビューのセットアップによって異なるが、変換の一貫性だけをテスト
        
        # 逆変換（ワールド→スクリーン）
        screen_point = view.mapFromScene(world_point)
        
        # 往復変換後に元の値に近い値が得られることを確認（浮動小数点の誤差を考慮）
        assert abs(screen_point.x() - test_point.x()) < 1.0
        assert abs(screen_point.y() - test_point.y()) < 1.0
    
    def test_world_to_screen_conversion(self, view):
        """ワールド座標からスクリーン座標への変換テスト"""
        # 原点付近のワールド座標
        world_point = QPointF(0, 0)
        
        # ワールド→スクリーン変換
        screen_point = view.mapFromScene(world_point)
        
        # 変換後の座標がスクリーン上の妥当な位置にあることを確認
        # 正確な値はビューのセットアップによって異なるが、スクリーン上に存在するはず
        assert isinstance(screen_point.x(), (int, float))
        assert isinstance(screen_point.y(), (int, float))
        
        # 逆変換（スクリーン→ワールド）
        back_world_point = view.mapToScene(screen_point)
        
        # 元のポイントと比較（許容誤差内）
        assert abs(back_world_point.x() - world_point.x()) < 1.0
        assert abs(back_world_point.y() - world_point.y()) < 1.0
    
    def test_zoom_and_pan_combined(self, view):
        """ズームとパンを組み合わせた基本操作のテスト"""
        # 初期状態を保存
        initial_transform = view.transform()
        
        # 1. まずズームイン
        mock_wheel_event = QWheelEvent(
            QPointF(100, 100),
            QPointF(100, 100),
            QPoint(0, 120),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False
        )
        view.wheelEvent(mock_wheel_event)
        
        # ズーム後の状態を確認
        post_zoom_transform = view.transform()
        assert view.current_zoom > 1.0
        
        # 2. 次にパン
        mock_press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(100, 100),
            QPointF(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mousePressEvent(mock_press_event)
        
        mock_move_event = QMouseEvent(
            QEvent.MouseMove,
            QPointF(150, 150),
            QPointF(150, 150),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseMoveEvent(mock_move_event)
        
        mock_release_event = QMouseEvent(
            QEvent.MouseButtonRelease,
            QPointF(150, 150),
            QPointF(150, 150),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseReleaseEvent(mock_release_event)
        
        # 最終状態を取得
        final_transform = view.transform()
        
        # ズームとパンの両方が適用されていることを確認
        # 1. スケール要素が初期状態から変わっている
        assert final_transform.m11() > initial_transform.m11()
        assert final_transform.m22() > initial_transform.m22()
        
        # 2. 移動要素が単なるズーム後の状態から変わっている
        assert final_transform.m31() != post_zoom_transform.m31()
        assert final_transform.m32() != post_zoom_transform.m32()
        
        # 3. 現在のズームレベルがまだ1.0より大きい
        assert view.current_zoom > 1.0
    
    def test_mouse_tracking(self, view):
        """マウス追跡の基本動作テスト"""
        # 初期状態では、ドラッグ関連のプロパティが存在するが未設定であることを確認
        assert hasattr(view, 'last_mouse_pos')
        assert hasattr(view, 'drag_start_time')
        assert view.drag_start_time is None
        
        # マウス押下（ドラッグ開始）
        mock_press_event = QMouseEvent(
            QEvent.MouseButtonPress,
            QPointF(100, 100),
            QPointF(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mousePressEvent(mock_press_event)
        
        # ドラッグ開始時のプロパティが設定されたことを確認
        assert view.last_mouse_pos.x() == 100
        assert view.last_mouse_pos.y() == 100
        assert view.drag_start_time is not None
        assert view.drag_start_pos.x() == 100
        assert view.drag_start_pos.y() == 100
        
        # マウスリリース（ドラッグ終了）
        mock_release_event = QMouseEvent(
            QEvent.MouseButtonRelease,
            QPointF(150, 150),
            QPointF(150, 150),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier
        )
        view.mouseReleaseEvent(mock_release_event)
        
        # ドラッグ終了時にプロパティがリセットされたことを確認
        assert view.drag_start_time is None
        assert view.drag_start_pos is None

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 