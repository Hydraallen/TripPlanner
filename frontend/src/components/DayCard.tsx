import React, { useState } from "react";
import { Card, List, Tag, Typography, Badge, Popover } from "antd";
import {
  CloudOutlined,
  ClockCircleOutlined,
  CarOutlined,
  LinkOutlined,
  EnvironmentOutlined,
} from "@ant-design/icons";
import type { DayPlan, WeatherInfo, Attraction } from "../api/client";
import { googleMapsSearchUrl, googleMapsDirectionsUrl, extractWikipediaUrl } from "../utils/maps";
import { fetchAllModes, type RouteInfo } from "../utils/routing";

const { Text, Link } = Typography;

const DAY_COLORS = [
  "#1677ff", "#52c41a", "#faad14", "#ff4d4f", "#722ed1",
  "#13c2c2", "#eb2f96", "#fa8c16", "#2f54eb", "#a0d911",
];

const MEAL_COLORS: Record<string, string> = {
  breakfast: "#faad14",
  lunch: "#52c41a",
  dinner: "#1677ff",
  snack: "#722ed1",
};

const MODE_LABELS: Record<string, { icon: string; label: string }> = {
  foot: { icon: "\ud83d\udeb6", label: "Walking" },
  car: { icon: "\ud83d\ude97", label: "Driving" },
  bike: { icon: "\ud83d\udeb2", label: "Cycling" },
};

interface Props {
  day: DayPlan;
  weather?: WeatherInfo | null;
  selected?: boolean;
  onAttractionClick?: (xid: string) => void;
}

const DayCard: React.FC<Props> = ({ day, weather, selected, onAttractionClick }) => {
  const color = DAY_COLORS[(day.day_number - 1) % DAY_COLORS.length];

  return (
    <Card
      size="small"
      style={{
        marginBottom: 12,
        borderLeft: `4px solid ${color}`,
        background: selected ? "#f0f5ff" : undefined,
        borderRadius: 10,
        boxShadow: "var(--shadow-sm)",
      }}
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Badge color={color} />
          <span style={{ fontWeight: 600 }}>Day {day.day_number} — {day.date}</span>
          {weather && (
            <Tag icon={<CloudOutlined />} style={{ marginLeft: "auto", borderRadius: 6 }}>
              {weather.temp_low.toFixed(0)}–{weather.temp_high.toFixed(0)}°C
            </Tag>
          )}
          <Tag style={{ borderRadius: 6 }}>{day.transportation}</Tag>
        </div>
      }
    >
      {day.attractions.length > 0 && (
        <List
          size="small"
          dataSource={day.attractions}
          renderItem={(a, idx) => (
            <AttractionRow
              attraction={a}
              prevAttraction={idx > 0 ? day.attractions[idx - 1] : undefined}
              index={idx}
              onAttractionClick={onAttractionClick}
            />
          )}
        />
      )}
      {day.meals.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <List
            size="small"
            dataSource={day.meals}
            renderItem={(m, idx) => (
              <List.Item
                className="anim-slide-in-left"
                style={{ animationDelay: `${idx * 60}ms`, borderRadius: 6, padding: "6px 12px" }}
              >
                <Text>
                  <Tag color={MEAL_COLORS[m.type] || "default"} style={{ borderRadius: 6 }}>
                    {m.type}
                  </Tag>
                  {m.time_slot && (
                    <Text type="secondary" style={{ marginRight: 8 }}>
                      {m.time_slot}
                    </Text>
                  )}
                  {m.name} (~{m.estimated_cost.toFixed(0)})
                </Text>
              </List.Item>
            )}
          />
        </div>
      )}
    </Card>
  );
};

interface AttractionRowProps {
  attraction: Attraction;
  prevAttraction?: Attraction;
  index: number;
  onAttractionClick?: (xid: string) => void;
}

const AttractionRow: React.FC<AttractionRowProps> = ({
  attraction: a,
  prevAttraction,
  index,
  onAttractionClick,
}) => {
  const [routeInfo, setRouteInfo] = useState<RouteInfo[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [popoverOpen, setPopoverOpen] = useState(false);

  const mapsUrl = googleMapsSearchUrl(a.name, a.location.latitude, a.location.longitude);
  const wikiUrl = extractWikipediaUrl(a.description ?? null);

  const handlePopoverOpen = (open: boolean) => {
    setPopoverOpen(open);
    if (open && !routeInfo && !loading && prevAttraction) {
      setLoading(true);
      fetchAllModes(prevAttraction.location, a.location).then((info) => {
        setRouteInfo(info);
        setLoading(false);
      });
    }
  };

  const directionsUrl = prevAttraction
    ? googleMapsDirectionsUrl(prevAttraction.location, a.location)
    : null;

  const commuteTag = a.commute_minutes > 0 && index > 0 && prevAttraction ? (
    <Popover
      trigger="hover"
      open={popoverOpen}
      onOpenChange={handlePopoverOpen}
      placement="topLeft"
      content={
        <div style={{ minWidth: 180 }}>
          <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 13 }}>Transport Options</div>
          {loading ? (
            <Text type="secondary">Loading...</Text>
          ) : routeInfo ? (
            <>
              {routeInfo.map((r) => (
                <div key={r.mode} style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span>{MODE_LABELS[r.mode]?.icon} {MODE_LABELS[r.mode]?.label}</span>
                  <Text strong>{r.durationMinutes} min</Text>
                </div>
              ))}
              {directionsUrl && (
                <div style={{ marginTop: 8, borderTop: "1px solid #f0f0f0", paddingTop: 8 }}>
                  <Link href={directionsUrl} target="_blank" style={{ fontSize: 12 }}>
                    <EnvironmentOutlined /> Open in Google Maps
                  </Link>
                </div>
              )}
            </>
          ) : (
            <Text type="secondary">Failed to load</Text>
          )}
        </div>
      }
    >
      <Tag
        icon={<CarOutlined />}
        color="default"
        style={{ marginRight: 8, borderRadius: 6, cursor: "pointer" }}
      >
        {a.commute_minutes} min
      </Tag>
    </Popover>
  ) : null;

  return (
    <List.Item
      className="anim-slide-in-left"
      style={{
        animationDelay: `${index * 60}ms`,
        borderRadius: 6,
        padding: "8px 12px",
      }}
    >
      <List.Item.Meta
        title={
          <span>
            <Link
              href={mapsUrl}
              target="_blank"
              onClick={(e) => {
                e.stopPropagation();
                onAttractionClick?.(a.xid);
              }}
              style={{ fontSize: 14, fontWeight: 500 }}
            >
              {a.name}
            </Link>
            <Link
              href={mapsUrl}
              target="_blank"
              style={{ marginLeft: 6, fontSize: 12 }}
              onClick={(e) => e.stopPropagation()}
            >
              <LinkOutlined />
            </Link>
            {wikiUrl && (
              <Link
                href={wikiUrl}
                target="_blank"
                style={{ marginLeft: 4, fontSize: 12, color: "#6b7280" }}
                onClick={(e) => e.stopPropagation()}
              >
                W
              </Link>
            )}
            {a.time_slot && (
              <Tag
                icon={<ClockCircleOutlined />}
                color="blue"
                style={{ marginLeft: 8, borderRadius: 6 }}
              >
                {a.time_slot}
              </Tag>
            )}
            {a.rating && (
              <Tag color="gold" style={{ marginLeft: 4, borderRadius: 6 }}>
                {a.rating.toFixed(1)}
              </Tag>
            )}
          </span>
        }
        description={
          <span>
            {commuteTag}
            {a.address || a.kinds}
            <Text type="secondary"> ({a.visit_duration} min)</Text>
          </span>
        }
      />
    </List.Item>
  );
};

export default DayCard;
