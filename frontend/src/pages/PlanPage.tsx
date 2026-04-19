import React, { useState, useRef, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, Typography, Spin, Alert, Button, Space, Progress } from "antd";
import { CheckCircleOutlined, RocketOutlined } from "@ant-design/icons";
import TripForm from "../components/TripForm";
import type { TripFormValues } from "../components/TripForm";
import PlanComparison from "../components/PlanComparison";
import ChatPanel from "../components/ChatPanel";
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
  const [chatOpen, setChatOpen] = useState(false);
  const [plansContext, setPlansContext] = useState<string | null>(null);
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

    const params: Parameters<typeof generateMultiPlan>[0] = {
      city: values.city,
      start_date: values.startDate.format("YYYY-MM-DD"),
      end_date: values.endDate.format("YYYY-MM-DD"),
    };
    if (values.interests && values.interests.length > 0) {
      params.interests = values.interests;
    }
    if (values.transportMode) {
      params.transport_mode = values.transportMode;
    }

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

  const handleCompareWithAI = () => {
    const summary = alternatives
      .map((alt) => {
        const scoreStr = alt.scores
          ? `Score: ${Math.round((alt.scores.total ?? 0) * 100)} (Price:${Math.round((alt.scores.price ?? 0) * 100)} Rating:${Math.round((alt.scores.rating ?? 0) * 100)} Convenience:${Math.round((alt.scores.convenience ?? 0) * 100)} Diversity:${Math.round((alt.scores.diversity ?? 0) * 100)} Safety:${Math.round((alt.scores.safety ?? 0) * 100)} Popularity:${Math.round((alt.scores.popularity ?? 0) * 100)})`
          : "No scores";
        return `- ${alt.title} (${alt.focus}): ${alt.description || "No description"}. Cost: ¥${alt.estimated_cost}. ${scoreStr}`;
      })
      .join("\n");
    setPlansContext(`I'm comparing these travel plans:\n${summary}\n\nPlease help me compare them and recommend the best one.`);
    setChatOpen(true);
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
        <Card
          className="anim-fade-in"
          style={{
            textAlign: "center",
            padding: 40,
            marginBottom: 24,
            borderRadius: 12,
            boxShadow: "var(--shadow-md)",
          }}
        >
          <Spin size="large" indicator={<RocketOutlined style={{ fontSize: 36 }} />} />
          <div style={{ marginTop: 16, marginBottom: 12 }}>
            <Text type="secondary" style={{ fontSize: 16 }}>
              {progress?.step || "Starting generation..."}
            </Text>
          </div>
          <div style={{ maxWidth: 400, margin: "0 auto" }}>
            <Progress
              percent={progressPercent}
              status={isFailed ? "exception" : "active"}
              strokeColor={{
                "0%": "#1677ff",
                "50%": "#52c41a",
                "100%": "#faad14",
              }}
              style={{ marginBottom: 8 }}
            />
            {isCompleted && (
              <CheckCircleOutlined
                style={{
                  fontSize: 24,
                  color: "#52c41a",
                  animation: "bounceIn 0.5s ease both",
                }}
              />
            )}
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
          style={{ marginBottom: 24, borderRadius: 8 }}
        />
      )}

      {/* Plan Comparison */}
      {alternatives.length > 0 && (
        <div style={{ marginBottom: 24 }} className="anim-fade-in">
          <Title level={3}>
            <CheckCircleOutlined style={{ color: "#52c41a" }} /> Choose Your Plan
          </Title>
          <PlanComparison
            alternatives={alternatives}
            selectedId={selectedPlanId ?? undefined}
            onSelect={handleSelectPlan}
            loading={selecting}
            onCompareWithAI={handleCompareWithAI}
          />
          {selectedPlanId && (
            <Card
              className="anim-bounce-in"
              style={{
                marginTop: 16,
                textAlign: "center",
                borderRadius: 12,
                boxShadow: "var(--shadow-md)",
              }}
            >
              <Space>
                <Button
                  type="primary"
                  size="large"
                  onClick={handleViewTrip}
                  style={{
                    borderRadius: 8,
                    background: "linear-gradient(135deg, #1677ff 0%, #722ed1 100%)",
                    border: "none",
                  }}
                >
                  View Full Itinerary
                </Button>
                <Button onClick={handleReset} style={{ borderRadius: 8 }}>
                  Plan Another Trip
                </Button>
              </Space>
            </Card>
          )}
        </div>
      )}

      {/* Form (show when not generating and no results) */}
      {!loading && alternatives.length === 0 && (
        <Card
          className="card-elevated anim-slide-up"
          style={{ borderRadius: 12 }}
        >
          <TripForm
            onSubmit={handleSubmit}
            loading={loading}
            initialValues={{
              city: searchParams.get("city") || undefined,
            }}
          />
        </Card>
      )}

      <ChatPanel
        externalOpen={chatOpen}
        onOpenChange={setChatOpen}
        planContext={plansContext}
      />
    </div>
  );
};

export default PlanPage;
