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
<a href="/about.html" style="color:inherit">運営者情報</a> ・ © {date.today().year} {NAME}</footer>"""


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


def exam_page(ex):
    path = f"/{ex['id']}/"
    title = f"{ex['name']}の一問一答・解説つき問題一覧｜{NAME}"
    desc = f"{ex['name']}（{ex['sub']}）に一発合格するための一問一答。全{len(ex['qs'])}問、現役技術者の解説と現場メモつき。"
    items = "".join(
        f'<li><a href="q{i + 1:03d}.html"><small>{escape(q["c"])}</small>{escape(q["q"])}</a></li>'
        for i, q in enumerate(ex["qs"]))
    body = f"""<body style="--c:var(--c-{ex['color']})">
{header()}
<main class="wrap page">
<nav class="crumb"><a href="/">ホーム</a> › {escape(ex['name'])}</nav>
<h1>{escape(ex['name'])}の一問一答</h1>
<p style="margin:0 0 12px;color:var(--sub);font-size:14px">{escape(ex['sub'])}・{escape(ex['sched'])}。気になる問題を開くか、まとめて解いて弱点を見つけましょう。</p>
<a class="btn pri" href="/#{ex['id']}" style="margin-bottom:16px">10問チャレンジを始める</a>
<ul class="qlinks">{items}</ul>
</main>
{footer()}
</body></html>"""
    return path, head(title, desc, path) + body


def about_page():
    path = "/about.html"
    body = f"""<body>
{header()}
<main class="wrap page">
<nav class="crumb"><a href="/">ホーム</a> › 運営者情報</nav>
<h1>運営者情報</h1>
<div class="card">
<p>{NAME}は、電気・通信・家電の資格に一発合格したい人のための一問一答サイトです。</p>
<p>解説は、家電修理の現場で10年以上働く技術者が書いています。参考書には書いていない「現場ではこうなる」を、現場メモとして解説に添えています。</p>
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
    write("/", app)

    paths = ["/", "/about.html"]
    write(*about_page())
    for ex in exams:
        p, html = exam_page(ex)
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
