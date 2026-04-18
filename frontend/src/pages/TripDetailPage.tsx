import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Typography,
  Card,
  List,
  Tag,
  Button,
  Space,
  Spin,
  Descriptions,
  message,
} from "antd";
import {
  DownloadOutlined,
  ArrowLeftOutlined,
  EnvironmentOutlined,
} from "@ant-design/icons";
import {
  getTrip,
  exportTrip,
  type Trip,
  type DayPlan,
} from "../api/client";

const { Title, Text } = Typography;

const TripDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getTrip(id)
      .then(setTrip)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  const handleExport = async (format: "markdown" | "json" | "html") => {
    if (!id) return;
    try {
      const content = await exportTrip(id, format);
      const blob = new Blob([content], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${trip?.city || "trip"}-plan.${format === "markdown" ? "md" : format}`;
      a.click();
      URL.revokeObjectURL(url);
      message.success(`Exported as ${format}`);
    } catch {
      // handled by interceptor
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!trip || !trip.plan) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <Title level={4}>Trip not found</Title>
        <Button onClick={() => navigate("/trips")}>Back to Trips</Button>
      </div>
    );
  }

  const plan = trip.plan;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate("/trips")}
        style={{ marginBottom: 16 }}
      >
        Back
      </Button>

      <Title level={2}>
        <EnvironmentOutlined /> {plan.city} Trip
      </Title>
      <Text type="secondary">
        {plan.start_date} — {plan.end_date} &middot; {plan.days.length} days
      </Text>

      {plan.budget && (
        <Card size="small" style={{ margin: "16px 0" }}>
          <Descriptions title="Budget Overview" size="small" column={4}>
            <Descriptions.Item label="Attractions">
              {plan.budget.total_attractions.toFixed(0)}
            </Descriptions.Item>
            <Descriptions.Item label="Meals">
              {plan.budget.total_meals.toFixed(0)}
            </Descriptions.Item>
            <Descriptions.Item label="Hotels">
              {plan.budget.total_hotels.toFixed(0)}
            </Descriptions.Item>
            <Descriptions.Item label="Transport">
              {plan.budget.total_transportation.toFixed(0)}
            </Descriptions.Item>
          </Descriptions>
          <Title level={5} style={{ marginTop: 8 }}>
            Total: {plan.budget.total.toFixed(0)}
          </Title>
        </Card>
      )}

      <Space style={{ marginBottom: 16 }}>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport("markdown")}>
          Markdown
        </Button>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport("json")}>
          JSON
        </Button>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport("html")}>
          HTML
        </Button>
      </Space>

      {plan.days.map((day: DayPlan) => (
        <Card
          key={day.day_number}
          title={`Day ${day.day_number} — ${day.date}`}
          size="small"
          style={{ marginBottom: 12 }}
          extra={<Tag>{day.transportation}</Tag>}
        >
          {day.attractions.length > 0 && (
            <List
              size="small"
              dataSource={day.attractions}
              renderItem={(a) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <span>
                        {a.name}
                        {a.rating && (
                          <Tag color="blue" style={{ marginLeft: 8 }}>
                            {a.rating.toFixed(1)}
                          </Tag>
                        )}
                      </span>
                    }
                    description={a.address || a.kinds}
                  />
                </List.Item>
              )}
            />
          )}
          {day.meals.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">Meals:</Text>
              <List
                size="small"
                dataSource={day.meals}
                renderItem={(m) => (
                  <List.Item>
                    <Text>
                      {m.type}: {m.name} (~{m.estimated_cost.toFixed(0)})
                    </Text>
                  </List.Item>
                )}
              />
            </div>
          )}
        </Card>
      ))}
    </div>
  );
};

export default TripDetailPage;
