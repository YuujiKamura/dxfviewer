#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF Viewer - CADファイルビューア

PySide6を使用したDXFファイルビューアアプリケーション
"""

import os
import sys
# カレントディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import time
import argparse
import logging
import platform
import subprocess
import threading
import signal
import traceback
import json
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

# PySide6のインポート
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QFileDialog, QPushButton, QLabel, QMessageBox, QGraphicsScene, QGraphicsItem, QStatusBar, QComboBox, QDialog, 
    QTextEdit, QCheckBox, QSlider, QGroupBox, QSpinBox, QSizePolicy
)
from ui.graphics_view import DxfGraphicsView
from PySide6.QtGui import (
    QAction, QColor, QPen, QBrush, QTransform, QPainterPath, 
    QPolygonF, QFont, QFontMetricsF, QImage, QPainter, QClipboard,
    QPixmap
)
from PySide6.QtCore import (
    QPointF, QRectF, QLineF, Qt, QTimer, QFileSystemWatcher, QSize,
    QSettings
)

# ezdxfのインポート
try:
    import ezdxf
    # Vectorクラスをインポート
    try:
        from ezdxf.math import Vector as DxfVector
    except ImportError:
        try:
            # _vectorファイルから直接インポート
            from ezdxf.math._vector import Vector
        except ImportError:
            # 代替の定義（簡易版）
            class Vector:
                def __init__(self, x=0, y=0, z=0):
                    self.x = x
                    self.y = y
                    self.z = z
    from ezdxf import recover
    EZDXF_AVAILABLE = True
except ImportError as e:
    print(f"ezdxfモジュールのインポートエラー: {e}")
    print("pip install ezdxf を実行してインストールしてください。")
    EZDXF_AVAILABLE = False

# 基本設定
APP_NAME = "DXF Viewer (PySide6版)"
APP_VERSION = "1.0"
DEFAULT_LINE_WIDTH = 20.0
DEFAULT_LINE_WIDTH_MIN = 1.0
DEFAULT_LINE_WIDTH_MAX = 20.0

# ロガーの設定
logger = None
log_file = "dxf_viewer.log"
lock_file = "dxf_viewer.lock"

# 設定の保存と読み込み用のクラス
class AppSettings:
    """アプリケーション設定を管理するクラス"""
    
    def __init__(self):
        self.settings = QSettings("DXFViewer", "PySide6")
        # 強制線幅モードを無効化し、線幅倍率を導入
        self.force_linewidth = False
        self.linewidth_scale = 3.0  # 線幅の表示倍率を1.5から3.0に変更
    
    def load_line_width(self):
        # DXFの本来の線幅を使用し、表示用の倍率を適用
        base_width = self.settings.value("line_width", DEFAULT_LINE_WIDTH, type=float)
        logger.info(f"線幅設定：基本線幅 {base_width} × 倍率 {self.linewidth_scale}")
        return base_width
    
    def get_line_width_scale(self):
        """線幅表示倍率を取得"""
        return self.linewidth_scale

# ロギング関数
def setup_logger(debug_mode=False):
    """ロガーの設定をセットアップ"""
    global log_file
    
    # ロガーの作成
    logger = logging.getLogger('DXFViewer')
    
    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # デバッグモードならDEBUG、そうでなければINFOレベル
    logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    
    # ログのフォーマット設定
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    
    # コンソールへの出力設定
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    logger.addHandler(console_handler)
    
    # ログファイルの設定
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dxf_viewer.log")
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # ファイルには常にDEBUGレベルで出力
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"ログファイルのセットアップに失敗しました: {str(e)}")
    
    # デバッグモードなら詳細なメッセージを表示
    if debug_mode:
        logger.debug("デバッグモードが有効です")
        logger.debug(f"Python: {sys.version}")
        logger.debug(f"OS: {platform.platform()}")
        logger.debug(f"カレントディレクトリ: {os.getcwd()}")
    
    return logger

# コマンドライン引数の解析
def parse_arguments():
    parser = argparse.ArgumentParser(description=f'{APP_NAME} - DXFファイルビューア')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効化')
    parser.add_argument('--file', type=str, help='起動時に開くDXFファイル')
    parser.add_argument('--restart', action='store_true', help='アプリケーションの再起動フラグ')
    parser.add_argument('--parent-pid', type=int, help='親プロセスのPID')
    return parser.parse_args()

# グローバル変数初期化
args = parse_arguments()
logger = setup_logger(debug_mode=args.debug)

# シングルインスタンス管理（一時的に無効化）
def check_single_instance():
    """
    アプリケーションの重複起動をチェック
    すでに実行中なら警告してTrueを返す
    """
    # 常に実行を許可する（シングルインスタンス検出を無効化）
    return False
    
    # 以下の元の実装はコメントアウト
    """
    # ロックファイルのパス
    lock_file = os.path.join(tempfile.gettempdir(), 'dxf_viewer.lock')
    
    try:
        # ロックファイルが存在するか確認
        if os.path.exists(lock_file):
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            # プロセスが実行中か確認
            if psutil.pid_exists(pid):
                logger.warning(f"既に他のインスタンスが実行中です。終了します。")
                return True
            else:
                # ロックファイルが存在するがプロセスは実行されていない場合、ロックファイルを削除
                os.remove(lock_file)
        
        # 新しいロックファイルを作成
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        return False
    except Exception as e:
        # エラーが発生した場合は、安全のため重複起動とみなさない
        logger.error(f"シングルインスタンス検出中にエラー: {e}")
        return False
    """

# DXF情報関連の純粋関数
def get_dxf_version_info(doc):
    return f"<p><b>DXFバージョン:</b> {doc.dxfversion}</p>"

def get_dxf_layer_info(doc):
    layers = doc.layers
    info = [f"<p><b>レイヤー数:</b> {len(layers)}</p>", "<p><b>レイヤー一覧:</b></p><ul>"]
    for layer in layers:
        info.append(f"<li>{layer.dxf.name} (色: {layer.dxf.color})</li>")
    info.append("</ul>")
    return "".join(info)

def get_dxf_entity_count_info(doc):
    msp = doc.modelspace()
    entity_count = len(list(msp))
    return f"<p><b>エンティティ総数:</b> {entity_count}</p>"

def get_dxf_entity_types_info(doc):
    msp = doc.modelspace()
    entity_types = {}
    for entity in msp:
        entity_type = entity.dxftype()
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    
    info = ["<p><b>エンティティタイプ:</b></p><ul>"]
    for entity_type, count in entity_types.items():
        info.append(f"<li>{entity_type}: {count}個</li>")
    info.append("</ul>")
    return "".join(info)

def create_dxf_info_html(doc):
    info = ["<h3>DXFファイル情報</h3>"]
    info.append(get_dxf_version_info(doc))
    info.append(get_dxf_layer_info(doc))
    info.append(get_dxf_entity_count_info(doc))
    info.append(get_dxf_entity_types_info(doc))
    return "".join(info)

# DXF描画関連の純粋関数
def get_entity_lineweight(entity, app_settings, default_width=None):
    """エンティティの線幅を取得（純粋関数）"""
    # テスト用コードを削除し、本来のロジックを有効化
    if default_width is None:
        default_width = app_settings.load_line_width()
    
    # pure_dxf_functionsモジュールをインポート（存在しない場合は直接ロジックを使用）
    try:
        from old_impl.old_implementation.pure_dxf_functions import pdf
        return pdf.calculate_lineweight(entity, default_width)
    except ImportError:
        # 直接ロジックを実装（pure_dxf_functionsが利用できない場合）
        if hasattr(entity.dxf, 'lineweight'):
            lw = entity.dxf.lineweight
            if lw > 0:
                return max(lw / 10.0, DEFAULT_LINE_WIDTH_MIN)
            elif lw == -3 and hasattr(entity.dxf, 'layer'):
                layer_name = entity.dxf.layer
                if hasattr(entity, 'doc') and entity.doc:
                    layer = entity.doc.layers.get(layer_name)
                    if layer and hasattr(layer.dxf, 'lineweight') and layer.dxf.lineweight > 0:
                        return max(layer.dxf.lineweight / 10.0, DEFAULT_LINE_WIDTH_MIN)
        return default_width

def create_line(scene, start, end, color, entity=None, app_settings=None):
    # 線幅の取得（エンティティが提供されている場合）
    line_width = get_entity_lineweight(entity, app_settings) if entity else DEFAULT_LINE_WIDTH
    
    # ペンの設定
    pen = QPen(color)
    pen.setWidthF(line_width)
    
    # 線の作成
    line = scene.addLine(QLineF(QPointF(start[0], -start[1]), QPointF(end[0], -end[1])), pen)
    line.setFlag(QGraphicsItem.ItemIsSelectable)
    
    return line

def create_circle(scene, center, radius, color, entity=None, app_settings=None):
    # 線幅の取得
    line_width = get_entity_lineweight(entity, app_settings) if entity else DEFAULT_LINE_WIDTH
    
    # ペンの設定
    pen = QPen(color)
    pen.setWidthF(line_width)
    
    # 円の作成（中心から半径を引いた位置に配置）
    x, y = center[0] - radius, -center[1] - radius
    circle = scene.addEllipse(QRectF(x, y, radius * 2, radius * 2), pen)
    circle.setFlag(QGraphicsItem.ItemIsSelectable)
    
    return circle

def create_arc(scene, center, radius, start_angle, end_angle, color, entity=None, app_settings=None):
    # 線幅の取得
    line_width = get_entity_lineweight(entity, app_settings) if entity else DEFAULT_LINE_WIDTH
    
    # ペンの設定
    pen = QPen(color)
    pen.setWidthF(line_width)
    
    # 角度の調整（DXFは反時計回り、Qtは時計回り）
    # また、DXFは東（右）から開始、Qtは北（上）から開始
    qt_start_angle = (90 - start_angle) % 360
    qt_span_angle = ((start_angle - end_angle) % 360)
    
    # 円の中心から左上の座標に変換
    x, y = center[0] - radius, -center[1] - radius
    
    # 円弧の作成
    arc_path = QPainterPath()
    rect = QRectF(x, y, radius * 2, radius * 2)
    arc_path.arcMoveTo(rect, qt_start_angle)
    arc_path.arcTo(rect, qt_start_angle, -qt_span_angle)
    
    arc = scene.addPath(arc_path, pen)
    arc.setFlag(QGraphicsItem.ItemIsSelectable)
    
    return arc

def create_polyline(scene, points, color, entity=None, app_settings=None):
    # 線幅の取得
    line_width = get_entity_lineweight(entity, app_settings) if entity else DEFAULT_LINE_WIDTH
    
    # ペンの設定
    pen = QPen(color)
    pen.setWidthF(line_width)
    
    # ポリラインのパスを作成
    path = QPainterPath()
    
    # 座標変換（y座標の反転）
    transformed_points = [(p[0], -p[1]) for p in points]
    
    if transformed_points:
        path.moveTo(QPointF(transformed_points[0][0], transformed_points[0][1]))
        for point in transformed_points[1:]:
            path.lineTo(QPointF(point[0], point[1]))
    
    # 閉じたポリラインかどうかチェック
    if hasattr(entity, 'is_closed') and entity.is_closed:
        path.closeSubpath()
    
    polyline = scene.addPath(path, pen)
    polyline.setFlag(QGraphicsItem.ItemIsSelectable)
    
    return polyline

def create_text(scene, text, pos, height, color, entity=None):
    # テキストアイテムの作成
    text_item = scene.addText(text, QFont("Arial", height))
    
    # 基本的な配置と色の設定
    text_item.setPos(pos[0], -pos[1] - text_item.boundingRect().height())  # デフォルトは下揃え
    text_item.setDefaultTextColor(color)
    
    # エンティティが提供されている場合は追加の属性を適用
    if entity:
        # デバッグ用：エンティティのすべての属性を表示
        if 'logger' in globals() and logger is not None:
            logger.debug(f"テキストエンティティの属性: {text}")
            for attrib_name in dir(entity.dxf):
                if not attrib_name.startswith('_') and not callable(getattr(entity.dxf, attrib_name)):
                    try:
                        attrib_value = getattr(entity.dxf, attrib_name)
                        logger.debug(f"  {attrib_name}: {attrib_value}")
                    except:
                        pass
        
        width = text_item.boundingRect().width()
        height = text_item.boundingRect().height()
        
        # ezdxfによると、halignの値は:
        # 0 = 左揃え、1 = 不明、2 = 右揃え、3 = アライン、4 = 中央、5 = フィット
        # valignの値は:
        # 0 = ベースライン、1 = 下揃え、2 = 中央揃え、3 = 上揃え
        
        # 水平方向の配置（halign）
        h_align = 0  # デフォルト: 左揃え
        if hasattr(entity.dxf, 'halign'):
            h_align = entity.dxf.halign
            logger.debug(f"  halign属性を直接使用: {h_align}")
        
        # 垂直方向の配置（valign）
        v_align = 0  # デフォルト: ベースライン
        if hasattr(entity.dxf, 'valign'):
            v_align = entity.dxf.valign
            logger.debug(f"  valign属性を直接使用: {v_align}")
        
        # align_pointがある場合は位置を調整
        align_point = None
        if hasattr(entity.dxf, 'align_point') and entity.dxf.align_point:
            align_point = entity.dxf.align_point
            logger.debug(f"  align_point: {align_point}")
            
            # align_pointがあり、halignが0以外の場合はalign_pointを使用
            if h_align != 0:
                pos = (align_point.x, align_point.y)
                logger.debug(f"  align_pointを使用して位置を更新: ({pos[0]}, {pos[1]})")
                # 基本位置を再設定
                text_item.setPos(pos[0], -pos[1] - text_item.boundingRect().height())
        
        # text_generation_flagの処理
        text_gen = 0
        if hasattr(entity.dxf, 'text_generation_flag'):
            text_gen = entity.dxf.text_generation_flag
            logger.debug(f"  text_generation_flag: {text_gen}")
            # ミラーリング処理はここで追加できます
            # if text_gen & 2:  # X方向ミラー
            # if text_gen & 4:  # Y方向ミラー
        
        # テキストの回転
        if hasattr(entity.dxf, 'rotation') and entity.dxf.rotation:
            # Qtの回転は時計回りなので、DXFの反時計回り回転を変換
            rotation = -entity.dxf.rotation
            logger.debug(f"  rotation: {rotation}")
            
            # 回転の中心点を設定
            if h_align == 0:  # 左揃え
                text_item.setTransformOriginPoint(0, height)
            elif h_align == 2:  # 右揃え
                text_item.setTransformOriginPoint(width, height)
            elif h_align == 4:  # 中央揃え
                text_item.setTransformOriginPoint(width/2, height/2)
            else:
                text_item.setTransformOriginPoint(0, height)
                
            text_item.setRotation(rotation)
        
        # 水平方向の配置を適用
        if h_align == 0:  # 左揃え
            # デフォルト位置をそのまま使用
            pass
        elif h_align == 1:  # 特殊なケース
            # ezdxfのドキュメントではhalign=1の定義が不明確
            # 実験的に、これはTEXTエンティティの特殊なケースかもしれない
            # CADファイルのTEXTエンティティではhalign=1が多用されているようだ
            logger.debug(f"  halign=1の特殊処理を適用")
            # 配置は align_point と insert の関係に依存する可能性がある
            if align_point and hasattr(entity.dxf, 'insert'):
                # align_pointとinsertがある場合、適切な配置を試みる
                dx = align_point.x - entity.dxf.insert.x
                dy = align_point.y - entity.dxf.insert.y
                if abs(dx) > abs(dy):  # 水平方向の差が大きい
                    if dx > 0:  # align_pointがinsertより右にある
                        text_item.setPos(pos[0] - width, text_item.y())  # 右揃え
                    else:  # align_pointがinsertより左にある
                        pass  # 左揃えのままにする
                else:  # 垂直方向の差が大きい
                    text_item.setPos(pos[0] - width/2, text_item.y())  # 中央揃え
            else:
                # align_pointがない場合、少し右に寄せる処理を試みる（実験的）
                text_item.setPos(pos[0] + width * 0.1, text_item.y())
        elif h_align == 2:  # 右揃え
            text_item.setPos(pos[0] - width, text_item.y())
        elif h_align == 4:  # 中央揃え (Middle)
            text_item.setPos(pos[0] - width/2, text_item.y())
        elif h_align == 3 or h_align == 5:  # アライン/フィット
            # align_pointがある場合は、二点間に揃える特殊処理
            if align_point and hasattr(entity.dxf, 'insert'):
                # 処理は複雑なので基本的な処理のみ実装
                # 二点間の中央に配置
                p1 = entity.dxf.insert
                p2 = align_point
                mid_x = (p1.x + p2.x) / 2
                mid_y = (p1.y + p2.y) / 2
                text_item.setPos(mid_x - width/2, -mid_y - height/2)
        
        # 垂直方向の配置を適用
        if v_align == 0:  # ベースライン
            # DXFのベースラインは少し複雑なので、近似として下揃えを使用
            text_item.setPos(text_item.x(), -pos[1] - height)
        elif v_align == 1:  # 下揃え - DXFでは下揃えですが、元の実装に戻す
            text_item.setPos(text_item.x(), -pos[1] - height)
        elif v_align == 2:  # 中央揃え
            text_item.setPos(text_item.x(), -pos[1] - height/2)
        elif v_align == 3:  # 上揃え - DXFでは上揃えですが、元の実装に戻す
            text_item.setPos(text_item.x(), -pos[1])
        
        # デバッグログ
        logger.debug(f"テキスト配置: \"{text}\", 位置({pos[0]}, {pos[1]}), 配置(H:{h_align}, V:{v_align}), 回転: {entity.dxf.rotation if hasattr(entity.dxf, 'rotation') else 0}")
    
    return f"TEXT描画: \"{text}\", 位置({pos[0]}, {pos[1]}), 高さ={height}"

# サンプルDXF作成関数
def create_sample_dxf(filename):
    """サンプルDXFファイルを作成（純粋関数に委譲）"""
    try:
        # pure_dxf_functionsモジュールをインポート
        from old_impl.old_implementation.pure_dxf_functions import pdf
        return pdf.create_sample_dxf(filename)
    except ImportError:
        # モジュールがインポートできない場合はエラーを返す
        return None, "pure_dxf_functions モジュールをインポートできません"

# DXFファイル読み込み関数
def load_dxf_file(filename):
    try:
        doc = ezdxf.readfile(filename)
        return doc, None
    except Exception as e:
        error_details = traceback.format_exc()
        return None, (str(e), error_details)

# エンティティ描画関数
def process_dxf_entity(scene, entity, line_color, app_settings=None):
    """DXFエンティティを処理して描画アイテムを作成"""
    try:
        # PySide6とpure_dxf_functionsの橋渡しをするアダプターを作成
        from old_impl.old_implementation.dxf_ui_adapter import create_dxf_adapter
        adapter = create_dxf_adapter(scene)
        item, result_message = adapter.process_dxf_entity(entity, line_color)
        
        if item is None:
            return None, (result_message, traceback.format_exc(), entity.dxftype() if hasattr(entity, 'dxftype') else "不明")
        
        return result_message, None
    except ImportError:
        # dxf_ui_adapterが使用できない場合は、既存のコードを実行
        try:
            entity_type = entity.dxftype()
            entity_result = f"エンティティ {entity_type} を処理"
            
            if entity_type == 'LINE':
                start = (entity.dxf.start.x, entity.dxf.start.y)
                end = (entity.dxf.end.x, entity.dxf.end.y)
                create_line(scene, start, end, line_color, entity, app_settings)
                
            elif entity_type == 'CIRCLE':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                create_circle(scene, center, radius, line_color, entity, app_settings)
                
            elif entity_type == 'ARC':
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                create_arc(scene, center, radius, start_angle, end_angle, line_color, entity, app_settings)
                
            elif entity_type == 'POLYLINE' or entity_type == 'LWPOLYLINE':
                # ポリラインの頂点を取得
                if entity_type == 'LWPOLYLINE':
                    # LWポリラインは直接座標を持っている
                    points = [(point[0], point[1]) for point in entity.get_points()]
                else:
                    # 通常のポリラインは頂点オブジェクトを持っている
                    points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
                
                create_polyline(scene, points, line_color, entity, app_settings)
                
            elif entity_type == 'TEXT' or entity_type == 'MTEXT':
                # テキストの処理
                if entity_type == 'TEXT':
                    text = entity.dxf.text
                    pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                    height = entity.dxf.height
                else:  # MTEXT
                    text = entity.text
                    pos = (entity.dxf.insert.x, entity.dxf.insert.y)
                    height = entity.dxf.char_height
                
                create_text(scene, text, pos, height, line_color, entity)
                
            else:
                # 未対応のエンティティタイプ
                entity_result = f"未対応のエンティティタイプ: {entity_type}"
            
            return entity_result, None
                
        except Exception as e:
            error_details = traceback.format_exc()
            entity_type = entity.dxftype() if hasattr(entity, 'dxftype') else "不明"
            return None, (f"エンティティの処理中にエラーが発生: {str(e)}", error_details, entity_type)

# DXF Viewer コアクラス

class DXFViewer(QMainWindow):
    """DXFファイルビューアのメインウィンドウクラス"""
    
    def __init__(self, settings):
        super().__init__()
        
        self.settings = settings
        self.file_path = settings.get('file_path')
        self.debug_mode = settings.get('debug_mode', False)
        
        # ウィンドウ設定
        self.setWindowTitle(f"DXF Viewer - {os.path.basename(self.file_path) if self.file_path else 'No File'}")
        self.resize(1200, 800)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # グラフィックビューの作成（カスタムクラスを使用）
        self.view = DxfGraphicsView()
        layout.addWidget(self.view)
        
        # 原点にクロスラインを描画
        self.draw_origin_crosslines()
        
        # DXFファイルが指定されている場合は読み込む
        if self.file_path:
            self.load_dxf_file(self.file_path)
        
        # ステータスバーの設定
        self.statusBar().showMessage("Ready")
        
        # ファイル情報ラベル
        self.info_label = QLabel()
        self.statusBar().addPermanentWidget(self.info_label)
        
        # ユーザーインターフェースのセットアップ
        self.setup_ui()
        
        # ログ初期化
        logger.info(f"DXF Viewerを初期化しました。ファイル: {self.file_path}")

    def draw_origin_crosslines(self):
        """原点にクロスラインを描画する"""
        # 描画サイズ
        line_length = 1000
        
        # X軸（赤）
        pen_x = QPen(QColor(255, 0, 0))  # 赤
        pen_x.setWidth(2)
        self.view.scene().addLine(-line_length, 0, line_length, 0, pen_x)
        
        # Y軸（緑）
        pen_y = QPen(QColor(0, 255, 0))  # 緑
        pen_y.setWidth(2)
        self.view.scene().addLine(0, -line_length, 0, line_length, pen_y)
        
        # 原点マーク（青い円）
        pen_origin = QPen(QColor(0, 0, 255))  # 青
        pen_origin.setWidth(2)
        self.view.scene().addEllipse(-10, -10, 20, 20, pen_origin)
        
        # シーンの範囲を設定
        self.view.scene().setSceneRect(-line_length, -line_length, line_length * 2, line_length * 2)
        
        logger.debug("原点クロスラインを描画しました")

    def setup_ui(self):
        """ユーザーインターフェースのセットアップ"""
        # メニューバーの作成
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu('ファイル')
        
        # ファイルを開く
        open_action = QAction('開く...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        
        # 終了
        exit_action = QAction('終了', self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 表示メニュー
        view_menu = menubar.addMenu('表示')
        
        # 全体表示
        fit_action = QAction('全体表示', self)
        fit_action.setShortcut('F')
        fit_action.triggered.connect(self.fit_to_view)
        view_menu.addAction(fit_action)
        
        # ツールバーの作成
        toolbar = self.addToolBar('メインツールバー')
        toolbar.addAction(open_action)
        toolbar.addAction(fit_action)
        
        # ズームインボタン
        zoom_in_action = QAction('拡大', self)
        zoom_in_action.setShortcut('+')
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        view_menu.addAction(zoom_in_action)
        
        # ズームアウトボタン
        zoom_out_action = QAction('縮小', self)
        zoom_out_action.setShortcut('-')
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        view_menu.addAction(zoom_out_action)

    def load_dxf_file(self, file_path):
        """DXFファイルを読み込み、シーンに描画する"""
        try:
            logger.info(f"DXFファイル読み込み開始: {file_path}")
            
            # DXFファイルのパース
            dxf_data = parse_dxf_file(file_path)
            
            # シーンクリア
            self.view.scene().clear()
            
            # 原点クロスライン再描画
            self.draw_origin_crosslines()
            
            # DXFデータの描画
            draw_dxf_entities(self.view.scene(), dxf_data)
            
            # 表示範囲の調整
            self.fit_to_view()
            
            # ファイル情報の更新
            self.update_file_info(dxf_data)
            
            # 成功メッセージ
            self.statusBar().showMessage(f"DXFファイルを読み込みました: {os.path.basename(file_path)}")
            logger.info(f"DXFファイル読み込み成功: {file_path}")
            
        except Exception as e:
            # エラーメッセージ
            error_msg = f"DXFファイルの読み込みに失敗しました: {str(e)}"
            self.statusBar().showMessage(error_msg)
            logger.error(error_msg)
            logger.exception(e)
            
            # エラーダイアログ表示
            QMessageBox.critical(self, "読み込みエラー", error_msg)
    
    def update_file_info(self, dxf_data):
        """ファイル情報ラベルを更新"""
        if not dxf_data:
            self.info_label.setText("ファイル情報なし")
            return
        
        # エンティティ数をカウント
        entity_count = len(dxf_data.get('entities', []))
        
        # 情報テキスト
        info_text = f"エンティティ数: {entity_count}"
        self.info_label.setText(info_text)
    
    def open_file_dialog(self):
        """ファイル選択ダイアログを開く"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "DXFファイルを開く", "", "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_path:
            self.file_path = file_path
            self.setWindowTitle(f"DXF Viewer - {os.path.basename(file_path)}")
            self.load_dxf_file(file_path)
    
    def fit_to_view(self):
        """コンテンツを表示範囲に合わせる"""
        # DxfGraphicsViewの標準機能を使用
        # setup_scene_rectでシーンレクトを設定し、fitInViewで表示を調整
        self.view.setup_scene_rect(margin_factor=5.0)  # アイテムの5倍のシーンレクトを設定
        self.view.fit_scene_in_view()  # 表示内容に合わせて表示
        
        self.statusBar().showMessage("表示範囲を調整しました")
    
    def zoom_in(self):
        """拡大"""
        self.view.scale(1.2, 1.2)
        self.statusBar().showMessage("拡大しました")
    
    def zoom_out(self):
        """縮小"""
        self.view.scale(1/1.2, 1/1.2)
        self.statusBar().showMessage("縮小しました")

# DXFファイル読み込み関数
def parse_dxf_file(file_path):
    """
    DXFファイルを解析し、データ構造に変換する
    
    Args:
        file_path: DXFファイルのパス
        
    Returns:
        dict: DXFデータを含む辞書
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    
    try:
        # ezdxfでDXFファイルを読み込み
        if EZDXF_AVAILABLE:
            try:
                doc = ezdxf.readfile(file_path)
            except ezdxf.DXFError:
                logger.warning(f"ファイルの読み込みに問題があります。復旧モードで再試行: {file_path}")
                doc, auditor = recover.readfile(file_path)
                if auditor.has_errors:
                    logger.warning(f"復旧結果: {len(auditor.errors)}個のエラー")
            
            # DXFデータを辞書に格納
            dxf_data = {
                'entities': list(doc.modelspace()),
                'layers': list(doc.layers),
                'version': doc.dxfversion,
                'file_path': file_path
            }
            
            logger.debug(f"DXFファイルの解析完了: {len(dxf_data['entities'])}個のエンティティ")
            return dxf_data
        else:
            raise ImportError("ezdxfモジュールが利用できません")
            
    except Exception as e:
        logger.exception(f"DXFファイルの解析中にエラーが発生: {e}")
        raise

def draw_dxf_entities(scene, dxf_data):
    """
    DXFエンティティをシーンに描画する
    
    Args:
        scene: 描画先のQGraphicsScene
        dxf_data: DXFデータを含む辞書
    """
    if not dxf_data or 'entities' not in dxf_data:
        logger.warning("描画するDXFデータがありません")
        return
    
    # core/dxf_colorsからget_entity_colorをインポート（強制黒モード対応）
    try:
        from core.dxf_colors import get_entity_color
        use_core_colors = True
        logger.debug("core.dxf_colorsを使用して色を取得します（強制黒モード対応）")
    except ImportError:
        use_core_colors = False
        logger.debug("core.dxf_colorsが利用できないため、デフォルト色処理を使用します")
    
    # PySide6とpure_dxf_functionsの橋渡しをするアダプターを作成
    from old_impl.old_implementation.dxf_ui_adapter import create_dxf_adapter
    adapter = create_dxf_adapter(scene)
    
    # エンティティ数のカウント
    total_entities = len(dxf_data['entities'])
    processed_entities = 0
    
    # 進捗状況を10%ごとに表示
    progress_interval = max(1, total_entities // 10)
    
    # すべてのエンティティを処理
    for entity in dxf_data['entities']:
        try:
            # エンティティの色を取得
            if use_core_colors:
                # 強制黒モード対応の色取得
                color = get_entity_color(entity)
            else:
                # デフォルト色（白）
                color = (255, 255, 255)
            
            # エンティティをシーンに描画
            result, error = adapter.process_entity(entity, color)
            
            # 処理カウントを更新
            processed_entities += 1
            
            # 進捗状況を表示
            if processed_entities % progress_interval == 0:
                progress = int(processed_entities / total_entities * 100)
                logger.debug(f"描画進捗: {progress}% ({processed_entities}/{total_entities})")
                
        except Exception as e:
            logger.error(f"エンティティの描画中にエラー: {str(e)}")
    
    logger.info(f"描画完了: {processed_entities}/{total_entities}個のエンティティを処理")

# アプリケーションの起動処理
if __name__ == "__main__":
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
    
    # ロギング設定
    setup_logger(debug_mode=args.debug)
    
    # アプリケーション起動
    app = QApplication(sys.argv)
    viewer = DXFViewer(app_settings)
    viewer.show()
    
    # アプリケーション実行
    sys.exit(app.exec())
