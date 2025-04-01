@echo off
REM DXF Viewerを再起動するバッチファイル

REM 現在実行中のPythonプロセスのPIDを取得
for /f "tokens=2" %%a in ('tasklist ^| findstr "python"') do (
    set PID=%%a
    goto :found
)

:found
echo 実行中のPython PID: %PID%

REM 新しいプロセスを起動（--restart フラグを使用）
start "" python dxf_viewer_pyside6.py --restart --parent-pid %PID%

REM 少し待機
timeout /t 1 /nobreak > nul

REM 古いプロセスを終了
taskkill /PID %PID% /F

echo DXF Viewerを再起動しました。 