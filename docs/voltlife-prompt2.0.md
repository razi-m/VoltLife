# VoltLife — Full Frontend Implementation

**Repository:** https://github.com/razi-m/VoltLife.git

---

## Stitch Design Source of Truth

The design for this project lives in a Stitch project. Before implementing any screen, fetch all screen assets and code using the Stitch MCP.

**Project title:** VoltLife: India's Battery OS
**Project ID:** `8455219221847025515`

### Screens to fetch

| # | Screen name | Screen ID |
|---|---|---|
| 1 | Battery Intake & AI Assessment (v2) | `df873dc449c1405eabd1cea8cad740ec` |
| 2 | Sustainability Impact & India 2030 Vision (v2) | `c1b56d5e232144408a4948997d65e1a2` |
| 3 | Mission Control - VoltLife (v2) | `b6f7df3a2da6481d9905bb5310450492` |
| 4 | Deployment Command Center (v2) | `71c8f123967e42e4b2a174cf8614cc44` |
| 5 | Battery Aadhaar Number (BPAN) Registry (v2) | `db9dd0b8913d4bcfa7b1ac666703aabb` |
| 6 | Deep Health Analytics & Telemetry (v2) | `8696b69c5b1c4584a5920b6ed2a2df69` |
| 7 | Volt AI - Neural Chat Interface | `1542d1281d1549fcbc4132ff766b7b5b` |

### How to fetch

Use the Stitch MCP to retrieve images and code for each screen. For any hosted asset URLs returned, download them with:

```bash
curl -L <url> -o <local_path>
```

Save all fetched assets under:

```
frontend/
└── docs/
    └── stitch/
        ├── screens/        ← downloaded screen images
        └── components/     ← downloaded component code
```

### Design fidelity rules

- Treat every fetched screen as pixel-perfect reference — do not deviate
- Extract and codify all color tokens, typography scale, spacing units, and border radii into a single `tokens.css` or `tailwind.config` before writing any component
- Every component must match the Stitch layout, component structure, and visual hierarchy exactly
- Do not redesign, simplify, reinterpret, or substitute any element

---

## Phase 0 — Readiness Report (output before coding)

Before writing a single line of code, generate a structured report answering:

1. Is the backend ready for frontend integration?
2. List every Stitch screen with its intended route path.
3. For each screen: existing APIs ✓ / missing APIs ✗ / missing backend logic ✗
4. Which pages require WebSocket connections?
5. Which pages need seeded demo data?
6. What are the top 3 blockers to a working demo?

Output this as a structured table. Do not begin implementation until the report is complete.

---

## Phase 1 — Backend Gap Resolution

For every missing backend dependency identified in Phase 0:

- Create the route, schema, service, validation, and DB interaction
- Do not modify existing database architecture, API contracts, or technology choices
- Log each addition: `[NEW] POST /api/batteries/assess — BatteryService.assess()`

---

## Phase 2 — Frontend Implementation

### Build order

Follow this sequence strictly — do not skip ahead:

1. Fetch all Stitch screens and assets (see above)
2. Extract design tokens → `tailwind.config` or `tokens.css`
3. Build base UI components (buttons, inputs, cards, badges, tables)
4. Build layout shells (sidebar, navbar, page wrappers)
5. Implement each Stitch screen as a static page (no backend yet)
6. Wire backend data into each page
7. Implement the landing page + 3D experience last (isolated, won't block other screens)

### Folder structure

```
frontend/
├── docs/
│   └── stitch/
│       ├── screens/            ← Stitch screen exports
│       └── components/         ← Stitch component exports
├── src/
│   ├── components/
│   │   ├── ui/                 ← base design system components
│   │   └── features/           ← page-specific components
│   ├── pages/
│   ├── hooks/
│   ├── lib/
│   └── landing/
│       ├── LandingPage.tsx
│       ├── Scene.tsx           ← R3F canvas wrapper
│       ├── BatteryParticles.tsx
│       ├── ScrollStory.tsx     ← GSAP ScrollTrigger logic
│       └── scenes/
│           ├── IntroScene.tsx
│           ├── AadhaarScene.tsx
│           ├── AssessmentScene.tsx
│           └── ImpactScene.tsx
```

### Screen → route mapping

| Stitch screen | Route |
|---|---|
| Mission Control | `/dashboard` |
| Battery Intake & AI Assessment | `/assess` |
| Battery Aadhaar Number (BPAN) Registry | `/registry` |
| Deployment Command Center | `/deploy` |
| Deep Health Analytics & Telemetry | `/analytics` |
| Sustainability Impact & India 2030 Vision | `/impact` |
| Volt AI - Neural Chat Interface | `/ai` |
| Landing page | `/` |

### Non-negotiable UI requirements

Every interactive element must work — no `TODO`, no `console.log`, no disabled buttons, no "Coming Soon". Specifically:

- **Tables**: search, filter, sort, paginate, loading/empty/error states, connected to backend
- **Forms**: validation, submission, error/success handling, backend persistence, UI refresh
- **Modals**: open, close, submit, and reflect state changes
- **Navigation**: every route navigable, active states correct
- **Metrics**: all dashboard numbers load from real data
- **CRUD**: create/read/update/delete functional for all applicable resources
- **WebSockets**: all real-time pages connected; implement missing endpoints if needed

---

## Landing Page — Priority Implementation

The landing page is the highest-stakes surface. It must read as a funded climate-tech product within 15 seconds. It is **not** in Stitch — build it from scratch using the visual language extracted from the Stitch design tokens.

**Reference bar:** Apple Vision Pro product pages, Stripe.com, Linear.app

### Cinematic intro sequence (page load)

Implement using Three.js + React Three Fiber + Drei + GSAP + Framer Motion (only if compatible with existing architecture).

```
40M battery particles → converge → battery pack forms →
Battery Aadhaar activates → AI scan → health classification →
second-life recommendation → VoltLife platform revealed
```

### Scroll-driven storytelling

Camera position, lighting, and scene state evolve as the user scrolls through five acts:

| Section | Story beat |
|---|---|
| 1 | India's battery crisis |
| 2 | Battery Aadhaar identity |
| 3 | AI assessment |
| 4 | Deployment intelligence |
| 5 | Environmental impact |

### 3D interactive scenes

| Scene | What it shows |
|---|---|
| Battery Aadhaar viewer | Identity, lifecycle status, health, deployment state — user can inspect interactively |
| AI assessment visualizer | Battery → telemetry extraction → analysis → health classification → recommendation |
| Deployment pathways | Animated routes to EV reuse, solar storage, backup systems, recycling |
| Impact visualizer | 40M retiring batteries → recovered → repurposed → carbon reduction |

### Interactions to implement

Scroll-driven camera, mouse-responsive scenes, particle systems, animated lighting, metric counters, smooth camera interpolation, micro-interactions on hover/click.

### Performance requirements

- Fast initial load with lazy-loaded 3D assets
- Optimised geometry and textures
- WebGL unavailable → graceful HTML fallback
- Mobile → static/simplified fallback (no broken layout)

---

## Demo Readiness Checklist

A judge must be able to complete this full flow without hitting any errors:

1. Land on homepage → wowed within 15 seconds
2. Register or log in
3. Create a new battery
4. Trigger an AI assessment
5. View the Battery Aadhaar card
6. Review deployment recommendation
7. Explore the Impact Dashboard
8. Navigate every screen in the app

If any step in this flow is broken, the implementation is incomplete.

---

## Output Format

When implementation is complete, provide:

| # | Section | Details |
|---|---|---|
| 1 | Readiness report | Summary of findings |
| 2 | Backend gap report | Every added route/service |
| 3 | Files created | Path + purpose |
| 4 | Files modified | Path + what changed |
| 5 | APIs connected | Endpoint + screen |
| 6 | APIs created | Endpoint + purpose |
| 7 | WebSocket integrations | Event + screen |
| 8 | Landing page features | Feature + status |
| 9 | 3D features | Scene + status |
| 10 | Remaining risks | Issue + recommended fix |

Then stop and wait for validation before proceeding.
