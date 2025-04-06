#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Triangle UI アプリケーション

三角形管理UIのメインアプリケーションエントリーポイント
"""

import sys
import logging
from PySide6.QtWidgets import QApplication

# Triangle UIをインポート
from triangle_ui.triangle_manager_ui import TriangleManagerWindow

# ロガー設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    """メイン関数"""
    logger.info("Triangle UIアプリケーションを起動しています...")
    
    # QApplicationのインスタンス作成
    app = QApplication(sys.argv)
    
    # メインウィンドウの作成と表示
    window = TriangleManagerWindow()
    window.show()
    
    # アプリケーションの実行
    logger.info("アプリケーションが起動しました")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 