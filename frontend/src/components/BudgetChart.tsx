import React from "react";
import { Card, Empty, Typography, Space } from "antd";
import type { Budget } from "../api/client";

const { Title, Text } = Typography;

interface Props {
  budget: Budget | null;
}

const BudgetChart: React.FC<Props> = ({ budget }) => {
  if (!budget || budget.total === 0) {
    return (
      <Card size="small" style={{ borderRadius: 10 }}>
        <Empty description="No budget data" />
      </Card>
    );
  }

  const items = [
    { label: "Attractions", value: budget.total_attractions, color: "#1677ff" },
    { label: "Meals", value: budget.total_meals, color: "#52c41a" },
    { label: "Hotels", value: budget.total_hotels, color: "#faad14" },
    { label: "Transport", value: budget.total_transportation, color: "#ff4d4f" },
  ];

  return (
    <Card
      size="small"
      title={<span style={{ fontWeight: 600 }}>Budget Breakdown</span>}
      style={{ borderRadius: 10, boxShadow: "var(--shadow-sm)" }}
    >
      <Space direction="vertical" style={{ width: "100%" }}>
        {items.map((item) => (
          <div key={item.label}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <Text style={{ fontSize: 13 }}>{item.label}</Text>
              <Text strong style={{ fontSize: 13 }}>{item.value.toFixed(0)}</Text>
            </div>
            <div
              style={{
                height: 8,
                borderRadius: 4,
                background: "#f0f0f0",
                overflow: "hidden",
              }}
            >
              <div
                className="score-bar-fill"
                style={{
                  height: "100%",
                  borderRadius: 4,
                  background: item.color,
                  width: `${budget.total > 0 ? (item.value / budget.total) * 100 : 0}%`,
                  transition: "width 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
                }}
              />
            </div>
          </div>
        ))}
        <Title level={5} style={{ marginTop: 8, textAlign: "right" }}>
          Total: {budget.total.toFixed(0)}
        </Title>
      </Space>
    </Card>
  );
};

export default BudgetChart;
