import os
from collections import Counter

from flask import Flask, render_template, request
from supabase import create_client

from news_crawler import search_news

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def fetch_latest_run():
    if not supabase:
        return None, [], []

    latest = (
        supabase.table("cafe_posts")
        .select("run_at")
        .order("run_at", desc=True)
        .limit(1)
        .execute()
    )
    if not latest.data:
        return None, [], []

    run_at = latest.data[0]["run_at"]

    posts_response = (
        supabase.table("cafe_posts")
        .select("*")
        .eq("run_at", run_at)
        .order("company")
        .execute()
    )
    posts = posts_response.data

    counts = Counter(p["company"] for p in posts)
    summary = [
        {"company": company, "count": count} for company, count in counts.items()
    ]
    summary.sort(key=lambda x: x["count"], reverse=True)

    return run_at, summary, posts


@app.route("/")
def index():
    run_at, summary, posts = fetch_latest_run()
    return render_template(
        "index.html", run_at=run_at, summary=summary, posts=posts
    )


@app.route("/news", methods=["GET", "POST"])
def news():
    keyword = None
    days = 7
    results = []
    error = None
    searched = False

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        try:
            days = int(request.form.get("days", 7))
        except ValueError:
            days = 7

        if not keyword:
            error = "검색어를 입력해주세요."
        elif days <= 0:
            error = "최근 N일은 1 이상이어야 합니다."
        else:
            try:
                results = search_news(keyword, days)
                searched = True
            except Exception:
                error = "기사를 불러오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    return render_template(
        "news.html",
        keyword=keyword,
        days=days,
        results=results,
        error=error,
        searched=searched,
    )


if __name__ == "__main__":
    app.run(debug=True)
