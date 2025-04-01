import os
import sys
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
    QFileDialog, QPushButton, QLabel, QMessageBox, QGraphicsView, 
    QGraphicsScene, QGraphicsItem, QStatusBar, QComboBox, QDialog, 
    QTextEdit, QCheckBox, QSlider, QGroupBox, QSpinBox, QSizePolicy
)
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
        from ezdxf.math import Vector
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
DEFAULT_LINE_WIDTH = 12.0
DEFAULT_LINE_WIDTH_MIN = 1.0
DEFAULT_LINE_WIDTH_MAX = 20.0

# ロガーの設定
logger = None
log_file = "dxf_viewer.log"
lock_file = "dxf_viewer.lock"

# 設定の保存と読み込み用のクラス
class AppSettings:
    def __init__(self):
        self.settings = QSettings("DXFViewer", "PySide6")
        # 強制線幅モードの追加
        self.force_linewidth = True
        self.force_linewidth_value = 20.0
    
    def save_line_width(self, width):
        self.settings.setValue("line_width", width)
    
    def load_line_width(self):
        # 強制線幅モードが有効な場合は常に固定値を返す
        if self.force_linewidth:
            return self.force_linewidth_value
        # デフォルト値はDEFAULT_LINE_WIDTH
        return self.settings.value("line_width", DEFAULT_LINE_WIDTH, type=float)
    
    def reset_line_width(self):
        """線幅設定をリセットしてデフォルト値に戻す"""
        self.settings.remove("line_width")
        return DEFAULT_LINE_WIDTH
    
    def save_theme(self, theme):
        self.settings.setValue("theme", theme)
    
    def load_theme(self):
        return self.settings.value("theme", "dark")

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
logger = setup_logger(args.debug)

# シングルインスタンス管理（一時的に無効化）
def check_single_instance():
    """他のインスタンスが実行中かチェック（一時的に無効化）"""
    # 常にTrueを返して起動を許可
    return True

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
    # テスト用に常に大きな線幅を返す
    return 20.0

    # 以下の元の実装はコメントアウト
    """
    if default_width is None:
        default_width = app_settings.load_line_width()
    
    # デバッグ用に入力値を記録
    if 'logger' in globals() and logger is not None:
        logger.debug(f"線幅取得開始 - デフォルト値: {default_width}")
    
    # lineweight属性がある場合はそれを使用
    if hasattr(entity.dxf, 'lineweight'):
        lw = entity.dxf.lineweight
        if 'logger' in globals() and logger is not None:
            logger.debug(f"エンティティ線幅設定: {lw}")
        
        if lw > 0:  # 正の値の場合は直接その値を使用（100分の1 mm単位）
            # DXFの線幅（100分の1 mm）をQt用に変換し、最小値を設定
            result = max(lw / 10.0, DEFAULT_LINE_WIDTH_MIN)
            if 'logger' in globals() and logger is not None:
                logger.debug(f"計算された線幅: {result} (元の値: {lw}/10)")
            return result
        elif lw == -3:  # BYLAYER
            # レイヤーの線幅を取得
            if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'layer'):
                layer_name = entity.dxf.layer
                layer = entity.doc.layers.get(layer_name)
                if layer and hasattr(layer.dxf, 'lineweight') and layer.dxf.lineweight > 0:
                    result = max(layer.dxf.lineweight / 10.0, DEFAULT_LINE_WIDTH_MIN)
                    if 'logger' in globals() and logger is not None:
                        logger.debug(f"レイヤー線幅適用: {result} (レイヤー: {layer_name}, 値: {layer.dxf.lineweight}/10)")
                    return result
    
    # 情報が取得できない場合はデフォルト値を返す
    if 'logger' in globals() and logger is not None:
        logger.debug(f"デフォルト線幅使用: {default_width}")
    return default_width
    """

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
    if not filename:
        return None, "ファイル名が指定されていません"
    
    if not filename.lower().endswith('.dxf'):
        filename += '.dxf'
    
    try:
        with r12writer(filename) as dxf:
            # 線幅テスト用の平行線を描画（異なる線幅で比較できるように）
            for i in range(5):
                y = 150 + i * 20
                dxf.add_line((10, y), (190, y))
                dxf.add_text(f"線幅テスト {i+1}", (200, y), height=7)
            
            # 線を描画
            dxf.add_line((0, 0), (100, 0))
            dxf.add_line((100, 0), (100, 100))
            dxf.add_line((100, 100), (0, 100))
            dxf.add_line((0, 100), (0, 0))
            
            # 円を描画
            dxf.add_circle((50, 50), 40)
            
            # テキストを追加
            dxf.add_text("サンプルDXF", (10, 110), height=10)
            
            # 対角線を描画
            dxf.add_line((0, 0), (100, 100))
            dxf.add_line((0, 100), (100, 0))
            
            # 多角形（ポリライン）を描画
            points = [(150, 10), (170, 20), (190, 40), (180, 60), (150, 50)]
            dxf.add_polyline(points, close=True)
            
        logger.info(f"サンプルDXFファイルを作成しました: {filename}")
        return filename, None
        
    except Exception as e:
        error_details = traceback.format_exc()
        return None, (str(e), error_details)

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

# DXFビュークラス
class DXFGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_ = QGraphicsScene()
        self.setScene(self.scene_)
        
        # 固定の背景色と線の色を設定
        self.background_color = QColor(255, 255, 255)  # 白背景
        self.line_color = QColor(0, 0, 0)  # 黒い線
        
        # 初期化
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        
        # 背景色を設定
        self.setBackgroundBrush(QBrush(self.background_color))
        
        # ズーム関連
        self.zoom_factor = 1.2
        self.current_zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 50.0
        
        # マウス座標
        self.last_mouse_pos = QPointF(0, 0)
        
        # 強制線幅モード
        self.force_linewidth = True
        self.force_linewidth_value = 1.0  # 黒線なので普通の太さに
        
        logger.info("DXFGraphicsViewが初期化されました")
    
    def wheelEvent(self, event):
        # マウスホイールでズーム処理
        zoom_in = event.angleDelta().y() > 0
        factor = self.zoom_factor if zoom_in else 1 / self.zoom_factor
        self.scale(factor, factor)
        logger.debug(f"ズーム{'イン' if zoom_in else 'アウト'}: 倍率={factor}")
        super().wheelEvent(event)
    
    def mouseMoveEvent(self, event):
        # マウス位置を取得して座標を表示
        pos = self.mapToScene(event.position().toPoint())
        if self.parent() and hasattr(self.parent(), 'update_status_bar'):
            self.parent().update_status_bar(pos.x(), -pos.y())
        super().mouseMoveEvent(event)
    
    def reset_view(self):
        # ビューをリセット
        self.resetTransform()
        if self.scene().items():
            self.scene().setSceneRect(self.scene().itemsBoundingRect())
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)
        logger.debug("ビューがリセットされました")
    
    def apply_theme(self, theme_name):
        """テーマを適用（互換性のために残し、固定色に設定）"""
        # 固定テーマ
        self.background_color = QColor(255, 255, 255)  # 白背景
        self.line_color = QColor(0, 0, 0)  # 黒線
        self.setBackgroundBrush(QBrush(self.background_color))
        
        # シーン更新
        self.scene().update()
        
        logger.debug(f"固定テーマを適用しました（白背景、黒線）")

class DXFViewer(QMainWindow):
    def __init__(self, app_settings):
        super().__init__()
        self.current_doc = None
        self.current_file = None
        # デバッグモードの設定
        self.debug_mode = False
        if 'args' in globals() and hasattr(args, 'debug'):
            self.debug_mode = args.debug
        
        self.app_settings = app_settings
        # 最後に読み込んだファイル名を保存するキャッシュを追加
        self.last_loaded_file = None
        
        self.initUI()
        logger.info("DXFViewerアプリケーションが起動しました (PySide6版)")

    def initUI(self):
        self.setWindowTitle('DXF Viewer (PySide6版)')
        self.setGeometry(100, 100, 1000, 800)
        
        # メインウィジェットとレイアウトの設定
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # ツールバーの設定
        toolbar_layout = QHBoxLayout()
        
        # ファイル選択ボタン
        self.open_button = QPushButton('ファイルを開く')
        self.open_button.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.open_button)
        
        # ファイル情報ボタン
        self.info_button = QPushButton('ファイル情報')
        self.info_button.clicked.connect(self.show_file_info)
        self.info_button.setEnabled(False)
        toolbar_layout.addWidget(self.info_button)
        
        # リセットボタン
        self.reset_button = QPushButton('表示をリセット')
        self.reset_button.clicked.connect(self.reset_view)
        self.reset_button.setEnabled(False)
        toolbar_layout.addWidget(self.reset_button)
        
        # サンプル作成ボタン
        self.sample_button = QPushButton('サンプル作成')
        self.sample_button.clicked.connect(self.create_sample)
        toolbar_layout.addWidget(self.sample_button)
        
        # 再読み込みボタン
        self.reload_button = QPushButton('再読み込み')
        self.reload_button.clicked.connect(self.reload_current_file)
        self.reload_button.setEnabled(False)
        toolbar_layout.addWidget(self.reload_button)
        
        # 再起動ボタン
        self.restart_button = QPushButton('アプリ再起動')
        self.restart_button.clicked.connect(self.restart_application)
        toolbar_layout.addWidget(self.restart_button)
        
        # ファイル名表示ラベル
        self.file_label = QLabel('ファイル: なし')
        toolbar_layout.addWidget(self.file_label)
        
        # 右寄せのスペーサー
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar_layout.addWidget(spacer)
        
        # デバッグモードのチェックボックス
        self.debug_check = QCheckBox('デバッグモード')
        self.debug_check.setChecked(self.debug_mode)
        self.debug_check.stateChanged.connect(self.toggle_debug_mode)
        toolbar_layout.addWidget(self.debug_check)
        
        # ログ表示ボタン
        self.log_button = QPushButton('ログを表示')
        self.log_button.clicked.connect(self.show_debug_log)
        toolbar_layout.addWidget(self.log_button)
        
        # DXFビューを設定
        self.dxf_view = DXFGraphicsView(self)
        
        # ステータスバーを設定
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # レイアウトに追加
        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.dxf_view)
        
        # マウス座標表示のためにイベントを接続
        self.dxf_view.viewport().installEventFilter(self)
    
    def toggle_debug_mode(self, state):
        logger.debug(f"チェックボックスの状態値: {state}")
        # PyQt5ではQt.Checked(2)だが、PySide6では異なる場合がある
        self.debug_mode = bool(state)
        logger.info(f"デバッグモード: {'オン' if self.debug_mode else 'オフ'}")
        # デバッグモード切り替え時のファイル再読み込みは不要
    
    def show_debug_log(self):
        """デバッグログを表示"""
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            # ログダイアログを表示
            dialog = QDialog(self)
            dialog.setWindowTitle("デバッグログ")
            dialog.setGeometry(200, 200, 800, 600)
            
            layout = QVBoxLayout(dialog)
            
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setText(log_content)
            layout.addWidget(log_text)
            
            # スクロールを最下部に移動
            scrollbar = log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
            # 閉じるボタン
            close_button = QPushButton("閉じる")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ログファイルの読み込みに失敗しました: {str(e)}")
    
    def update_status_bar(self, x, y):
        # ステータスバーに座標情報を表示
        self.statusBar.showMessage(f"X: {x:.2f}, Y: {y:.2f}")
        
    def show_file_info(self):
        """ファイル情報ダイアログを表示"""
        if self.current_doc:
            if hasattr(self.current_doc, 'dxfversion'):
                version = self.current_doc.dxfversion
            else:
                version = "不明"
                
            info_text = f"DXFバージョン: {version}\n"
            info_text += f"ファイルパス: {self.current_file}\n"
            info_text += f"レイヤー数: {len(self.current_doc.layers)}\n"
            
            # レイヤー情報
            info_text += "\nレイヤー一覧:\n"
            for layer in self.current_doc.layers:
                info_text += f"- {layer.dxf.name}\n"
            
            # 情報ダイアログを表示
            QMessageBox.information(self, "DXFファイル情報", info_text)
    
    def create_sample(self):
        # サンプルDXFファイルを作成
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self, "サンプルDXFファイルを保存", "", "DXF Files (*.dxf)", options=options
        )
        
        if not filename:
            return
        
        logger.info(f"サンプルDXFファイルの作成を開始: {filename}")
            
        # 純粋関数を使用してサンプルファイルを作成
        result, error = create_sample_dxf(filename)
        
        if result:
            logger.info(f"サンプルDXFファイルの作成に成功: {result}")
            QMessageBox.information(self, "完了", f"サンプルDXFファイルを保存しました: {result}")
            
            # 保存したファイルを開く
            self.load_dxf(result)
            self.current_file = result
            self.file_label.setText(f'ファイル: {os.path.basename(result)}')
            self.reset_button.setEnabled(True)
            self.info_button.setEnabled(True)
        else:
            err_msg, err_details = error
            logger.error(f"サンプルDXFファイルの作成に失敗: {err_msg}\n{err_details}")
            
            error_message = f"サンプルDXFファイルの作成に失敗しました: {err_msg}"
            if self.debug_mode:
                error_message += f"\n\n詳細エラー情報:\n{err_details}"
                
            QMessageBox.critical(self, "エラー", error_message)
        
    def open_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, "DXFファイルを開く", "", "DXF Files (*.dxf)", options=options
        )
        
        if filename:
            logger.info(f"DXFファイルを開く: {filename}")
            self.load_and_display_dxf(filename)
    
    def load_and_display_dxf(self, filename):
        """DXFファイルを読み込み、表示する"""
        # 重複するログ出力を削除
        try:
            # ファイルの存在確認
            if not os.path.exists(filename):
                QMessageBox.critical(self, "エラー", f"ファイルが見つかりません: {filename}")
                return
            
            # ファイルの読み込み
            self.load_dxf(filename)
            
            # ファイル情報ボタンを有効化
            self.info_button.setEnabled(True)
            
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"DXFファイル読み込みエラー: {str(e)}\n{error_details}")
            QMessageBox.critical(
                self, 
                "ファイル読み込みエラー", 
                f"DXFファイル '{os.path.basename(filename)}' の読み込み中にエラーが発生しました:\n{str(e)}"
            )
    
    def load_dxf(self, filename):
        # 同じファイルが既に読み込まれている場合は再読み込みをスキップ
        if self.last_loaded_file == filename:
            logger.info(f"ファイル {filename} は既に読み込み済みです。再読み込みをスキップします。")
            return
            
        logger.info(f"DXFファイル読み込み開始: {filename}")
        
        # 最後に読み込んだファイル名を更新
        self.last_loaded_file = filename
        
        # ファイル読み込み
        doc, error = load_dxf_file(filename)
        if error:
            err_msg, err_details = error
            logger.error(f"DXFファイルの読み込みに失敗: {err_msg}\n{err_details}")
            raise Exception(err_msg)
        
        self.current_doc = doc
        self.current_file = filename  # 現在のファイルパスを保存
        logger.debug(f"DXFバージョン: {doc.dxfversion}")
        
        # シーンをクリア
        self.dxf_view.scene().clear()
        
        # モデル空間からエンティティを取得してシーンに描画
        self.process_entities(doc.modelspace())
        
        # ビューをリセット
        self.reset_view()
        
        # 変更を確実に反映するために更新を強制
        self.dxf_view.update()
        self.dxf_view.viewport().update()
        
        # 現在のウィンドウタイトルを更新
        self.setWindowTitle(f'{APP_NAME} - {os.path.basename(filename)}')
        
        # ファイル情報ボタンを有効化
        self.info_button.setEnabled(True)
        
        # 再読み込みボタンを有効化
        self.reload_button.setEnabled(True)
    
    def process_entities(self, entities):
        """モデル空間のエンティティを処理して描画（純粋関数の組み合わせ）"""
        entity_count = 0
        error_count = 0
        
        # 現在の線幅設定を取得
        line_width = self.app_settings.load_line_width()
        logger.debug(f"現在の線幅設定: {line_width}")
        
        # DXF UIアダプターを作成
        from dxf_ui_adapter import DXFSceneAdapter
        adapter = DXFSceneAdapter(self.dxf_view.scene())
        
        # 各エンティティを処理
        for entity in entities:
            entity_count += 1
            
            # エンティティ情報をログに出力（デバッグモードの場合）
            if self.debug_mode:
                if hasattr(entity, 'dxftype'):
                    logger.debug(f"エンティティ [{entity_count}]: タイプ={entity.dxftype()}")
                
                # エンティティの線幅設定を確認
                if hasattr(entity.dxf, 'lineweight'):
                    logger.debug(f"  線幅設定: {entity.dxf.lineweight}")
                
                # エンティティのレイヤー情報を確認
                if hasattr(entity.dxf, 'layer'):
                    layer_name = entity.dxf.layer
                    layer = self.current_doc.layers.get(layer_name)
                    if layer and hasattr(layer.dxf, 'lineweight'):
                        logger.debug(f"  レイヤー: {layer_name}, 線幅: {layer.dxf.lineweight}")
            
            # 純粋関数を使用してエンティティのデータを処理
            import pure_dxf_functions as pdf
            result = pdf.process_entity_data(entity, self.dxf_view.line_color, line_width)
            
            # 処理結果を描画
            if result.success:
                adapter.draw_entity_result(result)
            else:
                error_count += 1
                if self.debug_mode:
                    logger.warning(f"エンティティ [{entity_count}] 処理エラー: {result.error}")
        
        logger.info(f"DXFファイル読み込み完了: エンティティ総数={entity_count}, エラー数={error_count}")
        
        # デバッグモードを元に戻す
        self.dxf_view.update()  # シーンを更新
    
    def reset_view(self):
        self.dxf_view.reset_view()
    
    def take_screenshot(self):
        """現在のビューのスクリーンショットを作成"""
        try:
            # 現在のシーン全体の表示領域を取得
            scene_rect = self.dxf_view.scene().itemsBoundingRect()
            self.dxf_view.scene().setSceneRect(scene_rect)
            
            # 画像を作成
            image = QPixmap(scene_rect.width(), scene_rect.height())
            image.fill(Qt.transparent)
            
            # QPainterを使用して描画
            painter = QPainter(image)
            self.dxf_view.scene().render(painter, QRectF(), scene_rect)
            painter.end()
            
            # クリップボードにコピー
            QApplication.clipboard().setPixmap(image)
            
            # 保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_file = f"dxf_screenshot_{timestamp}.png"
            image.save(screenshot_file)
            
            logger.info(f"スクリーンショットをクリップボードにコピーしました")
            self.statusBar.showMessage(f"スクリーンショットを保存しました: {screenshot_file}", 5000)
            
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"スクリーンショット作成エラー: {str(e)}")
            QMessageBox.critical(
                self, 
                "スクリーンショットエラー", 
                f"スクリーンショットの作成中にエラーが発生しました:\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """アプリケーション終了時の処理"""
        logger.info("DXFViewerアプリケーションを終了します")
        super().closeEvent(event)
    
    def show_line_width_dialog(self):
        """線幅設定ダイアログを表示"""
        dialog = LineWidthDialog(self, self.app_settings)
        dialog.exec()
    
    def reload_current_file(self):
        """現在開いているファイルを再読み込み"""
        if self.current_file:
            logger.info(f"ファイル {self.current_file} を強制的に再読み込みします")
            # 最後に読み込んだファイル情報をリセットして強制再読み込み
            self.last_loaded_file = None
            self.load_dxf(self.current_file)
            # 成功メッセージを表示
            self.statusBar.showMessage(f"ファイル {os.path.basename(self.current_file)} を再読み込みしました", 3000)  # 3秒間表示
    
    def restart_application(self):
        """アプリケーションを手動で再起動するメソッド
        このメソッドは自動再起動機能が無効化された後も使用できます。
        """
        # 既に再起動処理中なら無視
        if hasattr(self, 'restarting') and self.restarting:
            return
            
        script_path = os.path.abspath(__file__)
        logger.info(f"アプリケーションを手動で再起動します: {script_path}")
        self.restarting = True
        
        # 現在のコマンドライン引数を取得
        current_args = []
        if self.debug_mode:
            current_args.append('--debug')
        if self.current_file:
            current_args.extend(['--file', str(self.current_file)])
        
        # 再起動フラグと親PIDを追加
        current_args.extend(['--restart', '--parent-pid', str(os.getpid())])
        
        # 新しいプロセスを起動するコマンドを構築
        cmd = [sys.executable, script_path] + current_args
        logger.info(f"再起動コマンド: {' '.join(cmd)}")
        
        try:
            # 新しいプロセスを起動
            if os.name == 'nt':  # Windows
                # プロセスを分離して起動
                CREATE_NO_WINDOW = 0x08000000
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                subprocess.Popen(
                    cmd,
                    creationflags=CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW,
                    close_fds=True
                )
            else:  # Linux/Mac
                # デタッチして起動
                subprocess.Popen(
                    cmd,
                    start_new_session=True,
                    close_fds=True
                )
            
            logger.info("新しいプロセスを起動しました。このプロセスは終了します。")
            
            # 現在のプロセスを終了（遅延させて通知を表示する時間を確保）
            QTimer.singleShot(1000, lambda: sys.exit(0))
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"再起動に失敗しました: {str(e)}\n{error_details}")
            self.restarting = False
            QMessageBox.critical(
                self,
                "再起動エラー",
                f"アプリケーションの再起動に失敗しました。\n手動で再起動してください。\nエラー: {str(e)}"
            )

# アプリケーションの起動処理
if __name__ == '__main__':
    # コマンドライン引数の解析
    args = parse_arguments()
    
    # ezdxfが利用できない場合は終了
    if not EZDXF_AVAILABLE:
        print("ezdxfモジュールが利用できないため、プログラムを終了します。")
        sys.exit(1)
    
    # ロガーのセットアップ
    logger = setup_logger(args.debug)
    
    try:
        # シングルインスタンスチェック
        if check_single_instance():
            # アプリケーション初期化
            app = QApplication(sys.argv)
            app_settings = AppSettings()
            
            # 線幅設定をリセットしてデフォルト値を使用
            app_settings.reset_line_width()
            logger.info(f"線幅設定をリセットしました。デフォルト値 {DEFAULT_LINE_WIDTH} を使用します。")
            
            viewer = DXFViewer(app_settings)
            viewer.show()
            
            # ファイルが指定されていれば開く
            if hasattr(args, 'file') and args.file:
                viewer.load_and_display_dxf(args.file)
            
            # 実行開始
            logger.info("アプリケーションの実行を開始します")
            sys.exit(app.exec())
        else:
            logger.warning("既に他のインスタンスが実行中です。終了します。")
            sys.exit(0)
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {str(e)}")
        traceback.print_exc()
        if 'logger' in globals() and logger is not None:
            logger.error(f"予期せぬエラーが発生しました: {str(e)}", exc_info=True)
        if 'QApplication' in globals():
            QMessageBox.critical(None, "エラー", f"予期せぬエラーが発生しました:\n{str(e)}")
        sys.exit(1)

# 線幅設定ダイアログ
class LineWidthDialog(QDialog):
    def __init__(self, parent=None, app_settings=None):
        super().__init__(parent)
        self.parent = parent
        self.app_settings = app_settings
        self.setWindowTitle("線幅設定")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 線幅のグループボックス
        group_box = QGroupBox("線の太さ")
        group_layout = QVBoxLayout()
        
        # 現在の線幅を取得
        current_width = self.app_settings.load_line_width()
        
        # スライダーとスピンボックスの設定
        slider_layout = QHBoxLayout()
        
        # ラベル
        self.width_label = QLabel(f"線幅: {current_width:.1f}")
        
        # スライダー
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setMinimum(int(DEFAULT_LINE_WIDTH_MIN * 10))
        self.width_slider.setMaximum(int(DEFAULT_LINE_WIDTH_MAX * 10))
        self.width_slider.setValue(int(current_width * 10))
        self.width_slider.setTickPosition(QSlider.TicksBelow)
        self.width_slider.setTickInterval(10)
        
        # スピンボックス
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setMinimum(int(DEFAULT_LINE_WIDTH_MIN * 10))
        self.width_spinbox.setMaximum(int(DEFAULT_LINE_WIDTH_MAX * 10))
        self.width_spinbox.setValue(int(current_width * 10))
        self.width_spinbox.setSuffix(" px/10")
        
        # レイアウトに追加
        slider_layout.addWidget(self.width_label)
        slider_layout.addWidget(self.width_slider)
        slider_layout.addWidget(self.width_spinbox)
        
        group_layout.addLayout(slider_layout)
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        
        # OKボタンと適用ボタン
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("適用")
        self.apply_button.clicked.connect(self.apply_settings)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_and_apply)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # シグナル接続
        self.width_slider.valueChanged.connect(self.update_spinbox)
        self.width_spinbox.valueChanged.connect(self.update_slider)
    
    def update_spinbox(self, value):
        self.width_spinbox.setValue(value)
        self.width_label.setText(f"線幅: {value/10:.1f}")
    
    def update_slider(self, value):
        self.width_slider.setValue(value)
        self.width_label.setText(f"線幅: {value/10:.1f}")
    
    def get_settings(self):
        return self.width_slider.value() / 10.0
    
    def apply_settings(self):
        width = self.get_settings()
        self.app_settings.save_line_width(width)
        # 親ウィンドウがDXFViewerの場合、再読み込み
        if self.parent and hasattr(self.parent, 'reload_current_file'):
            self.parent.reload_current_file()
    
    def accept_and_apply(self):
        self.apply_settings()
        self.accept() 