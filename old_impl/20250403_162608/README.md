# DXFビューア

シンプルなDXFファイルビューアアプリケーション。PySide6を使用してDXFファイルを表示します。

## 機能

- DXFファイルの読み込みと表示
- 線、円、円弧、ポリライン、テキストなどの基本的なDXFエンティティの表示
- ズーム、パン操作
- マウスホイールによるズーム
- 中ボタンまたはAlt+左ボタンによるパン

## 必要条件

- Python 3.6以上
- PySide6
- ezdxf

## インストール

1. リポジトリをクローン:
   ```
   git clone https://github.com/yourusername/dxfviewer.git
   cd dxfviewer
   ```

2. 依存パッケージのインストール:
   ```
   pip install PySide6 ezdxf
   ```

## 使用方法

1. アプリケーションの実行:
   ```
   python main.py
   ```

2. コマンドラインからDXFファイルを直接開く:
   ```
   python main.py /path/to/your/file.dxf
   ```

## キーボードショートカット

- `Ctrl+O`: ファイルを開く
- `F`: 表示をリセットし、全体を表示
- `+`: ズームイン
- `-`: ズームアウト
- `Esc`: 選択解除

## プロジェクト構造

```
dxfviewer/
├── core/              # DXFファイル読み込みと内部データ構造
│   ├── __init__.py
│   ├── dxf_entities.py  # DXFエンティティのデータクラス
│   └── dxf_reader.py    # DXFファイル読み込み機能
├── renderer/          # 描画ロジック
│   ├── __init__.py
│   └── renderer.py      # DXFエンティティ描画クラス
├── ui/                # ユーザーインターフェース
│   ├── __init__.py
│   ├── graphics_view.py # カスタムグラフィックスビュー
│   └── main_window.py   # メインウィンドウ
├── main.py            # エントリポイント
├── sample_dxf/        # サンプルDXFファイル
└── old_implementation/  # 古い実装（参考用）
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。 