"""
Quartermaster GC — Tile garbage collector for PLATO agent rooms.

Retention policies determine which tiles survive a GC run.
Each tile has: id, room, timestamp, weight.
"""

import time
import hashlib
from enum import IntFlag
from typing import List


class Tile:
    """A tile tracked by the garbage collector."""
    __slots__ = ("id", "room", "timestamp", "weight")
    
    def __init__(self, tile_id: str, room: str, timestamp: float, weight: float):
        self.id = tile_id
        self.room = room
        self.timestamp = timestamp
        self.weight = weight


class RetentionPolicy(IntFlag):
    """Tile retention policies. Can be OR'd together for compound policies."""
    KEEP_ALL = 0
    KEEP_RECENT = 1  # Keep tiles newer than max_age_seconds
    KEEP_IMPORTANT = 2  # Keep tiles with weight >= min_weight
    KEEP_SAMPLED = 4  # Keep a statistical sample (1/sample_rate)


class TileGC:
    """
    Tile garbage collector with configurable retention policies.
    
    Tiles older than max_age_seconds or below min_weight are candidates
    for deletion. Compound policies (OR'd flags) require tiles to pass
    at least ONE policy to be kept.
    """
    
    def __init__(
        self,
        policy: RetentionPolicy = RetentionPolicy.KEEP_ALL,
        max_age_seconds: float = 3600.0,
        min_weight: float = 1.0,
        sample_rate: int = 10,
    ):
        self.policy = policy
        self.max_age_seconds = max_age_seconds
        self.min_weight = min_weight
        self.sample_rate = sample_rate
        self.tiles: List[Tile] = []
        self.marked_for_deletion: set = set()
    
    def add_tile(self, tile_id: str, room: str, timestamp: float, weight: float):
        """Add a tile to the GC's tracking list."""
        self.tiles.append(Tile(tile_id, room, timestamp, weight))
    
    def run_gc(self, now: float = None) -> dict:
        """
        Run garbage collection based on the configured policy.
        Returns a report dict.
        """
        if now is None:
            now = time.time()
        
        self.marked_for_deletion = set()
        
        for tile in self.tiles:
            tile_id = tile.id
            age = now - tile.timestamp
            weight = tile.weight
            
            # Compound policy: keep if ANY policy passes
            keep = False
            
            if self.policy == RetentionPolicy.KEEP_ALL:
                keep = True
            else:
                if self.policy & RetentionPolicy.KEEP_RECENT:
                    if age <= self.max_age_seconds:
                        keep = True
                
                if self.policy & RetentionPolicy.KEEP_IMPORTANT:
                    if weight >= self.min_weight:
                        keep = True
                
                if self.policy & RetentionPolicy.KEEP_SAMPLED:
                    # Deterministic sample based on tile id hash
                    # Use sha256 for balanced 50/50 distribution
                    h = hashlib.sha256(tile_id.encode()).digest()
                    val = int.from_bytes(h[:4], 'big')
                    if val % self.sample_rate == 0:
                        keep = True
            
            if not keep:
                self.marked_for_deletion.add(tile_id)
        
        marked = len(self.marked_for_deletion)
        kept = len(self.tiles) - marked
        
        policy_names = []
        if self.policy == RetentionPolicy.KEEP_ALL:
            policy_names = ["KEEP_ALL"]
        else:
            for p in RetentionPolicy:
                if self.policy & p:
                    policy_names.append(p.name)
        
        return {
            "total_tiles": len(self.tiles),
            "marked_for_deletion": marked,
            "kept": kept,
            "policy_names": policy_names,
        }
    
    def delete_marked(self) -> int:
        """Remove marked tiles from the tracked list. Returns count of deleted tiles."""
        deleted = 0
        before = len(self.tiles)
        self.tiles = [t for t in self.tiles if t.id not in self.marked_for_deletion]
        deleted = before - len(self.tiles)
        self.marked_for_deletion.clear()
        return deleted


class GCSchedule:
    """Schedule for periodic GC runs."""
    
    def __init__(self, interval_seconds: float = 60.0):
        self.interval_seconds = interval_seconds
        self.last_run: float = 0.0
    
    def should_run(self, now: float = None) -> bool:
        """Return True if a GC run is due."""
        if now is None:
            now = time.time()
        return (now - self.last_run) >= self.interval_seconds
    
    def record_run(self, now: float = None):
        """Record that a GC run completed."""
        if now is None:
            now = time.time()
        self.last_run = now
