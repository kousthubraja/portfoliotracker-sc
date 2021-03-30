from .models import *


def validate_trade(portfolio, security, trade_type, count):
    positions_on_security = Position.objects.filter(portfolio=portfolio, security=security)
    # Validate the trade for short selling
    if trade_type == Trade.SELL:
        if len(positions_on_security) == 1:
            position = positions_on_security[0]
            if position.count < count:
                raise Exception('Sell quantity more than holdings')
        else:
            raise Exception('Cannot sell securities not being held')


def add_trade(ticker, trade_type, count, trade_price, portfolio_id=1):
    portfolio = Portfolio.objects.get(id=portfolio_id)
    security = ticker

    positions_on_security = Position.objects.filter(portfolio=portfolio, security=security)

    validate_trade(portfolio, security, trade_type, count)

    trade = Trade.objects.create(portfolio=portfolio,
                                 security=security,
                                 count=count,
                                 trade_price=trade_price,
                                 trade_type=trade_type)

    if len(positions_on_security) == 0:
        Position.objects.create(
            portfolio=portfolio,
            security=security,
            count=count,
            average_price=trade_price
        )
    else:
        position = positions_on_security[0]
        if trade_type == Trade.BUY:
            new_average_price = (position.average_price * position.count + trade_price * count) / (
                        position.count + count)
            position.count = position.count + count
            position.average_price = new_average_price
            position.save()
        else:
            position.count = position.count - count
            position.save()

    return trade


def delete_trade(trade_id):
    trade = Trade.objects.get(id=trade_id)

    trades_on_security = Trade.objects.filter(portfolio=trade.portfolio,
                                              security=trade.security) \
        .order_by('trade_time')

    # Only BUY order deletion cause validation error
    if trade.trade_type == Trade.BUY:
        count = 0
        for t in trades_on_security:
            if t == trade:
                continue
            if t.trade_type == Trade.BUY:
                count += t.count
            else:
                count -= t.count
            if count < 0:
                raise Exception('Position becomes negative on deletion of this trade')

    count = 0
    average_price = 0
    for t in trades_on_security:
        if t == trade:
            continue

        if t.trade_type == Trade.BUY:
            count += t.count
            average_price += t.trade_price * t.count
        else:
            count -= t.count
            average_price -= t.trade_price * t.count

    average_price /= count

    positions_on_security = Position.objects.filter(portfolio=trade.portfolio, security=trade.security)
    # Todo - Make positions time series and snapshot position at each time there's a change so only trades post
    # trade to be deleted need to be checked
    if len(positions_on_security) > 0:
        position = positions_on_security[0]
        position.count = count
        position.average_price = average_price
        position.save()


def update_trade(trade_id, ticker, trade_type, count, trade_price):
    trade = Trade.objects.get(id=trade_id)

    return trade
