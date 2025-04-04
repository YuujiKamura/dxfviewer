# DXF Viewer UI テスト群

このディレクトリには、DXF Viewerのユーザーインターフェース要素をテストするためのスクリプト群が含まれています。

## テスト概要

### 1. test_viewer_rendering.py
- **目的**: DXFViewerのレンダリング設定と操作をテスト
- **機能**: 
  - QGraphicsViewの設定が正しく適用されているか確認
  - パン操作のテスト
  - ズーム操作のテスト

### 2. test_perf_rendering.py
- **目的**: レンダリングのパフォーマンスを測定
- **機能**:
  - パン操作の応答速度測定
  - ズーム操作の応答速度測定
  - レンダリング設定の違いによるパフォーマンスへの影響を評価

### 3. simple_pan_test.py
- **目的**: マウスによるパン操作とズーム操作の基本テスト
- **機能**: 
  - 座標系とサンプル円を表示
  - 左ドラッグでパン操作
  - マウスホイールでズーム操作
  - 操作時の変換行列などの詳細をコンソールに出力

## 実行方法

### 通常のユニットテスト

```bash
# レンダリング設定と操作テスト
python tests/test_viewer_rendering.py

# パフォーマンステスト
python tests/test_perf_rendering.py
```

### インタラクティブテスト

インタラクティブモードではユーザーが操作して動作を確認できます：

```bash
# レンダリングテストをインタラクティブモードで実行
python tests/test_viewer_rendering.py --interactive

# パフォーマンステストをインタラクティブモードで実行
python tests/test_perf_rendering.py --interactive

# シンプルなパンテスト
python tests/ui_tests/simple_pan_test.py
```

## 画面操作テスト時の重要設定

QGraphicsViewを継承したクラスで、以下の設定を行うことで描画の問題を解決できます：

```python
# レンダリング品質と更新方式の設定
self.setRenderHint(QPainter.RenderHint.Antialiasing)
self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
```

パンやズーム操作後には明示的な画面更新を要求することも重要です：

```python
# 変換行列更新後
self.viewport().update()
```

## 本番コードへの適用

このテストから得られた知見は、以下の方法で本番のDXF Viewerコードに適用されています：

1. `dxf_ui_adapter.py`に`DXFSceneAdapter`クラスのヘルパーメソッドとして以下を追加:
   - `configure_graphics_view()`: QGraphicsViewのレンダリング設定を最適化
   - `request_viewport_update()`: パン/ズーム操作後のビューポート更新を明示的に要求

2. `dxf_viewer_pyside6.py`の機能強化:
   - `DXFGraphicsView.panBy()`メソッドの改善（ズームレベルを考慮したパン量調整）
   - ビューポート更新の明示的要求を追加 