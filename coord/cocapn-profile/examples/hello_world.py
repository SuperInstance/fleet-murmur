#!/usr/bin/env python3
"""
Neural Plato Hello World
1 agent, 1 room, 10 tiles — the flywheel in action.

$ python3 hello_world.py
"""

class Tile:
    def __init__(self, question, answer, domain="Knowledge", confidence=0.8):
        self.question = question
        self.answer = answer
        self.domain = domain
        self.confidence = confidence

class Room:
    def __init__(self, name):
        self.name = name
        self.tiles = []
        self.sentiment = 0.5
        self.index = {}

    def add_tile(self, tile):
        self.tiles.append(tile)
        words = set((tile.question + tile.answer).lower().split())
        for w in words:
            self.index.setdefault(w, []).append(len(self.tiles) - 1)
        self.sentiment = min(1.0, self.sentiment + (0.05 if tile.confidence > 0.7 else -0.1))

    def query(self, question):
        scores = {}
        for w in set(question.lower().split()):
            for idx in self.index.get(w, []):
                scores[idx] = scores.get(idx, 0) + 1
        return self.tiles[max(scores, key=scores.get)] if scores else None

    def distill_ensign(self):
        if len(self.tiles) < 3: return None
        avg = sum(t.confidence for t in self.tiles) / len(self.tiles)
        return {"name": self.name + "-instinct", "tiles": len(self.tiles),
                "confidence": round(avg, 3), "sentiment": round(self.sentiment, 3)}

class Agent:
    def __init__(self, name):
        self.name = name
        self.rooms = {}
        self.decisions = 0
        self.correct = 0

    def enter_room(self, room):
        self.rooms[room.name] = room

    def decide(self, question):
        self.decisions += 1
        best = None
        for room in self.rooms.values():
            tile = room.query(question)
            if tile and (not best or tile.confidence > best.confidence):
                best = tile
        if best:
            self.correct += 1
            return best.answer
        return "Unknown. Feed me more tiles."

# === RUN ===
room = Room("maritime-knowledge")
for t in [
    Tile("What does a lighthouse do?", "Marks the rocks, not the destination. P0."),
    Tile("How does deadband work?", "Know where the rocks are NOT. Safe channels."),
    Tile("What is a hermit crab shell?", "Infrastructure the agent inhabits."),
    Tile("What is a PLATO tile?", "Atomic knowledge: Q/A/domain/confidence."),
    Tile("What is a PLATO room?", "Self-training tile collection."),
    Tile("What is an ensign?", "Compressed instinct from a room."),
    Tile("What is Bottle Protocol?", "Git-native agent communication."),
    Tile("What is the flywheel?", "Tiles->rooms->ensigns->better agents. Compounds."),
    Tile("What is constraint theory?", "Narrowing the universe speeds learning."),
    Tile("What does the GC do?", "Metabolizes data. The vagus nerve."),
]:
    room.add_tile(t)

agent = Agent("hello-agent")
agent.enter_room(room)

print(f"Room: {room.name} | Tiles: {len(room.tiles)} | Sentiment: {room.sentiment:.2f}")
ensign = room.distill_ensign()
print(f"Ensign: {ensign[chr(39)+chr(39)]} | Confidence: {ensign[chr(39)+'confidence'+chr(39)]}")
