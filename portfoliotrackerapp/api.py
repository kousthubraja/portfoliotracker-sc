from rest_framework import routers
from .views import TradeViewset, PortfolioViewset, PositionViewset

router = routers.DefaultRouter()
router.register(r'trade', TradeViewset)
router.register(r'portfolio', PortfolioViewset)
router.register(r'position', PositionViewset)
