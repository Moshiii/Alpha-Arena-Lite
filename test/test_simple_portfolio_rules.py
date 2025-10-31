
import pytest
from simple_portfolio import SimplePortfolio


@pytest.fixture
def portfolio():
    return SimplePortfolio(initial_cash=1000.0)


def test_add_then_close_position(portfolio):
    # Open long position
    opened = portfolio.add_order(
        symbol="BTC",
        quantity=1.0,
        price=100.0,
        leverage=5.0,
        signal="buy",
    )
    assert opened is True
    # Collateral = 1 * 100 / 5 = 20
    assert portfolio.available_cash == 980.0
    assert "BTC" in portfolio.positions

    # Close existing position
    closed = portfolio.add_order(
        symbol="BTC",
        quantity=0.0,
        price=100.0,
        leverage=5.0,
        signal="close",
    )
    assert closed is True
    assert portfolio.available_cash == 1000.0
    assert "BTC" not in portfolio.positions


def test_reject_buy_or_sell_when_existing(portfolio):
    # Open initial long
    assert portfolio.add_order("ETH", 1.0, 200.0, leverage=5.0, signal="buy") is True
    prev_cash = portfolio.available_cash
    prev_positions = dict(portfolio.positions)

    # Try add another buy -> should be rejected
    assert portfolio.add_order("ETH", 1.0, 200.0, leverage=5.0, signal="buy") is False
    assert portfolio.available_cash == prev_cash
    assert portfolio.positions.keys() == prev_positions.keys()

    # Try add sell while position exists -> should be rejected
    assert portfolio.add_order("ETH", -1.0, 200.0, leverage=5.0, signal="sell") is False
    assert portfolio.available_cash == prev_cash
    assert portfolio.positions.keys() == prev_positions.keys()


def test_close_when_no_position(portfolio):
    # No BTC position exists
    assert portfolio.add_order("BTC", 0.0, 100.0, leverage=5.0, signal="close") is False
    assert portfolio.available_cash == 1000.0
    assert "BTC" not in portfolio.positions


def test_hold_with_existing_position(portfolio):
    assert portfolio.add_order("SOL", 2.0, 50.0, leverage=5.0, signal="buy") is True
    prev_cash = portfolio.available_cash
    prev_positions = dict(portfolio.positions)

    # hold should do nothing
    assert portfolio.add_order("SOL", 0.0, 50.0, leverage=5.0, signal="hold") is False
    assert portfolio.available_cash == prev_cash
    assert portfolio.positions.keys() == prev_positions.keys()


def test_hold_without_position(portfolio):
    assert portfolio.add_order("SOL", 0.0, 50.0, leverage=5.0, signal="hold") is False
    assert portfolio.available_cash == 1000.0
    assert "SOL" not in portfolio.positions


@pytest.mark.parametrize(
    "symbol, quantity, price, leverage",
    [
        ("ETH", -1.0, 100.0, 5.0),  # short via sell
        ("BTC", 1.0, 100.0, 5.0),   # long via buy
    ],
)
def test_open_position_when_no_existing(symbol, quantity, price, leverage):
    portfolio = SimplePortfolio(initial_cash=1000.0)
    signal = "sell" if quantity < 0 else "buy"
    opened = portfolio.add_order(symbol, quantity, price, leverage=leverage, signal=signal)
    assert opened is True
    # Collateral = |qty| * price / leverage = 20
    assert portfolio.available_cash == 980.0
    assert symbol in portfolio.positions
    assert portfolio.positions[symbol].quantity == quantity


