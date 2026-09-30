"""Script to generate the comprehensive, professional Excel guide with Meiryo UI font
and sophisticated monotone color palette.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_workbook():
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Styles
    FONT_NAME = "Meiryo UI"
    
    # Fonts
    title_font = Font(name=FONT_NAME, size=16, bold=True, color="FFFFFF")
    section_font = Font(name=FONT_NAME, size=12, bold=True, color="FFFFFF")
    sub_section_font = Font(name=FONT_NAME, size=11, bold=True, color="222222")
    header_font = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
    regular_font = Font(name=FONT_NAME, size=9.5, color="222222")
    bold_regular_font = Font(name=FONT_NAME, size=9.5, bold=True, color="111111")
    code_font = Font(name="Consolas", size=9, color="1A1A1A")
    note_font = Font(name=FONT_NAME, size=8.5, italic=True, color="555555")
    
    # Fills (Monotone Palette)
    fill_title = PatternFill(start_color="1F2421", end_color="1F2421", fill_type="solid")       # Very dark charcoal
    fill_section = PatternFill(start_color="333A42", end_color="333A42", fill_type="solid")     # Charcoal grey
    fill_header = PatternFill(start_color="495057", end_color="495057", fill_type="solid")      # Medium dark slate grey
    fill_sub_header = PatternFill(start_color="6C757D", end_color="6C757D", fill_type="solid")  # Slate grey
    fill_zebra = PatternFill(start_color="F8F9FA", end_color="F8F9FA", fill_type="solid")       # Very subtle light grey
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")       # Pure white
    fill_highlight = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")   # Accent light neutral grey
    fill_badge_rec = PatternFill(start_color="343A40", end_color="343A40", fill_type="solid")   # Tag dark
    
    # Borders
    thin_border_side = Side(border_style="thin", color="CCCCCC")
    thick_border_bottom = Side(border_style="medium", color="495057")
    double_border_bottom = Side(border_style="double", color="333333")
    
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    header_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=double_border_bottom)
    section_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thick_border_bottom)

    # Alignments
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=True)
    align_title = Alignment(horizontal="left", vertical="center", indent=1)
    
    # -------------------------------------------------------------
    # Sheet 1: 概要・方針比較 (Summary & Comparisons)
    # -------------------------------------------------------------
    ws1 = wb.create_sheet(title="概要・方針比較")
    ws1.views.sheetView[0].showGridLines = True
    
    # Title Banner
    ws1.merge_cells("A1:G1")
    title_cell = ws1["A1"]
    title_cell.value = "JMeter × AWS Cognito 性能試験 設計方針・比較評価サマリー"
    title_cell.font = title_font
    title_cell.fill = fill_title
    title_cell.alignment = align_title
    ws1.row_dimensions[1].height = 42

    # Subtitle / Metadata
    ws1.merge_cells("A2:G2")
    ws1["A2"].value = "本書は、Cognito 認証を伴う API Gateway 性能試験におけるクライアントクレデンシャル選定、トークン再利用、抽出器の技術指針をまとめたものです。"
    ws1["A2"].font = note_font
    ws1["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.row_dimensions[2].height = 22

    # Section 1 Header: クライアントクレデンシャル比較
    row = 4
    ws1.merge_cells(f"A{row}:G{row}")
    sec1 = ws1[f"A{row}"]
    sec1.value = "1. クライアントクレデンシャル選定方針の比較評価（専用登録 vs 既存流用）"
    sec1.font = section_font
    sec1.fill = fill_section
    sec1.alignment = align_title
    ws1.row_dimensions[row].height = 28

    row += 1
    headers1 = ["評価項目", "重要度", "性能試験専用クレデンシャル登録 (推奨)", "既存クレデンシャルの流用・調整 (非推奨)", "技術的根拠・実運用への影響", "推奨判定"]
    col_spans1 = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "F"), ("G", "G")]
    
    for idx, h_text in enumerate(headers1):
        c_letter = ["A", "B", "C", "D", "E", "G"][idx]
        cell = ws1[f"{c_letter}{row}"]
        cell.value = h_text
        cell.font = header_font
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = header_border
    ws1.merge_cells(f"E{row}:F{row}")
    ws1[f"F{row}"].border = header_border
    ws1.row_dimensions[row].height = 26

    data_cred = [
        ("APIスロットリング隔離", "極めて高", "完全隔離。性能試験が限界に達しても既存業務システムに影響を与えない。", "共連れ停止リスク。負荷試験により既存のApp Clientやユーザープール全体が429超過となる。", "Cognitoトークンエンドポイントには厳格なソフトリミット(例:500-1500 TPS)が存在する。", "◎ 推奨"),
        ("セキュリティ・鍵管理", "極めて高", "試験専用のシークレットを払い出し、試験終了後に即座に無効化・削除可能。", "既存の重要シークレットをJMeterシナリオに設定するため、Git漏洩等の侵害リスクが増大。", "シナリオファイル(JMX)の配布やCI/CD連携時のクレデンシャル漏洩範囲を局所化できる。", "◎ 推奨"),
        ("監査・CloudTrail追跡性", "高", "CloudTrail上で専用ClientIdをフィルタリングするだけで、試験負荷トラフィックを100%識別可能。", "通常トラフィックと試験トラフィックが混濁し、障害調査やアクセス分析が困難になる。", "セキュリティ監査時に性能試験による大量リクエストを「正規のアクセス」と区別して除外できる。", "◎ 推奨"),
        ("トークン有効期限の調整", "中", "試験シナリオ（例: 24時間耐久試験）に合わせてトークン有効期限を個別に柔軟設定可能。", "既存システムのセキュリティ基準（例: 1時間固定）に拘束され、独自変更が許されない。", "App Client単位でトークン有効期限(5分〜24時間)を個別定義できるCognitoの利点を活用可能。", "◎ 推奨"),
        ("OAuthスコープの最小権限", "高", "試験対象となるAPIのスコープ（例: api/read）のみに絞り込み、過剰な権限を剥奪可能。", "既存クライアントが保持する広範な更新・削除・管理者スコープをそのまま持ってしまう。", "テストデータの誤削除や試験対象外の決済系APIへの誤爆リクエストを未然に防止する。", "◎ 推奨"),
        ("試験後クリーンアップ", "中", "App Client自体をボタン1つで削除または非アクティブ化して完全終了。", "試験用に行った設定変更を元に戻す作業が発生し、設定漏れ・先祖返りインシデントの温床となる。", "IaC(Terraform/CloudFormation)管理下でも試験用ワークスペースのみで破棄が容易。", "◎ 推奨"),
    ]

    for item in data_cred:
        row += 1
        ws1.row_dimensions[row].height = 36
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws1[f"A{row}"] = item[0]
        ws1[f"A{row}"].font = bold_regular_font
        ws1[f"A{row}"].alignment = align_left
        
        ws1[f"B{row}"] = item[1]
        ws1[f"B{row}"].font = regular_font
        ws1[f"B{row}"].alignment = align_center
        
        ws1[f"C{row}"] = item[2]
        ws1[f"C{row}"].font = regular_font
        ws1[f"C{row}"].alignment = align_left
        
        ws1[f"D{row}"] = item[3]
        ws1[f"D{row}"].font = regular_font
        ws1[f"D{row}"].alignment = align_left
        
        ws1.merge_cells(f"E{row}:F{row}")
        ws1[f"E{row}"] = item[4]
        ws1[f"E{row}"].font = regular_font
        ws1[f"E{row}"].alignment = align_left
        
        ws1[f"G{row}"] = item[5]
        ws1[f"G{row}"].font = bold_regular_font
        ws1[f"G{row}"].alignment = align_center

        for col_l in ["A", "B", "C", "D", "E", "F", "G"]:
            ws1[f"{col_l}{row}"].fill = fill_curr
            ws1[f"{col_l}{row}"].border = cell_border

    # Section 2 Header: トークン取得方針比較 (都度取得 vs 使い回し)
    row += 2
    ws1.merge_cells(f"A{row}:G{row}")
    sec2 = ws1[f"A{row}"]
    sec2.value = "2. トークン取得方針の比較（APIリクエスト都度取得 vs 有効期間内の使い回し）"
    sec2.font = section_font
    sec2.fill = fill_section
    sec2.alignment = align_title
    ws1.row_dimensions[row].height = 28

    row += 1
    headers2 = ["比較項目", "都度取得方式 (リクエスト毎にCognito呼出)", "有効期間内の使い回し方式 (キャッシュ再利用)", "システム的根拠・影響の詳細", "判定"]
    col_idx2 = [("A", "B"), ("C", "C"), ("D", "D"), ("E", "F"), ("G", "G")]
    
    ws1.merge_cells(f"A{row}:B{row}")
    ws1[f"A{row}"] = headers2[0]
    ws1[f"C{row}"] = headers2[1]
    ws1[f"D{row}"] = headers2[2]
    ws1.merge_cells(f"E{row}:F{row}")
    ws1[f"E{row}"] = headers2[3]
    ws1[f"G{row}"] = headers2[4]
    
    for c_letter in ["A", "B", "C", "D", "E", "F", "G"]:
        ws1[f"{c_letter}{row}"].font = header_font
        ws1[f"{c_letter}{row}"].fill = fill_header
        ws1[f"{c_letter}{row}"].alignment = align_center
        ws1[f"{c_letter}{row}"].border = header_border
    ws1.row_dimensions[row].height = 26

    data_reuse = [
        ("Cognito負荷とスロットリング", "致命的。Cognitoの秒間リクエスト上限に即座に衝突し、HTTP 429 エラーで試験が停止する。", "安全。Cognitoへのアクセスは初回(または1時間毎)の極少回数のみで、制限抵触の恐れが皆無。", "Cognitoは認証基盤であり、超大量トランザクションのAPIゲートウェイと同等負荷を受ける設計ではない。", "使い回し一択"),
        ("試験目的（対象APIの測定）", "歪曲される。測定時間の大部分がCognito認証処理（TLS+RSA署名計算）となり、対象APIが測れない。", "正確。JMeterが印加する負荷の100%がAPI GatewayとバックエンドAPIに集中し、真の限界を測定できる。", "試験目的は「業務APIの性能限界特定」であり「Cognitoの限界測定」ではない。", "使い回し一択"),
        ("レスポンスタイム(レイテンシ)", "大幅悪化。毎回50ms〜200msのCognito認証オーバーヘッドが余計に加算される。", "極めて正確。API GatewayおよびバックエンドAPI自体の純粋なレスポンス時間のみが記録される。", "エッジのAPI GatewayはJWTをインメモリ署名検証(約0.1ms)するため、都度取得は非現実的遅延を生む。", "使い回し一択"),
        ("実運用クライアントの再現性", "非現実的。現実のWebブラウザ・スマホアプリ・マイクロサービスは都度取得などしない。", "完全再現。実運用サービスと同様に、トークン有効期間(例:3600秒)内はキャッシュして使い回す。", "OAuth 2.0 RFC 6749でもアクセストークンは有効期間内キャッシュして再利用することが標準仕様。", "使い回し一択"),
        ("AWS課金コスト", "高コスト。Cognitoの月間アクティブユーザー(MAU)やAPI呼出回数、NAT GW転送量が増大。", "最小コスト。トークン発行回数が数回〜数十回で済むため、課金影響はほぼゼロ。", "秒間数千リクエストを長時間流した場合、数千万回のCognito API呼出課金が発生するリスクを回避。", "使い回し一択"),
    ]

    for item in data_reuse:
        row += 1
        ws1.row_dimensions[row].height = 36
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws1.merge_cells(f"A{row}:B{row}")
        ws1[f"A{row}"] = item[0]
        ws1[f"A{row}"].font = bold_regular_font
        ws1[f"A{row}"].alignment = align_left
        
        ws1[f"C{row}"] = item[1]
        ws1[f"C{row}"].font = regular_font
        ws1[f"C{row}"].alignment = align_left
        
        ws1[f"D{row}"] = item[2]
        ws1[f"D{row}"].font = regular_font
        ws1[f"D{row}"].alignment = align_left
        
        ws1.merge_cells(f"E{row}:F{row}")
        ws1[f"E{row}"] = item[3]
        ws1[f"E{row}"].font = regular_font
        ws1[f"E{row}"].alignment = align_left
        
        ws1[f"G{row}"] = item[4]
        ws1[f"G{row}"].font = bold_regular_font
        ws1[f"G{row}"].alignment = align_center

        for col_l in ["A", "B", "C", "D", "E", "F", "G"]:
            ws1[f"{col_l}{row}"].fill = fill_curr
            ws1[f"{col_l}{row}"].border = cell_border

    # Section 3 Header: 抽出器比較 (JSON Extractor vs 正規表現抽出)
    row += 2
    ws1.merge_cells(f"A{row}:G{row}")
    sec3 = ws1[f"A{row}"]
    sec3.value = "3. JMeterトークン抽出方式の比較（JSON Extractor vs 正規表現抽出）"
    sec3.font = section_font
    sec3.fill = fill_section
    sec3.alignment = align_title
    ws1.row_dimensions[row].height = 28

    row += 1
    headers3 = ["抽出方式", "抽出式・設定値", "メリット", "デメリット・リスク", "推奨ユースケース", "推奨度"]
    
    ws1[f"A{row}"] = headers3[0]
    ws1.merge_cells(f"B{row}:C{row}")
    ws1[f"B{row}"] = headers3[1]
    ws1[f"D{row}"] = headers3[2]
    ws1[f"E{row}"] = headers3[3]
    ws1[f"F{row}"] = headers3[4]
    ws1[f"G{row}"] = headers3[5]

    for c_letter in ["A", "B", "C", "D", "E", "F", "G"]:
        ws1[f"{c_letter}{row}"].font = header_font
        ws1[f"{c_letter}{row}"].fill = fill_header
        ws1[f"{c_letter}{row}"].alignment = align_center
        ws1[f"{c_letter}{row}"].border = header_border
    ws1.row_dimensions[row].height = 26

    data_extractor = [
        ("JSON Extractor (推奨・現代標準)", "$.access_token\nMatch No: 1\nDefault: NOT_FOUND", "構文解析(JSONPath)を行うため、JSONキー順序の変更、改行、スペース等の書式変動に100%耐性がある。極めて直感的。", "正規表現と比較してわずかにJSONパースのCPUオーバーヘッドがある（秒間数万の超高負荷時以外は無視可能）。", "REST API / OAuth2 応答の抽出における現代の標準ベストプラクティス。JMeter 5.x推奨。", "◎ 強く推奨"),
        ("Regular Expression Extractor (正規表現抽出)", "\"access_token\"\\s*:\\s*\"([^\"]+)\"\nTemplate: $1$\nMatch No: 1", "文字列スキャンによる正規表現エンジンのため、CPU負荷・メモリ消費が最も小さい。JMeter初期から存在。", "JSON構造を理解しないため、空白の有無やエスケープシーケンス、改行等でマッチ失敗の脆さがある。可読性が低い。", "JMeter 2.x/3.x時代の旧資産、または負荷生成機自体のCPUリソースが極度に逼迫している場合。", "○ 利用可"),
    ]

    for item in data_extractor:
        row += 1
        ws1.row_dimensions[row].height = 42
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws1[f"A{row}"] = item[0]
        ws1[f"A{row}"].font = bold_regular_font
        ws1[f"A{row}"].alignment = align_left
        
        ws1.merge_cells(f"B{row}:C{row}")
        ws1[f"B{row}"] = item[1]
        ws1[f"B{row}"].font = code_font
        ws1[f"B{row}"].alignment = align_left
        
        ws1[f"D{row}"] = item[2]
        ws1[f"D{row}"].font = regular_font
        ws1[f"D{row}"].alignment = align_left
        
        ws1[f"E{row}"] = item[3]
        ws1[f"E{row}"].font = regular_font
        ws1[f"E{row}"].alignment = align_left
        
        ws1[f"F{row}"] = item[4]
        ws1[f"F{row}"].font = regular_font
        ws1[f"F{row}"].alignment = align_left
        
        ws1[f"G{row}"] = item[5]
        ws1[f"G{row}"].font = bold_regular_font
        ws1[f"G{row}"].alignment = align_center

        for col_l in ["A", "B", "C", "D", "E", "F", "G"]:
            ws1[f"{col_l}{row}"].fill = fill_curr
            ws1[f"{col_l}{row}"].border = cell_border

    # Adjust Column Widths for Sheet 1
    col_widths1 = {"A": 22, "B": 14, "C": 34, "D": 34, "E": 26, "F": 26, "G": 16}
    for col_l, width in col_widths1.items():
        ws1.column_dimensions[col_l].width = width

    # -------------------------------------------------------------
    # Sheet 2: 登場歴史と背景 (History & Evolution)
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="登場歴史と背景")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2.merge_cells("A1:F1")
    t2 = ws2["A1"]
    t2.value = "Web認証・認可アーキテクチャの進化の歴史とステートレス化の必然性"
    t2.font = title_font
    t2.fill = fill_title
    t2.alignment = align_title
    ws2.row_dimensions[1].height = 42

    ws2.merge_cells("A2:F2")
    ws2["A2"].value = "なぜセッションCookieからOAuth 2.0 / JWTへと移行し、API Gatewayでのゼロ通信検証が必要になったのかの体系的記録。"
    ws2["A2"].font = note_font
    ws2["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[2].height = 22

    row = 4
    headers_hist = ["時代・年代", "代表的技術方式", "動作の仕組み・プロトコル", "直面した限界・性能上のボトルネック", "生み出されたブレイクスルー・現在の意義"]
    ws2[f"A{row}"] = headers_hist[0]
    ws2[f"B{row}"] = headers_hist[1]
    ws2[f"C{row}"] = headers_hist[2]
    ws2.merge_cells(f"D{row}:E{row}")
    ws2[f"D{row}"] = headers_hist[3]
    ws2[f"F{row}"] = headers_hist[4]
    
    for c in ["A", "B", "C", "D", "E", "F"]:
        ws2[f"{c}{row}"].font = header_font
        ws2[f"{c}{row}"].fill = fill_header
        ws2[f"{c}{row}"].alignment = align_center
        ws2[f"{c}{row}"].border = header_border
    ws2.row_dimensions[row].height = 26

    hist_data = [
        ("1990年代\n黎明期", "Basic認証\nフォーム認証\nCookieセッション", "サーバー側メモリ/ファイルでセッション(JSESSIONID等)をステートフル管理。ブラウザCookieで識別。", "サーバー増設時にセッション共有ストレージ(DB/KVS)へのアクセスが集中し、性能試験でDBが真っ先にダウン。モバイルアプリ・外部API連携に対応不能。", "認証状態をサーバー側で抱える「ステートフル設計」の限界が露呈。認証の分離要求が高まる。"),
        ("2000年代中盤\nWeb 2.0", "パスワード直接委譲\nOAuth 1.0 (RFC 5849)", "外部サービスにユーザー名/パスワードを入力させる危険運用が横行。OAuth 1.0でHMAC-SHA1署名による認可委託を試みる。", "リクエスト毎の厳密な暗号署名文字列構築が極めて複雑で、モバイルアプリでの実装バグが多発。サーバー側の署名検証計算負荷も深刻な負荷問題に。", "「パスワードを第三者に渡さない認可委譲」の概念確立。しかし署名計算の複雑さから仕様刷新が不可避に。"),
        ("2012年\n標準化", "OAuth 2.0 (RFC 6749)\nBearer Token (RFC 6750)", "通信路暗号化(TLS/HTTPS)を前提とし、署名計算を全廃。HTTPヘッダにBearerトークンを添えるだけのシンプルな仕様に転換。", "トークン自体がランダム文字列（Opaque Token）だったため、APIサーバーが毎回認証サーバーのDBに「有効か？」と問い合わせる(イントロスペクション)負荷が発生。", "マシン間連携(M2M)専用の「Client Credentials」グラントが正式定義。システム間認証のデファクトスタンダードに。"),
        ("2014-2015年\n近代化", "OpenID Connect (OIDC)\nJWT (RFC 7519)", "OAuth 2.0の上にIDトークンを定義(OIDC)。トークン内に属性情報(クレーム)と改ざん検知電子署名を内包するJWTが策定される。", "JWTの肥大化によるHTTPヘッダ帯域圧迫や、即時失効(Revocation)が難しいステートレス性の副作用が議論されるが、性能面では圧倒的優位を確立。", "「認証サーバーに問い合わせずに、APIサーバーが単独で即座に検証できる」完全ステートレスアーキテクチャの完成。"),
        ("現在\nクラウドネイティブ", "AWS Cognito\nAmazon API Gateway\nJWKS エッジ自律検証", "CognitoがJWT(アクセストークン)を発行。API GatewayはCognitoの公開鍵(JWKS)をメモリキャッシュし、エッジでマイクロ秒検証。", "性能試験時にトークンを都度取得すると、本来の対象APIではなくCognitoのトークンエンドポイントがボトルネック(429)になる現象が顕在化。", "トークンを有効期間内キャッシュしてAPI Gatewayに負荷を集中させる性能試験パターンの標準化。"),
    ]

    for item in hist_data:
        row += 1
        ws2.row_dimensions[row].height = 54
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws2[f"A{row}"] = item[0]
        ws2[f"A{row}"].font = bold_regular_font
        ws2[f"A{row}"].alignment = align_center
        
        ws2[f"B{row}"] = item[1]
        ws2[f"B{row}"].font = bold_regular_font
        ws2[f"B{row}"].alignment = align_left
        
        ws2[f"C{row}"] = item[2]
        ws2[f"C{row}"].font = regular_font
        ws2[f"C{row}"].alignment = align_left
        
        ws2.merge_cells(f"D{row}:E{row}")
        ws2[f"D{row}"] = item[3]
        ws2[f"D{row}"].font = regular_font
        ws2[f"D{row}"].alignment = align_left
        
        ws2[f"F{row}"] = item[4]
        ws2[f"F{row}"].font = regular_font
        ws2[f"F{row}"].alignment = align_left

        for col_l in ["A", "B", "C", "D", "E", "F"]:
            ws2[f"{col_l}{row}"].fill = fill_curr
            ws2[f"{col_l}{row}"].border = cell_border

    col_widths2 = {"A": 16, "B": 24, "C": 36, "D": 22, "E": 22, "F": 40}
    for col_l, width in col_widths2.items():
        ws2.column_dimensions[col_l].width = width

    # -------------------------------------------------------------
    # Sheet 3: 動作原理と小学生向け解説 (Principles & Analogy)
    # -------------------------------------------------------------
    ws3 = wb.create_sheet(title="動作原理と小学生向け解説")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3.merge_cells("A1:F1")
    t3 = ws3["A1"]
    t3.value = "動作原理の深掘り ＆ 小学生にもわかる遊園地アナロジー解説"
    t3.font = title_font
    t3.fill = fill_title
    t3.alignment = align_title
    ws3.row_dimensions[1].height = 42

    # Analogy Section
    row = 3
    ws3.merge_cells(f"A{row}:F{row}")
    ws3[f"A{row}"] = "【小学生にもわかる！】テーマパーク（遊園地）と魔法のリストバンドのたとえ話"
    ws3[f"A{row}"].font = section_font
    ws3[f"A{row}"].fill = fill_section
    ws3[f"A{row}"].alignment = align_title
    ws3.row_dimensions[row].height = 28

    row += 1
    ws3.merge_cells(f"A{row}:B{row}")
    ws3[f"A{row}"] = "システムの登場人物"
    ws3.merge_cells(f"C{row}:D{row}")
    ws3[f"C{row}"] = "遊園地でのたとえ"
    ws3.merge_cells(f"E{row}:F{row}")
    ws3[f"E{row}"] = "役割とふるまい"
    
    for c in ["A", "B", "C", "D", "E", "F"]:
        ws3[f"{c}{row}"].font = header_font
        ws3[f"{c}{row}"].fill = fill_header
        ws3[f"{c}{row}"].alignment = align_center
        ws3[f"{c}{row}"].border = header_border
    ws3.row_dimensions[row].height = 24

    analogy_items = [
        ("JMeter (負荷テストツール)", "乗り物が壊れないかテストする「検査員ロボット」", "何万人分もの速さでアトラクションに乗りまくって、安全かどうかチェックする。"),
        ("AWS Cognito (認証サーバー)", "遊園地の正面ゲートにある「王様の受付窓口」", "身分証を確認して、今日有効な「魔法の乗り放題リストバンド」を腕に巻いてくれる。"),
        ("クライアントクレデンシャル", "検査員ロボットが持っている「社員証と暗証番号」", "「私は公式の点検スタッフです」と受付窓口に証明するための秘密のカード。"),
        ("アクセストークン (JWT)", "王様の魔法の印鑑と有効期限が押された「リストバンド」", "これを見せるだけで、アトラクションに何回でも乗れるフリーパス。"),
        ("Amazon API Gateway", "各アトラクションの入口に立っている「門番（係員）」", "リストバンドの魔法の印鑑をチラッと見るだけで通してくれる（受付に電話したりしない！）。"),
        ("バックエンドAPI (Lambda/ECS)", "実際にみんなが乗る「ジェットコースター」", "本当にスピードや耐久力をテストしたい乗り物本体。"),
    ]

    for item in analogy_items:
        row += 1
        ws3.row_dimensions[row].height = 30
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws3.merge_cells(f"A{row}:B{row}")
        ws3[f"A{row}"] = item[0]
        ws3[f"A{row}"].font = bold_regular_font
        ws3[f"A{row}"].alignment = align_left
        
        ws3.merge_cells(f"C{row}:D{row}")
        ws3[f"C{row}"] = item[1]
        ws3[f"C{row}"].font = bold_regular_font
        ws3[f"C{row}"].alignment = align_left
        
        ws3.merge_cells(f"E{row}:F{row}")
        ws3[f"E{row}"] = item[2]
        ws3[f"E{row}"].font = regular_font
        ws3[f"E{row}"].alignment = align_left

        for col_l in ["A", "B", "C", "D", "E", "F"]:
            ws3[f"{col_l}{row}"].fill = fill_curr
            ws3[f"{col_l}{row}"].border = cell_border

    # Technical Principles Section
    row += 2
    ws3.merge_cells(f"A{row}:F{row}")
    ws3[f"A{row}"] = "【技術深掘り】Cognito + API Gateway のトークン検証動作原理（ゼロ通信検証）"
    ws3[f"A{row}"].font = section_font
    ws3[f"A{row}"].fill = fill_section
    ws3[f"A{row}"].alignment = align_title
    ws3.row_dimensions[row].height = 28

    row += 1
    p_headers = ["ステップ", "実行主体", "処理内容・プロトコル", "内部アルゴリズム / 暗号数学的処理", "性能・スケーラビリティ上の特徴"]
    ws3[f"A{row}"] = p_headers[0]
    ws3[f"B{row}"] = p_headers[1]
    ws3.merge_cells(f"C{row}:D{row}")
    ws3[f"C{row}"] = p_headers[2]
    ws3[f"E{row}"] = p_headers[3]
    ws3[f"F{row}"] = p_headers[4]

    for c in ["A", "B", "C", "D", "E", "F"]:
        ws3[f"{c}{row}"].font = header_font
        ws3[f"{c}{row}"].fill = fill_header
        ws3[f"{c}{row}"].alignment = align_center
        ws3[f"{c}{row}"].border = header_border
    ws3.row_dimensions[row].height = 26

    principles_data = [
        ("Step 1", "JMeter", "POST /oauth2/token\ngrant_type=client_credentials", "クライアントIDとシークレットをBasic認証またはPOST本文で送信。", "試験開始時のみ実行。Cognitoの秒間制限に抵触させない。"),
        ("Step 2", "AWS Cognito", "クライアント資格情報の検証と\nJWTアクセストークンの発行", "秘密鍵(RSA Private Key)により Header+Payload のSHA256ハッシュ値を暗号化署名。", "トークンには有効期限(exp: 3600)やスコープ(scope)、鍵ID(kid)が格納される。"),
        ("Step 3", "JMeter", "トークン抽出とメモリ格納\nAPI Gatewayへのリクエスト送信", "JSON Extractor($.access_token)で抽出。\nヘッダ: Authorization: Bearer ${token}", "有効期限内は同一スレッドまたは全スレッドでメモリ上の変数を再利用。"),
        ("Step 4", "API Gateway", "JWKS公開鍵セットの\nインメモリキャッシュ", "Cognitoの /.well-known/jwks.json からRSA公開鍵一覧を取得しメモリ保持。", "初回または鍵ローテーション時のみキャッシュ。通常リクエスト時はCognito通信ゼロ。"),
        ("Step 5", "API Gateway", "暗号数学的自律検証\n(Stateless Verification)", "1. JWTヘッダのkidに対応する公開鍵で電子署名を復号。\n2. expが現在時刻後、issが指定プール、scopeが一致か確認。", "CPUメモリ上で約0.1ミリ秒で完了。CognitoやDBへの通信が一切発生せず、秒間数十万件へスケール。"),
        ("Step 6", "API Gateway\n-> Backend", "リクエスト転送と\nバックエンド業務処理", "認証済みコンテキスト(Claims情報)をヘッダ等に付与してLambda/ECS等へプロキシ転送。", "性能試験では、このステップ（API Gateway＋バックエンド）の処理能力のみを純粋に測定できる。"),
    ]

    for item in principles_data:
        row += 1
        ws3.row_dimensions[row].height = 44
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws3[f"A{row}"] = item[0]
        ws3[f"A{row}"].font = bold_regular_font
        ws3[f"A{row}"].alignment = align_center
        
        ws3[f"B{row}"] = item[1]
        ws3[f"B{row}"].font = bold_regular_font
        ws3[f"B{row}"].alignment = align_center
        
        ws3.merge_cells(f"C{row}:D{row}")
        ws3[f"C{row}"] = item[2]
        ws3[f"C{row}"].font = code_font
        ws3[f"C{row}"].alignment = align_left
        
        ws3[f"E{row}"] = item[3]
        ws3[f"E{row}"].font = regular_font
        ws3[f"E{row}"].alignment = align_left
        
        ws3[f"F{row}"] = item[4]
        ws3[f"F{row}"].font = regular_font
        ws3[f"F{row}"].alignment = align_left

        for col_l in ["A", "B", "C", "D", "E", "F"]:
            ws3[f"{col_l}{row}"].fill = fill_curr
            ws3[f"{col_l}{row}"].border = cell_border

    col_widths3 = {"A": 12, "B": 18, "C": 26, "D": 26, "E": 40, "F": 38}
    for col_l, width in col_widths3.items():
        ws3.column_dimensions[col_l].width = width

    # -------------------------------------------------------------
    # Sheet 4: JMeter実装設計 (JMeter Scenarios)
    # -------------------------------------------------------------
    ws4 = wb.create_sheet(title="JMeter実装設計")
    ws4.views.sheetView[0].showGridLines = True
    
    ws4.merge_cells("A1:F1")
    t4 = ws4["A1"]
    t4.value = "JMeter 5.6.3 トークン再利用・認証シナリオ実装詳細仕様"
    t4.font = title_font
    t4.fill = fill_title
    t4.alignment = align_title
    ws4.row_dimensions[1].height = 42

    ws4.merge_cells("A2:F2")
    ws4["A2"].value = "JMeterにおける4つのトークン使い回しパターンのツリー構成、エレメント設定値、Groovyスクリプト完全リファレンス。"
    ws4["A2"].font = note_font
    ws4["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws4.row_dimensions[2].height = 22

    row = 4
    headers_jm = ["パターン名", "適用推奨シーン", "主要エレメント構成", "トークン共有範囲", "メリット", "デメリット・留意点"]
    for idx, h in enumerate(headers_jm):
        col_l = ["A", "B", "C", "D", "E", "F"][idx]
        ws4[f"{col_l}{row}"] = h
        ws4[f"{col_l}{row}"].font = header_font
        ws4[f"{col_l}{row}"].fill = fill_header
        ws4[f"{col_l}{row}"].alignment = align_center
        ws4[f"{col_l}{row}"].border = header_border
    ws4.row_dimensions[row].height = 26

    jm_patterns = [
        ("パターン1\n動的有効期限判定\n(JSR223 + If)", "2時間以上の長時間耐久試験、浸透試験。実運用クライアントの自動更新挙動を完全再現したい場合。", "JSR223 PreProcessor\nIf Controller (${__groovy(...)})\n └ Cognito Token Request\n    └ JSON Extractor\n    └ JSR223 PostProcessor\nHTTP Request (Target API)", "スレッド個別\nまたはプロパティ連動", "トークン期限切れ(exp)を検知して自動で再取得。試験が何日間続いてもトークン切れで止まらない完全自律型。", "If ControllerやJSR223 Groovyスクリプトの設定が必要でシナリオ構築の難易度がやや高い。"),
        ("パターン2\nsetUpスレッド共有\n(M2M・プロパティ共有)", "1時間以内の高負荷ストレステスト、スパイク試験。Client Credentialsによるマシン間連携。", "setUp Thread Group (1スレッド)\n └ Cognito Token Request\n    └ JSON Extractor\n    └ JSR223 (props.put)\nMain Thread Group (Nスレッド)\n └ Header (${__P(...)})", "全スレッド共有\n(グローバルProperty)", "設定が極めてシンプル。Cognitoへのアクセスが試験全体で完全に「1回だけ」となり、Cognito負荷ゼロを保証。", "トークンの有効期間（デフォルト1時間）を超える長時間試験では、トークン失効により後半全て401エラーとなる。"),
        ("パターン3\nOnce Only Controller\n(一度だけ実行)", "スレッド毎に異なるユーザーIDやセッションを模擬したい場合。各仮想ユーザーの起動時初期化処理。", "Main Thread Group\n └ Once Only Controller\n    └ Cognito Token Request\n       └ JSON Extractor\n └ Target API Request", "スレッド単位\n(Thread Local)", "標準コントローラを置くだけでノンコードで実装可能。各スレッドが最初の1ループ目だけトークン取得する。", "スレッドが終了して再起動されたり、Ramp-up中に新規スレッドが立ち上がる度に都度Cognitoを呼ぶ。"),
        ("パターン4\nInterleave / Module\n(周期間隔更新)", "一定ループ回数（例: 500回呼出ごと）またはタイマー連動で定期的にリフレッシュを挟みたい場合。", "Main Thread Group\n └ Loop Controller\n    ├ Module Controller (Token)\n    └ Target API Request", "スレッド単位", "Groovyを書かずにループカウンタ等で簡易的にリフレッシュを組み込める。", "時間経過ではなくループ回数依存となるため、バックエンドの詰まり等で想定時刻に更新されないリスク。"),
    ]

    for item in jm_patterns:
        row += 1
        ws4.row_dimensions[row].height = 60
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws4[f"A{row}"] = item[0]
        ws4[f"A{row}"].font = bold_regular_font
        ws4[f"A{row}"].alignment = align_center
        
        ws4[f"B{row}"] = item[1]
        ws4[f"B{row}"].font = regular_font
        ws4[f"B{row}"].alignment = align_left
        
        ws4[f"C{row}"] = item[2]
        ws4[f"C{row}"].font = code_font
        ws4[f"C{row}"].alignment = align_left
        
        ws4[f"D{row}"] = item[3]
        ws4[f"D{row}"].font = bold_regular_font
        ws4[f"D{row}"].alignment = align_center
        
        ws4[f"E{row}"] = item[4]
        ws4[f"E{row}"].font = regular_font
        ws4[f"E{row}"].alignment = align_left
        
        ws4[f"F{row}"] = item[5]
        ws4[f"F{row}"].font = regular_font
        ws4[f"F{row}"].alignment = align_left

        for col_l in ["A", "B", "C", "D", "E", "F"]:
            ws4[f"{col_l}{row}"].fill = fill_curr
            ws4[f"{col_l}{row}"].border = cell_border

    # Groovy Scripts Reference
    row += 2
    ws4.merge_cells(f"A{row}:F{row}")
    ws4[f"A{row}"] = "【スクリプト詳細】動的有効期限判定（パターン1）の Groovy 完全コード"
    ws4[f"A{row}"].font = section_font
    ws4[f"A{row}"].fill = fill_section
    ws4[f"A{row}"].alignment = align_title
    ws4.row_dimensions[row].height = 28

    row += 1
    ws4.merge_cells(f"A{row}:B{row}")
    ws4[f"A{row}"] = "エレメント名"
    ws4.merge_cells(f"C{row}:F{row}")
    ws4[f"C{row}"] = "Groovy スクリプト内容"
    for c in ["A", "B", "C", "D", "E", "F"]:
        ws4[f"{c}{row}"].font = header_font
        ws4[f"{c}{row}"].fill = fill_header
        ws4[f"{c}{row}"].alignment = align_center
        ws4[f"{c}{row}"].border = header_border
    ws4.row_dimensions[row].height = 24

    scripts_data = [
        ("JSR223 PreProcessor\n(判定処理)", 
         "long currentTime = System.currentTimeMillis();\nString token = vars.get(\"cognito_access_token\");\nString expiryStr = vars.get(\"token_expiry_timestamp\");\n\nif (token == null || token.isEmpty() || expiryStr == null) {\n    vars.put(\"NEED_TOKEN\", \"true\");\n} else {\n    long expiryTime = Long.parseLong(expiryStr);\n    // 有効期限の60秒前(安全マージン)を過ぎていたら更新フラグON\n    if (currentTime >= (expiryTime - 60000)) {\n        vars.put(\"NEED_TOKEN\", \"true\");\n    } else {\n        vars.put(\"NEED_TOKEN\", \"false\");\n    }\n}"),
        ("JSR223 PostProcessor\n(有効期限計算・保存)",
         "long currentTime = System.currentTimeMillis();\nString expiresInStr = vars.get(\"cognito_expires_in\"); // 例: 3600\nlong expiresInSeconds = (expiresInStr != null) ? Long.parseLong(expiresInStr) : 3600L;\n\n// 有効期限タイムスタンプを計算（ミリ秒）\nlong expiryTimestamp = currentTime + (expiresInSeconds * 1000L);\nvars.put(\"token_expiry_timestamp\", String.valueOf(expiryTimestamp));\nvars.put(\"NEED_TOKEN\", \"false\");\nlog.info(\"Cognito Token updated. Expires at: \" + new Date(expiryTimestamp));"),
    ]

    for item in scripts_data:
        row += 1
        ws4.row_dimensions[row].height = 80
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws4.merge_cells(f"A{row}:B{row}")
        ws4[f"A{row}"] = item[0]
        ws4[f"A{row}"].font = bold_regular_font
        ws4[f"A{row}"].alignment = align_center
        
        ws4.merge_cells(f"C{row}:F{row}")
        ws4[f"C{row}"] = item[1]
        ws4[f"C{row}"].font = code_font
        ws4[f"C{row}"].alignment = align_left

        for col_l in ["A", "B", "C", "D", "E", "F"]:
            ws4[f"{col_l}{row}"].fill = fill_curr
            ws4[f"{col_l}{row}"].border = cell_border

    col_widths4 = {"A": 22, "B": 24, "C": 30, "D": 20, "E": 30, "F": 30}
    for col_l, width in col_widths4.items():
        ws4.column_dimensions[col_l].width = width

    # -------------------------------------------------------------
    # Sheet 5: OpenAPI自動生成仕様 (Automation Tool Specs)
    # -------------------------------------------------------------
    ws5 = wb.create_sheet(title="OpenAPI自動生成ツール仕様")
    ws5.views.sheetView[0].showGridLines = True
    
    ws5.merge_cells("A1:F1")
    t5 = ws5["A1"]
    t5.value = "OpenAPI to JMeter 5.6.3 自動生成スクリプト機能・パラメータ仕様"
    t5.font = title_font
    t5.fill = fill_title
    t5.alignment = align_title
    ws5.row_dimensions[1].height = 42

    ws5.merge_cells("A2:F2")
    ws5["A2"].value = "RHEL 9.8 (Bash) および Windows 11 (PowerShell) で動作する OpenAPI -> JMX 変換ツールの完全仕様。"
    ws5["A2"].font = note_font
    ws5["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws5.row_dimensions[2].height = 22

    row = 4
    headers_tool = ["スクリプト種別", "対応OS環境", "実行コマンド構文", "主要機能・処理内容", "出力ファイル", "GUI確認方法"]
    for idx, h in enumerate(headers_tool):
        col_l = ["A", "B", "C", "D", "E", "F"][idx]
        ws5[f"{col_l}{row}"] = h
        ws5[f"{col_l}{row}"].font = header_font
        ws5[f"{col_l}{row}"].fill = fill_header
        ws5[f"{col_l}{row}"].alignment = align_center
        ws5[f"{col_l}{row}"].border = header_border
    ws5.row_dimensions[row].height = 26

    tool_data = [
        ("シェルスクリプト\n(generate_jmx_from_openapi.sh)", "Red Hat Enterprise Linux\n(RHEL) 9.8", "./generate_jmx_from_openapi.sh \\\n  -i api_spec.yaml \\\n  -o scenario.jmx \\\n  -h localhost \\\n  -p 8080", "1. OpenAPI 3.0/3.1/Swagger 2.0 (YAML/JSON) 解析\n2. スキーマ定義型に基づくランダムテストデータ生成\n3. Cognito OAuth2 Tokenリクエスト自動生成\n4. JSON & 正規表現抽出器の自動組み込み\n5. 固定ヘッダ X-API-KEY: XXXXXXXXXXXX 付与\n6. 最小スレッドグループ (1スレッド/1ループ)", "output.jmx\nresults.jtl\njmeter.log", "JMeter GUIを起動し、\n[ファイル] -> [開く] で JMXを選択。\n[View Results Tree] から results.jtl を開く。"),
        ("PowerShellスクリプト\n(generate_jmx_from_openapi.ps1)", "Microsoft Windows 11\n(PowerShell 5.1 / 7+)", ".\\generate_jmx_from_openapi.ps1 `\n  -InputFile api_spec.json `\n  -OutputFile scenario.jmx `\n  -HostName localhost `\n  -Port 8080", "Windowsネイティブ環境での完全自動変換。\nパスパラメータ({id})置換、クエリ文字列生成、JSONリクエストボディの型安全な自動モック生成に対応。\nCognito Client CredentialsフローとAuthorizationヘッダ自動バインド。", "output.jmx\nresults.jtl\njmeter.log", "Windows上の JMeter GUI (jmeter.bat) からJMXを開き、緑色の開始ボタンで実行後、JTLをグラフィカル確認可能。"),
    ]

    for item in tool_data:
        row += 1
        ws5.row_dimensions[row].height = 75
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws5[f"A{row}"] = item[0]
        ws5[f"A{row}"].font = bold_regular_font
        ws5[f"A{row}"].alignment = align_center
        
        ws5[f"B{row}"] = item[1]
        ws5[f"B{row}"].font = bold_regular_font
        ws5[f"B{row}"].alignment = align_center
        
        ws5[f"C{row}"] = item[2]
        ws5[f"C{row}"].font = code_font
        ws5[f"C{row}"].alignment = align_left
        
        ws5[f"D{row}"] = item[3]
        ws5[f"D{row}"].font = regular_font
        ws5[f"D{row}"].alignment = align_left
        
        ws5[f"E{row}"] = item[4]
        ws5[f"E{row}"].font = code_font
        ws5[f"E{row}"].alignment = align_center
        
        ws5[f"F{row}"] = item[5]
        ws5[f"F{row}"].font = regular_font
        ws5[f"F{row}"].alignment = align_left

        for col_l in ["A", "B", "C", "D", "E", "F"]:
            ws5[f"{col_l}{row}"].fill = fill_curr
            ws5[f"{col_l}{row}"].border = cell_border

    # Data Types Generation Rules Table
    row += 2
    ws5.merge_cells(f"A{row}:F{row}")
    ws5[f"A{row}"] = "【テストデータ生成ルール】OpenAPIデータ型からJMeter初期値への自動マッピング仕様"
    ws5[f"A{row}"].font = section_font
    ws5[f"A{row}"].fill = fill_section
    ws5[f"A{row}"].alignment = align_title
    ws5.row_dimensions[row].height = 28

    row += 1
    headers_dt = ["OpenAPIデータ型", "フォーマット指定", "生成ロジック / 乱数ルール", "生成される値の具体例", "適用箇所", "カスタマイズ性"]
    for idx, h in enumerate(headers_dt):
        col_l = ["A", "B", "C", "D", "E", "F"][idx]
        ws5[f"{col_l}{row}"] = h
        ws5[f"{col_l}{row}"].font = header_font
        ws5[f"{col_l}{row}"].fill = fill_header
        ws5[f"{col_l}{row}"].alignment = align_center
        ws5[f"{col_l}{row}"].border = header_border
    ws5.row_dimensions[row].height = 26

    dt_data = [
        ("string", "uuid / date / email / なし", "フォーマット指定に応じた疑似ランダム文字列生成。指定なし時は英数字8文字乱数。", "\"c9bf9e57-1685-4c89-bafb-ff5af830be8a\"\n\"test_user_782@example.com\"\n\"random_str_a1b2c3\"", "パス変数, クエリ, Body", "OpenAPIのexample値があればそれを最優先採用"),
        ("integer / number", "int32 / int64 / float / なし", "minimum / maximum の制約内、または 1〜1000 の範囲でランダム整数/実数を生成。", "42\n100\n99.5", "パス変数(ID), クエリ(limit), Body", "schemaのdefaultまたはenumから自動選択"),
        ("boolean", "なし", "50%の確率で true または false を生成。", "true / false", "クエリパラメータ, Body", "boolean型スキーマに対応"),
        ("array", "items で型指定", "items スキーマに基づき、1〜3件のランダム要素を持つJSON配列を生成。", "[\"tag_1\", \"tag_2\"]\n[101, 102]", "リクエストBody, クエリ(配列)", "要素数・最大最小アイテム数に準拠"),
        ("object", "properties で型指定", "各プロパティの型に応じて再帰的にランダムデータを生成し、ネストJSONを構築。", "{\n  \"userId\": \"usr_123\",\n  \"status\": \"active\"\n}", "リクエストBody (application/json)", "ネストオブジェクト・参照($ref)に対応"),
    ]

    for item in dt_data:
        row += 1
        ws5.row_dimensions[row].height = 36
        fill_curr = fill_zebra if row % 2 == 0 else fill_white
        
        ws5[f"A{row}"] = item[0]
        ws5[f"A{row}"].font = bold_regular_font
        ws5[f"A{row}"].alignment = align_center
        
        ws5[f"B{row}"] = item[1]
        ws5[f"B{row}"].font = regular_font
        ws5[f"B{row}"].alignment = align_center
        
        ws5[f"C{row}"] = item[2]
        ws5[f"C{row}"].font = regular_font
        ws5[f"C{row}"].alignment = align_left
        
        ws5[f"D{row}"] = item[3]
        ws5[f"D{row}"].font = code_font
        ws5[f"D{row}"].alignment = align_left
        
        ws5[f"E{row}"] = item[4]
        ws5[f"E{row}"].font = regular_font
        ws5[f"E{row}"].alignment = align_center
        
        ws5[f"F{row}"] = item[5]
        ws5[f"F{row}"].font = regular_font
        ws5[f"F{row}"].alignment = align_left

        for col_l in ["A", "B", "C", "D", "E", "F"]:
            ws5[f"{col_l}{row}"].fill = fill_curr
            ws5[f"{col_l}{row}"].border = cell_border

    col_widths5 = {"A": 22, "B": 20, "C": 34, "D": 32, "E": 18, "F": 30}
    for col_l, width in col_widths5.items():
        ws5.column_dimensions[col_l].width = width

    # Save to file
    out_file = r"C:\Users\taka_\Agy\JMeter_Cognito_Token_Agy\Cognito_JMeter_Performance_Testing_Guide.xlsx"
    wb.save(out_file)
    print(f"Successfully generated Excel guide at: {out_file}")

if __name__ == "__main__":
    build_workbook()
