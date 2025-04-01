# DXF Viewer

PySide6を使用したDXFファイルビューアです。ezdxfライブラリを利用してDXFファイルを読み込み、グラフィカルに表示します。

## 機能

- DXFファイルの読み込みと表示
- ズーム、パン操作によるDXF図面の閲覧
- テーマ切り替え（ダーク、ライト、ブルー）
- 線幅設定のカスタマイズ
- アプリケーションの再起動機能
- ファイルの再読み込み機能
- サンプルDXFファイル作成機能
- スクリーンショット機能

## 必要条件

- Python 3.6以上
- PySide6
- ezdxf

## インストール方法

```bash
pip install PySide6 ezdxf
```

## 使用方法

```bash
python dxf_viewer_pyside6.py [--debug] [--file <DXFファイルパス>]
```

## コマンドラインオプション

- `--debug`: デバッグモードを有効化します
- `--file`: 起動時に開くDXFファイルを指定します
- `--restart`: アプリケーションの再起動フラグ（内部使用）
- `--parent-pid`: 親プロセスのPID（内部使用）

## ライセンス

[MIT License](LICENSE) 