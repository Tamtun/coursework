from unittest.mock import patch
import pandas as pd
import pytest
from src.reports import (
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
)


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "Дата операции": pd.date_range(start="2023-09-01", end="2023-11-30", freq="D"),
            "Сумма платежа": [100 + i for i in range(91)],
            "Категория": ["Еда" if i % 2 == 0 else "Транспорт" for i in range(91)],
        }
    )


@patch("pandas.Timestamp.now")
def test_spending_by_weekday(mock_now, sample_data):
    mock_now.return_value = pd.Timestamp("2023-12-01")
    report = spending_by_weekday(sample_data)

    # Собираем все дни недели из отчета
    weekdays = [entry["День недели"] for entry in report]

    assert len(report) == 7
    assert all(
        day in weekdays
        for day in [
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ]
    )


@patch("pandas.Timestamp.now")
def test_spending_by_workday(mock_now, sample_data):
    mock_now.return_value = pd.Timestamp("2023-12-01")
    report = spending_by_workday(sample_data)

    # Собираем все типы дней из отчета
    day_types = [entry["Тип дня"] for entry in report]

    assert len(report) == 2
    assert "Рабочий" in day_types
    assert "Выходной" in day_types
