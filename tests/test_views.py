import pytest
import json
import pandas as pd
from unittest.mock import patch
from src.views import main_page


@pytest.fixture
def sample_date():
    return pd.Timestamp("2025-04-01")  # Исправлено: теперь это Timestamp


@pytest.fixture
def mock_transactions():
    return [
        {"Дата операции": "2025-03-10", "Категория": "Еда", "Сумма платежа": 500},
        {"Дата операции": "2025-03-15", "Категория": "Транспорт", "Сумма платежа": 300},
        {"Дата операции": "2025-03-20", "Категория": "Еда", "Сумма платежа": 400},
    ]


@pytest.fixture
def mock_settings():
    return {"user_currencies": ["USD", "EUR"]}


@patch("src.views.load_transactions")
@patch("src.views.load_user_settings")
@patch("src.views.get_date_range")
@patch("src.views.get_greeting")
@patch("src.views.get_card_stats")
@patch("src.views.get_top_transactions")
@patch("src.views.get_currency_rates")
@patch("src.views.get_sp500_price")
def test_main_page(
    mock_sp500_price,
    mock_currency_rates,
    mock_top_transactions,
    mock_card_stats,
    mock_greeting,
    mock_date_range,
    mock_user_settings,
    mock_load_transactions,
    sample_date,
    mock_transactions,
    mock_settings,
):
    """Тест успешного выполнения main_page"""
    mock_load_transactions.return_value = pd.DataFrame(mock_transactions)
    mock_load_transactions.return_value["Дата операции"] = pd.to_datetime(
        mock_load_transactions.return_value["Дата операции"]
    )
    mock_user_settings.return_value = mock_settings
    mock_date_range.return_value = (pd.Timestamp("2025-03-01"), pd.Timestamp("2025-03-31"))
    mock_greeting.return_value = "Добрый день!"
    mock_card_stats.return_value = {"cards": [{"name": "Visa", "balance": 1000}]}
    mock_top_transactions.return_value = {"transactions": [{"Категория": "Еда", "Сумма": 500}]}
    mock_currency_rates.return_value = {"USD": 75.5, "EUR": 82.3}
    mock_sp500_price.return_value = 4500.25

    result = main_page(sample_date)

    if isinstance(result, dict):
        data = result
    else:
        data = json.loads(result)

    assert isinstance(data, dict)
    assert data.get("greeting") == "Добрый день!"
    assert "cards" in data
    assert "top_transactions" in data
    assert data.get("currency_rates", {}).get("USD") == 75.5
    assert data.get("sp500_price") == 4500.25


@patch("src.views.load_transactions", side_effect=Exception("Ошибка загрузки данных"))
def test_main_page_load_transactions_error(mock_load_transactions, sample_date):
    """Тест обработки ошибки при загрузке данных"""
    result = main_page(sample_date)

    assert isinstance(result, dict)
    assert "error" in result
    assert result["error"] == "Ошибка загрузки данных"


@patch("src.views.get_currency_rates", side_effect=Exception("Ошибка получения курсов"))
def test_main_page_currency_error(mock_currency_rates, sample_date, mock_transactions, mock_settings):
    """Тест обработки ошибки при получении курсов валют"""

    mock_df = pd.DataFrame(mock_transactions)
    mock_df["Дата операции"] = pd.to_datetime(mock_df["Дата операции"])  # Конвертация в Timestamp

    with (
        patch("src.views.load_transactions", return_value=mock_df),
        patch("src.views.load_user_settings", return_value=mock_settings),
        patch("src.views.get_date_range", return_value=(pd.Timestamp("2025-03-01"), pd.Timestamp("2025-03-31"))),
        patch("src.views.get_greeting", return_value="Добрый день!"),
        patch("src.views.get_card_stats", return_value={"cards": [{"name": "Visa", "balance": 1000}]}),
        patch("src.views.get_top_transactions", return_value={"transactions": [{"Категория": "Еда", "Сумма": 500}]}),
        patch("src.views.get_sp500_price", return_value=4500.25),
    ):
        result = main_page(sample_date.strftime("%Y-%m-%d"))  # Теперь формат совместим с get_date_range()

        assert isinstance(result, dict)
        assert "error" in result
        assert result["error"] == "Ошибка получения курсов"
