#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DXF処理の純粋関数とUIの橋渡しをするアダプターモジュール。
データ計算とUI描画を分離し、テスト可能な構造を提供します。
"""

from typing import List, Tuple, Dict, Any, Optional
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainterPath, QTransform
from PySide6.QtCore import QPointF, QRectF, QLineF, Qt
import traceback
import ezdxf

# 純粋関数モジュールをインポート
import pure_dxf_functions as pdf

class DXFSceneAdapter:
    """
    純粋なデータ構造からグラフィックスシーンへの変換を行うアダプタークラス
    """
    
    def __init__(self, scene: QGraphicsScene):
        """
        アダプタークラスの初期化
        
        Args:
            scene: 描画先のグラフィックスシーン
        """
        self.scene = scene
        self.dxf_doc = None  # DXFドキュメント
        self.bg_color = (255, 255, 255)  # デフォルト背景色は白
        self.default_color = (0, 0, 0)   # デフォルト線色は黒
        
        # グリッドと座標軸の参照を保持
        self.grid_items = []
        self.axes_items = []
    
    def rgb_to_qcolor(self, rgb: Tuple[int, int, int], aci: int = None) -> QColor:
        """
        RGB値をQColorに変換（背景色に応じてACI 7を調整）
        
        Args:
            rgb: RGB値のタプル (R, G, B)
            aci: 元のカラーインデックス値
            
        Returns:
            QColor: 変換されたQColor
        """
        # デバッグ情報
        print(f"RGB値: {rgb} -> QColor, ACI={aci}")
        
        # ACI 7の特殊処理（背景色が白の場合は黒に、黒の場合は白に）
        if aci == 7:
            print(f"  ACI 7の特殊処理を適用します")
            return QColor(0, 0, 0)  # 常に黒を返す（白背景に対して）
        
        return QColor(rgb[0], rgb[1], rgb[2])
    
    def draw_line(self, line_data: pdf.LineData) -> QGraphicsItem:
        """
        LineDataを基にシーンに線を描画
        
        Args:
            line_data: 線の描画データ
            
        Returns:
            QGraphicsItem: 作成された線オブジェクト
        """
        # デバッグ情報
        print(f"線の描画: ACI={line_data.aci}, 線種={line_data.linetype}")
        
        # ACIからRGBに変換
        rgb = pdf.dxf_color_to_rgb(line_data.aci)
        color = self.rgb_to_qcolor(rgb, line_data.aci)
        
        # ペンの設定
        pen = QPen(color)
        pen.setWidthF(max(line_data.width, 0.1))  # 最小幅を設定
        
        # 線種の設定（強化版）
        dash_pattern = pdf.get_line_pattern(line_data.linetype)
        if dash_pattern:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(dash_pattern)
            # ダッシュパターンの結合スタイルを設定
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        else:
            # 実線の場合
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            
        # Qt6では標準の座標系を使用（Y座標の反転は不要）
        line = self.scene.addLine(
            QLineF(
                QPointF(line_data.start_x, line_data.start_y),
                QPointF(line_data.end_x, line_data.end_y)
            ),
            pen
        )
        line.setFlag(QGraphicsItem.ItemIsSelectable)
        return line
    
    def draw_circle(self, circle_data: pdf.CircleData) -> QGraphicsItem:
        """
        CircleDataを基にシーンに円を描画
        
        Args:
            circle_data: 円の描画データ
            
        Returns:
            QGraphicsItem: 作成された円オブジェクト
        """
        # デバッグ情報
        print(f"円の描画: ACI={circle_data.aci}, 線種={circle_data.linetype}, 半径={circle_data.radius}")
        
        # ACIからRGBに変換
        rgb = pdf.dxf_color_to_rgb(circle_data.aci)
        color = self.rgb_to_qcolor(rgb, circle_data.aci)
        
        # ペンの設定
        pen = QPen(color)
        pen.setWidthF(max(circle_data.width, 0.1))  # 最小幅を設定
        
        # 線種の設定（強化版）
        dash_pattern = pdf.get_line_pattern(circle_data.linetype)
        if dash_pattern:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(dash_pattern)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        else:
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # 円の左上座標を計算（中心から半径を引く）
        x = circle_data.center_x - circle_data.radius
        y = circle_data.center_y - circle_data.radius
        
        circle = self.scene.addEllipse(
            QRectF(x, y, circle_data.radius * 2, circle_data.radius * 2),
            pen
        )
        circle.setFlag(QGraphicsItem.ItemIsSelectable)
        return circle
    
    def draw_arc(self, arc_data: pdf.ArcData) -> QGraphicsItem:
        """
        ArcDataを基にシーンに円弧を描画
        
        Args:
            arc_data: 円弧の描画データ
            
        Returns:
            QGraphicsItem: 作成された円弧オブジェクト
        """
        # デバッグ情報
        print(f"円弧の描画: ACI={arc_data.aci}, 線種={arc_data.linetype}, 半径={arc_data.radius}")
        
        # ACIからRGBに変換
        rgb = pdf.dxf_color_to_rgb(arc_data.aci)
        color = self.rgb_to_qcolor(rgb, arc_data.aci)
        
        # ペンの設定
        pen = QPen(color)
        pen.setWidthF(max(arc_data.width, 0.1))  # 最小幅を設定
        
        # 線種の設定（強化版）
        dash_pattern = pdf.get_line_pattern(arc_data.linetype)
        if dash_pattern:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(dash_pattern)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        else:
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # 角度の調整（DXFは反時計回り、Qtは時計回り）
        qt_start_angle = (90 - arc_data.start_angle) % 360
        qt_span_angle = ((arc_data.start_angle - arc_data.end_angle) % 360)
        
        # 円弧の左上座標
        x = arc_data.center_x - arc_data.radius
        y = arc_data.center_y - arc_data.radius
        
        # 円弧のパスを作成
        arc_path = QPainterPath()
        rect = QRectF(x, y, arc_data.radius * 2, arc_data.radius * 2)
        arc_path.arcMoveTo(rect, qt_start_angle)
        arc_path.arcTo(rect, qt_start_angle, -qt_span_angle)
        
        arc = self.scene.addPath(arc_path, pen)
        arc.setFlag(QGraphicsItem.ItemIsSelectable)
        return arc
    
    def draw_polyline(self, polyline_data: pdf.PolylineData) -> QGraphicsItem:
        """
        PolylineDataを基にシーンにポリラインを描画
        
        Args:
            polyline_data: ポリラインの描画データ
            
        Returns:
            QGraphicsItem: 作成されたポリラインオブジェクト
        """
        # デバッグ情報
        print(f"ポリラインの描画: ACI={polyline_data.aci}, 線種={polyline_data.linetype}, 点数={len(polyline_data.points)}")
        
        # ACIからRGBに変換
        rgb = pdf.dxf_color_to_rgb(polyline_data.aci)
        color = self.rgb_to_qcolor(rgb, polyline_data.aci)
        
        # ペンの設定
        pen = QPen(color)
        pen.setWidthF(max(polyline_data.width, 0.1))  # 最小幅を設定
        
        # 線種の設定（強化版）
        dash_pattern = pdf.get_line_pattern(polyline_data.linetype)
        if dash_pattern:
            pen.setStyle(Qt.PenStyle.CustomDashLine)
            pen.setDashPattern(dash_pattern)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        else:
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # ポリラインのパスを作成
        path = QPainterPath()
        
        # Y座標の反転は不要
        points = polyline_data.points
        
        if points:
            path.moveTo(QPointF(points[0][0], points[0][1]))
            for point in points[1:]:
                path.lineTo(QPointF(point[0], point[1]))
        
        # 閉じたポリラインかどうか
        if polyline_data.is_closed:
            path.closeSubpath()
        
        polyline = self.scene.addPath(path, pen)
        polyline.setFlag(QGraphicsItem.ItemIsSelectable)
        return polyline
    
    def draw_text(self, text_data: pdf.TextData) -> QGraphicsItem:
        """
        TextDataを基にシーンにテキストを描画
        
        Args:
            text_data: テキストの描画データ
            
        Returns:
            QGraphicsItem: 作成されたテキストオブジェクト
        """
        # ACIからRGBに変換
        rgb = pdf.dxf_color_to_rgb(text_data.aci)
        
        # テキストアイテムの作成
        text_item = self.scene.addText(text_data.text, QFont("Arial", text_data.height))
        text_item.setDefaultTextColor(self.rgb_to_qcolor(rgb, text_data.aci))
        
        # 位置の計算
        width = text_item.boundingRect().width()
        height = text_item.boundingRect().height()
        
        # デバッグログ - 処理前の値
        if pdf.logger:
            pdf.logger.debug(f"テキスト '{text_data.text}' の配置処理前: h_align={text_data.h_align}, pos=({text_data.pos_x}, {text_data.pos_y}), 幅={width}, 高さ={height}")
        
        # 基本位置（デフォルトは左下揃え）
        base_x = text_data.pos_x
        base_y = text_data.pos_y
        
        # 水平方向の配置
        if text_data.h_align == 0:  # 左揃え
            pass
        elif text_data.h_align == 2:  # 右揃え
            base_x -= width
        elif text_data.h_align == 4 or text_data.h_align == 1:  # 中央揃え (TEXTは4、MTEXTは1を使用することがある)
            base_x -= width/2
            if pdf.logger:
                pdf.logger.debug(f"  中央揃え適用: h_align={text_data.h_align}, base_x = {text_data.pos_x} - {width}/2 = {base_x}")
        
        # 垂直方向の配置
        if text_data.v_align == 0:  # ベースライン
            pass
        elif text_data.v_align == 1:  # 下揃え
            pass
        elif text_data.v_align == 2:  # 中央揃え
            base_y += height/2
        elif text_data.v_align == 3:  # 上揃え
            base_y += height
        
        text_item.setPos(base_x, base_y)
        
        # デバッグログ - 処理後の値
        if pdf.logger:
            pdf.logger.debug(f"テキスト '{text_data.text}' の配置処理後: 位置=({base_x}, {base_y})")
        
        # 回転の適用
        if text_data.rotation:
            # 回転の中心点を設定
            if text_data.h_align == 0:  # 左揃え
                text_item.setTransformOriginPoint(0, height)
            elif text_data.h_align == 2:  # 右揃え
                text_item.setTransformOriginPoint(width, height)
            elif text_data.h_align == 4 or text_data.h_align == 1:  # 中央揃え (TEXTは4、MTEXTは1を使用することがある)
                text_item.setTransformOriginPoint(width/2, height/2)
            else:
                text_item.setTransformOriginPoint(0, height)
                
            # Qtの回転は時計回り、DXFは反時計回りなので反転
            text_item.setRotation(-text_data.rotation)
        
        return text_item
    
    def draw_entity_result(self, result: pdf.Result) -> Optional[QGraphicsItem]:
        """
        エンティティ処理結果をシーンに描画
        
        Args:
            result: エンティティ処理結果
            
        Returns:
            Optional[QGraphicsItem]: 作成されたグラフィックスアイテム、失敗時はNone
        """
        if not result.success or result.data is None:
            return None
        
        data = result.data
        
        if isinstance(data, pdf.LineData):
            return self.draw_line(data)
        elif isinstance(data, pdf.CircleData):
            return self.draw_circle(data)
        elif isinstance(data, pdf.ArcData):
            return self.draw_arc(data)
        elif isinstance(data, pdf.PolylineData):
            return self.draw_polyline(data)
        elif isinstance(data, pdf.TextData):
            return self.draw_text(data)
        else:
            return None
    
    def set_scene_theme(self, theme_name: str) -> None:
        """
        シーンにテーマを適用（背景色に応じてACI 7の色を設定）
        
        Args:
            theme_name: テーマ名（互換性のためだけに残す）
        """
        # 固定の色を設定
        self.bg_color = (255, 255, 255)  # 白背景
        
        # 背景色を適用
        self.scene.setBackgroundBrush(QBrush(QColor(*self.bg_color)))
    
    def apply_color_to_all_items(self, color: Tuple[int, int, int]) -> None:
        """
        シーン内のすべてのアイテムに色を適用
        
        Args:
            color: 適用する色 (R, G, B)
        """
        qcolor = self.rgb_to_qcolor(color)
        for item in self.scene.items():
            if hasattr(item, 'pen'):
                # ペンがあるアイテムは線の色を変更
                pen = item.pen()
                pen.setColor(qcolor)
                item.setPen(pen)
            elif hasattr(item, 'setBrush') and hasattr(item, 'brush'):
                # ブラシがあるアイテムは塗りつぶし色を変更
                brush = item.brush()
                brush.setColor(qcolor)
                item.setBrush(brush)
            elif hasattr(item, 'setDefaultTextColor'):
                # テキストアイテムはテキスト色を変更
                item.setDefaultTextColor(qcolor)
                
    def process_entity(self, entity) -> Optional[QGraphicsItem]:
        """
        DXFエンティティを処理して対応するQGraphicsItemを作成
        
        Args:
            entity: DXFエンティティ
            
        Returns:
            Optional[QGraphicsItem]: 作成されたグラフィックスアイテム
        """
        # エンティティタイプに応じて処理する
        if hasattr(entity, 'dxftype'):
            dxf_type = entity.dxftype()
            print(f"エンティティ処理: {dxf_type}, レイヤー: {entity.dxf.layer if hasattr(entity.dxf, 'layer') else 'なし'}")
            
            # 色処理の準備（BYLAYERの処理）
            color_index = None
            linetype = "CONTINUOUS"
            
            # レイヤー情報を取得
            layer_name = None
            if hasattr(entity.dxf, 'layer'):
                layer_name = entity.dxf.layer
                
                # レイヤーの色を取得
                if self.dxf_doc and layer_name in self.dxf_doc.layers:
                    layer = self.dxf_doc.layers.get(layer_name)
                    if layer:
                        if hasattr(layer, 'color'):
                            color_index = layer.color
                        if hasattr(layer, 'linetype'):
                            linetype = layer.linetype
            
            # エンティティ自身の色を確認
            if hasattr(entity.dxf, 'color'):
                entity_color = entity.dxf.color
                # 0や負の値はBYLAYER、256はBYBLOCKを示す
                if entity_color != 0 and entity_color != 256:
                    color_index = entity_color
            
            # エンティティの線種を確認
            if hasattr(entity.dxf, 'linetype') and entity.dxf.linetype != "BYLAYER":
                linetype = entity.dxf.linetype
            
            # 色情報がなければデフォルト値を使用
            if color_index is None:
                color_index = 7  # デフォルトは白/黒
                
            print(f"色とライン種の解決結果: ACI={color_index}, 線種={linetype}")
            
            # LINE（線）
            if dxf_type == "LINE":
                # 線の各点の座標
                start = (entity.dxf.start.x, entity.dxf.start.y)
                end = (entity.dxf.end.x, entity.dxf.end.y)
                
                # 線の描画データを計算
                line_data = pdf.compute_line_data(start, end, color_index, entity)
                line_data.linetype = linetype
                
                # 線を描画
                return self.draw_line(line_data)
                
            # CIRCLE（円）
            elif dxf_type == "CIRCLE":
                # 円の中心座標と半径
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                
                # 円の描画データを計算
                circle_data = pdf.compute_circle_data(center, radius, color_index, entity)
                circle_data.linetype = linetype
                
                # 円を描画
                return self.draw_circle(circle_data)
                
            # ARC（円弧）
            elif dxf_type == "ARC":
                # 円弧の中心座標と半径
                center = (entity.dxf.center.x, entity.dxf.center.y)
                radius = entity.dxf.radius
                
                # 角度（度数）
                start_angle = entity.dxf.start_angle
                end_angle = entity.dxf.end_angle
                
                # 円弧の描画データを計算
                arc_data = pdf.compute_arc_data(center, radius, start_angle, end_angle, color_index, entity)
                arc_data.linetype = linetype
                
                # 円弧を描画
                return self.draw_arc(arc_data)
                
            # LWPOLYLINE（ポリライン）
            elif dxf_type == "LWPOLYLINE":
                # 頂点リスト
                points = [(vertex[0], vertex[1]) for vertex in entity.get_points()]
                
                # ポリラインの描画データを計算
                polyline_data = pdf.compute_polyline_data(points, color_index, entity)
                polyline_data.linetype = linetype
                
                # ポリラインを描画
                return self.draw_polyline(polyline_data)
                
            # Polyline（旧形式ポリライン）- 3Dを含む
            elif dxf_type == "POLYLINE":
                # 2Dポリラインのみ処理
                if not entity.is_3d_polyline:
                    # 頂点リスト（2D）
                    points = [(vertex.dxf.location.x, vertex.dxf.location.y) for vertex in entity.vertices]
                    
                    # ポリラインの描画データを計算
                    polyline_data = pdf.compute_polyline_data(points, color_index, entity)
                    polyline_data.linetype = linetype
                    
                    # ポリラインを描画
                    return self.draw_polyline(polyline_data)
                    
        return None

    def load_dxf(self, filepath: str) -> bool:
        """
        DXFファイルを読み込みシーンに表示
        
        Args:
            filepath: DXFファイルのパス
            
        Returns:
            bool: 読み込み成功したらTrue
        """
        try:
            # DXFドキュメントを読み込む
            self.dxf_doc = ezdxf.readfile(filepath)
            
            # モデルスペースを取得
            modelspace = self.dxf_doc.modelspace()
            
            # シーンをクリア
            self.scene.clear()
            
            # エンティティを処理
            processed_count = 0
            for entity in modelspace:
                item = self.process_entity(entity)
                if item:
                    processed_count += 1
            
            # グリッドを描画
            self.draw_grid(100, 1000, 1000)
            
            # 座標軸を描画
            self.draw_axes()
            
            # 読み込み結果を表示
            print(f"{processed_count}個のエンティティを処理しました")
            return True
            
        except IOError as e:
            print(f"ファイルの読み込みに失敗しました: {str(e)}")
            return False
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"DXFの処理中にエラーが発生しました: {str(e)}")
            print(error_details)
            return False

    def set_background_color(self, bg_color: Tuple[int, int, int]) -> None:
        """
        シーンの背景色を設定
        
        Args:
            bg_color: 背景色のRGB値 (R, G, B)
        """
        self.bg_color = bg_color
        self.scene.setBackgroundBrush(QBrush(QColor(*bg_color)))
        
        # 背景色に応じてグリッドの色を調整
        self.update_grid_color()
        
    def update_grid_color(self) -> None:
        """背景色に応じてグリッドの色を調整する"""
        # 背景色の明るさを計算
        brightness = sum(self.bg_color) / 3
        
        # 明るい背景には暗いグリッド、暗い背景には明るいグリッド
        if brightness > 128:
            grid_color = (80, 80, 80)  # 暗めのグレー
        else:
            grid_color = (180, 180, 180)  # 明るめのグレー
            
        # グリッドを再描画（あるいはグリッドのアイテムの色を変更）
        # 実装は省略 - 必要に応じて追加
        
    def set_theme(self, bg_color: Tuple[int, int, int], default_color: Tuple[int, int, int]) -> None:
        """
        テーマを設定（背景色と標準の線の色を一度に設定）
        
        Args:
            bg_color: 背景色のRGB値 (R, G, B)
            default_color: 標準の線色のRGB値 (R, G, B)
        """
        # 背景色を設定
        self.set_background_color(bg_color)
        
        # すべてのアイテムの色を変更
        self.apply_color_to_all_items(default_color)
        
        # ACI 7の特殊処理ロジックを更新（背景が黒なら白、背景が白なら黒）
        self.default_color = default_color

    def draw_grid(self, spacing: float, width: float, height: float) -> None:
        """
        グリッドを描画
        
        Args:
            spacing: グリッド間隔
            width: 描画範囲の幅
            height: 描画範囲の高さ
        """
        # 既存のグリッドを削除
        for item in self.grid_items:
            self.scene.removeItem(item)
        self.grid_items = []
        
        # グリッドの色を決定（背景色に基づいて調整）
        brightness = sum(self.bg_color) / 3
        if brightness > 128:
            grid_color = QColor(200, 200, 200)  # 明るい背景用の薄いグレー
        else:
            grid_color = QColor(80, 80, 80)  # 暗い背景用の濃いグレー
        
        # グリッド線の設定
        pen = QPen(grid_color)
        pen.setWidth(0)  # 最小幅
        pen.setStyle(Qt.PenStyle.DotLine)
        
        # 横線を描画
        for y in range(-int(height / 2), int(height / 2) + 1, int(spacing)):
            line = self.scene.addLine(
                -width / 2, y, width / 2, y, pen
            )
            self.grid_items.append(line)
        
        # 縦線を描画
        for x in range(-int(width / 2), int(width / 2) + 1, int(spacing)):
            line = self.scene.addLine(
                x, -height / 2, x, height / 2, pen
            )
            self.grid_items.append(line)
    
    def draw_axes(self) -> None:
        """座標軸を描画"""
        # 既存の座標軸を削除
        for item in self.axes_items:
            self.scene.removeItem(item)
        self.axes_items = []
        
        # X軸は赤、Y軸は緑
        x_axis_pen = QPen(QColor(255, 0, 0))  # 赤
        y_axis_pen = QPen(QColor(0, 200, 0))  # 緑
        
        # 線の太さを設定
        x_axis_pen.setWidth(2)
        y_axis_pen.setWidth(2)
        
        # X軸とY軸を描画
        x_axis = self.scene.addLine(-5000, 0, 5000, 0, x_axis_pen)
        y_axis = self.scene.addLine(0, -5000, 0, 5000, y_axis_pen)
        
        # 参照を保持
        self.axes_items.append(x_axis)
        self.axes_items.append(y_axis)

# インターフェースの簡略化
def create_dxf_adapter(scene: QGraphicsScene) -> DXFSceneAdapter:
    """
    DXFSceneAdapterのインスタンスを作成する補助関数
    
    Args:
        scene: 描画先のグラフィックスシーン
        
    Returns:
        DXFSceneAdapter: 新しいアダプターインスタンス
    """
    return DXFSceneAdapter(scene) 