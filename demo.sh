#!/bin/bash
# TripPlanner Demo Script
# Requires OPENTRIPMAP_API_KEY set in .env

set -e

echo "=== TripPlanner Demo ==="

echo ""
echo "1. Planning a 3-day Tokyo trip..."
tripplanner plan --city Tokyo --dates 2026-05-01 2026-05-03 --interests museums,food,shrines --export markdown --output /tmp/tokyo.md

echo ""
echo "2. Listing all trips..."
tripplanner list

echo ""
echo "3. Getting the trip ID from the saved trips..."
TRIP_ID=$(tripplanner list --format json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['id'])" 2>/dev/null || echo "")

if [ -z "$TRIP_ID" ]; then
    echo "No trip ID found. Skipping show/export/delete."
    exit 0
fi

echo ""
echo "4. Showing trip details..."
tripplanner show "$TRIP_ID"

echo ""
echo "5. Exporting to HTML..."
tripplanner export "$TRIP_ID" --format html --output /tmp/tokyo.html
echo "Exported to /tmp/tokyo.html"

echo ""
echo "6. Deleting the trip..."
tripplanner delete "$TRIP_ID" --force

echo ""
echo "7. Verifying deletion..."
tripplanner list

echo ""
echo "=== Demo Complete ==="
