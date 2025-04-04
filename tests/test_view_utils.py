#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ビュー操作ユーティリティのテスト

center_view_on_entities、configure_view_for_cadなどの純粋関数をテストします。
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# テスト対象のモジュールへのパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
from ui.view_utils import center_view_on_entities, configure_view_for_cad, request_viewport_update

# PySide6のクラスをモックに置き換え
class MockQtClass:
    """Qtクラスとそのプロパティをモックするクラス"""
    def __init__(self):
        # Qtのモック
        self.AspectRatioMode = MagicMock()
        self.AspectRatioMode.KeepAspectRatio = "AspectRatioMode.KeepAspectRatio"
        self.AspectRatioMode.IgnoreAspectRatio = "AspectRatioMode.IgnoreAspectRatio"
        
        self.ScrollBarPolicy = MagicMock()
        self.ScrollBarPolicy.ScrollBarAlwaysOff = "ScrollBarPolicy.ScrollBarAlwaysOff"

# モックQPainter
class MockQPainterClass:
    """QPainterクラスとそのプロパティをモックするクラス"""
    def __init__(self):
        self.RenderHint = MagicMock()
        self.RenderHint.Antialiasing = "RenderHint.Antialiasing"
        self.RenderHint.SmoothPixmapTransform = "RenderHint.SmoothPixmapTransform"

# モックQt
mock_qt = MockQtClass()

# モックQPainter
mock_qpainter = MockQPainterClass()

# モックQGraphicsViewAnchor
class MockViewportAnchor:
    """ViewportAnchorモック"""
    AnchorViewCenter = "AnchorViewCenter"
    AnchorUnderMouse = "AnchorUnderMouse"

# モックQGraphicsViewモード
class MockViewMode:
    """ViewModeモック"""
    NoDrag = "NoDrag"
    MinimalViewportUpdate = "MinimalViewportUpdate"
    CacheBackground = "CacheBackground"
    DontAdjustForAntialiasing = "DontAdjustForAntialiasing"
    DontSavePainterState = "DontSavePainterState"

# モックQGraphicsView
class MockQGraphicsView:
    """QGraphicsViewのモック"""
    ViewportAnchor = MockViewportAnchor
    DragMode = MockViewMode
    ViewportUpdateMode = MockViewMode
    CacheModeFlag = MockViewMode
    OptimizationFlag = MockViewMode
    
    def __init__(self):
        self.transform_anchor = None
        self.resize_anchor = None
        self.scene_mock = MagicMock()
        self.viewport_mock = MagicMock()
        
        # 呼び出し記録
        self.calls = []
    
    def scene(self):
        return self.scene_mock
    
    def transformationAnchor(self):
        return self.transform_anchor
    
    def setTransformationAnchor(self, anchor):
        self.transform_anchor = anchor
        self.calls.append(('setTransformationAnchor', anchor))
    
    def resizeAnchor(self):
        return self.resize_anchor
    
    def setResizeAnchor(self, anchor):
        self.resize_anchor = anchor
        self.calls.append(('setResizeAnchor', anchor))
    
    def fitInView(self, rect, mode):
        self.calls.append(('fitInView', rect, mode))
    
    def setHorizontalScrollBarPolicy(self, policy):
        self.calls.append(('setHorizontalScrollBarPolicy', policy))
    
    def setVerticalScrollBarPolicy(self, policy):
        self.calls.append(('setVerticalScrollBarPolicy', policy))
    
    def setDragMode(self, mode):
        self.calls.append(('setDragMode', mode))
    
    def setRenderHint(self, hint):
        self.calls.append(('setRenderHint', hint))
    
    def setViewportUpdateMode(self, mode):
        self.calls.append(('setViewportUpdateMode', mode))
    
    def setCacheMode(self, mode):
        self.calls.append(('setCacheMode', mode))
    
    def setOptimizationFlag(self, flag, enabled):
        self.calls.append(('setOptimizationFlag', flag, enabled))
    
    def viewport(self):
        return self.viewport_mock


class TestViewUtils(unittest.TestCase):
    """ビュー操作ユーティリティのテストクラス"""
    
    def setUp(self):
        """各テスト前の準備"""
        # モックを準備
        self.view_mock = MockQGraphicsView()
        
        # モックの境界矩形を作成
        self.empty_rect = MagicMock()
        self.empty_rect.isEmpty.return_value = True
        
        self.valid_rect = MagicMock()
        self.valid_rect.isEmpty.return_value = False
    
    def test_center_view_on_entities_no_scene(self):
        """シーンがない場合のテスト"""
        # シーンをNoneに設定
        self.view_mock.scene_mock = None
        
        # 関数を実行
        result = center_view_on_entities(self.view_mock)
        
        # 結果を検証
        self.assertFalse(result, "シーンがない場合はFalseを返すべき")
        
        # メソッド呼び出しがないことを確認
        self.assertEqual(len(self.view_mock.calls), 0, "シーンがない場合はメソッド呼び出しをしないべき")
    
    def test_center_view_on_entities_empty_rect(self):
        """エンティティがない場合のテスト"""
        # 空の境界矩形を設定
        self.view_mock.scene_mock.itemsBoundingRect.return_value = self.empty_rect
        
        # 関数を実行
        result = center_view_on_entities(self.view_mock)
        
        # 結果を検証
        self.assertFalse(result, "エンティティがない場合はFalseを返すべき")
        
        # メソッド呼び出しを確認
        self.assertEqual(len(self.view_mock.calls), 0, "エンティティがない場合はfitInViewを呼び出さないべき")
    
    def test_center_view_on_entities_success(self):
        """正常にビューを中心化できる場合のテスト"""
        # 有効な境界矩形を設定
        self.view_mock.scene_mock.itemsBoundingRect.return_value = self.valid_rect
        
        # アンカー設定
        self.view_mock.transform_anchor = "OriginalTransformAnchor"
        self.view_mock.resize_anchor = "OriginalResizeAnchor"
        
        # 関数を実行
        with patch('ui.view_utils.Qt', mock_qt):
            result = center_view_on_entities(self.view_mock)
        
        # 結果を検証
        self.assertTrue(result, "正常なケースではTrueを返すべき")
        
        # メソッド呼び出しを検証
        call_names = [call[0] for call in self.view_mock.calls]
        self.assertIn('setTransformationAnchor', call_names, "変換アンカーを設定すべき")
        self.assertIn('setResizeAnchor', call_names, "リサイズアンカーを設定すべき")
        self.assertIn('fitInView', call_names, "fitInViewを呼び出すべき")
        
        # アンカーが元に戻されていることを確認
        self.assertEqual(self.view_mock.transform_anchor, "OriginalTransformAnchor", "変換アンカーを元に戻すべき")
        self.assertEqual(self.view_mock.resize_anchor, "OriginalResizeAnchor", "リサイズアンカーを元に戻すべき")
        
        # 正しい順序で呼び出されていることを確認
        set_transform_index = call_names.index('setTransformationAnchor')
        set_resize_index = call_names.index('setResizeAnchor')
        fit_in_view_index = call_names.index('fitInView')
        
        self.assertTrue(set_transform_index < fit_in_view_index, "アンカー設定はfitInViewの前に行うべき")
        self.assertTrue(set_resize_index < fit_in_view_index, "アンカー設定はfitInViewの前に行うべき")
    
    def test_configure_view_for_cad(self):
        """CAD表示設定のテスト"""
        # 関数を実行
        with patch('ui.view_utils.Qt', mock_qt), patch('ui.view_utils.QPainter', mock_qpainter):
            configure_view_for_cad(self.view_mock)
        
        # 呼び出されるべきメソッド
        expected_methods = [
            'setHorizontalScrollBarPolicy',
            'setVerticalScrollBarPolicy',
            'setDragMode',
            'setTransformationAnchor',
            'setResizeAnchor',
            'setRenderHint',
            'setViewportUpdateMode',
            'setCacheMode',
            'setOptimizationFlag'
        ]
        
        # メソッド呼び出しを検証
        call_names = [call[0] for call in self.view_mock.calls]
        for method in expected_methods:
            self.assertIn(method, call_names, f"{method}が呼び出されるべき")
    
    def test_request_viewport_update(self):
        """ビューポート更新要求のテスト"""
        # 関数を実行
        request_viewport_update(self.view_mock)
        
        # viewportメソッドが呼び出されたことを確認
        self.view_mock.viewport_mock.update.assert_called_once()


if __name__ == '__main__':
    unittest.main() 