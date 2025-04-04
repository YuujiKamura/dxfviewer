#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication, QGraphicsScene
from PySide6.QtCore import QRect, QRectF

# テスト対象のモジュールパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# QApplicationが必要なため、テスト実行前に作成
@pytest.fixture(scope="session")
def qapp():
    """テスト全体で使用するQApplicationのインスタンスを提供するフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # クリーンアップはしない（セッション終了まで保持）

# モック化されたシーン
@pytest.fixture
def mock_scene():
    """テスト用のモックシーンを作成するフィクスチャ
    
    QGraphicsSceneのインスタンスを返し、必要なメソッドをオーバーライドします。
    """
    scene = QGraphicsScene()
    
    # シーンの境界を設定
    scene.setSceneRect(QRectF(0, 0, 1000, 1000))
    
    # 必要に応じてitems()メソッドをオーバーライド
    original_items = scene.items
    scene.items = MagicMock(return_value=[])
    
    # sceneRectメソッドをオーバーライド
    original_sceneRect = scene.sceneRect
    scene.sceneRect = MagicMock(return_value=QRectF(0, 0, 1000, 1000))
    
    return scene 