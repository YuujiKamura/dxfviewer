#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ビューのセンタリング機能のデバッグ用自動テスト

このスクリプトは、center_view_on_entities関数の動作を自動的にテストし、
詳細なログを取得するためのものです。
"""

import sys
import logging
import io
from contextlib import redirect_stdout, redirect_stderr
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem
from PySide6.QtCore import QRectF, QPointF
from PySide6.QtGui import QTransform

# テスト対象のモジュールをインポート
sys.path.append('.')  # プロジェクトルートからの相対パスを解決できるようにする
from ui.view_utils import center_view_on_entities

def setup_logging():
    """テスト用のロギング設定"""
    logger = logging.getLogger("dxf_viewer")
    logger.setLevel(logging.DEBUG)
    
    # すべてのハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 文字列IOへ出力するハンドラを追加
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger, log_stream

def run_center_view_test(test_name, setup_func):
    """
    中心化テストを実行する関数
    
    Args:
        test_name: テスト名
        setup_func: テスト環境をセットアップする関数
        
    Returns:
        dict: テスト結果を含む辞書
    """
    print(f"\n=== テスト実行: {test_name} ===")
    
    # ロギングのセットアップ
    logger, log_stream = setup_logging()
    
    # Qtアプリケーションの初期化
    app = QApplication.instance() or QApplication(sys.argv)
    
    # テスト環境のセットアップ
    view, scene, items_rect = setup_func()
    
    # 画面に表示（非表示だとレイアウトが計算されない場合がある）
    view.show()
    
    # イベントループを少し回してレイアウトを確定させる
    for _ in range(5):
        app.processEvents()
    
    # テスト対象の関数を実行
    success = center_view_on_entities(view, items_rect)
    
    # イベントループを処理して、ビューの更新を完了させる
    for _ in range(10):
        app.processEvents()
    
    # テスト結果を収集
    logs = log_stream.getvalue()
    
    # 現在のビュー状態を取得
    viewport_rect = view.viewport().rect()
    viewport_center = viewport_rect.center()
    scene_center = view.mapToScene(viewport_center)
    
    # アイテム中心と最終ビュー中心の差を計算
    if items_rect and not items_rect.isEmpty():
        items_center = items_rect.center()
        error_x = abs(items_center.x() - scene_center.x())
        error_y = abs(items_center.y() - scene_center.y())
    else:
        error_x = error_y = float('nan')
    
    # テスト結果をまとめる
    result = {
        "test_name": test_name,
        "success": success,
        "logs": logs,
        "items_rect": items_rect,
        "viewport_center": viewport_center,
        "scene_center": scene_center,
        "error_x": error_x,
        "error_y": error_y,
        "h_scrollbar": view.horizontalScrollBar().value(),
        "v_scrollbar": view.verticalScrollBar().value(),
        "transform": view.transform()
    }
    
    # クリーンアップ
    view.hide()
    view.deleteLater()
    
    print(f"テスト完了: {test_name}")
    print(f"成功: {success}")
    print(f"X誤差: {error_x:.2f}, Y誤差: {error_y:.2f}")
    
    return result

def setup_rectangle_test():
    """単一の長方形をシーンに配置するテスト環境"""
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.resize(800, 600)
    
    # テスト用の長方形を追加
    rect_item = QGraphicsRectItem(0, 0, 100, 50)
    scene.addItem(rect_item)
    
    # アイテムの範囲を直接指定
    items_rect = QRectF(0, 0, 100, 50)
    
    return view, scene, items_rect

def setup_offset_rectangle_test():
    """オフセット位置に長方形を配置するテスト環境"""
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.resize(800, 600)
    
    # オフセット位置に長方形を追加
    rect_item = QGraphicsRectItem(200, 150, 100, 50)
    scene.addItem(rect_item)
    
    # アイテムの範囲を直接指定
    items_rect = QRectF(200, 150, 100, 50)
    
    return view, scene, items_rect

def setup_multiple_items_test():
    """複数アイテムを配置するテスト環境"""
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.resize(800, 600)
    
    # 複数のアイテムを追加
    scene.addItem(QGraphicsRectItem(50, 50, 100, 100))
    scene.addItem(QGraphicsRectItem(200, 150, 150, 75))
    scene.addItem(QGraphicsRectItem(100, 250, 80, 60))
    
    # シーン全体のアイテム範囲を使用
    items_rect = scene.itemsBoundingRect()
    
    return view, scene, items_rect

def run_all_tests():
    """すべてのテストを実行"""
    results = []
    
    results.append(run_center_view_test("単一長方形のセンタリング", setup_rectangle_test))
    results.append(run_center_view_test("オフセット長方形のセンタリング", setup_offset_rectangle_test))
    results.append(run_center_view_test("複数アイテムのセンタリング", setup_multiple_items_test))
    
    return results

def analyze_results(results):
    """テスト結果を分析して問題点を特定"""
    print("\n=== テスト結果分析 ===")
    
    for result in results:
        print(f"\nテスト: {result['test_name']}")
        print(f"成功: {result['success']}")
        print(f"X誤差: {result['error_x']:.2f}, Y誤差: {result['error_y']:.2f}")
        print(f"スクロールバー位置: 水平={result['h_scrollbar']}, 垂直={result['v_scrollbar']}")
        
        # 主要なログメッセージを抽出して表示
        important_log_lines = [
            line for line in result["logs"].split('\n') 
            if any(key in line for key in [
                "アイテム中心", "ビュー中心", "差分", "スクロールバー位置", "センタリング誤差"
            ])
        ]
        
        print("\n重要なログ:")
        for line in important_log_lines:
            print(f"  {line}")
    
    # 問題の特定
    print("\n=== 問題分析 ===")
    any_large_error = False
    
    for result in results:
        if result["error_x"] > 1.0 or result["error_y"] > 1.0:
            any_large_error = True
            print(f"テスト「{result['test_name']}」でセンタリング誤差が大きすぎます")
            print(f"  X誤差: {result['error_x']:.2f}, Y誤差: {result['error_y']:.2f}")
    
    if not any_large_error:
        print("すべてのテストでセンタリングが正常に機能しています")

if __name__ == "__main__":
    results = run_all_tests()
    analyze_results(results)
    print("\nテスト完了") 