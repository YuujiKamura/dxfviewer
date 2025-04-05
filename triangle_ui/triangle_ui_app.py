#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
三角形管理アプリケーション
"""

import sys
import os
import logging
from pathlib import Path

# 親ディレクトリをパスに追加
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

# PySide6のインポート
from PySide6.QtWidgets import QApplication

# triangle_managerからTriangleManagerWindowをインポート
from triangle_ui.triangle_manager import TriangleManagerWindow

# ロガーの設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    """メイン関数"""
    logger.info("Triangle UIアプリケーションを起動しています...")
    
    app = QApplication(sys.argv)
    window = TriangleManagerWindow()
    window.show()
    
    logger.info("アプリケーションが起動しました")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 