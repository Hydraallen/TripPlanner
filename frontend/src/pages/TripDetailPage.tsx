import React, { Component, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Typography,
  Button,
  Space,
  Spin,
  message,
  Row,
  Col,
  Alert,
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

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class TripErrorBoundary extends Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <Alert
          type="error"
          message="Something went wrong displaying this trip"
          description={this.state.error?.message}
          showIcon
          style={{ margin: 24 }}
          action={
            <Button onClick={() => window.location.reload()}>
              Reload
            </Button>
          }
        />
      );
    }
    return this.props.children;
  }
}

const TripDetailPage: React.FC<Props> = ({ onPlanContextChange }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAttraction, setSelectedAttraction] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    getTrip(id)
      .then((t) => {
        setTrip(t);
        if (t?.plan) {
          const ctx = `Trip to ${t.plan.city}, ${t.plan.start_date} to ${t.plan.end_date}, ${t.plan.days.length} days`;
          onPlanContextChange?.(ctx);
        }
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load trip");
      })
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

  if (error) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <Alert type="error" message={error} style={{ marginBottom: 16 }} />
        <Button onClick={() => navigate("/trips")}>Back to Trips</Button>
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
    <TripErrorBoundary>
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
    </TripErrorBoundary>
  );
};

export default TripDetailPage;
