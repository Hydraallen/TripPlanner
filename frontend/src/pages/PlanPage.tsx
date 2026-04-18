import React, { useState, useRef, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, Typography, Spin, Alert, Button, Space, Progress } from "antd";
import { CheckCircleOutlined, RocketOutlined } from "@ant-design/icons";
import TripForm from "../components/TripForm";
import type { TripFormValues } from "../components/TripForm";
import PlanComparison from "../components/PlanComparison";
import {
  generateMultiPlan,
  getPlanAlternatives,
  selectPlan,
  createProgressSSE,
  type PlanAlternative,
  type GenerationProgress,
} from "../api/client";

const { Title, Text } = Typography;

const PlanPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tripId, setTripId] = useState<string | null>(null);
  const [progress, setProgress] = useState<GenerationProgress | null>(null);
  const [alternatives, setAlternatives] = useState<PlanAlternative[]>([]);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [selecting, setSelecting] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const handleProgress = useCallback((prog: GenerationProgress) => {
    setProgress(prog);
    if (prog.status === "completed") {
      // Fetch alternatives once complete
      setTimeout(() => {
        if (prog.plan_id) {
          getPlanAlternatives(prog.plan_id).then(setAlternatives).catch(() => {});
        }
      }, 500);
    }
  }, []);

  const handleSubmit = async (values: TripFormValues) => {
    setLoading(true);
    setError(null);
    setTripId(null);
    setProgress(null);
    setAlternatives([]);
    setSelectedPlanId(null);

    if (esRef.current) {
      esRef.current.close();
    }

    const params = {
      city: values.city,
      start_date: values.startDate.format("YYYY-MM-DD"),
      end_date: values.endDate.format("YYYY-MM-DD"),
      interests: values.interests,
      transport_mode: values.transportMode,
    };

    try {
      const { trip_id } = await generateMultiPlan(params);
      setTripId(trip_id);

      // Start SSE progress tracking
      const es = createProgressSSE(trip_id, handleProgress, () => {
        // SSE error - try polling as fallback
      });
      esRef.current = es;

      // Also poll for alternatives in case SSE misses
      const poll = setInterval(async () => {
        try {
          const alts = await getPlanAlternatives(trip_id);
          if (alts.length > 0) {
            setAlternatives(alts);
            clearInterval(poll);
            setLoading(false);
          }
        } catch {
          // keep polling
        }
      }, 3000);

      // Stop polling after 2 minutes
      setTimeout(() => clearInterval(poll), 120000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan generation failed");
      setLoading(false);
    }
  };

  const handleSelectPlan = async (planId: string) => {
    if (!tripId) return;
    setSelecting(true);
    try {
      await selectPlan(tripId, planId);
      setSelectedPlanId(planId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to select plan");
    } finally {
      setSelecting(false);
    }
  };

  const handleViewTrip = () => {
    if (tripId) {
      navigate(`/trips/${tripId}`);
    }
  };

  const handleReset = () => {
    setTripId(null);
    setProgress(null);
    setAlternatives([]);
    setSelectedPlanId(null);
    setError(null);
    setLoading(false);
    if (esRef.current) {
      esRef.current.close();
    }
  };

  const progressPercent = progress ? Math.round(progress.progress) : 0;
  const isCompleted = progress?.status === "completed";
  const isFailed = progress?.status === "failed";

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <Title level={2}>Plan a Trip</Title>

      {/* Generation Progress */}
      {loading && !isCompleted && (
        <Card style={{ textAlign: "center", padding: 40, marginBottom: 24 }}>
          <Spin size="large" indicator={<RocketOutlined style={{ fontSize: 36 }} />} />
          <div style={{ marginTop: 16, marginBottom: 12 }}>
            <Text type="secondary" style={{ fontSize: 16 }}>
              {progress?.step || "Starting generation..."}
            </Text>
          </div>
          <Progress
            percent={progressPercent}
            status={isFailed ? "exception" : "active"}
            style={{ maxWidth: 400, margin: "0 auto" }}
          />
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

      {/* Plan Comparison */}
      {alternatives.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <Title level={3}>
            <CheckCircleOutlined style={{ color: "#52c41a" }} /> Choose Your Plan
          </Title>
          <PlanComparison
            alternatives={alternatives}
            selectedId={selectedPlanId ?? undefined}
            onSelect={handleSelectPlan}
            loading={selecting}
          />
          {selectedPlanId && (
            <Card style={{ marginTop: 16, textAlign: "center" }}>
              <Space>
                <Button type="primary" size="large" onClick={handleViewTrip}>
                  View Full Itinerary
                </Button>
                <Button onClick={handleReset}>Plan Another Trip</Button>
              </Space>
            </Card>
          )}
        </div>
      )}

      {/* Form (show when not generating and no results) */}
      {!loading && alternatives.length === 0 && (
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
