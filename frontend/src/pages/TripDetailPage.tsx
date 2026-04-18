import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Typography,
  Button,
  Space,
  Spin,
  message,
  Row,
  Col,
} from "antd";
import {
  DownloadOutlined,
  ArrowLeftOutlined,
  EnvironmentOutlined,
} from "@ant-design/icons";
import { getTrip, exportTrip, type Trip, type DayPlan } from "../api/client";
import MapView from "../components/MapView";
import DayCard from "../components/DayCard";
import BudgetChart from "../components/BudgetChart";

const { Title, Text } = Typography;

interface Props {
  onPlanContextChange?: (ctx: string | null) => void;
}

const TripDetailPage: React.FC<Props> = ({ onPlanContextChange }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAttraction, setSelectedAttraction] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getTrip(id)
      .then((t) => {
        setTrip(t);
        if (t?.plan) {
          const ctx = `Trip to ${t.plan.city}, ${t.plan.start_date} to ${t.plan.end_date}, ${t.plan.days.length} days`;
          onPlanContextChange?.(ctx);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    return () => onPlanContextChange?.(null);
  }, [id, onPlanContextChange]);

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
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
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

      <Space style={{ margin: "16px 0" }}>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport("markdown")}>
          Markdown
        </Button>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport("json")}>
          JSON
        </Button>
        <Button icon={<DownloadOutlined />} onClick={() => handleExport("html")}>
          HTML
        </Button>
        <Button onClick={() => navigate(`/plan?city=${encodeURIComponent(plan.city)}`)}>
          Switch Plan
        </Button>
      </Space>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={14}>
          <div style={{ position: "sticky", top: 16 }}>
            <MapView
              days={plan.days}
              selectedAttraction={selectedAttraction}
              onAttractionClick={setSelectedAttraction}
            />
          </div>
        </Col>
        <Col xs={24} lg={10}>
          <div style={{ marginBottom: 16 }}>
            <BudgetChart budget={plan.budget} />
          </div>
          {plan.days.map((day: DayPlan) => {
            const weather = plan.weather?.find(
              (w) => w.date === day.date
            );
            return (
              <DayCard
                key={day.day_number}
                day={day}
                weather={weather || null}
                selected={day.attractions.some((a) => a.xid === selectedAttraction)}
                onAttractionClick={setSelectedAttraction}
              />
            );
          })}
        </Col>
      </Row>
    </div>
  );
};

export default TripDetailPage;
