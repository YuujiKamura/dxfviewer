# DXF Viewer

PySide6を使用したシンプルなDXFファイルビューアです。CADファイル（DXF形式）を読み込み、表示、ズーム・パン操作を行うことができます。

## 機能

* DXFファイルの読み込みと表示
* ズーム、パン操作によるDXF図面の閲覧
* 線幅設定のカスタマイズ
* 原点表示機能
* ファイル情報の表示

## 主要ファイル構成

プロジェクトは以下のようなモジュール構成になっています：

```
dxf_viewer.py           - メインのエントリーポイント・アプリケーション
├── dxf_core/           - DXF処理の中核機能
│   ├── __init__.py     - パッケージ初期化
│   ├── adapter.py      - DXFデータとQt描画の橋渡し
│   ├── parser.py       - DXFファイル解析
│   └── renderer.py     - 描画ロジック
│
├── ui/                 - ユーザーインターフェース
│   ├── __init__.py     - パッケージ初期化
│   ├── graphics_view.py - カスタムグラフィックスビュー
│   ├── main_window.py  - メインウィンドウ（参照用）
│   └── view_utils.py   - ビュー用ユーティリティ
│
├── requirements.txt    - 依存パッケージ
└── simple_samples/     - 実装例・サンプルコード
```

### 依存パッケージ

* PySide6 >= 6.5.0
* ezdxf >= 1.0.0

## インストール方法

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python dxf_viewer.py [--debug] [--file <DXFファイルパス>]
```

### コマンドラインオプション

* `--debug`: デバッグモードを有効化します
* `--file`: 起動時に開くDXFファイルを指定します

## 実験的コード・過去のコード

このリポジトリには、開発過程で作成されたいくつかの実験的実装や重複コードが含まれています。これらは後学のために保存されていますが、現在のプロジェクトでは使用されていません。

### old_impl/

このディレクトリには以下のような過去の実装や実験コードが含まれています：

* `old_implementation/` - 最初期の実装
* `20250403_160516/` - 基本的なグラフィックビューの実験
* `20250403_162608/` - モジュール分割を試みた実装
* `20250403_182555/` - 新しいUIアプローチの実験

### simple_samples/

このディレクトリには、以下のような参考実装やサンプルコードが含まれています：

* `pyside_pan_zoom_sample.py` - PySide6を使用したパン・ズーム実装サンプル
* `pyqt_pan_zoom_sample.py` - PyQtを使用したパン・ズーム実装サンプル
* `tkinter_dxf_viewer.py` - Tkinterを使用したDXFビューア実装
* `tkinter_pan_sample.py` - Tkinterを使用したパン操作サンプル
* `tkinter_rotated_text_sample.py` - Tkinterでの回転テキスト実装サンプル

## プロジェクト構造の解説

### 現在の実装 (dxf_viewer.py)

現在のメイン実装は `dxf_viewer.py` を中心に構成されています。このファイルは以下のモジュールを使用しています：

1. `ui.graphics_view.DxfGraphicsView` - ズーム・パン機能を持つカスタムグラフィックスビュー
2. `dxf_core.parser` - DXFファイルの解析機能
3. `dxf_core.renderer` - 解析したDXFデータの描画機能
4. `dxf_core.adapter` - Qt描画システムとDXFデータの橋渡し

### 実験的な実装 (core/, renderer/)

`core/` と `renderer/` ディレクトリには、より構造化されたアプローチによる実装が含まれていますが、現在のメインアプリケーションでは直接使用されていません。これらは将来の開発のリファレンスとして保持されています。

## ライセンス

MIT License 