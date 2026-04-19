import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import type { DayPlan, Attraction } from "../api/client";

import "leaflet/dist/leaflet.css";

const DAY_COLORS = [
  "#1677ff", "#52c41a", "#faad14", "#ff4d4f", "#722ed1",
  "#13c2c2", "#eb2f96", "#fa8c16", "#2f54eb", "#a0d911",
];

function createDayIcon(color: string) {
  return L.divIcon({
    html: `<svg viewBox="0 0 24 36" width="24" height="36"><path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24C24 5.4 18.6 0 12 0z" fill="${color}"/><circle cx="12" cy="12" r="5" fill="white"/></svg>`,
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36],
    className: "",
  });
}

interface Props {
  days: DayPlan[];
  selectedAttraction?: string | null;
  onAttractionClick?: (xid: string) => void;
}

function FitBounds({ days }: { days: DayPlan[] }) {
  const map = useMap();
  const prevLengthRef = useRef(0);

  useEffect(() => {
    const points: L.LatLngTuple[] = [];
    days.forEach((day) => {
      day.attractions.forEach((a) => {
        if (a.location.latitude && a.location.longitude) {
          points.push([a.location.latitude, a.location.longitude]);
        }
      });
    });

    if (points.length > 0 && points.length !== prevLengthRef.current) {
      prevLengthRef.current = points.length;
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [days, map]);

  return null;
}

const MapView: React.FC<Props> = ({ days, onAttractionClick }) => {
  const allAttractions = days.flatMap((day) =>
    day.attractions.map((a) => ({ ...a, dayNumber: day.day_number }))
  );

  if (allAttractions.length === 0) {
    return (
      <div
        className="map-fade-in"
        style={{
          height: 400,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#f5f5f5",
          borderRadius: 10,
        }}
      >
        <span style={{ color: "#999" }}>No attractions to display on map</span>
      </div>
    );
  }

  return (
    <div className="map-fade-in" style={{ borderRadius: 10, overflow: "hidden", boxShadow: "var(--shadow-sm)" }}>
      <MapContainer
        center={[35, 135]}
        zoom={5}
        style={{ height: 500, width: "100%" }}
        scrollWheelZoom
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds days={days} />

        {days.map((day) => {
          const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];
          const positions: L.LatLngTuple[] = day.attractions
            .filter((a) => a.location.latitude && a.location.longitude)
            .map((a) => [a.location.latitude, a.location.longitude]);

          return (
            <React.Fragment key={day.day_number}>
              {day.attractions.map((a: Attraction) => (
                <Marker
                  key={a.xid}
                  position={[a.location.latitude, a.location.longitude]}
                  icon={createDayIcon(color)}
                  eventHandlers={{
                    click: () => onAttractionClick?.(a.xid),
                  }}
                >
                  <Popup>
                    <div>
                      <strong>{a.name}</strong>
                      {a.rating && <span> ({a.rating.toFixed(1)}/5)</span>}
                      <br />
                      <span style={{ color }}>Day {day.day_number}</span>
                      {a.address && <><br /><small>{a.address}</small></>}
                    </div>
                  </Popup>
                </Marker>
              ))}
              {positions.length > 1 && (
                <Polyline
                  positions={positions}
                  pathOptions={{ color, weight: 3, opacity: 0.7 }}
                />
              )}
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default MapView;
