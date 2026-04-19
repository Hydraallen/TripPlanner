import React from "react";
import { Card, Tag, Button, Space, Typography } from "antd";
import {
  DollarOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  AppstoreOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  FireOutlined,
} from "@ant-design/icons";
import type { PlanAlternative, PlanScores } from "../api/client";

const { Text, Paragraph } = Typography;

const FOCUS_CONFIG: Record<
  string,
  { color: string; hex: string; label: string; emoji: string; icon: React.ReactNode }
> = {
  budget: { color: "green", hex: "#52c41a", label: "Budget", emoji: "\uD83D\uDCB0", icon: <DollarOutlined /> },
  culture: { color: "blue", hex: "#1677ff", label: "Culture", emoji: "\uD83C\uDFAD", icon: <TrophyOutlined /> },
  nature: { color: "cyan", hex: "#13c2c2", label: "Nature", emoji: "\uD83C\uDF3F", icon: <AppstoreOutlined /> },
  food: { color: "orange", hex: "#fa8c16", label: "Food", emoji: "\uD83C\uDF5C", icon: <DollarOutlined /> },
  romantic: { color: "pink", hex: "#eb2f96", label: "Romantic", emoji: "\uD83D\uDC95", icon: <TrophyOutlined /> },
  adventure: { color: "red", hex: "#f5222d", label: "Adventure", emoji: "\uD83C\uDFD4\uFE0F", icon: <AppstoreOutlined /> },
};

function ScoreBar({ label, value, icon, color }: { label: string; value: number; icon: React.ReactNode; color?: string }) {
  const pct = Math.round(value * 100);
  const barColor = color ?? (value >= 0.7 ? "#52c41a" : value >= 0.4 ? "#faad14" : "#ff4d4f");

  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 2 }}>
        <Space size={4}>
          {icon}
          <Text type="secondary" style={{ fontSize: 12 }}>
            {label}
          </Text>
        </Space>
        <Text style={{ fontSize: 11, fontWeight: 500 }}>{pct}</Text>
      </div>
      <div
        style={{
          height: 6,
          borderRadius: 3,
          background: "#f0f0f0",
          overflow: "hidden",
        }}
      >
        <div
          className="score-bar-fill"
          style={{
            height: "100%",
            borderRadius: 3,
            background: barColor,
            width: `${pct}%`,
            transition: "width 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        />
      </div>
    </div>
  );
}

interface PlanComparisonProps {
  alternatives: PlanAlternative[];
  selectedId?: string;
  onSelect: (planId: string) => void;
  loading?: boolean;
  onCompareWithAI?: () => void;
}

export default function PlanComparison({
  alternatives,
  selectedId,
  onSelect,
  loading,
  onCompareWithAI,
}: PlanComparisonProps) {
  const bestId = alternatives.reduce((best, alt) => {
    if (!best) return alt.id;
    const bestScore = alternatives.find((a) => a.id === best)?.scores?.total ?? 0;
    return (alt.scores?.total ?? 0) > bestScore ? alt.id : best;
  }, "");

  return (
    <div>
      {onCompareWithAI && (
        <div style={{ marginBottom: 16, textAlign: "center" }}>
          <Button
            icon={<RobotOutlined />}
            size="large"
            onClick={onCompareWithAI}
            style={{ borderRadius: 8 }}
          >
            Ask AI to Compare Plans
          </Button>
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
      {alternatives.map((alt, idx) => {
        const config = FOCUS_CONFIG[alt.focus] ?? FOCUS_CONFIG.budget;
        const isSelected = alt.id === selectedId;
        const isRecommended = alt.id === bestId;
        const planDays = alt.plan.days?.length ?? 0;
        const attractionCount = alt.plan.days?.reduce(
          (sum, d) => sum + (d.attractions?.length ?? 0),
          0,
        ) ?? 0;

        return (
          <Card
            key={alt.id}
            className={`hover-lift anim-slide-up stagger-${idx + 1}`}
            style={{
              borderRadius: 12,
              border: isSelected
                ? `2px solid ${config.hex}`
                : isRecommended
                  ? `2px solid #faad14`
                  : undefined,
              overflow: "hidden",
            }}
            title={
              <Space>
                <Tag
                  color={config.color}
                  icon={config.icon}
                  style={{ borderRadius: 6, fontWeight: 500 }}
                >
                  {config.emoji} {config.label}
                </Tag>
                <Text strong>{alt.title}</Text>
                {isRecommended && (
                  <Tag
                    color="gold"
                    className="badge-recommended"
                    style={{ borderRadius: 6, fontWeight: 600 }}
                  >
                    Recommended
                  </Tag>
                )}
              </Space>
            }
          >
            {alt.description && (
              <Paragraph type="secondary" style={{ marginBottom: 12 }}>
                {alt.description}
              </Paragraph>
            )}

            <Space direction="vertical" style={{ width: "100%", marginBottom: 12 }}>
              <Text>
                {planDays} days &middot; {attractionCount} attractions
              </Text>
              {alt.estimated_cost > 0 && (
                <Text>
                  Est. cost: <Text strong>¥{alt.estimated_cost.toLocaleString()}</Text>
                </Text>
              )}
            </Space>

            {alt.scores && <ScoreSection scores={alt.scores} focusHex={config.hex} />}

            <Button
              type={isSelected ? "primary" : "default"}
              block
              onClick={() => onSelect(alt.id)}
              loading={loading}
              disabled={isSelected}
              style={{
                borderRadius: 8,
                marginTop: 4,
                ...(isSelected ? { background: config.hex, borderColor: config.hex } : {}),
              }}
            >
              {isSelected ? "Selected" : "Select This Plan"}
            </Button>
          </Card>
        );
      })}
      </div>
    </div>
  );
}

function ScoreSection({ scores, focusHex }: { scores: PlanScores; focusHex: string }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <ScoreBar label="Price" value={scores.price} icon={<DollarOutlined />} color={focusHex} />
      <ScoreBar label="Rating" value={scores.rating} icon={<TrophyOutlined />} color={focusHex} />
      <ScoreBar
        label="Convenience"
        value={scores.convenience}
        icon={<ThunderboltOutlined />}
        color={focusHex}
      />
      <ScoreBar label="Diversity" value={scores.diversity} icon={<AppstoreOutlined />} color={focusHex} />
      <ScoreBar label="Safety" value={scores.safety} icon={<SafetyCertificateOutlined />} color={focusHex} />
      <ScoreBar label="Popularity" value={scores.popularity} icon={<FireOutlined />} color={focusHex} />
      <div style={{ marginTop: 8, textAlign: "center" }}>
        <Text strong style={{ fontSize: 16 }}>
          Total: {Math.round(scores.total * 100)}
        </Text>
      </div>
    </div>
  );
}
