あなたは、空のディレクトリから新しい Skill リポジトリを実装してください。

# 作りたい Skill の概要

この Skill は、ドキュメント・GitHubリポジトリ・Pull Request・設計メモ・仕様書などの「理解対象」を、ユーザーが理解しやすい形の単一 HTML ファイルとして出力するための Skill です。

ただし、この Skill の目的は、固定された図解テンプレートを生成することではありません。

目的は、同じ理解対象を、ユーザーごとの理解しやすい表現に変換しやすくすることです。

たとえば、ある人はテーブル表現が理解しやすいかもしれません。別の人はワークツリー表現、カード表現、FAQ、比較表、シーケンス、ストーリー形式、コードリーディング順序、影響範囲マップのほうが理解しやすいかもしれません。

この Skill は、そのような個人差に対応するために、最終成果物として以下を含む単一 HTML ファイルを生成します。

* iframe 内: 対象理解を助ける図解・説明 UI
* iframe 外: ユーザーが別の AI チャットにコピペしやすいプロンプトテンプレート集
* 必要に応じて inline JavaScript
* 必要に応じて inline CSS
* 外部依存なしで開ける self-contained HTML

# 重要な設計思想

## やりたいこと

この Skill は、以下の流れで動作するものとして設計してください。

```txt
Input
  - pasted document
  - repository summary
  - PR diff summary
  - README
  - design document
  - any technical/business text

↓ analyze

core.yaml
  - 理解対象の意味構造
  - 概念
  - 関係
  - 重要度
  - 難易度
  - 根拠
  - source references

↓ view strategy

view.yaml
  - どのような人に向けるか
  - どの表現形式が向いているか
  - 避けたい表現は何か
  - 情報密度
  - 強調観点

↓ generate

single HTML file
  - iframe 内に、今回の理解対象に合わせた図解 UI
  - iframe 外に、コピペしやすいプロンプトテンプレート
```

## やってはいけないこと

以下のような設計にはしないでください。

* Webアプリケーションとして実装する
* サーバーやAPI routeを前提にする
* チャットUIを作る
* iframe外にClaudeやAIとの会話機能を実装する
* HTMLを固定rendererで機械的に生成するだけにする
* table / tree / faq など数種類の固定テンプレートに閉じる
* YAMLを単なるHTML設計図として扱う
* 外部CDNや外部CSSに依存する
* iframe内HTMLから外部通信する
* iframe内HTMLから親DOMへアクセスする
* API keyやsecretをHTMLに含める

## 大事な考え方

この Skill の中心は renderer ではありません。

中心は以下です。

1. 理解対象を意味構造化する core.yaml
2. ユーザーの理解スタイルを表す view.yaml
3. HTML生成ルールに従って、柔軟な iframe 内 UI を生成すること
4. iframe外に、ユーザーが再生成・変換・深掘りを依頼しやすいプロンプトテンプレートを置くこと

# 成果物

このリポジトリには、少なくとも以下を作成してください。

```txt
adaptive-understanding-html/
  SKILL.md
  agents/
    openai.yaml
  scripts/
    build_html.py
    validate_html.py
  references/
    core-yaml-schema.md
    view-yaml-schema.md
    html-generation-rules.md
    prompt-template-patterns.md
    output-html-structure.md
    examples.md
  README.md
```

Skill 名は `adaptive-understanding-html` としてください。

# SKILL.md の要件

`SKILL.md` は、この Skill のエントリーポイントです。

以下のような frontmatter を持たせてください。

```yaml
---
name: adaptive-understanding-html
description: generate a single self-contained html file that helps users understand documents, repositories, pull requests, design notes, or specifications through personalized visual explanations. use when the user wants an html output with an iframe-based explanation area and copyable prompt templates for asking another ai to regenerate or transform the explanation into tables, worktrees, cards, faq, comparison views, sequence views, story views, or other user-friendly representations.
---
```

本文には、Skill実行時の具体的な手順を書いてください。

特に以下を明記してください。

* 入力を読む
* 必要に応じて core.yaml を作る
* 必要に応じて view.yaml を作る
* iframe内に表示するHTMLを生成する
* iframe外にプロンプトテンプレート集を生成する
* 最終的に単一HTMLファイルを出力する
* `scripts/build_html.py` を使ってHTMLを組み立てる
* `scripts/validate_html.py` で安全性を検査する
* 問題があれば修正してからユーザーに渡す

# core.yaml の設計

`references/core-yaml-schema.md` に core.yaml の考え方と schema を書いてください。

core.yaml は UI ではなく、理解対象の意味構造を表します。

例:

```yaml
version: core/v1
target:
  type: document
  title: string
  summary: string
  source_label: string

concepts:
  - id: string
    label: string
    kind: file | module | function | concept | flow | decision | risk | actor | requirement | unknown
    summary: string
    detail: string
    importance: low | medium | high
    difficulty: low | medium | high
    confidence: number
    source_refs:
      - id: string
        path: string
        url: string
        excerpt: string
        lines:
          start: number
          end: number

relations:
  - id: string
    from: string
    to: string
    type: depends_on | calls | contains | changes | affects | explains | contrasts | sequence_next | blocks | supports | unknown
    label: string
    reason: string
    confidence: number

questions:
  - id: string
    question: string
    why_it_matters: string
    related_concept_ids:
      - string

risks:
  - id: string
    label: string
    description: string
    severity: low | medium | high
    related_concept_ids:
      - string

source_refs:
  - id: string
    title: string
    type: file | diff | document | url | note
    path: string
    url: string
    excerpt: string
```

core.yaml は、固定的なHTML構造を指示するものではありません。あくまで、対象を理解するための意味構造です。

# view.yaml の設計

`references/view-yaml-schema.md` に view.yaml の考え方と schema を書いてください。

view.yaml は、そのユーザーにどのように見せると理解しやすいかを表します。

例:

```yaml
version: view/v1
audience:
  role: engineer | designer | product_manager | business | beginner | custom
  familiarity: beginner | intermediate | advanced | unknown
  stated_preferences:
    - worktree
    - sequence
  dislikes:
    - dense_table

intent:
  primary_goal: "この対象を短時間で理解する"
  secondary_goals:
    - "重要概念を把握する"
    - "次に読むべき箇所を知る"

presentation:
  preferred_forms:
    - worktree
    - cards
    - faq
  avoid_forms:
    - dense_table
  density: low | medium | high
  tone: concise | friendly | technical | tutorial
  visual_style: "clean, readable, not decorative"
  interaction_level: low | medium | high

focus:
  emphasize:
    - purpose
    - impact
    - dependencies
    - risks
    - reading_order
  de_emphasize:
    - minor_details

html_generation_policy:
  allow_creative_layout: true
  must_include:
    - overview
    - source_references
    - prompt_templates
  should_include:
    - progressive_disclosure
    - visual_grouping
    - next_questions
  must_not_include:
    - external_script
    - remote_css
    - network_request
```

view.yaml も固定rendererへの命令ではありません。
HTMLを生成するAIに対して、表現方針を伝えるための中間表現です。

# HTML の最終構造

`references/output-html-structure.md` に、最終HTMLの基本構造を書いてください。

最終HTMLは self-contained な単一ファイルです。

最低限、以下を含めてください。

```txt
<html>
  <head>
    inline style
  </head>
  <body>
    app shell
      header
      main layout
        prompt template panel
        iframe preview panel
      optional metadata panel
      optional source references panel
    inline script
  </body>
</html>
```

## iframe 内

iframe内には、今回の理解対象に合わせた図解UIを表示してください。

iframe内の表現は固定しないでください。

たとえば、view.yaml と対象に応じて、以下を自由に組み合わせてよいです。

* table
* worktree
* cards
* faq
* comparison
* sequence
* timeline
* reading path
* risk map
* dependency map
* glossary
* beginner tutorial
* review checklist
* decision map
* impact map

iframe内HTMLは、できるだけ親HTMLから独立した document としてください。

iframeは `srcdoc` または JavaScript による安全な注入で表示してください。

iframeには `sandbox` を付けてください。

原則として以下を使ってください。

```html
<iframe sandbox="allow-scripts"></iframe>
```

`allow-same-origin` は付けないでください。

## iframe 外

iframe外にはチャットUIを作らないでください。

代わりに、コピペしやすいプロンプトテンプレート集を置いてください。

目的は、ユーザーが別AIに対して以下のような依頼をしやすくすることです。

* テーブル表記で再生成して
* ワークツリー表記で再生成して
* 初心者向けにして
* 影響範囲中心にして
* コードを読む順番が分かる形にして
* リスク中心にして
* FAQ形式にして
* より短くして
* より詳しくして
* iframe内HTMLだけ差し替えたい
* このHTML全体を再生成したい

各テンプレートには copy button を付けてください。

JavaScript で clipboard copy を実装して構いません。

# プロンプトテンプレートの要件

`references/prompt-template-patterns.md` に、HTMLへ埋め込むべきプロンプトテンプレートのパターンを書いてください。

生成HTMLの iframe外には、少なくとも以下のプロンプトテンプレートを含めてください。

## 1. HTML全体を再生成するテンプレート

目的:

* 現在のHTML全体を別AIに渡して、別の表現で再生成してもらう

内容に含めるもの:

* 現在の理解対象の概要
* core.yaml
* view.yaml
* 希望する表現
* 出力は単一HTMLファイルにすること
* iframe内に新しい理解UIを置くこと
* iframe外にはプロンプトテンプレートを残すこと
* 外部依存なしにすること

## 2. iframe内HTMLだけ再生成するテンプレート

目的:

* 外側のHTML構造は維持し、iframe内の図解部分だけ変えたい

内容に含めるもの:

* core.yaml
* 現在のview.yaml
* 希望する表現
* 出力は iframe 内に入れる HTML document のみ
* 外部通信禁止
* inline CSS / inline JS 可

## 3. テーブル表現テンプレート

目的:

* テーブルで理解しやすい人向け

含める要件:

* 概念一覧
* 重要度
* 難易度
* 関係性
* 根拠
* 次に読むべき箇所

## 4. ワークツリー表現テンプレート

目的:

* リポジトリ構造や階層で理解したい人向け

含める要件:

* tree view
* directory / file / concept の階層
* どこから読むべきか
* 変更影響が強い箇所
* expandable section

## 5. 初心者向けテンプレート

目的:

* 前提知識が少ない人向け

含める要件:

* 専門用語の説明
* なぜ重要か
* 3ステップで理解する導線
* 例え話
* 質問例

## 6. エンジニア向けテンプレート

目的:

* 実装者・レビューア向け

含める要件:

* 依存関係
* 変更ファイル
* 読む順番
* レビュー観点
* リスク
* テスト観点

## 7. PdM / Biz向けテンプレート

目的:

* 技術詳細よりも目的・影響・判断材料を知りたい人向け

含める要件:

* 何が変わるか
* なぜ重要か
* ユーザー影響
* 業務影響
* 意思決定ポイント
* リスクと確認事項

## 8. 自由変換テンプレート

目的:

* ユーザーが自由に「こういう表現にしたい」と書ける

テンプレート内に `{{希望する表現}}` のような placeholder を含めてください。

# HTML生成ルール

`references/html-generation-rules.md` に、AIがHTMLを生成するときに守るルールを書いてください。

## 安全性ルール

以下は禁止です。

* 外部 script
* 外部 CSS
* 外部 iframe
* fetch
* XMLHttpRequest
* WebSocket
* localStorage
* sessionStorage
* document.cookie
* window.parent へのアクセス
* window.top へのアクセス
* top navigation
* form submit
* API key や secret の埋め込み
* 大量の原文全文の埋め込み

## 許可するもの

以下は許可します。

* inline CSS
* inline JS
* iframe内で完結するUI interaction
* details / summary
* tabs
* accordion
* filter
* copy button
* collapsible tree
* client-side only interactions

## UIルール

* ユーザーの view.yaml に合わせて表現を選ぶ
* fixed templateではなく、理解しやすさを優先する
* 情報量が多い場合は progressive disclosure を使う
* 重要度・難易度・confidence を視覚的に表す
* source reference を表示する
* 次に読むべき箇所を表示する
* 次にAIへ聞くとよい質問を表示する
* アクセシビリティを意識する
* responsive にする
* prefers-reduced-motion を考慮する

# scripts/build_html.py の要件

`scripts/build_html.py` を実装してください。

このスクリプトは、AIが生成した構造化データとHTML断片をもとに、単一HTMLファイルを組み立てるための補助スクリプトです。

ただし、これは固定rendererではありません。

このスクリプトの役割は以下に限定してください。

* outer HTML shell を組み立てる
* iframe 用HTMLを安全に埋め込む
* prompt templates をHTMLに埋め込む
* core.yaml / view.yaml をmetadataとして埋め込む
* copy button 用のJSを埋め込む
* self-contained HTMLとして保存する

このスクリプトが、core.yamlを機械的に解釈して固定表現の図解を作る設計にはしないでください。

入力例:

```bash
python scripts/build_html.py \
  --core core.yaml \
  --view view.yaml \
  --iframe iframe.html \
  --prompts prompts.json \
  --output output.html
```

`prompts.json` は、以下のような構造にしてください。

```json
[
  {
    "id": "regenerate-full",
    "title": "HTML全体を再生成する",
    "description": "現在のHTML全体を、希望する表現で再生成したいときに使う",
    "prompt": "..."
  },
  {
    "id": "iframe-only-table",
    "title": "iframe内をテーブル表現にする",
    "description": "iframe内の理解UIだけをテーブル表現に変換したいときに使う",
    "prompt": "..."
  }
]
```

# scripts/validate_html.py の要件

`scripts/validate_html.py` を実装してください。

このスクリプトは、生成されたHTMLに危険なパターンがないか確認します。

最低限、以下を検出してください。

* `<script src=`
* `<iframe` の外部 src
* `<object`
* `<embed`
* `<link rel="stylesheet"`
* `fetch(`
* `XMLHttpRequest`
* `WebSocket`
* `localStorage`
* `sessionStorage`
* `document.cookie`
* `window.parent`
* `window.top`
* `target="_top"`
* `http://`
* `https://`

ただし、iframeそのものはこのSkillの要件なので禁止しないでください。
禁止するのは、外部URLを読む iframe です。

validate に失敗した場合は、問題箇所を出力し、non-zero exit code で終了してください。

# examples.md の要件

`references/examples.md` に、Skill利用時の例を書いてください。

最低限、以下の例を含めてください。

## 例1: PRをエンジニア向けに理解する

入力:

* PR概要
* 変更ファイル
* diff summary

出力:

* iframe内: worktree + reading order + review checklist
* iframe外: エンジニア向け変換テンプレート、テーブル変換テンプレート、レビュー観点追加テンプレート

## 例2: 仕様書をPdM向けに理解する

入力:

* 仕様書本文

出力:

* iframe内: purpose / impact / decision points / risks
* iframe外: Biz向けテンプレート、FAQ化テンプレート、影響範囲中心テンプレート

## 例3: 初心者向けに技術文書を理解する

入力:

* 技術文書

出力:

* iframe内: 3ステップ解説 + 用語集 + FAQ
* iframe外: もっと簡単にするテンプレート、例え話を追加するテンプレート、テーブル化テンプレート

# README.md の要件

READMEには以下を書いてください。

* この Skill の目的
* Webアプリではないこと
* 最終アウトプットは単一HTMLファイルであること
* iframe内とiframe外の役割
* core.yaml と view.yaml の違い
* なぜチャットUIではなくプロンプトテンプレートを置くのか
* なぜ固定rendererではなくHTML生成ルールを使うのか
* scripts/build_html.py の使い方
* scripts/validate_html.py の使い方
* 生成HTMLの安全性方針
* Skill利用例
* 今後の拡張案

# 生成HTMLのUX要件

最終HTMLは、ブラウザで直接開いて使えるようにしてください。

外部依存は不要です。

画面は大きく2ペインにしてください。

```txt
左ペイン:
  - プロンプトテンプレート集
  - 表現変換テンプレート
  - コピーボタン
  - core.yaml / view.yaml の表示切替
  - 使い方

右ペイン:
  - iframe preview
  - iframe内に図解UI
```

モバイルや狭い画面では縦並びにしてください。

# iframe外のプロンプトテンプレート表示仕様

各プロンプトテンプレートはカード形式にしてください。

各カードには以下を含めてください。

* タイトル
* 用途説明
* prompt本文
* copy button
* optional tags

copy button は JS で実装してください。

clipboard API が使えない場合は textarea select fallback を実装してください。

# iframe内HTMLの方針

iframe内HTMLは、対象に応じて自由に生成してよいです。

ただし、以下は守ってください。

* source references を表示する
* 重要概念を表示する
* 関係性を表示する
* 次に読むべき箇所を表示する
* 次にAIへ聞くとよい質問を表示する
* ユーザーの理解スタイルに合わせる
* 単なる文章の羅列にしない
* 視覚的な構造を持たせる

# テスト・検証

以下を実行できるようにしてください。

```bash
python scripts/build_html.py --help
python scripts/validate_html.py --help
```

また、サンプルデータで以下が動くようにしてください。

```bash
python scripts/build_html.py \
  --core references/sample-core.yaml \
  --view references/sample-view.yaml \
  --iframe references/sample-iframe.html \
  --prompts references/sample-prompts.json \
  --output sample-output.html

python scripts/validate_html.py sample-output.html
```

必要であれば sample ファイルも作成してください。

# 受け入れ条件

以下を満たしてください。

* Skill構造が完成している
* `SKILL.md` がある
* `agents/openai.yaml` がある
* `references/` に必要な設計資料がある
* `scripts/build_html.py` がある
* `scripts/validate_html.py` がある
* sample data から単一HTMLを生成できる
* 生成HTMLをブラウザで開ける
* 生成HTMLに iframe が含まれている
* iframe外にプロンプトテンプレート集がある
* 各テンプレートに copy button がある
* iframe内に図解UIが表示される
* HTMLはself-contained
* 外部CDNに依存しない
* validate script が危険パターンを検出できる
* README がある

# 実装後にやること

最後に以下を実行してください。

```bash
python scripts/build_html.py \
  --core references/sample-core.yaml \
  --view references/sample-view.yaml \
  --iframe references/sample-iframe.html \
  --prompts references/sample-prompts.json \
  --output sample-output.html

python scripts/validate_html.py sample-output.html
```

そのうえで、以下を要約してください。

* 作成したファイル一覧
* この Skill の使い方
* sample-output.html の確認方法
* 今後改善できる点

