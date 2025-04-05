# Qt のテキスト配置システムと CAD システムとの違い

## はじめに

Qt フレームワークと CAD システム（DXF など）では、テキストの配置方法に大きな違いがあります。この文書では、Qt の `QGraphicsTextItem` におけるベースラインからのスペース計算方法と、CAD システムのテキスト配置との違いについて調査結果をまとめています。

## Qt のテキスト配置の基本概念

Qt のテキスト描画システムは、フォントメトリクスに基づいて以下の要素で構成されています：

### 1. 主要な測定値

- **キャップハイト (Cap Height)**:
  - 大文字のフラット文字（H や I など）の高さ
  - `QFontMetrics::capHeight()` で取得可能

- **アセント (Ascent)**:
  - ベースラインから文字の最上部までの距離
  - `QFontMetrics::ascent()` で取得可能

- **ディセント (Descent)**:
  - ベースラインから文字の最下部までの距離
  - `QFontMetrics::descent()` で取得可能

- **行間隔 (Line Spacing)**:
  - 行と行の間の距離
  - `lineSpacing() = leading() + height()`

### 2. バウンディングレクト

- **バウンディングレクト (Bounding Rectangle)**:
  - テキスト全体を囲む矩形領域
  - `QFontMetrics::boundingRect()` で取得可能

- **タイトバウンディングレクト (Tight Bounding Rectangle)**:
  - より厳密にテキストを囲む矩形
  - `QFontMetrics::tightBoundingRect()` で取得可能
  - Windows では計算コストが高い

## CAD システムと Qt の違い

CAD システム（DXF など）と Qt でのテキスト配置には、以下のような本質的な違いがあります：

### 1. 基準点の扱い

- **CAD システム**:
  - 通常、挿入ポイント（insertion point）を基準に配置
  - テキストは挿入点から特定の方向へ展開される
  - 挿入点の位置は通常左下、中央下などから選択可能

- **Qt システム**:
  - `QGraphicsTextItem` の boundingRect の左上端（0, 0）を基準に配置
  - テキスト全体の矩形が基準となる

### 2. 余白（マージン）の扱い

- **CAD システム**:
  - 余白は最小限または厳密に定義される
  - 精密な技術図面の要件を満たすように設計

- **Qt システム**:
  - 自動的に余白（マージン）を追加し、読みやすさを優先
  - `QTextDocument` のマージン設定が影響する

### 3. 行間の計算方法

- **CAD システム**:
  - 通常、行間は明示的に指定する必要がある
  - フォントの高さに基づいて計算

- **Qt システム**:
  - `QTextDocument` のスタイルシートで調整可能
  - 例：`document()->setDefaultStyleSheet("p { margin: 0; }")`
  - 行の高さは自動的に計算され、余分なスペースが追加されることがある

## テキスト配置の調整方法

### Qt での調整方法

1. **ドキュメントマージンの調整**:
   ```cpp
   textItem->document()->setDocumentMargin(0);
   ```

2. **スタイルシートの適用**:
   ```cpp
   textItem->document()->setDefaultStyleSheet("p { margin: 0; }");
   ```

3. **フォントメトリクスを使用した位置調整**:
   ```cpp
   QFontMetricsF fm(textItem->font());
   qreal ascent = fm.ascent();
   textItem->setPos(x, y - ascent); // ベースライン位置に合わせる
   ```

### CAD 互換性を高める方法

1. **カスタムテキストアイテムの作成**:
   - `QGraphicsItem` を継承してカスタムの描画ロジックを実装
   - `paint()` メソッド内で `QPainter::drawText()` を直接使用

2. **変換レイヤーの実装**:
   - CAD の挿入点座標を Qt の座標系に変換するロジックを作成
   - アライメント（左揃え、中央揃えなど）に基づいて調整

3. **オフセット計算**:
   - フォントメトリクスを使用して正確なオフセットを計算
   - テキスト配置時にこのオフセットを適用

## まとめ

Qt と CAD システムのテキスト配置の違いは、それぞれの設計目的に由来しています：

- **Qt**: 一般的な UI 向けに設計され、見た目の美しさと読みやすさを優先
- **CAD**: 精密な技術図面向けに設計され、正確な位置と寸法を優先

これらの違いを理解し、必要に応じて調整することで、Qt ベースの CAD アプリケーションでもより正確なテキスト配置が可能になります。

CAD アプリケーションを開発する際には、Qt の自動的なレイアウト調整機能に依存するのではなく、フォントメトリクスを使用して明示的に位置を計算することが重要です。

## 具体的な相違点と事例

### 事例：寸法表示

CAD システムでは、寸法テキストは以下のような厳密な配置が必要です：

```
    150
<---------->
   ^
   |
   |
   v
  5.00
<------>
  600
```

このようなケースでの相違点：

1. **CAD システム**:
   - テキスト「5.00」の位置は厳密に指定された座標に配置
   - 数値の基準点が明確（挿入点）

2. **Qt システム**:
   - テキストの周囲に余分なスペースが自動的に追加される
   - バウンディングボックスベースの配置により、実際のテキスト位置が予測しにくい

### 測定値の違い

同じフォントサイズでも、測定される値が異なります：

| 測定項目       | CAD システム | Qt システム |
|---------------|-------------|------------|
| テキスト高さ    | フォントの定義による | アセント + ディセント + 余分なスペース |
| ベースライン位置 | 明示的に定義  | フォントメトリクスから計算 |
| 文字間隔       | 固定またはカーニングテーブルによる | フォントのカーニング + 追加の調整 |

### 実装上の注意点

1. **精密な配置が必要な場合**:
   - Qt のテキストアイテムをそのまま使用せず、カスタム描画を検討
   - `QPainter::drawText()` を直接使用する際に、適切な位置調整を行う

2. **DXF からの変換時**:
   - DXF のテキスト挿入点から Qt の座標への正確な変換を実装
   - フォントスタイル（太字、イタリックなど）の違いによる位置の変化を考慮

3. **テスト**:
   - 異なるフォント、サイズ、スタイルでのテキスト配置をテスト
   - 特に日本語などの非ラテン文字での動作確認が重要

## DXF ビューアにおける実装方針

この調査結果に基づき、DXF ビューアでのテキスト表示に関する実装方針を以下にまとめます：

### 1. カスタムテキストアイテムの実装

```python
class DxfTextItem(QGraphicsItem):
    def __init__(self, text, position, height, rotation=0, style=None, parent=None):
        super().__init__(parent)
        self.text = text
        self.position = position  # DXF 挿入点
        self.height = height      # テキスト高さ
        self.rotation = rotation
        self.style = style or {}
        
    def paint(self, painter, option, widget):
        # フォントの設定
        font = QFont(self.style.get("font_family", "Arial"))
        font.setPointSizeF(self.height)
        painter.setFont(font)
        
        # 回転の適用
        painter.save()
        painter.translate(self.position.x(), self.position.y())
        painter.rotate(self.rotation)
        
        # 水平方向の配置（左/中央/右）に応じた調整
        metrics = QFontMetricsF(font)
        x_offset = 0
        if self.style.get("alignment") == "center":
            x_offset = -metrics.horizontalAdvance(self.text) / 2
        elif self.style.get("alignment") == "right":
            x_offset = -metrics.horizontalAdvance(self.text)
            
        # テキスト描画（ベースラインに合わせる）
        painter.drawText(x_offset, 0, self.text)
        painter.restore()
```

### 2. DXF テキストエンティティの変換

```python
def convert_dxf_text_to_graphics_item(dxf_text_entity, scale_factor=1.0):
    """DXF テキストエンティティを Qt グラフィックスアイテムに変換"""
    
    # DXF テキスト属性の取得
    text = dxf_text_entity.dxf.text
    position = QPointF(
        dxf_text_entity.dxf.insert.x * scale_factor,
        -dxf_text_entity.dxf.insert.y * scale_factor  # Y 軸の反転
    )
    height = dxf_text_entity.dxf.height * scale_factor
    rotation = dxf_text_entity.dxf.rotation
    
    # スタイル情報の準備
    style = {
        "font_family": "Arial",  # DXF スタイルテーブルから取得するのが理想的
        "alignment": "left"      # DXF 水平配置から変換
    }
    
    # DXF 水平配置の変換
    if hasattr(dxf_text_entity.dxf, "halign"):
        if dxf_text_entity.dxf.halign == 1:
            style["alignment"] = "center"
        elif dxf_text_entity.dxf.halign in [2, 3]:
            style["alignment"] = "right"
    
    # カスタムテキストアイテムの作成
    return DxfTextItem(text, position, height, rotation, style)
```

### 3. テキスト配置のデバッグ補助

```python
def debug_text_placement(scene, text_item):
    """テキスト配置をデバッグするための補助マーカーを追加"""
    
    # 挿入点のマーカー（赤い十字）
    cross = QGraphicsItemGroup()
    pos = text_item.position
    
    # 水平線
    line_h = QGraphicsLineItem(pos.x() - 5, pos.y(), pos.x() + 5, pos.y())
    line_h.setPen(QPen(QColor("red"), 0.5))
    cross.addToGroup(line_h)
    
    # 垂直線
    line_v = QGraphicsLineItem(pos.x(), pos.y() - 5, pos.x(), pos.y() + 5)
    line_v.setPen(QPen(QColor("red"), 0.5))
    cross.addToGroup(line_v)
    
    # バウンディングボックス（青い矩形）
    rect = text_item.boundingRect()
    box = QGraphicsRectItem(rect)
    box.setPen(QPen(QColor("blue"), 0.5))
    box.setPos(text_item.pos())
    
    # シーンへの追加
    scene.addItem(cross)
    scene.addItem(box)
```

### 4. フォントメトリクス活用戦略

CAD の正確なテキスト配置を実現するためには、Qt のフォントメトリクスを効果的に活用する必要があります：

1. **キャップハイトに基づく調整**：
   - DXF のテキスト高さはキャップハイト（大文字の高さ）で定義されることが多い
   - Qt では `QFontMetrics::capHeight()` を使用して調整可能

2. **アセントとディセントの考慮**：
   - 下付き文字やアンダースコアがある場合、ディセントを考慮
   - 上付き文字やアクセント記号がある場合、アセントを考慮

3. **文字間隔の調整**：
   - DXF の等幅配置とは異なる場合があるため、必要に応じて調整
   - `QFontMetrics::horizontalAdvance()` を使用して計算

### 5. テストと検証戦略

テキスト表示の実装を検証するためのテスト戦略：

1. **基準テストケース**：
   - 単純な数字とアルファベットの配置テスト
   - 異なる配置（左/中央/右揃え）のテスト
   - 異なる回転角度のテスト

2. **複雑なケース**：
   - 日本語などのマルチバイト文字のテスト
   - 特殊記号や数式を含むテキストのテスト
   - マルチラインテキストのテスト

3. **比較検証**：
   - 商用 CAD ソフトと同じ DXF ファイルを開いて表示を比較
   - 出力された PDF などでの表示を比較 