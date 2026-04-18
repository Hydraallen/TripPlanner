import React from "react";
import { Card, Empty, Typography, Progress, Space } from "antd";
import type { Budget } from "../api/client";

const { Title, Text } = Typography;

interface Props {
  budget: Budget | null;
}

const BudgetChart: React.FC<Props> = ({ budget }) => {
  if (!budget || budget.total === 0) {
    return (
      <Card size="small">
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
    <Card size="small" title="Budget Breakdown">
      <Space direction="vertical" style={{ width: "100%" }}>
        {items.map((item) => (
          <div key={item.label}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <Text>{item.label}</Text>
              <Text strong>{item.value.toFixed(0)}</Text>
            </div>
            <Progress
              percent={budget.total > 0 ? (item.value / budget.total) * 100 : 0}
              strokeColor={item.color}
              showInfo={false}
              size="small"
            />
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
