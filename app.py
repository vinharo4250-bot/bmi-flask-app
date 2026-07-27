import os
from collections import Counter

from flask import Flask, render_template
from supabase import create_client

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


if __name__ == "__main__":
    app.run(debug=True)
