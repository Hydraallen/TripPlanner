# Sprint S20: Map Visualization + Display

**Phase:** 5 (Full-Stack Web Application)
**Depends on:** S19
**Estimated complexity:** Medium

---

## Goal

Add interactive map visualization with Leaflet, day-by-day itinerary display, and budget breakdown chart. Implement route polylines between POIs and utilities for external map links.

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/src/components/MapView.tsx` | Create — Leaflet map with color-coded markers and route polylines |
| `frontend/src/components/DayCard.tsx` | Create — day-by-day itinerary card with POI details |
| `frontend/src/components/BudgetChart.tsx` | Create — budget breakdown chart (accommodation, food, transport, activities) |
| `frontend/src/utils/maps.ts` | Create — Google Maps link generators for POIs and routes |
| `frontend/src/utils/routing.ts` | Create — OSRM route comparison utilities |

## Done Criteria

- [x] MapView renders an interactive Leaflet map centered on the trip destination
- [x] POI markers are color-coded by category (e.g., museums vs restaurants)
- [x] Route polylines connect POIs within each day using OSRM data
- [x] DayCard displays each day's itinerary with POI names, descriptions, and time slots
- [x] BudgetChart renders a breakdown chart by spending category
- [x] Google Maps link generators produce correct deep-link URLs
- [x] Map components handle missing coordinates gracefully

## Evaluation Criteria

| Criterion | Pass | Fail |
|-----------|------|------|
| Map rendering | Leaflet map loads with all POI markers visible | Map blank or missing markers |
| Polylines | Route lines drawn between sequential POIs per day | No routes or incorrect paths |
| Day cards | All days displayed with complete POI information | Missing days or empty cards |
| Budget chart | Chart renders with correct category breakdown | Chart missing or incorrect data |
