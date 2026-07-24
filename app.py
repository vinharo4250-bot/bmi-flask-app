import os

from flask import Flask, render_template, request
from supabase import create_client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def calc_bmi(height_cm: float, weight_kg: float) -> float:
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "저체중"
    elif bmi < 23:
        return "정상"
    elif bmi < 25:
        return "과체중"
    else:
        return "비만"


def save_record(height, weight, bmi, category):
    if not supabase:
        return
    supabase.table("bmi_records").insert({
        "height_cm": height,
        "weight_kg": weight,
        "bmi": bmi,
        "category": category,
    }).execute()


def fetch_recent_records(limit=5):
    if not supabase:
        return []
    response = (
        supabase.table("bmi_records")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        try:
            height = float(request.form["height"])
            weight = float(request.form["weight"])

            if height <= 0 or weight <= 0:
                error = "키와 몸무게는 0보다 큰 값을 입력해주세요."
            else:
                bmi = calc_bmi(height, weight)
                category = bmi_category(bmi)
                result = {
                    "height": height,
                    "weight": weight,
                    "bmi": round(bmi, 2),
                    "category": category,
                }
                save_record(height, weight, result["bmi"], category)
        except (ValueError, KeyError):
            error = "올바른 숫자를 입력해주세요."

    recent_records = fetch_recent_records()
    return render_template(
        "index.html", result=result, error=error, recent_records=recent_records
    )


if __name__ == "__main__":
    app.run(debug=True)
