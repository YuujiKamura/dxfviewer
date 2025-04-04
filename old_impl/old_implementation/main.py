#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXFビューアのメインプログラム

PySide6を使用したDXFファイルビューアの実行スクリプトです。
"""

import sys
import os
import logging
import argparse
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.main_window import MainWindow

def setup_logging():
    """ロギングの設定"""
    logger = logging.getLogger("dxf_viewer")
    logger.setLevel(logging.DEBUG)  # 常にDEBUGレベルに設定
    
    # コンソールハンドラ
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)  # ハンドラもDEBUGレベルに設定
    
    # フォーマッタ
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    
    # ファイルハンドラ
    fh = logging.FileHandler("dxf_viewer.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    
    # ハンドラを追加
    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger

def main():
    """メインプログラム"""
    # ロギングのセットアップ
    logger = setup_logging()
    logger.info("アプリケーション開始")
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='DXF Viewerアプリケーション')
    parser.add_argument('--file', help='開くDXFファイルのパス')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効にする')
    args = parser.parse_args()
    
    # アプリケーション設定
    app_settings = {
        'file_path': args.file,
        'debug_mode': args.debug
    }
    
    # Qtアプリケーション作成
    app = QApplication(sys.argv)
    app.setApplicationName("DXFビューア")
    
    # ハイDPIスケーリングを有効化
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # メインウィンドウ作成
    main_window = MainWindow(app_settings)
    main_window.show()
    
    # アプリケーション実行
    exit_code = app.exec()
    
    logger.info(f"アプリケーション終了 (コード: {exit_code})")
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 