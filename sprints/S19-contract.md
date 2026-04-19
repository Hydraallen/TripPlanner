# Sprint S19: React Scaffolding + Core Pages

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S18
**Estimated complexity:** Medium

---

## Goal

Scaffold the React frontend with TypeScript, Vite, and Ant Design. Implement the three core pages (Home, Plan, Trip Detail), shared layout, trip form, and typed API client that proxies to the FastAPI backend.

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/package.json` | Create — React 19, TypeScript, Vite 8, Ant Design 5, React Router |
| `frontend/vite.config.ts` | Create — dev server with /api proxy to localhost:8000 |
| `frontend/tsconfig.json` | Create — strict TypeScript config |
| `frontend/src/main.tsx` | Create — app entry with router provider |
| `frontend/src/pages/HomePage.tsx` | Create — landing page with TripForm |
| `frontend/src/pages/PlanPage.tsx` | Create — plan generation with SSE progress display |
| `frontend/src/pages/TripDetailPage.tsx` | Create — selected plan view with map and itinerary |
| `frontend/src/components/Layout.tsx` | Create — shared layout with navigation |
| `frontend/src/components/TripForm.tsx` | Create — trip input form (city, dates, interests, budget) |
| `frontend/src/api/client.ts` | Create — typed API client for all backend endpoints |

## Done Criteria

- [x] `npm install && npm run dev` starts Vite dev server with hot reload
- [x] Vite proxies `/api/*` requests to `localhost:8000`
- [x] HomePage renders TripForm with city, dates, interests, and budget fields
- [x] PlanPage shows real-time progress during plan generation via SSE
- [x] TripDetailPage displays selected plan details
- [x] Layout provides consistent navigation across pages
- [x] API client has typed interfaces for all backend endpoints
- [x] TypeScript strict mode enabled with no compilation errors

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Dev server | `npm run dev` starts without errors | Build or runtime errors |
| Routing | All three pages navigable via React Router | Missing routes or 404s |
| API proxy | Frontend requests to /api/* reach backend | CORS or proxy failures |
| Type safety | `tsc --noEmit` passes with strict mode | Type errors present |
