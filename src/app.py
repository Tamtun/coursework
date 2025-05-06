import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, Response, request
import pandas as pd
import numpy as np
from src.services import (
    profitable_cashback,
    investment_bank,
    find_phone_transactions,
    find_person_transfers,
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)

# Настройка кодировки
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


class CustomJSONEncoder(json.JSONEncoder):
    """Кастомный энкодер для обработки Pandas/Numpy объектов"""

    def default(self, obj):
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def json_response(data, status=200):
    """Универсальный JSON-ответ с правильной сериализацией"""
    return Response(
        json.dumps(data, ensure_ascii=False, cls=CustomJSONEncoder),
        status=status,
        mimetype="application/json; charset=utf-8",
    )


# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

COLUMNS_TO_RETURN = ["Дата операции", "Описание", "Сумма операции", "Категория"]


def load_transactions() -> pd.DataFrame:
    """Загрузка и предварительная обработка транзакций из Excel"""
    try:
        filepath = Path(__file__).parent.parent / "data" / "operations.xlsx"

        df = pd.read_excel(
            filepath,
            engine="openpyxl",
            dtype={"Категория": str, "Описание": str, "Сумма платежа": str},
            thousands=None,
            decimal=",",
        )

        df["Дата операции"] = pd.to_datetime(
            df["Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True, errors="coerce"
        )

        df["Сумма платежа"] = df["Сумма платежа"].str.replace(",", ".").astype(float)

        logger.info(f"Успешно загружено {len(df)} транзакций")
        return df

    except FileNotFoundError:
        logger.error("Файл operations.xlsx не найден")
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {str(e)}", exc_info=True)
        raise


def filter_response(data):
    """Фильтрация полей с проверкой типов"""
    result = []
    for item in data:
        filtered = {}
        for k, v in item.items():
            if k in COLUMNS_TO_RETURN:
                if isinstance(v, (pd.Timestamp, datetime)):
                    v = v.strftime("%Y-%m-%d %H:%M:%S")
                filtered[k] = v
        result.append(filtered)
    return result


@app.route("/")
def home():
    """Главная страница API"""
    return json_response(
        {
            "status": "API работает",
            "endpoints": {
                "investkopilka": "/api/investkopilka?month=YYYY-MM&limit=N",
                "search_phone": "/api/search/phone",
                "search_person": "/api/search/person",
                "cashback": "/api/cashback?year=YYYY&month=MM",
                "reports": {
                    "by_category": "/api/reports/category?category=NAME",
                    "by_weekday": "/api/reports/weekday",
                    "by_workday": "/api/reports/workday",
                },
            },
        }
    )


# Эндпоинты поиска
@app.route("/api/search/person", methods=["GET"])
def search_person():
    try:
        df = load_transactions()
        transactions = df.to_dict("records")
        result = find_person_transfers(transactions)
        return json_response(filter_response(result))
    except Exception as e:
        logger.error(f"Ошибка поиска переводов: {str(e)}")
        return json_response({"error": "Внутренняя ошибка сервера"}, 500)


@app.route("/api/search/phone", methods=["GET"])
def search_phone():
    try:
        df = load_transactions()
        transactions = df.to_dict("records")
        result = find_phone_transactions(transactions)
        return json_response(filter_response(result))
    except Exception as e:
        logger.error(f"Ошибка поиска телефонов: {str(e)}")
        return json_response({"error": "Внутренняя ошибка сервера"}, 500)


# Эндпоинты финансовых сервисов
@app.route("/api/investkopilka", methods=["GET"])
def get_investkopilka():
    try:
        month = request.args.get("month")
        if not month:
            return json_response({"error": "Parameter 'month' is required"}, 400)

        limit = int(request.args.get("limit", 100))
        df = load_transactions()
        transactions = df.to_dict("records")
        result = investment_bank(month, transactions, limit)
        return json_response(result)
    except Exception as e:
        logger.error(f"Ошибка расчета инвесткопилки: {str(e)}")
        return json_response({"error": str(e)}, 400)


@app.route("/api/cashback", methods=["GET"])
def get_cashback():
    try:
        year = int(request.args.get("year"))
        month = int(request.args.get("month"))
        df = load_transactions()
        transactions = df.to_dict("records")
        result = profitable_cashback(year, month, transactions)

        if "error" in result:
            return json_response(result, 400)
        return json_response(result)

    except (ValueError, TypeError):
        return json_response({"error": "Год и месяц должны быть числами"}, 400)
    except Exception as e:
        logger.error(f"Ошибка расчета кешбэка: {str(e)}")
        return json_response({"error": "Внутренняя ошибка сервера"}, 500)


# Эндпоинты отчетов
@app.route("/api/reports/category", methods=["GET"])
def report_by_category():
    try:
        category = request.args.get("category")
        if not category:
            return json_response({"error": "Parameter 'category' is required"}, 400)

        df = load_transactions()
        result = spending_by_category(df, category)
        return json_response(result)
    except Exception as e:
        logger.error(f"Ошибка отчета по категории: {str(e)}")
        return json_response({"error": "Внутренняя ошибка сервера"}, 500)


@app.route("/api/reports/weekday", methods=["GET"])
def report_by_weekday():
    try:
        df = load_transactions()
        result = spending_by_weekday(df)
        return json_response({"report_type": "by_weekday", "data": result.to_dict("records")})
    except Exception as e:
        logger.error(f"Ошибка отчета по дням недели: {str(e)}")
        return json_response({"error": "Внутренняя ошибка сервера"}, 500)


@app.route("/api/reports/workday", methods=["GET"])
def report_by_workday():
    try:
        df = load_transactions()
        result = spending_by_workday(df)
        return json_response({"report_type": "by_workday", "data": result.to_dict("records")})
    except Exception as e:
        logger.error(f"Ошибка отчета по типам дней: {str(e)}")
        return json_response({"error": "Внутренняя ошибка сервера"}, 500)

    return Response(response_data, status=status, mimetype="application/json")


if __name__ == "__main__":
    app.json_encoder = CustomJSONEncoder
    app.run(host="0.0.0.0", port=5000, debug=True)
