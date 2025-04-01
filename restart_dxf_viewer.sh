#!/bin/bash
# DXF Viewerを再起動するシェルスクリプト

# 現在実行中のPythonプロセスのPIDを取得
PID=$(tasklist | grep -i python | awk '{print $2}' | head -1)

if [ -z "$PID" ]; then
  echo "実行中のPythonプロセスが見つかりません"
  exit 1
fi

echo "実行中のPython PID: $PID"

# 新しいプロセスを起動（--restart フラグを使用）
python dxf_viewer_pyside6.py --restart --parent-pid $PID &

# 少し待機
sleep 1

# 古いプロセスを終了
taskkill //PID $PID //F

echo "DXF Viewerを再起動しました。" 