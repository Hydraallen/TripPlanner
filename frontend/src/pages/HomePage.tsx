import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Typography, Button, Card, List, Space, Input, DatePicker, Row, Col } from "antd";
import {
  RocketOutlined,
  CompassOutlined,
  BulbOutlined,
  SwapOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import type { Dayjs } from "dayjs";
import { listTrips, type TripSummary } from "../api/client";

const { Title, Paragraph, Text } = Typography;
const { RangePicker } = DatePicker;

const FEATURES = [
  {
    icon: <BulbOutlined style={{ fontSize: 28, color: "#1677ff" }} />,
    title: "Smart Planning",
    description: "AI-powered itinerary generation with multiple travel styles",
  },
  {
    icon: <SwapOutlined style={{ fontSize: 28, color: "#722ed1" }} />,
    title: "Multi-Plan Comparison",
    description: "Compare budget, culture, nature, food, romantic, and adventure plans side by side",
  },
  {
    icon: <RobotOutlined style={{ fontSize: 28, color: "#52c41a" }} />,
    title: "AI Advisor",
    description: "Chat with an AI travel expert to refine your perfect trip",
  },
];

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [city, setCity] = useState("");
  const [dates, setDates] = useState<[Dayjs, Dayjs] | null>(null);
  const [recentTrips, setRecentTrips] = useState<TripSummary[]>([]);

  useEffect(() => {
    listTrips()
      .then((trips) => setRecentTrips(trips.slice(0, 5)))
      .catch(() => {});
  }, []);

  const handleQuickPlan = () => {
    const params = new URLSearchParams({ city });
    if (dates) {
      params.set("start", dates[0].format("YYYY-MM-DD"));
      params.set("end", dates[1].format("YYYY-MM-DD"));
    }
    navigate(`/plan?${params.toString()}`);
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      {/* Hero Section */}
      <div
        className="hero-section anim-fade-in"
        style={{ marginBottom: 40, textAlign: "center" }}
      >
        <Title level={1} style={{ color: "white", marginBottom: 8, fontSize: 42, position: "relative" }}>
          <CompassOutlined style={{ marginRight: 8 }} />
          TripPlanner
        </Title>
        <Paragraph
          style={{
            color: "rgba(255, 255, 255, 0.9)",
            fontSize: 20,
            marginBottom: 0,
            position: "relative",
          }}
        >
          Generate personalized travel itineraries with AI-powered planning
        </Paragraph>
      </div>

      {/* Quick Plan Card */}
      <Card
        className="card-elevated anim-slide-up"
        style={{ marginBottom: 40, borderRadius: 12 }}
      >
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Input
            size="large"
            placeholder="Where do you want to go?"
            prefix={<CompassOutlined />}
            value={city}
            onChange={(e) => setCity(e.target.value)}
            onPressEnter={handleQuickPlan}
            style={{ borderRadius: 8 }}
          />
          <RangePicker
            size="large"
            style={{ width: "100%", borderRadius: 8 }}
            onChange={(vals) => setDates(vals as [Dayjs, Dayjs] | null)}
          />
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={handleQuickPlan}
            disabled={!city}
            block
            style={{
              height: 48,
              fontSize: 16,
              borderRadius: 8,
              background: "linear-gradient(135deg, #1677ff 0%, #722ed1 100%)",
              border: "none",
            }}
          >
            Plan My Trip
          </Button>
        </Space>
      </Card>

      {/* Feature Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 40 }}>
        {FEATURES.map((feat, idx) => (
          <Col xs={24} md={8} key={feat.title}>
            <Card
              className={`feature-card anim-slide-up stagger-${idx + 1}`}
              style={{ textAlign: "center", height: "100%" }}
            >
              <div style={{ marginBottom: 12 }}>{feat.icon}</div>
              <Title level={5} style={{ marginBottom: 4 }}>{feat.title}</Title>
              <Text type="secondary" style={{ fontSize: 13 }}>{feat.description}</Text>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Recent Trips */}
      {recentTrips.length > 0 && (
        <div className="anim-slide-up stagger-3">
          <Title level={4}>Recent Trips</Title>
          <List
            dataSource={recentTrips}
            renderItem={(trip) => (
              <List.Item
                className="hover-lift"
                style={{
                  cursor: "pointer",
                  borderRadius: 8,
                  padding: "12px 16px",
                  marginBottom: 4,
                }}
                onClick={() => navigate(`/trips/${trip.id}`)}
              >
                <List.Item.Meta
                  title={trip.city}
                  description={`${trip.start_date} — ${trip.end_date}`}
                />
              </List.Item>
            )}
          />
        </div>
      )}
    </div>
  );
};

export default HomePage;
