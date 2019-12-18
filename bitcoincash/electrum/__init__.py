from .exc import ElectrumErrorResponse
from .client import StratumClient
class Electrum(StratumClient):
    pass

__all__ = (
    'Electrum',
)
