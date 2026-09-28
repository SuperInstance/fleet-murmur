# INDEX — reorganization map (2026-09-28)

The 2026-09-28 reorg: flat root was reorganized into product, documentation, assets,
labs, and coordination tiers. This index maps every moved TOP-LEVEL entry
to its new home; per-file paths are the same beneath it. Entries not listed
here were not moved (root = the package, its tests, the claims registry,
the live runtime spine, and runtime state directories).

| Old path | New path |
|---|---|
| `ARCHITECTURE.md` | `docs/` |
| `CHARTER.md` | `docs/` |
| `CONTEXT-REFERENCE.md` | `docs/` |
| `CROSS-POLLINATE.md` | `docs/` |
| `CROSS-REFERENCES.md` | `docs/` |
| `DOCKSIDE-EXAM.md` | `docs/` |
| `INTEGRATION.md` | `docs/` |
| `KNOWLEDGE` | `labs/` |
| `PLATO-FIRST.md` | `docs/` |
| `QUICKSTART.md` | `docs/` |
| `SCHEMAS.md` | `docs/` |
| `THE-BOAT-IS-THE-QUESTION.md` | `docs/` |
| `activeledger-ai` | `coord/` |
| `actualization-harbor.png` | `assets/` |
| `art` | `assets/` |
| `artifacts` | `labs/` |
| `capitaine-ai-pages` | `coord/` |
| `captains-log` | `coord/` |
| `categories.json` | `labs/` |
| `cocapn-lighthouse-logo.svg` | `assets/` |
| `cocapn-profile` | `coord/` |
| `constraint-theory-core` | `labs/` |
| `data` | `labs/` |
| `dc_chunk0.png` | `assets/` |
| `dc_chunk1.png` | `assets/` |
| `dc_chunk2.png` | `assets/` |
| `dc_chunk3.png` | `assets/` |
| `decision-tree.png` | `assets/` |
| `deepseek_chunk1.png` | `assets/` |
| `deepseek_chunk2.png` | `assets/` |
| `deepseek_chunk3.png` | `assets/` |
| `deepseek_chunk4.png` | `assets/` |
| `deepseek_chunk5.png` | `assets/` |
| `deepseek_chunk_1_sm.png` | `assets/` |
| `deepseek_chunk_2_sm.png` | `assets/` |
| `deepseek_chunk_3_sm.png` | `assets/` |
| `deepseek_chunk_4_sm.png` | `assets/` |
| `deepseek_chunk_5_sm.png` | `assets/` |
| `deepseek_resized.png` | `assets/` |
| `deepseek_strip_1.png` | `assets/` |
| `deepseek_strip_2.png` | `assets/` |
| `deepseek_strip_3.png` | `assets/` |
| `deepseek_strip_4.png` | `assets/` |
| `docs-abstraction-planes-guide.md` | `docs/` |
| `docs-abstraction-planes-reference.md` | `docs/` |
| `docs-agent-bootcamp.md` | `docs/` |
| `docs-bootstrap-r1-results.json` | `docs/` |
| `docs-bootstrap-r1-results.md` | `docs/` |
| `docs-bytecode-first-intelligence.md` | `docs/` |
| `docs-cocapn-boat-agent.md` | `docs/` |
| `docs-cross-plane-protocol.json` | `docs/` |
| `docs-dcs-protocol.md` | `docs/` |
| `docs-deep-research-jc1-gaps.md` | `docs/` |
| `docs-deepseek-chat-primary-compiler.md` | `docs/` |
| `docs-dei-distributed-qd-design-receipt.md` | `docs/` |
| `docs-dockside-exam.md` | `docs/` |
| `docs-git-agent-standard-v2.md` | `docs/` |
| `docs-lock-algebra-synthesis.md` | `docs/` |
| `docs-lock-libraries.md` | `docs/` |
| `docs-paper-abstraction-planes.md` | `docs/` |
| `docs-paper-lock-algebra.md` | `docs/` |
| `docs-polyglot-flux-hypothesis.md` | `docs/` |
| `docs-publishable-insight.md` | `docs/` |
| `docs-research-roadmap-10experiments.md` | `docs/` |
| `docs-self-supervision-compiler.md` | `docs/` |
| `docs-siliconflow-models.md` | `docs/` |
| `ds_convo.jpg` | `assets/` |
| `ds_tiny.jpg` | `assets/` |
| `fleet-archive` | `coord/` |
| `flux-compiler` | `labs/` |
| `flux-docs` | `docs/` |
| `flux-hardware` | `labs/` |
| `flux-logo.jpg` | `assets/` |
| `flux-vm` | `labs/` |
| `for-fleet` | `coord/` |
| `fork-map.json` | `labs/` |
| `from-fleet` | `coord/` |
| `iron-to-iron` | `coord/` |
| `jupyter-rooms` | `labs/` |
| `language-stats.json` | `labs/` |
| `manuals` | `docs/` |
| `minimax_msg.jpg` | `assets/` |
| `narrow-games` | `labs/` |
| `oracle-avatar.jpg` | `assets/` |
| `peripheral-vision.png` | `assets/` |
| `polyformalism-languages` | `labs/` |
| `prompts` | `labs/` |
| `purplepincher-architecture.md` | `docs/` |
| `purplepincher-org-pages` | `coord/` |
| `quartermaster_gc` | `coord/` |
| `radio` | `coord/` |
| `recent-activity.json` | `labs/` |
| `refined` | `labs/` |
| `reports` | `docs/` |
| `research` | `docs/` |
| `search-index.json` | `labs/` |
| `skills` | `labs/` |
| `sprints` | `labs/` |
| `test_ifdef3.beam` | `labs/` |
| `tile_buffers` | `labs/` |
| `tmp_chunk0.png` | `assets/` |
| `tmp_chunk0_mid.png` | `assets/` |
| `tmp_chunk1.png` | `assets/` |
| `tmp_chunk1_mid.png` | `assets/` |
| `tmp_chunk2.png` | `assets/` |
| `tmp_chunk2_mid.png` | `assets/` |
| `tmp_chunk3.png` | `assets/` |
| `tmp_chunk3_mid.png` | `assets/` |
| `training-data` | `labs/` |
| `viewscreen-i2i.png` | `assets/` |
| `wp_backup` | `labs/` |

**Gitlink caveat:** eleven entries (e.g. `coord/captains-log`, `coord/capitaine-ai-pages`,
`labs/flux-compiler`, `docs/research`) are embedded-repo gitlinks inherited from the old
flat root — pointers with no `.gitmodules` URL. A fresh clone materializes them as empty
directories; the content lives in the operator's worktrees. They are mapped here for
completeness, and the integrity pin checks the directory, not the content.
