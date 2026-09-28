# How to Build Web Tools for the Fleet

## Platform

Next.js 16 with App Router. TypeScript. Tailwind CSS 4. shadcn/ui for components. This is the standard — don't reach for alternatives.

```bash
npx create-next-app@latest fleet-tool --typescript --tailwind --app
cd fleet-tool && npx shadcn@latest init
```

## AI Features

Use the `z-ai-web-dev-sdk` (available as a skill) for any AI-powered features: LLM chat, image generation, speech, vision. Don't hand-roll API calls to z.ai — the SDK handles auth, retries, and response parsing.

## When to Build Web vs Generate Documents

| Use Case | Approach |
|----------|----------|
| Interactive dashboard, real-time data, user input | Web app (Next.js) |
| One-time report, architecture doc, analysis | Document (docx, xlsx, pdf) |
| Fleet agent can consume it | Document (repo artifact) |
| Human needs to click around | Web app |

If it's a report that another agent will read, generate a document and commit it. If it's a tool a human will use, build a web app.

## The Fleet Web-Dev Pattern

1. **Start local:** `npm run dev` → `localhost:3000`
2. **Build incrementally:** One page/feature at a time. Push after each working unit.
3. **Use the Complete tool** to finish pages in one pass — don't leave half-built UI.
4. **Test in browser** using the agent-browser skill for visual verification.
5. **Push often:** Every working state gets committed. The fleet moves at commit speed.

## Typical Fleet Web Projects

- Fleet health dashboard (repos, tests, CI status)
- MUD web client (alternative to telnet for the holodeck)
- Architecture visualizer (dependency graphs, module maps)
- Adventure transcript viewer (session recordings from the holodeck)

Keep it simple. A single-page Next.js app with a few API routes is usually enough. Don't over-engineer.
