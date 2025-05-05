import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, mock_open
from src.reports import spending_by_category, spending_by_weekday, spending_by_workday, report_to_file


@pytest.fixture
def sample_transactions():
    data = {
        "Дата операции": [
            "01.01.2023 12:00:00",  # Воскресенье
            "02.01.2023 09:00:00",  # Понедельник
            "07.01.2023 18:00:00",  # Суббота
            "16.01.2023 10:00:00",  # Понедельник
        ],
        "Категория": ["Супермаркеты", "Кафе", "Супермаркеты", "Транспорт"],
        "Сумма платежа": [1000, 500, 800, 300],
    }
    df = pd.DataFrame(data)
    # Преобразуем даты сразу в фикстуре
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    return df


def test_spending_by_category(sample_transactions):
    with patch("pandas.Timestamp.now", return_value=pd.Timestamp("2023-02-01")):
        result = spending_by_category(sample_transactions, "Супермаркеты")
        assert isinstance(result, list)
        assert len(result) == 1  # Одна запись за январь
        assert result[0]["Сумма платежа"] == 1800  # 1000 + 800


def test_spending_by_weekday(sample_transactions):
    with patch("pandas.Timestamp.now", return_value=pd.Timestamp("2023-02-01")):
        result = spending_by_weekday(sample_transactions)
        assert isinstance(result, list)
        assert len(result) == 3  # Понедельник, Суббота, Воскресенье
        weekdays = {item["День недели"] for item in result}
        assert "Понедельник" in weekdays


def test_spending_by_workday(sample_transactions):
    with patch("pandas.Timestamp.now", return_value=pd.Timestamp("2023-02-01")):
        result = spending_by_workday(sample_transactions)
        assert isinstance(result, list)
        assert len(result) == 2  # Рабочие и выходные дни
        day_types = {item["Тип дня"] for item in result}
        assert "Рабочий" in day_types


def test_report_to_file_decorator():
    test_data = [{"A": 1, "B": 2}]  # Теперь ожидаем список словарей

    with patch("builtins.open", mock_open()) as mocked_file:

        @report_to_file("test_report.json")
        def dummy_func():
            return test_data

        result = dummy_func()

        assert result == test_data  # Проверяем что функция вернула исходные данные
        mocked_file.assert_called_once_with("test_report.json", "w", encoding="utf-8")


def test_error_handling():
    invalid_df = pd.DataFrame({"Дата операции": ["invalid_date"], "Категория": ["Тест"], "Сумма платежа": [100]})
    result = spending_by_category(invalid_df, "Тест")
    assert isinstance(result, list)
    assert len(result) == 0
