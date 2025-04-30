import pandas as pd
import pytest

from src.services import *


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2023-01-15", "2023-01-20", "2023-02-01"]),
            "Сумма операции": [100, 200, 300],
            "Кешбэк": [5, 10, 15],
            "Категория": ["Еда", "Транспорт", "Переводы"],
            "Описание": [
                "Покупка в Пятерочке +7 999 123-45-67",
                "Такси Иван П.",
                "Перевод Марии С.",
            ],
        }
    )


def test_profitable_cashback(sample_data):
    result = profitable_cashback(sample_data, 2023, 1)
    assert result == {"Еда": 5, "Транспорт": 10}


def test_investment_bank():
    transactions = [
        {"Дата операции": "2023-01-15", "Сумма операции": 147},
        {"Дата операции": "2023-01-20", "Сумма операции": 823},
    ]
    assert investment_bank("2023-01", transactions, 50) == 30.0


def test_simple_search(sample_data):
    result = simple_search(sample_data, "Такси")
    assert len(result) == 1
    assert result[0]["Категория"] == "Транспорт"


def test_find_phone_transactions(sample_data):
    result = find_phone_transactions(sample_data)
    assert len(result) == 1
    assert "+7 999 123-45-67" in result[0]["Описание"]


def test_find_person_transfers(sample_data):
    result = find_person_transfers(sample_data)
    assert len(result) == 1
    assert "Марии С." in result[0]["Описание"]
