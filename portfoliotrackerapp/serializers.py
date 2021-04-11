from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import *

""" Serializer has most of our business logic """


class PortfolioSerializer(serializers.ModelSerializer):
    stocks = serializers.SerializerMethodField()
    returns = serializers.SerializerMethodField()

    def get_stocks(self, portfolio):
        allocations = Position.objects.filter(portfolio=portfolio)
        serializer = PositionSerializer(data=allocations, many=True)
        serializer.is_valid()
        return serializer.data

    def get_returns(self, portfolio):
        # Returns calculations are done during serialization.
        positions = Position.objects.filter(portfolio=portfolio)
        returns = 0
        for position in positions:
            # We assume current price of every stock as 100
            returns += (100 - position.average_price) * position.count
        return returns

    class Meta:
        model = Portfolio
        fields = '__all__'


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = '__all__'

    def validate(self, attrs):
        try:
            positions_on_security = Position.objects.filter(portfolio=attrs['portfolio'],
                                                            security=attrs['security'])
            # Validate the trade for short selling
            if attrs['trade_type'] == Trade.SELL:
                if len(positions_on_security) == 1:
                    position = positions_on_security[0]
                    if position.count < attrs['count']:
                        raise Exception('Sell quantity more than holdings')
                else:
                    raise Exception('Cannot sell securities not being held')
        except:
            raise serializers.ValidationError('This trade results in invalid position')
        return attrs

    def create(self, validated_data):
        positions_on_security = Position.objects.filter(portfolio=self.validated_data['portfolio'],
                                                        security=self.validated_data['security'])
        if len(positions_on_security) == 0:
            Position.objects.create(
                portfolio=self.validated_data['portfolio'],
                security=self.validated_data['security'],
                count=self.validated_data['count'],
                average_price=self.validated_data['trade_price']
            )
        else:
            position = positions_on_security[0]
            if self.validated_data['trade_type'] == Trade.BUY:
                new_average_price = (position.average_price * position.count + self.validated_data['trade_price'] * self.validated_data['count']) / (
                        position.count + self.validated_data['count'])
                position.count = position.count + self.validated_data['count']
                position.average_price = new_average_price
                position.save()
            else:
                position.count = position.count - self.validated_data['count']
                position.save()
        trade = Trade(**validated_data)
        trade.save()
        return trade

    def update(self, trade, validated_data):
        # Update is tricky as the security can change. We need to validate the positions for new as well
        # as old security when the security change for a trade
        trades_on_security = Trade.objects.filter(portfolio=trade.portfolio,
                                                  security=trade.security) \
            .order_by('trade_time')

        count = 0
        buy_count = 0
        average_price = 0
        for t in trades_on_security:
            if t == trade:
                if t.security == validated_data['security']:
                    t = Trade(trade_type=validated_data['trade_type'],
                              count=validated_data['count'],
                              trade_price=validated_data['trade_price'])
                else:
                    continue

            if t.trade_type == Trade.BUY:
                count += t.count
                buy_count += t.count
                average_price += t.trade_price * t.count
            else:
                count -= t.count
                # average_price -= t.trade_price * t.count
            if count < 0:
                raise ValidationError('Position becomes invalid on updating this trade')

        # Handle security change on trade, need validation for positions on new security
        if trade.security != validated_data['security']:
            trades_on_security = Trade.objects.filter(portfolio=trade.portfolio,
                                                      security=validated_data['security'])\
                .order_by('trade_time')
            count_new_sec = 0
            average_price_new_sec = 0
            for t in trades_on_security:
                if trade.time_of_addition > t.time_of_addition:
                    t = Trade(trade_type=validated_data['trade_type'],
                              count=validated_data['count'],
                              average_price=validated_data['average_price'])
                if t.trade_type == Trade.BUY:
                    count_new_sec += t.count
                    average_price_new_sec += t.trade_price * t.count
                else:
                    count_new_sec -= t.count
                    average_price_new_sec -= t.trade_price * t.count
                if count_new_sec < 0:
                    raise ValidationError('Position becomes invalid on updating this trade')

        if buy_count != 0:
            average_price /= buy_count
        else:
            average_price = 0

        positions_on_security = Position.objects.filter(portfolio=trade.portfolio, security=trade.security)
        # Ideally positions can be time series snapshots for every new trade. For simplicity, storing only latest now.
        # Former way helps with lower compute as only positions post that point need to be checked.
        if len(positions_on_security) > 0:
            position = positions_on_security[0]
            position.count = count
            position.average_price = average_price
            position.save()

        trade.security = validated_data['security']
        trade.count = validated_data['count']
        trade.trade_type = validated_data['trade_type']
        trade.trade_price = validated_data['trade_price']
        trade.save()
        return trade


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('security', 'count', 'average_price')
