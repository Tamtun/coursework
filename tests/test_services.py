import pytest
import pandas as pd
from src.services import (
    profitable_cashback,
    investment_bank,
    find_phone_transactions,
    find_person_transfers,
    spending_by_category,
    spending_by_weekday,
    spending_by_workday
)


@pytest.fixture
def sample_transactions():
    return [
        {"Дата операции": "2025-03-10", "Категория": "Еда", "Кешбэк": 50.0},
        {"Дата операции": "2025-03-15", "Категория": "Транспорт", "Кешбэк": 30.5},
        {"Дата операции": "2025-03-20", "Категория": "Еда", "Кешбэк": 20.0},
    ]


@pytest.fixture
def sample_phone_transactions():
    return [
        {"Описание": "Перевод на +79031234567"},
        {"Описание": "Оплата через телефон 8 (911) 123-45-67"},
        {"Описание": "Покупка в магазине"},
    ]


@pytest.fixture
def sample_person_transfers():
    return [
        {"Категория": "Переводы", "Описание": "Иванов И."},
        {"Категория": "Переводы", "Описание": "Петров П."},
        {"Категория": "Еда", "Описание": "Ресторан"},
    ]


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({
        "Дата операции": pd.to_datetime(["2025-01-10", "2025-02-15", "2025-03-20"]),
        "Категория": ["Еда", "Транспорт", "Еда"],
        "Сумма платежа": [100, 200, 300]
    })


def test_profitable_cashback(sample_transactions):
    result = profitable_cashback(2025, 3, sample_transactions)
    assert isinstance(result, dict)
    assert "Еда" in result
    assert result["Еда"] == 70.0  # Проверяем сумму кешбэка по категории "Еда"


def test_investment_bank():
    transactions = [
        {"Дата операции": "2025-03-10", "Сумма операции": 172.0},
        {"Дата операции": "2025-03-11", "Сумма операции": 65.5},
    ]
    result = investment_bank("2025-03", transactions, 100)
    assert isinstance(result, dict)
    assert result["total"] == 62.5  # Проверяем округление


def test_investment_bank_invalid_format():
    """Тест ошибки при неверном формате даты"""
    transactions = [
        {"Дата операции": "invalid_date", "Сумма операции": 172.0}
    ]
    result = investment_bank("2025-03", transactions, 100)
    assert isinstance(result, dict)
    assert result["total"] == 0.0  # Проверяем, что ошибка не ломает логику

def test_find_phone_transactions(sample_phone_transactions):
    result = find_phone_transactions(sample_phone_transactions)
    assert isinstance(result, list)
    assert len(result) == 2  # Должны найти два номера


def test_find_person_transfers(sample_person_transfers):
    result = find_person_transfers(sample_person_transfers)
    assert isinstance(result, list)
    assert len(result) == 2  # Должны найти два перевода физлицам


def test_spending_by_category(sample_dataframe):
    """Тест анализа трат по категории"""
    result = spending_by_category(sample_dataframe, "Еда")
    assert isinstance(result, dict)
    assert "data" in result
    assert len(result["data"]) >= 1  # Должен быть хотя бы один месяц


def test_spending_by_weekday(sample_dataframe):
    """Тест анализа трат по дням недели"""
    result = spending_by_weekday(sample_dataframe)
    assert isinstance(result, pd.DataFrame)
    assert "День недели" in result.columns
    assert "Сумма платежа" in result.columns


def test_spending_by_workday(sample_dataframe):
    """Тест анализа трат по рабочим/выходным дням"""
    result = spending_by_workday(sample_dataframe)
    assert isinstance(result, pd.DataFrame)
    assert "Тип дня" in result.columns
    assert "Сумма платежа" in result.columns

def test_profitable_cashback_empty():
    result = profitable_cashback(2025, 3, [])
    assert result == {"error": "Нет данных для анализа"}

def test_profitable_cashback_missing_columns():
    transactions = [{"Дата операции": "2025-03-10", "Кешбэк": 50.0}]
    result = profitable_cashback(2025, 3, transactions)
    assert "error" in result

def test_investment_bank_negative_amount():
    transactions = [{"Дата операции": "2025-03-10", "Сумма операции": -50.0}]
    result = investment_bank("2025-03", transactions, 100)
    assert result["total"] == 0.0

def test_investment_bank_missing_fields():
    transactions = [
        {"Дата операции": "2025-03-10"},
        {"Сумма операции": 172.0}
    ]
    result = investment_bank("2025-03", transactions, 100)
    assert result["total"] == 0.0

def test_spending_by_workday_empty():
    df = pd.DataFrame(columns=["Дата операции", "Сумма платежа"])
    result = spending_by_workday(df)
    assert result.empty

def test_spending_by_category_empty():
    df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма платежа"])
    result = spending_by_category(df, "Еда")
    assert "data" in result
    assert result["data"] == []
