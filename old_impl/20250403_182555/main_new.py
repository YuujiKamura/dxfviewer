#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFビューアのメインプログラム（パン操作検証用）

PySide6を使用したDXFファイルビューアの簡易版です。
パン操作の検証に焦点を当てています。
"""

import sys
import os
import logging
import argparse
from typing import Dict, Any

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui_new.main_window import MainWindow

def setup_logging():
    """ロギングの設定"""
    # ロガーの作成
    logger = logging.getLogger("dxf_viewer")
    logger.setLevel(logging.DEBUG)
    
    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # フォーマッタ
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # ハンドラを追加
    logger.addHandler(console_handler)
    
    # ファイルハンドラ
    try:
        file_handler = logging.FileHandler("dxf_viewer_new.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except:
        logger.warning("ログファイルを作成できませんでした")
    
    return logger

def main():
    """メインプログラム"""
    # ロギングのセットアップ
    logger = setup_logging()
    logger.info("アプリケーション開始 - パン操作検証版")
    
    # 引数の解析
    parser = argparse.ArgumentParser(description="DXFビューアのパン操作検証版")
    parser.add_argument("--file", help="開くDXFファイルのパス")
    args = parser.parse_args()
    
    # アプリケーション設定
    app_settings = {
        "file_path": args.file
    }
    
    # Qtアプリケーション作成
    app = QApplication(sys.argv)
    app.setApplicationName("DXFビューア（パン操作検証）")
    
    # メインウィンドウの作成と表示
    main_window = MainWindow(app_settings)
    main_window.show()
    
    # アプリケーション実行
    exit_code = app.exec()
    
    logger.info(f"アプリケーション終了（コード: {exit_code}）")
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 