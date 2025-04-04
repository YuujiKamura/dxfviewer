#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
強制黒モード機能のデバッグテスト

グローバル変数FORCE_BLACK_MODEとシングルトンColorSettingsが正しく更新されるかを確認します
"""

import sys
import os

# モジュールへのパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 強制黒モード関連の変数と関数をインポート
print("強制黒モード関連のモジュールをインポートします...")
from core.dxf_colors import FORCE_BLACK_MODE, set_force_black_mode, color_settings

# 初期状態を確認
print(f"初期状態:")
print(f"  FORCE_BLACK_MODE: {FORCE_BLACK_MODE}")
print(f"  color_settings.is_force_black_mode: {color_settings.is_force_black_mode}")

# 強制黒モードを有効化
print("\n強制黒モードを有効にします...")
set_force_black_mode(True)

# 変更後の状態を確認
print(f"有効化後:")
print(f"  FORCE_BLACK_MODE: {FORCE_BLACK_MODE}")
print(f"  color_settings.is_force_black_mode: {color_settings.is_force_black_mode}")

# 強制黒モードを無効化
print("\n強制黒モードを無効にします...")
set_force_black_mode(False)

# 変更後の状態を確認
print(f"無効化後:")
print(f"  FORCE_BLACK_MODE: {FORCE_BLACK_MODE}")
print(f"  color_settings.is_force_black_mode: {color_settings.is_force_black_mode}")

# シングルトンを直接変更してみる
print("\nシングルトンを直接変更してみます...")
color_settings.is_force_black_mode = True
print(f"シングルトン直接変更後:")
print(f"  FORCE_BLACK_MODE: {FORCE_BLACK_MODE}")
print(f"  color_settings.is_force_black_mode: {color_settings.is_force_black_mode}")

# 直接色変換関数を呼び出してみる
print("\n色変換関数を呼び出してみます...")
from core.dxf_colors import convert_dxf_color
print(f"convert_dxf_color(1) = {convert_dxf_color(1)}")

print("\nテスト完了。") 