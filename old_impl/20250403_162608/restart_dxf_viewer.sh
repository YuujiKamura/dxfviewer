#!/bin/bash
# DXFビューア起動スクリプト
# このスクリプトは、DXFビューアを起動するためのシェルスクリプトです。

# 現在のスクリプトの絶対パスを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# カレントディレクトリをスクリプトのディレクトリに変更
cd "$SCRIPT_DIR"

# コマンドライン引数として渡されたDXFファイルを処理
if [ $# -gt 0 ]; then
    # ファイルパスが指定された場合
    FILE_PATH="$1"
    
    # ファイルが存在するかチェック
    if [ -f "$FILE_PATH" ]; then
        echo "DXFファイルを読み込みます: $FILE_PATH"
        python main.py "$FILE_PATH"
    else
        echo "エラー: 指定されたファイルが見つかりません: $FILE_PATH"
        exit 1
    fi
else
    # 引数なしでアプリケーションを起動
    python main.py
fi 