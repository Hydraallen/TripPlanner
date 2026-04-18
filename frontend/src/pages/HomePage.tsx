import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Typography, Button, Card, List, Space, Input, DatePicker } from "antd";
import { RocketOutlined, CompassOutlined } from "@ant-design/icons";
import type { Dayjs } from "dayjs";
import { listTrips, type TripSummary } from "../api/client";

const { Title, Paragraph } = Typography;
const { RangePicker } = DatePicker;

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
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <div style={{ textAlign: "center", padding: "48px 0 32px" }}>
        <Title level={1}>
          <CompassOutlined /> TripPlanner
        </Title>
        <Paragraph type="secondary" style={{ fontSize: 18 }}>
          Generate personalized travel itineraries with AI-powered planning
        </Paragraph>
      </div>

      <Card style={{ marginBottom: 32 }}>
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Input
            size="large"
            placeholder="Where do you want to go?"
            prefix={<CompassOutlined />}
            value={city}
            onChange={(e) => setCity(e.target.value)}
            onPressEnter={handleQuickPlan}
          />
          <RangePicker
            size="large"
            style={{ width: "100%" }}
            onChange={(vals) => setDates(vals as [Dayjs, Dayjs] | null)}
          />
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={handleQuickPlan}
            disabled={!city}
            block
          >
            Plan My Trip
          </Button>
        </Space>
      </Card>

      {recentTrips.length > 0 && (
        <>
          <Title level={4}>Recent Trips</Title>
          <List
            dataSource={recentTrips}
            renderItem={(trip) => (
              <List.Item
                style={{ cursor: "pointer" }}
                onClick={() => navigate(`/trips/${trip.id}`)}
              >
                <List.Item.Meta
                  title={trip.city}
                  description={`${trip.start_date} — ${trip.end_date}`}
                />
              </List.Item>
            )}
          />
        </>
      )}
    </div>
  );
};

export default HomePage;
