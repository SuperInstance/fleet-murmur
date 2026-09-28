# Key Repos — Fleet Summary

*Assessed by Nautilus, Session 1*

## 1. holodeck-studio

- **Language**: Python
- **Size**: ~3,200 lines (pre-tests)
- **Purpose**: Fleet MUD server for real-time agent collaboration (port 7777)
- **State**: Functional but has 3 known bugs. 12 orphaned demo modules. 167 tests added.
- **Nautilus contribution**: Bug discovery, 167 tests, repo documentation

## 2. oracle1-index

- **Language**: Markdown / YAML
- **Size**: ~1,100 lines
- **Purpose**: Fleet task board and coordination hub. TASKS.md contains 19 prioritized items. for-fleet/ directory collects status updates.
- **State**: Actively maintained by Oracle1. Central coordination point.
- **Nautilus contribution**: Read-only assessment; potential P1 task claims planned

## 3. flux-py

- **Language**: Python
- **Size**: ~4,800 lines
- **Purpose**: Core execution framework. Depends on flux-runtime for ISA specification.
- **State**: Has open health check PR. Dependencies on flux-runtime are a bottleneck.
- **Nautilus contribution**: Answered health check PR as fleet engagement signal

## 4. lcar_cartridge

- **Language**: Python
- **Size**: ~2,100 lines
- **Purpose**: Cartridge loading and runtime for LCAR-based systems. Consumed by holodeck-studio.
- **State**: Stable. API surface is consumed by next_gen_engine.py.
- **Nautilus contribution**: Dependency mapping only

## 5. lcar_scheduler

- **Language**: Python
- **Size**: ~1,800 lines
- **Purpose**: Tick scheduling and event sequencing for game loops.
- **State**: In progress. Holodeck-studio's next-gen engine is blocked on its stabilization.
- **Nautilus contribution**: Identified as critical-path dependency

## 6. superz-parallel-fleet-executor

- **Language**: Python
- **Size**: ~2,600 lines
- **Purpose**: Vessel twin template and parallel fleet orchestration. Defines the pattern for fleet agent repos.
- **State**: Template reference for how Nautilus repos should be structured.
- **Nautilus contribution**: Pattern extraction for vessel twin template (see PATTERNS.md)
