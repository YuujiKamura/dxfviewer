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
logger = setup_logger(args.debug)

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
        import pure_dxf_functions as pdf
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
        import pure_dxf_functions as pdf
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
        # dxf_ui_adapterを使用してエンティティを処理
        from dxf_ui_adapter import DXFSceneAdapter
        
        adapter = DXFSceneAdapter(scene)
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

# DXFビュークラス
class DXFGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_ = QGraphicsScene()
        self.setScene(self.scene_)
        
        # テーマ関連の拡張
        self.themes = {
            "ライト": {"background": QColor(255, 255, 255), "foreground": QColor(0, 0, 0)},
            "ダーク": {"background": QColor(40, 40, 40), "foreground": QColor(220, 220, 220)},
            "ブルー": {"background": QColor(235, 245, 255), "foreground": QColor(0, 50, 100)}
        }
        self.current_theme = "ライト"
        
        # 固定の背景色と線の色を設定（初期設定）
        self.background_color = self.themes[self.current_theme]["background"]
        self.line_color = self.themes[self.current_theme]["foreground"]
        
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
        
        # アダプターの初期化（dxf_ui_adapterが使用可能な場合）
        try:
            from dxf_ui_adapter import DXFSceneAdapter
            self.adapter = DXFSceneAdapter(self.scene_)
        except ImportError:
            self.adapter = None
        
        # マウス座標を正確に初期化
        self.last_mouse_pos = QPointF(0.0, 0.0)
        
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
    
    def mousePressEvent(self, event):
        """マウスボタンが押された時のイベント処理"""
        if event.button() == Qt.MouseButton.LeftButton:
            # ドラッグ開始時の位置を記録
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.last_mouse_pos = event.position()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """マウス移動時のイベント処理"""
        # ドラッグ処理（左ボタンが押されている場合）
        if Qt.MouseButton.LeftButton & event.buttons():
            # 現在のマウス位置と前回位置の差分を計算
            current_pos = event.position()
            delta = current_pos - self.last_mouse_pos
            
            # デバッグ情報を詳細に出力
            if self.parent() and hasattr(self.parent(), 'debug_mode') and self.parent().debug_mode:
                logger.debug(f"移動追跡: 現在位置=({current_pos.x():.2f}, {current_pos.y():.2f}), "
                           f"前回位置=({self.last_mouse_pos.x():.2f}, {self.last_mouse_pos.y():.2f}), "
                           f"差分=({delta.x():.2f}, {delta.y():.2f})")
                transform = self.transform()
                logger.debug(f"変換行列: m11={transform.m11():.3f}, m12={transform.m12():.3f}, "
                           f"m21={transform.m21():.3f}, m22={transform.m22():.3f}, "
                           f"dx={transform.dx():.3f}, dy={transform.dy():.3f}")
            
            # ビューの変換行列を直接操作してモデルを移動（パン）
            self.translate(delta.x(), delta.y())
            
            # 変換後の情報をログに出力
            if self.parent() and hasattr(self.parent(), 'debug_mode') and self.parent().debug_mode:
                transform = self.transform()
                logger.debug(f"変換後: m11={transform.m11():.3f}, m12={transform.m12():.3f}, "
                           f"m21={transform.m21():.3f}, m22={transform.m22():.3f}, "
                           f"dx={transform.dx():.3f}, dy={transform.dy():.3f}")
            
            # 現在位置を更新
            self.last_mouse_pos = current_pos
            # カーソルを手のアイコンに（視覚的フィードバック）
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        # マウス位置を取得して座標を表示
        pos = self.mapToScene(event.position().toPoint())
        if self.parent() and hasattr(self.parent(), 'update_status_bar'):
            self.parent().update_status_bar(pos.x(), -pos.y())
        
        # CAD操作は自前処理で完結するので親クラスは呼ばない
        # super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """マウスボタンが離された時のイベント処理"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def reset_view(self):
        # ビューをリセット
        self.resetTransform()
        if self.scene().items():
            self.scene().setSceneRect(self.scene().itemsBoundingRect())
            self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)
        logger.debug("ビューがリセットされました")
    
    def apply_theme(self, theme_name):
        """テーマを適用"""
        if theme_name not in self.themes:
            theme_name = "ライト"
        
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        # 色の取得
        self.background_color = theme["background"]
        self.line_color = theme["foreground"]
        
        # 背景色を設定
        self.setBackgroundBrush(QBrush(self.background_color))
        
        # すべてのアイテムの色を更新
        if hasattr(self, 'adapter') and self.adapter:
            self.adapter.apply_color_to_all_items(
                (self.line_color.red(), self.line_color.green(), self.line_color.blue())
            )
        else:
            # アダプターがない場合は直接アイテムの色を変更
            for item in self.scene_.items():
                if hasattr(item, 'pen'):
                    pen = item.pen()
                    pen.setColor(self.line_color)
                    item.setPen(pen)
                elif hasattr(item, 'setDefaultTextColor'):
                    item.setDefaultTextColor(self.line_color)
        
        # シーン更新
        self.scene().update()
        
        logger.debug(f"テーマを適用しました: {theme_name}")

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
        """DXFファイルを読み込んで処理"""
        if not filename:
            return
        
        try:
            logger.info(f"DXFファイル読み込み開始: {filename}")
            
            # ezdxfでDXFを読み込み
            try:
                doc = ezdxf.readfile(filename)
            except Exception as e:
                # 読み込みエラーが発生した場合、リカバリーモードで再試行
                doc, auditor = recover.readfile(filename)
                if auditor.has_errors:
                    logger.warning(f"DXFファイルの読み込み時に問題が検出されました: {len(auditor.errors)} エラー")
            
            # DXFのバージョン情報をログに出力
            if logger and hasattr(doc, 'dxfversion'):
                logger.debug(f"DXFバージョン: {doc.dxfversion}")
            
            # 線幅設定を取得
            line_width_scale = self.app_settings.get_line_width_scale()
            default_width = self.app_settings.load_line_width()
            logger.debug(f"現在の線幅設定: {default_width} (スケール: {line_width_scale})")
            
            # シーンをクリア
            self.dxf_view.scene().clear()
            
            # 白背景と黒線に固定
            bg_color = (255, 255, 255)  # 白
            line_color = (0, 0, 0)      # 黒
            
            # 背景色の設定
            self.dxf_view.scene().setBackgroundBrush(QBrush(QColor(*bg_color)))
            
            # モデル空間を取得
            modelspace = doc.modelspace()
            
            # DXFデータとUIの橋渡しをするアダプターを作成
            from dxf_ui_adapter import DXFSceneAdapter
            adapter = DXFSceneAdapter(self.dxf_view.scene())
            
            # エンティティ処理用のカウンター
            processed = 0
            errors = 0
            
            # モデル空間内のすべてのエンティティを処理
            for entity in modelspace:
                try:
                    # エンティティタイプをログに出力
                    if logger:
                        logger.debug(f"エンティティ [{processed+1}]: タイプ={entity.dxftype()}")
                    
                    # 線幅情報をログに出力
                    if hasattr(entity.dxf, 'lineweight'):
                        logger.debug(f"  線幅設定: {entity.dxf.lineweight}")
                    
                    # レイヤー情報をログに出力
                    if hasattr(entity.dxf, 'layer'):
                        layer_name = entity.dxf.layer
                        layer = doc.layers.get(layer_name)
                        if layer and hasattr(layer.dxf, 'lineweight'):
                            logger.debug(f"  レイヤー: {layer_name}, 線幅: {layer.dxf.lineweight}")
                    
                    # 純粋関数を使用してエンティティを処理
                    import pure_dxf_functions as pdf
                    result = pdf.process_entity_data(entity, line_color, default_width, line_width_scale)
                    
                    # 処理が成功した場合、アダプターを使用してUIに描画
                    if result.success:
                        adapter.draw_entity_result(result)
                        processed += 1
                    else:
                        # エラーがあった場合はログに出力
                        logger.warning(f"エンティティ [{processed+1}] 処理エラー: {result.error}")
                        errors += 1
                except Exception as e:
                    # 例外が発生した場合もログに出力
                    logger.error(f"エンティティ処理中に例外: {str(e)}")
                    errors += 1
            
            logger.info(f"DXFファイル読み込み完了: エンティティ総数={processed}, エラー数={errors}")
            
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
            
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"DXFファイル読み込みエラー: {str(e)}\n{error_details}")
            QMessageBox.critical(
                self, 
                "ファイル読み込みエラー", 
                f"DXFファイル '{os.path.basename(filename)}' の読み込み中にエラーが発生しました:\n{str(e)}"
            )
    
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
        """アプリケーションを再起動"""
        # 再起動機能を無効化
        logger.info("再起動機能は現在無効化されています。")
        return
    
    # 以下の元の実装はコメントアウト
    """
    # 現在のファイルパスを取得
    current_file_path = self.current_file if self.current_file else ""
    
    # 現在の実行ファイル
    script_path = os.path.abspath(__file__)
    logger.info(f"アプリケーションを手動で再起動します: {script_path}")
    
    # Python実行ファイルのパス
    python_exe = sys.executable
    
    # 再起動コマンドを構築
    restart_cmd = [python_exe, script_path]
    
    # ファイルが開かれていれば、そのパスを引数に追加
    if current_file_path:
        restart_cmd.extend(["--file", current_file_path])
    
    # 再起動フラグと親プロセスIDを追加
    restart_cmd.extend(["--restart", "--parent-pid", str(os.getpid())])
    
    # デバッグモードが有効なら引数に追加
    if self.debug_mode:
        restart_cmd.append("--debug")
    
    # コマンドをログに記録
    logger.info(f"再起動コマンド: {' '.join(restart_cmd)}")
    
    # 新しいプロセスを起動
    subprocess.Popen(restart_cmd)
    logger.info("新しいプロセスを起動しました。このプロセスは終了します。")
    
    # 現在のプロセスを終了
    self.app.quit()
    """

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
        # if check_single_instance():
        #     sys.exit(1)
        
        # グローバルアプリケーションインスタンスの作成
        app = QApplication(sys.argv)
        app.setStyle("Fusion")  # Fusionスタイルを使用（プラットフォーム間で一貫した外観）
        
        # アプリケーション設定の初期化
        app_settings = AppSettings()
        logger.info(f"線幅設定：基本線幅 {app_settings.load_line_width()} × 倍率 {app_settings.get_line_width_scale()}")
        
        viewer = DXFViewer(app_settings)
        viewer.show()
        
        # ファイルが指定されていれば開く
        if hasattr(args, 'file') and args.file:
            viewer.load_and_display_dxf(args.file)
        
        # 実行開始
        logger.info("アプリケーションの実行を開始します")
        sys.exit(app.exec())
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