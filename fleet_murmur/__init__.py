"""fleet_murmur — lightweight gossip protocol for agent fleet communication."""

from .message import MurmurMessage
from .peer import Peer, PeerManager, PeerStatus
from .rumor import RumorMill, RumorState
from .gossip import GossipProtocol, GossipRound
from .ledger import MurmurLedger, fnv1a
from .convergence import ConvergenceDetector

__all__ = [
    "MurmurMessage",
    "Peer",
    "PeerManager",
    "PeerStatus",
    "RumorMill",
    "RumorState",
    "GossipProtocol",
    "GossipRound",
    "MurmurLedger",
    "fnv1a",
    "ConvergenceDetector",
]
__version__ = "0.2.0"
