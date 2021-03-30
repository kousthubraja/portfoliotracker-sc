from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .logic import validate_trade
from .models import *


class PortfolioSerializer(serializers.ModelSerializer):
    stocks = serializers.SerializerMethodField()
    returns = serializers.SerializerMethodField()

    def get_stocks(self, portfolio):
        allocations = Position.objects.filter(portfolio=portfolio)
        serializer = PositionSerializer(data=allocations, many=True)
        serializer.is_valid()
        return serializer.data

    def get_returns(self, portfolio):
        positions = Position.objects.filter(portfolio=portfolio)
        returns = 0
        for position in positions:
            returns += (position.average_price - 100) * position.count
        return returns

    class Meta:
        model = Portfolio
        fields = '__all__'


class PortfolioAddSerializer(serializers.ModelSerializer):
    date_last_rebalanced = serializers.SerializerMethodField()

    def get_created_date(self, portfolio):
        return portfolio.created_date.strftime("%Y-%m-%d")

    class Meta:
        model = Portfolio
        fields = '__all__'


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = '__all__'

    def validate(self, attrs):
        try:
            validate_trade(attrs['portfolio'], attrs['security'],
                           attrs['trade_type'], attrs['count'])
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
        trades_on_security = Trade.objects.filter(portfolio=trade.portfolio,
                                                  security=trade.security) \
            .order_by('trade_time')

        count = 0
        average_price = 0
        for t in trades_on_security:
            if t == trade:
                t = Trade(trade_type=validated_data['trade_type'],
                          count=validated_data['count'],
                          average_price=validated_data['average_price'])

            if t.trade_type == Trade.BUY:
                count += t.count
                average_price += t.trade_price * t.count
            else:
                count -= t.count
                average_price -= t.trade_price * t.count
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

        if count != 0:
            average_price /= count
        else:
            average_price = 0

        positions_on_security = Position.objects.filter(portfolio=trade.portfolio, security=trade.security)
        # Todo - Make positions time series and snapshot position at each time there's a change so only trades post
        # trade to be deleted need to be checked
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
