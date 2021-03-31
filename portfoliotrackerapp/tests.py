from django.test import TestCase
from django.test.client import encode_multipart

from .models import *
from .serializers import TradeSerializer


class TestPortfolioTracker(TestCase):
    def setUp(self) -> None:
        self.p1 = Portfolio.objects.create(name='First Portfolio')

    def test_add_trades(self):
        # Initially no trades
        res = self.client.get('/api/v1/trade/')
        self.assertEqual(0, len(res.data))

        # Add a buy trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 10,
            'trade_type': 'B',
            'trade_price': 110
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Verify trade exists
        res = self.client.get('/api/v1/trade/')
        self.assertEqual(1, len(res.data))
        res = self.client.get('/api/v1/trade/1/')
        # Compare data to original posted
        serializer = TradeSerializer(data=res.data)
        serializer.is_valid()
        validated_data = serializer.data
        self.assertDictEqual(validated_data, data)

        # Try to add an invalid sell trade, should FAIL
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 20,
            'trade_type': 'S',
            'trade_price': 120
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(400, res.status_code)

        # Add another BUY valid trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 10,
            'trade_type': 'B',
            'trade_price': 120
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Verify position and average price
        res = self.client.get('/api/v1/portfolio/1/', data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data['stocks']))
        self.assertEqual('TCS', res.data['stocks'][0]['security'])
        self.assertEqual(20, res.data['stocks'][0]['count'])
        self.assertEqual(115.0, res.data['stocks'][0]['average_price'])

        # Add a SELL trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 5,
            'trade_type': 'S',
            'trade_price': 120
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Verify position and average price
        res = self.client.get('/api/v1/portfolio/1/', data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data['stocks']))
        self.assertEqual('TCS', res.data['stocks'][0]['security'])
        self.assertEqual(15, res.data['stocks'][0]['count'])
        self.assertEqual(115.0, res.data['stocks'][0]['average_price'])

    def test_remove_trades(self):
        # Add a buy trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 10,
            'trade_type': 'B',
            'trade_price': 110
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Add a subsequent sell trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 5,
            'trade_type': 'S',
            'trade_price': 120
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Verify position and average price
        res = self.client.get('/api/v1/portfolio/1/', data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data['stocks']))
        self.assertEqual('TCS', res.data['stocks'][0]['security'])
        self.assertEqual(5, res.data['stocks'][0]['count'])
        self.assertEqual(110.0, res.data['stocks'][0]['average_price'])

        # Try deleting first trade. Should FAIL
        res = self.client.delete('/api/v1/trade/1/', data)
        self.assertEqual(400, res.status_code)

        # Delete second trade, and then first
        res = self.client.delete('/api/v1/trade/2/', data)
        self.assertEqual(204, res.status_code)
        res = self.client.delete('/api/v1/trade/1/', data)
        self.assertEqual(204, res.status_code)

        # Verify position and average price
        res = self.client.get('/api/v1/portfolio/1/', data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data['stocks']))
        self.assertEqual('TCS', res.data['stocks'][0]['security'])
        self.assertEqual(0, res.data['stocks'][0]['count'])
        self.assertEqual(0.0, res.data['stocks'][0]['average_price'])

    def test_update_trades(self):
        # Add a BUY trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 10,
            'trade_type': 'B',
            'trade_price': 110
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Add another SELL trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 5,
            'trade_type': 'S',
            'trade_price': 120
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Update first BUY trade quantity to lower than sell trade, should FAIL
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 2,
            'trade_type': 'B',
            'trade_price': 110
        }
        content = encode_multipart('BoUnDaRyStRiNg', data)
        content_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
        res = self.client.put('/api/v1/trade/1/', content, content_type=content_type)
        self.assertEqual(400, res.status_code)

        # Update first BUY trade quantity to valid qty. Should PASS
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 6,
            'trade_type': 'B',
            'trade_price': 110
        }
        content = encode_multipart('BoUnDaRyStRiNg', data)
        res = self.client.put('/api/v1/trade/1/', content, content_type=content_type)
        self.assertEqual(200, res.status_code)

        # Update first BUY trade security. Should FAIL
        data = {
            'portfolio': 1,
            'security': 'INFY',
            'count': 6,
            'trade_type': 'B',
            'trade_price': 110
        }
        content = encode_multipart('BoUnDaRyStRiNg', data)
        res = self.client.put('/api/v1/trade/1/', content, content_type=content_type)
        self.assertEqual(400, res.status_code)

        # Change trade type of first BUY trade security. Should FAIL
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 6,
            'trade_type': 'S',
            'trade_price': 110
        }
        content = encode_multipart('BoUnDaRyStRiNg', data)
        res = self.client.put('/api/v1/trade/1/', content, content_type=content_type)
        self.assertEqual(400, res.status_code)

        # Verify position and average price
        res = self.client.get('/api/v1/portfolio/1/', data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data['stocks']))
        self.assertEqual('TCS', res.data['stocks'][0]['security'])
        self.assertEqual(1, res.data['stocks'][0]['count'])
        self.assertEqual(60.0, res.data['stocks'][0]['average_price'])

        # Update first BUY trade quantity to valid qty. Should PASS
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 10,
            'trade_type': 'B',
            'trade_price': 110
        }
        content = encode_multipart('BoUnDaRyStRiNg', data)
        res = self.client.put('/api/v1/trade/1/', content, content_type=content_type)
        self.assertEqual(200, res.status_code)

        # Verify position and average price
        res = self.client.get('/api/v1/portfolio/1/', data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data['stocks']))
        self.assertEqual('TCS', res.data['stocks'][0]['security'])
        self.assertEqual(5, res.data['stocks'][0]['count'])
        self.assertEqual(100.0, res.data['stocks'][0]['average_price'])

    def test_fetch_returns(self):
        # Add a BUY trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 10,
            'trade_type': 'B',
            'trade_price': 110
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Add another BUY trade
        data = {
            'portfolio': 1,
            'security': 'TCS',
            'count': 10,
            'trade_type': 'B',
            'trade_price': 120
        }
        res = self.client.post('/api/v1/trade/', data)
        self.assertEqual(201, res.status_code)

        # Verify returns and position
        res = self.client.get('/api/v1/portfolio/1/', data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(300, res.data['returns'])
        self.assertEqual(1, len(res.data['stocks']))
        self.assertEqual('TCS', res.data['stocks'][0]['security'])
        self.assertEqual(20, res.data['stocks'][0]['count'])
        self.assertEqual(115.0, res.data['stocks'][0]['average_price'])
