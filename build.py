"""一発合格ラボ のサイト生成スクリプト。

data/questions.json を元に、site/ 以下へ静的HTMLを書き出す。
- /                 … 一問一答アプリ（ホーム）
- /{資格}/          … 資格ごとの問題一覧（検索流入用）
- /{資格}/q001.html … 1問ずつの解説ページ（検索流入用）
- /about.html       … 運営者情報
- sitemap.xml, robots.txt

使い方: python3 build.py
"""
import json
import shutil
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE = "https://ippatsu-gokaku.com"
NAME = "一発合格ラボ"
CONTACT_URL = "https://forms.gle/4JthoGubcLiXgCX56"
TAG = "現役技術者が教える電気・通信・家電の資格"
LETTERS = "ABCD"

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=BIZ+UDPGothic:wght@400;700'
    '&family=Zen+Kaku+Gothic+New:wght@700;900&display=swap" rel="stylesheet">'
)


def head(title, desc, path, extra=""):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{NAME}">
{FONTS}
<link rel="stylesheet" href="/assets/style.css">
{extra}
</head>"""


def header():
    return f"""<header class="top"><div class="wrap">
<a class="logo" href="/" style="text-decoration:none"><i></i><span>{NAME}<small class="tagline">{TAG}</small></span></a>
</div></header>"""


def footer():
    return f"""<footer class="wrap">問題はすべてオリジナルで、試験の過去問ではありません。<br>
<a href="/about.html" style="color:inherit">運営者情報</a> ・ <a href="/privacy.html" style="color:inherit">プライバシーポリシー</a> ・ <a href="/contact.html" style="color:inherit">お問い合わせ</a><br>© {date.today().year} {NAME}</footer>"""


def snippet(text, n=60):
    return text if len(text) <= n else text[:n] + "…"


def question_page(ex, i, q):
    num = f"{i + 1:03d}"
    path = f"/{ex['id']}/q{num}.html"
    title = f"【{ex['name']}】{q['q']}｜{NAME}"
    desc = f"{ex['name']}（{ex['sub']}）の一問一答。{snippet(q['q'], 50)} 正解と現役技術者の解説つき。"
    opts = "".join(f"<li><b>{LETTERS[j]}</b><span>{escape(o)}</span></li>" for j, o in enumerate(q["o"]))
    tip = (f'<div class="tip" style="margin-top:10px"><strong>現場メモ</strong><span>{escape(q["t"])}</span></div>'
           if q.get("t") else "")
    prev_link = f'<a href="q{i:03d}.html">← 前の問題</a>' if i > 0 else "<span></span>"
    next_link = f'<a href="q{i + 2:03d}.html">次の問題 →</a>' if i + 1 < len(ex["qs"]) else "<span></span>"
    ld = {
        "@context": "https://schema.org", "@type": "Quiz", "name": q["q"],
        "about": ex["name"], "educationalLevel": ex["sub"],
        "hasPart": [{
            "@type": "Question", "name": q["q"], "eduQuestionType": "Multiple choice",
            "suggestedAnswer": [{"@type": "Answer", "text": o} for j, o in enumerate(q["o"]) if j != q["a"]],
            "acceptedAnswer": {"@type": "Answer", "text": q["o"][q["a"]], "answerExplanation": {"@type": "Comment", "text": q["e"]}},
        }],
    }
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    body = f"""<body style="--c:var(--c-{ex['color']})">
{header()}
<main class="wrap page">
<nav class="crumb"><a href="/">ホーム</a> › <a href="/{ex['id']}/">{escape(ex['name'])}</a> › 問題{i + 1}</nav>
<div class="card" style="margin-top:8px">
<div class="cat">{escape(ex['name'])}｜{escape(q['c'])}</div>
<h1>{escape(q['q'])}</h1>
<ol class="olist">{opts}</ol>
<details class="ans"><summary>正解と解説を見る</summary>
<p class="verdict" style="margin:0;color:var(--ok)">正解は {LETTERS[q['a']]}：{escape(q['o'][q['a']])}</p>
<p style="margin:6px 0 0">{escape(q['e'])}</p>
{tip}
</details>
<div class="cta">
<a class="btn pri" href="/#{ex['id']}">{escape(ex['name'])}を10問まとめて解く</a>
</div>
<div class="pager">{prev_link}{next_link}</div>
</div>
</main>
{footer()}
</body></html>"""
    return path, head(title, desc, path, extra) + body


def render_blocks(blocks):
    out = []
    for b in blocks:
        if "h" in b:
            out.append(f"<h2>{escape(b['h'])}</h2>")
        elif "p" in b:
            out.append(f"<p>{escape(b['p'])}</p>")
        elif "ul" in b or "ol" in b:
            tag = "ul" if "ul" in b else "ol"
            out.append(f"<{tag}>" + "".join(f"<li>{escape(x)}</li>" for x in b[tag]) + f"</{tag}>")
        elif "table" in b:
            rows = b["table"]
            th = "".join(f"<th>{escape(c)}</th>" for c in rows[0])
            tr = "".join("<tr>" + "".join(f"<td>{escape(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f'<div class="tbl"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')
        elif "tip" in b:
            out.append(f'<div class="tip"><strong>現場メモ</strong><span>{escape(b["tip"])}</span></div>')
    return "\n".join(out)


def article_page(ex, art):
    path = f"/{ex['id']}/{art['slug']}.html"
    title = f"{art['title']}｜{NAME}"
    rel = [(i, q) for i, q in enumerate(ex["qs"]) if q["c"] in art["cats"]][:8]
    rel_html = "".join(
        f'<li><a href="q{i + 1:03d}.html"><small>{escape(q["c"])}</small>{escape(q["q"])}</a></li>' for i, q in rel)
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": art["title"],
          "description": art["desc"], "dateModified": date.today().isoformat(),
          "author": {"@type": "Person", "name": f"{NAME} 編集部（家電修理技術者）"},
          "publisher": {"@type": "Organization", "name": NAME}}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    body = f"""<body style="--c:var(--c-{ex['color']})">
{header()}
<main class="wrap page article">
<nav class="crumb"><a href="/">ホーム</a> › <a href="/{ex['id']}/">{escape(ex['name'])}</a> › まとめ</nav>
<h1>{escape(art['title'])}</h1>
<p class="lead">{escape(art['desc'])}</p>
<div class="card">
{render_blocks(art['blocks'])}
</div>
<a class="btn pri" href="/#{ex['id']}" style="margin:16px 0">{escape(ex['name'])}を10問まとめて解く</a>
<h2 class="h2">この記事に関連する問題</h2>
<ul class="qlinks">{rel_html}</ul>
</main>
{footer()}
</body></html>"""
    return path, head(title, art["desc"], path, extra) + body


def exam_page(ex, arts=()):
    path = f"/{ex['id']}/"
    title = f"{ex['name']}の一問一答・解説つき問題一覧｜{NAME}"
    desc = f"{ex['name']}（{ex['sub']}）に一発合格するための一問一答。全{len(ex['qs'])}問、現役技術者の解説と現場メモつき。"
    items = "".join(
        f'<li><a href="q{i + 1:03d}.html"><small>{escape(q["c"])}</small>{escape(q["q"])}</a></li>'
        for i, q in enumerate(ex["qs"]))
    art_html = ""
    if arts:
        art_html = '<h2 class="h2">まとめ記事</h2><ul class="qlinks" style="margin-bottom:20px">' + "".join(
            f'<li><a href="{a["slug"]}.html"><small>まとめ</small>{escape(a["title"])}</a></li>' for a in arts) + "</ul>"
    body = f"""<body style="--c:var(--c-{ex['color']})">
{header()}
<main class="wrap page">
<nav class="crumb"><a href="/">ホーム</a> › {escape(ex['name'])}</nav>
<h1>{escape(ex['name'])}の一問一答</h1>
<p style="margin:0 0 12px;color:var(--sub);font-size:14px">{escape(ex['sub'])}・{escape(ex['sched'])}。気になる問題を開くか、まとめて解いて弱点を見つけましょう。</p>
<a class="btn pri" href="/#{ex['id']}" style="margin-bottom:16px">10問チャレンジを始める</a>
{art_html}
<h2 class="h2">問題一覧</h2>
<ul class="qlinks">{items}</ul>
</main>
{footer()}
</body></html>"""
    return path, head(title, desc, path) + body


def simple_page(path, title, desc, inner):
    body = f"""<body>
{header()}
<main class="wrap page article" style="--c:var(--brand)">
<nav class="crumb"><a href="/">ホーム</a> › {escape(title)}</nav>
<h1>{escape(title)}</h1>
<div class="card">
{inner}
</div>
</main>
{footer()}
</body></html>"""
    return path, head(f"{title}｜{NAME}", desc, path) + body


def privacy_page():
    inner = f"""<h2>個人情報の取り扱い</h2>
<p>お問い合わせフォームで入力いただいた情報（お名前、メールアドレス、内容）は、お問い合わせへの返信と、内容の確認のためだけに使います。法令にもとづく場合を除き、本人の同意なく第三者に提供しません。</p>
<h2>学習記録の保存について</h2>
<p>一問一答の解答記録、連続学習日数、「あとで見直す」に保存した問題は、お使いのブラウザの中（ローカルストレージ）にだけ保存されます。当サイトのサーバーに送られることはありません。ブラウザのデータを削除すると、記録も消えます。</p>
<h2>広告について</h2>
<p>当サイトでは、今後、第三者配信の広告サービス（Google AdSenseなど）や、商品・サービスを紹介するアフィリエイトプログラムを利用することがあります。広告を掲載する記事では、本文中に広告である旨を明記します。</p>
<p>Googleなどの第三者配信事業者は、Cookie（クッキー）を使用して、ユーザーが当サイトや他のサイトに過去にアクセスした際の情報にもとづいて広告を配信します。Googleが広告Cookieを使用することにより、Googleやそのパートナーは、ユーザーが当サイトや他のサイトにアクセスした際の情報にもとづいて、適切な広告を表示できます。</p>
<p>パーソナライズ広告は、<a href="https://adssettings.google.com/" target="_blank" rel="noopener">Googleの広告設定</a>で無効にできます。Googleによるデータの使用については、<a href="https://policies.google.com/technologies/ads?hl=ja" target="_blank" rel="noopener">Googleのポリシーと規約</a>をご覧ください。</p>
<h2>アクセス解析</h2>
<p>当サイトは、サイトの利用状況を把握し、内容を改善するために、Cloudflare社のアクセス解析（Cloudflare Web Analytics）を利用しています。閲覧されたページ、参照元（どのサイトや検索から来たか）、国や地域、端末やブラウザの種類などを、個人を特定しない形で集計します。この解析は、Cookieを使いません。</p>
<p>また、Google検索での表示回数や、検索に使われた言葉などを把握するために、Google Search Consoleを利用しています。これはGoogle検索の統計情報で、当サイトの訪問者を個人として特定するものではありません。</p>
<h2>免責事項</h2>
<p>掲載している問題や解説は、正確さに注意して作成していますが、内容の正確性や最新性を保証するものではありません。試験の日程、受験料、出題範囲などは、必ず各試験の実施機関の公式情報でご確認ください。当サイトの利用によって生じた損害について、当サイトは責任を負いかねます。リンク先のサイトで提供される情報やサービスについても、責任を負いかねます。</p>
<h2>著作権について</h2>
<p>当サイトに掲載している問題は、すべてオリジナルで作成したもので、試験の過去問を転載したものではありません。文章や問題の無断転載はご遠慮ください。</p>
<h2>内容の変更</h2>
<p>このポリシーの内容は、予告なく変更することがあります。</p>
<p style="color:var(--sub);font-size:13px">制定日：2026年11月18日</p>"""
    return simple_page("/privacy.html", "プライバシーポリシー", f"{NAME}のプライバシーポリシー、広告、アクセス解析、免責事項について。", inner)


def contact_page():
    inner = f"""<p>問題や解説の誤りのご指摘、内容についてのご質問、掲載についてのご相談は、下のフォームからお送りください。</p>
<p><a class="btn pri" href="{CONTACT_URL}" target="_blank" rel="noopener noreferrer">お問い合わせフォームを開く</a></p>
<h2>お送りいただく前に</h2>
<ul>
<li>どの問題・記事についてのお問い合わせかがわかるように、ページのURLや問題の番号を書き添えてください。</li>
<li>お返事までにお時間をいただくことがあります。すべてのご質問にお返事できるとは限りません。</li>
<li>試験の申し込みや合否についてのお問い合わせは、各試験の実施機関にお願いします。</li>
<li>入力いただいた情報の扱いは、<a href="/privacy.html">プライバシーポリシー</a>をご覧ください。</li>
</ul>"""
    return simple_page("/contact.html", "お問い合わせ", f"{NAME}へのお問い合わせ。問題や解説の誤りのご指摘などはこちらから。", inner)


def about_page():
    path = "/about.html"
    body = f"""<body>
{header()}
<main class="wrap page">
<nav class="crumb"><a href="/">ホーム</a> › 運営者情報</nav>
<h1>運営者情報</h1>
<div class="card">
<p>{NAME}は、電気・通信・家電の資格に一発合格したい人のための一問一答サイトです。</p>
<p>解説は、家電修理の現場で15年以上働く技術者が書いています。参考書には書いていない「現場ではこうなる」を、現場メモとして解説に添えています。</p>
<p><strong>保有資格</strong><br>家電製品エンジニア／工事担任者 総合通信</p>
<p><strong>掲載している問題について</strong><br>すべてオリジナルの問題です。試験の過去問を転載したものではありません。内容の誤りに気づいた場合はお知らせください。</p>
</div>
</main>
{footer()}
</body></html>"""
    return path, head(f"運営者情報｜{NAME}", f"{NAME}の運営者情報。", path) + body


def write(path, html):
    f = OUT / path.lstrip("/")
    if path.endswith("/"):
        f = f / "index.html"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(html, encoding="utf-8")


def main():
    exams = json.loads((ROOT / "data/questions.json").read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copy(ROOT / "src/style.css", OUT / "assets/style.css")

    # ホーム（アプリ）
    app_data = [dict(e, color=f"var(--c-{e['color']})") for e in exams]
    app = (ROOT / "src/app.html").read_text(encoding="utf-8")
    app = app.replace("__DATA__", json.dumps(app_data, ensure_ascii=False))
    arts_all = json.loads((ROOT / "data/articles.json").read_text(encoding="utf-8"))
    names = {e["id"]: e["name"] for e in exams}
    app = app.replace("__ARTICLES__", '<ul class="qlinks" style="--c:var(--brand)">' + "".join(
        f'<li><a href="/{a["exam"]}/{a["slug"]}.html"><small>{escape(names[a["exam"]])}</small>{escape(a["title"])}</a></li>'
        for a in arts_all) + "</ul>")
    write("/", app)

    paths = ["/", "/about.html", "/privacy.html", "/contact.html"]
    write(*about_page())
    write(*privacy_page())
    write(*contact_page())
    articles = json.loads((ROOT / "data/articles.json").read_text(encoding="utf-8"))
    for ex in exams:
        arts = [a for a in articles if a["exam"] == ex["id"]]
        p, html = exam_page(ex, arts)
        write(p, html)
        paths.append(p)
        for a in arts:
            p, html = article_page(ex, a)
            write(p, html)
            paths.append(p)
        for i, q in enumerate(ex["qs"]):
            p, html = question_page(ex, i, q)
            write(p, html)
            paths.append(p)

    today = date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>" for p in paths)
    (OUT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print(f"{len(paths)} ページを書き出しました → {OUT}")


if __name__ == "__main__":
    main()
