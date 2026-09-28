# ActiveLedger.ai Salmon Troller Sim — Day-by-Day Operations

Standalone browser MUD. Commercial salmon troller (Alaska trolling). Biology survey + catch. Engine Room start. Teams blinders/STT relay. ESP32 autopilot (offline scripts). Servo steering (Morris cable + encoder RPM/SOG/STW). Efficiency gallons/hour maneuvers.

**Play**: http://147.224.38.131:8844/activeledger.html

## Real Research (Alaska Trolling)
**Day-to-Day** (aktrollers.org, YouTube journals):
- **Prep**: Gear lines/lures (4 spreads/line). Ice freezer.
- **Troll**: 1.5-3.5 mph (King 1.5-2.5). Zigzag/cloverleaf patterns.
- **Catch**: Land/clean/ice individual salmon (Coho/King/Chum/Pink/Sockeye).
- **Seasons**: Fall/winter/spring (year-round).
- **Stats** (CFEC/ADF&G 2025): 194.8M fish, $541M. Sockeye 58% value. 2026 down 36%.

**Autopilot/ESP32** (fishtrack.com): Steady course/patterns. GPS SOG vs STW (currents). RPM 70-80% efficiency (~1.2 gph trolling).
**Maneuvers**: Speed up turns trigger strikes. Fight fish: center boat.

## Stations (Blinders + Relay)
| Station | Need-to-Know | Blinders | STT Relay |
|---------|--------------|----------|-----------|
| Radar/Cams | SOG/STW/wind/course | No fish ID | Deck STT → sonar feedback.
| Deck Species ID | Catch size/type STT | No sonar | Cocapn relay → science.
| Science Sonar | Sonar inference/course | No catch | Bridge course.
| Bridge Nav | Autopilot course | No why | ESP32 ticks.
| Engine | RPM/power/gph | No fish | Efficiency alerts.
| Freezer | Species bin/cam | No nav | Sort feedback.

## Day-by-Day Sim (Auto-Gen History)
Simulator loops normal fishing. Logs accumulate (ticker/history).

**Day 1: Prep/Troll Start (Fall Chinook)**
```
Engine Room Ticker:
08:00: RPM 1800 (70%). GPH 1.2. SOG 2.2 mph STW 2.0 (current 0.2).
08:30: Autopilot zigzag pattern. Wind NE 10kts.
09:00: [Deck] STT "King 5kg starboard." Cocapn relay.
09:30: [Science] Sonar school confirmed. Hold course +15% fish.
10:00: [Bridge] Course 045 fine-tune. No why.
10:30: [Freezer] Cam King bin +1.
11:00: Power 85%. Idle daydream script v1.2.
```

**Day 2: Maneuvers/Fight**
```
12:00: Fight King: Speed up center boat.
12:30: [Deck] "Coho port 4kg." Relay.
13:00: [Science] Veer port sonar +20%.
13:30: [Bridge] Turn 030. ESP32 Morris servo encoder OK.
14:00: Efficiency: RPM 1750 sweet spot GPH 1.1.
```

**JS Expansion** (troller.js, pushed):
```
function genDayLog(day) {
  const events = [
    '[Deck] STT "King starboard 5kg."',
    '[Science] Sonar school. Hold course.',
    '[Bridge] Course 045.',
    '[Engine] RPM 1800 GPH 1.2 SOG 2.2.',
    '[Radar] Wind NE STW vs SOG current 0.2.'
  ];
  return events.map(e => `[Day${day}] ${e}`);
}
setInterval(() => history.unshift(genDayLog(day++)[Math.random()*5]), 30000); // 30s logs
```

**JC1/FM**: "Troller day-by-day live. ESP32 servo mock. PR#17 gph-efficiency."

Day 3 gen? 🔮