from flask import Flask, jsonify, request
from services import *
from utils import *

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# Колонки для возврата в API
COLUMNS_TO_RETURN = [
    "Дата операции",
    "Описание",
    "Сумма операции",
    "Категория",
]


def filter_response(data: List[dict]) -> List[dict]:
    """Фильтрация полей ответа"""
    return [{k: v for k, v in item.items() if k in COLUMNS_TO_RETURN} for item in data]


@app.route("/api/investkopilka", methods=["GET"])
def get_investkopilka():
    try:
        month = request.args.get("month")
        if not month:
            return jsonify({"error": "Month parameter is required"}), 400

        limit = int(request.args.get("limit", 100))

        df = load_transactions()
        transactions = df[["Дата операции", "Сумма операции"]].to_dict("records")
        result = investment_bank(month, transactions, limit)

        response = json.dumps({"total": result}, ensure_ascii=False)
        return (
            response,
            200,
            {"Content-Type": "application/json; charset=utf-8"},
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search/phone", methods=["GET"])
def search_phone():
    try:
        df = load_transactions()
        raw_result = find_phone_transactions(df)
        filtered_result = filter_response(raw_result)

        response = json.dumps(filtered_result, ensure_ascii=False)
        return (
            response,
            200,
            {"Content-Type": "application/json; charset=utf-8"},
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search/person", methods=["GET"])
def search_person():
    try:
        df = load_transactions()
        raw_result = find_person_transfers(df)
        filtered_result = filter_response(raw_result)

        response = json.dumps(filtered_result, ensure_ascii=False)
        return (
            response,
            200,
            {"Content-Type": "application/json; charset=utf-8"},
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
