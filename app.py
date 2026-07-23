from flask import Flask, render_template, request

app = Flask(__name__)


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
                result = {
                    "height": height,
                    "weight": weight,
                    "bmi": round(bmi, 2),
                    "category": bmi_category(bmi),
                }
        except (ValueError, KeyError):
            error = "올바른 숫자를 입력해주세요."

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    app.run(debug=True)
