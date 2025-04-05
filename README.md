# DXF Viewer & Triangle Manager

PySide6を使用したDXFファイルビューアと三角形管理アプリケーション

このリポジトリには2つのアプリケーションが含まれています:
1. **DXF Viewer**: DXFファイルを表示・操作するビューア
2. **Triangle Manager**: 三角形の作成・管理を行うツール

## 機能概要

### DXF Viewer (dxf_viewer.py)

- DXFファイルの読み込みと表示
- ズーム・パン操作による表示範囲の調整
- 線幅の調整機能
- 原点表示機能

### Triangle Manager (triangle_ui_app.py)

- 三角形の作成と表示
- 三角形の辺の長さと角度の調整
- 複数の三角形を辺で連結
- 三角形データのDXF形式での出力
- JSONによるデータの保存と読み込み

## 必要条件

- Python 3.9以上
- PySide6
- ezdxf (DXF読み込み・出力用)

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

### DXF Viewerの起動

```bash
python dxf_viewer.py [DXFファイルのパス]
```

#### DXF Viewerの操作方法

- **ファイルを開く**: ボタンクリックでDXFファイルを選択
- **ビューをリセット**: 表示を全体表示に戻す
- **原点表示**: 原点(0,0)を中心にする
- **線幅倍率**: ドロップダウンで線幅を調整
- **マウス操作**: ドラッグでパン、ホイールでズーム

### Triangle Managerの起動

```bash
python triangle_ui_app.py
```

#### Triangle Managerの操作方法

- **三角形追加**: ボタンクリックで三角形を追加
- **辺の選択**: 三角形の辺をクリックして新しい三角形を追加する位置を指定
- **リセット**: すべての三角形をクリア
- **全体表示**: すべての三角形が見えるようにビューを調整
- **DXF出力**: 三角形データをDXFファイルとして出力

## 新機能: DXF出力

Triangle Managerでは、CADソフトで読み込み可能なDXF形式で三角形データを出力できるようになりました。「DXF出力」ボタンをクリックして保存先を指定すると、現在表示されている三角形がDXFファイルとして出力されます。

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