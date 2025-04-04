@echo off
REM DXFビューア起動バッチファイル
REM このバッチファイルは、DXFビューアを起動するためのものです。

REM カレントディレクトリをバッチファイルと同じディレクトリに変更
cd /d "%~dp0"

REM コマンドライン引数をチェック
if "%~1"=="" (
    REM 引数なしでアプリケーションを起動
    python main.py
) else (
    REM ファイルパスが指定された場合
    if exist "%~1" (
        echo DXFファイルを読み込みます: %~1
        python main.py "%~1"
    ) else (
        echo エラー: 指定されたファイルが見つかりません: %~1
        exit /b 1
    )
) 