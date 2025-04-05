# Triangle Manager

三角形の作成・管理と連結表示を行うPython/PySide6アプリケーション

## 機能概要

- 三角形の作成と表示
- 三角形の辺の長さと角度の調整
- 複数の三角形を辺で連結
- 三角形データのDXF形式での出力
- JSONによるデータの保存と読み込み

## 必要条件

- Python 3.9以上
- PySide6
- ezdxf (DXF出力用)

## インストール方法

```bash
# 仮想環境の作成
python -m venv .venv
source .venv/bin/activate  # Linuxの場合
.venv\Scripts\activate     # Windowsの場合

# 依存パッケージのインストール
pip install -r requirements.txt
```

## 使用方法

```bash
python triangle_ui_app.py
```

## 新機能: DXF出力

CADソフトで読み込み可能なDXF形式で三角形データを出力できるようになりました。「DXF出力」ボタンをクリックして保存先を指定すると、現在表示されている三角形がDXFファイルとして出力されます。

出力されるDXFには以下の情報が含まれます：
- 三角形の形状（ポリライン）
- 各辺の長さ（テキスト）

## テスト

アプリケーションには以下の自動テストが含まれています：

```bash
# DXF出力と読み込みの同一性テスト
python -m tests.test_triangle_dxf_export

# JSON保存と読み込みの同一性テスト
python -m tests.test_triangle_dxf_save_load

# 三角形の接続関係のテスト
python -m triangle_ui.test_triangle_connections
```

## ライセンス

MIT 