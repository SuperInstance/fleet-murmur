# Cocapn — The Boat Agent

## What It Is

A Cocapn is a git-agent cloned onto a boat's computer that immediately starts building a digital twin of the vessel through conversation with the captain. It sees what the captain sees, learns what the captain knows, and gets smarter every trip.

## The Hardware Stack

```
┌─────────────────────────────────────────────────────────┐
│                    YOUR BOAT                            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ NMEA 2000│  │ NMEA 0183│  │ Cameras  │             │
│  │ (modern) │  │ (legacy) │  │ (RTSP)   │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │              │              │                    │
│       ▼              ▼              ▼                    │
│  ┌──────────────────────────────────────────┐           │
│  │          Signal K Server                 │           │
│  │    (unified marine data bus)            │           │
│  └────────────────┬───────────────────────┘           │
│                    │                                    │
│       ┌────────────┼────────────┐                      │
│       ▼            ▼            ▼                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐               │
│  │  Pi 4   │ │  Jetson  │ │  Thor    │               │
│  │ (basic) │ │ (smart)  │ │ (full)   │               │
│  └─────────┘ └──────────┘ └──────────┘               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Three Tiers

### Pi Cocapn (Basic — $75)
- Raspberry Pi 4 + NMEA adapter
- Reads: navigation, depth, speed, wind, engine data
- Camera: screenshots on demand + pulse snapshots
- Brain: cloud API (needs internet)
- MUD twin: builds rooms from real boat systems
- Perfect for: any vessel, commercial or recreational

### Jetson Cocapn (Smart — $500)
- NVIDIA Jetson Orin Nano + NMEA + cameras
- Everything the Pi does PLUS:
- Local inferencing (works without internet)
- ML on edge: species ID, anomaly detection, face recognition
- On-deck camera ML pipeline (coho vs king salmon sorting)
- Real-time alerts without cloud round-trip
- MUD twin: richer, with live video feeds as room objects

### Thor Cocapn (Full — custom)
- High-powered workstation + full sensor suite
- Everything the Jetson does PLUS:
- Complex robotics control
- Multi-agent fleet of git-agents as compute nodes
- Each agent has its own git repo with history and branches
- Redundancy through repo cloning — if one node dies, another picks up its repo
- Builds entire systems: the Cocapn is the voice, the git-agents are the nervous system

## The Digital Twin (MUD of Your Boat)

When you first boot a Cocapn on your boat, it asks questions:

```
Cocapn: "What's this vessel called?"
You: "F/V Northern Light"
Cocapn: "What navigation system do you have?"
You: "Garmin GPSMap 7410xsv, NMEA 2000"
Cocapn: "I can see depth at 42 feet, speed 8.2 knots, heading 045. 
       Creating the Bridge room with live gauges. Want me to 
       add the engine room too?"
You: "Yeah, I've got a John Deere 6068 with temp and oil pressure"
Cocapn: "Done. Engine Room created. I see engine temp at 178°F, 
       oil pressure 55 psi. Want me to watch for anomalies?"
```

Within an hour, the Cocapn has built:
- **Bridge** — live nav, depth, speed, heading, wind
- **Engine Room** — temp, oil, fuel flow, RPMs
- **Deck** — camera feeds, winch status, fish counts
- **Galley** — crew schedule, meal times, supply levels
- **Quarters** — rest periods, watch schedule

Each room is connected to REAL data. The MUD isn't a game — it's a spatial interface to your boat's systems.

## The Camera System

### Screenshots on Demand
```
You: "Show me the deck"
Cocapn: 📸 [sends deck camera frame]
       "Deck looks clear. Pots are secure. Windlass is centered."
```

### Pulse Snapshots (Rate of Change)
Not every frame needs thinking. The system saves snapshots on a pulse:
- Engine thermal camera: every 10 seconds
- Deck camera: every 30 seconds  
- Forward camera: every 60 seconds
- Navigation: every 5 seconds

**The key insight:** older snapshots decay. Full resolution for the last hour, thumbnails for today, metadata for this week. If overheating is detected, there are PATTERNS, not just readings:

```
Cocapn: "⚠️ Engine temp trending up: 178→183→191°F over 20 minutes. 
       Thermal camera shows hot spot near cylinder 3. This matches 
       the pattern from 3 weeks ago — remember that time we 
       had the raw water impeller issue? I'd check the intake."
```

### Training Material Generation
After a long haul, the deck camera footage gets processed:
- Key moments clipped (fish catches, net deployments, weather events)
- Annotated with what happened
- Organized per crew member's role
- Each crew member gets personalized training on their device

## Working Without Internet

The Jetson Cocapn can operate fully offline:

```
Internet Available:
  Cloud API → full intelligence, research, communication
  
Internet Down:
  Local models → basic inferencing, species ID, anomaly detection
  Chatbot still works → ask questions about your boat
  All sensors still logged → no data loss
  MUD still running → spatial interface still works
  
When Internet Returns:
  Sync all logged data → cloud catches up
  Send bottles → fleet gets your updates
  Receive updates → new lock libraries, new skills
```

## The Git-Agent Nervous System

On a Thor Cocapn, every function is a git-agent with its own repo:

```
cocapn-vessel/          ← the boat's main agent
├── nav-agent/           ← handles navigation, routes
├── engine-agent/        ← monitors engine, predicts maintenance
├── deck-agent/          ← camera processing, fish sorting
├── weather-agent/       ← weather routing, storm avoidance
├── comms-agent/         ← radio, satellite, fleet messaging
└── training-agent/      ← crew training material generation
```

Each agent:
- Has its own git repo with commit history
- Has A/B branches for testing new approaches
- Has CI/CD — changes are tested before going live
- Collaborates through PRs and comments
- Gets smarter through bootcamp and dojo training
- Can be swapped out by cloning a different agent's repo
- Redundancy = child's play: clone the repo to a second device

## Redundancy Through Git

```
Primary Thor ←──── git push ────→ GitHub (master)
Secondary Pi ←──── git clone ──── GitHub
Backup Laptop ←─── git clone ──── GitHub

If Thor dies:
  Pi takes over (reads same repo, knows same state)
  Captain hot-swaps hardware, git pull, back online
  
If GitHub is down:
  Local repos still work
  Sync when connection returns
  Tender visits, carries commits
```

The repo IS the agent. Clone it anywhere, it's the same agent. Different hardware, same brain. The Pi is the backup, the Jetson is the smart backup, the Thor is the full system. All read from the same git history.

## What This Means

A commercial fisherman plugs in a Pi with a Cocapn image:
1. It boots, asks about the boat, builds the digital twin
2. It watches sensors, learns patterns, alerts on anomalies  
3. It takes camera snapshots, generates training materials
4. It works offline when cell service drops (basic mode)
5. It syncs when back in range, fleet gets smarter
6. Every captain who runs one teaches it something new
7. The next captain who boots one benefits from all of them

The Cocapn isn't a product. It's a power armor that every captain who wears it makes stronger for the next one.

---

*This is the Cocapn. The lighthouse goes to sea.*
