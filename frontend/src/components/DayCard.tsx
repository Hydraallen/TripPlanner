import React from "react";
import { Card, List, Tag, Typography, Badge } from "antd";
import {
  CloudOutlined,
  ClockCircleOutlined,
  CarOutlined,
} from "@ant-design/icons";
import type { DayPlan, WeatherInfo } from "../api/client";

const { Text } = Typography;

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
      }}
      title={
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Badge color={color} />
          <span>Day {day.day_number} — {day.date}</span>
          {weather && (
            <Tag icon={<CloudOutlined />} style={{ marginLeft: "auto" }}>
              {weather.temp_low.toFixed(0)}–{weather.temp_high.toFixed(0)}°C
            </Tag>
          )}
          <Tag>{day.transportation}</Tag>
        </div>
      }
    >
      {day.attractions.length > 0 && (
        <List
          size="small"
          dataSource={day.attractions}
          renderItem={(a, idx) => (
            <List.Item
              style={{ cursor: onAttractionClick ? "pointer" : undefined }}
              onClick={() => onAttractionClick?.(a.xid)}
            >
              <List.Item.Meta
                title={
                  <span>
                    {a.name}
                    {a.time_slot && (
                      <Tag
                        icon={<ClockCircleOutlined />}
                        color="blue"
                        style={{ marginLeft: 8 }}
                      >
                        {a.time_slot}
                      </Tag>
                    )}
                    {a.rating && (
                      <Tag color="gold" style={{ marginLeft: 4 }}>
                        {a.rating.toFixed(1)}
                      </Tag>
                    )}
                  </span>
                }
                description={
                  <span>
                    {a.commute_minutes > 0 && idx > 0 && (
                      <Tag
                        icon={<CarOutlined />}
                        color="default"
                        style={{ marginRight: 8 }}
                      >
                        {a.commute_minutes} min
                      </Tag>
                    )}
                    {a.address || a.kinds}
                    <Text type="secondary"> ({a.visit_duration} min)</Text>
                  </span>
                }
              />
            </List.Item>
          )}
        />
      )}
      {day.meals.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <List
            size="small"
            dataSource={day.meals}
            renderItem={(m) => (
              <List.Item>
                <Text>
                  <Tag color={MEAL_COLORS[m.type] || "default"}>
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

export default DayCard;
