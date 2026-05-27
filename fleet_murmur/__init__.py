"""fleet_murmur — lightweight gossip protocol for agent fleet communication."""

from .message import MurmurMessage
from .peer import Peer, PeerManager
from .rumor import RumorMill, RumorState
from .gossip import GossipProtocol
from .convergence import ConvergenceDetector

__all__ = [
    "MurmurMessage",
    "Peer",
    "PeerManager",
    "RumorMill",
    "RumorState",
    "GossipProtocol",
    "ConvergenceDetector",
]
__version__ = "0.1.0"
