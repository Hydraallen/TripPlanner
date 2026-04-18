import React, { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, Typography, Spin, Alert, Button, Space } from "antd";
import { CheckCircleOutlined } from "@ant-design/icons";
import TripForm from "../components/TripForm";
import type { TripFormValues } from "../components/TripForm";
import {
  generatePlan,
  generateLLMPlan,
  createTrip,
  type TripPlan,
} from "../api/client";

const { Title, Text } = Typography;

type PlanResult = TripPlan & { error?: string };

const PlanPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<TripPlan | null>(null);
  const [tripId, setTripId] = useState<string | null>(null);

  const handleSubmit = async (values: TripFormValues) => {
    setLoading(true);
    setError(null);
    setPlan(null);
    setTripId(null);

    const params = {
      city: values.city,
      start_date: values.startDate.format("YYYY-MM-DD"),
      end_date: values.endDate.format("YYYY-MM-DD"),
      interests: values.interests,
      transport_mode: values.transportMode,
      ...(values.preferences ? { preferences: values.preferences } : {}),
    };

    try {
      const result = values.useLLM
        ? await generateLLMPlan(params) as PlanResult
        : await generatePlan(params) as PlanResult;

      if (result.error) {
        setError(result.error as string);
        return;
      }

      setPlan(result);

      const { id } = await createTrip({
        city: params.city,
        start_date: params.start_date,
        end_date: params.end_date,
        interests: params.interests,
        transport_mode: params.transport_mode,
      });
      setTripId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: "0 auto" }}>
      <Title level={2}>Plan a Trip</Title>

      {loading && (
        <Card style={{ textAlign: "center", padding: 40, marginBottom: 24 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">Generating your travel plan...</Text>
          </div>
        </Card>
      )}

      {error && (
        <Alert
          type="error"
          message="Generation Failed"
          description={error}
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 24 }}
        />
      )}

      {plan && !loading && (
        <Card style={{ marginBottom: 24 }}>
          <Space direction="vertical" size="small" style={{ width: "100%" }}>
            <Title level={4}>
              <CheckCircleOutlined style={{ color: "#52c41a" }} />{" "}
              {plan.city} Trip Plan
            </Title>
            <Text>
              {plan.start_date} — {plan.end_date} &middot; {plan.days.length} days
              &middot; {plan.source === "llm" ? "AI-Generated" : "Algorithmic"}
            </Text>
            {plan.budget && (
              <Text strong>
                Estimated budget: {plan.budget.total.toFixed(0)}
              </Text>
            )}
            <Space>
              {tripId && (
                <Button type="primary" onClick={() => navigate(`/trips/${tripId}`)}>
                  View Full Itinerary
                </Button>
              )}
              <Button onClick={() => setPlan(null)}>Plan Another</Button>
            </Space>
          </Space>
        </Card>
      )}

      {!plan && !loading && (
        <Card>
          <TripForm
            onSubmit={handleSubmit}
            loading={loading}
            initialValues={{
              city: searchParams.get("city") || undefined,
            }}
          />
        </Card>
      )}
    </div>
  );
};

export default PlanPage;
