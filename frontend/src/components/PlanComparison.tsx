import { Card, Tag, Button, Progress, Space, Typography } from "antd";
import {
  DollarOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  AppstoreOutlined,
} from "@ant-design/icons";
import type { PlanAlternative, PlanScores } from "../api/client";

const { Text, Paragraph } = Typography;

const FOCUS_CONFIG: Record<
  string,
  { color: string; label: string; icon: React.ReactNode }
> = {
  budget: { color: "green", label: "Budget", icon: <DollarOutlined /> },
  culture: { color: "blue", label: "Culture", icon: <TrophyOutlined /> },
  nature: { color: "cyan", label: "Nature", icon: <AppstoreOutlined /> },
};

function ScoreBar({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 4 }}>
      <Space size={4}>
        {icon}
        <Text type="secondary" style={{ fontSize: 12 }}>
          {label}
        </Text>
      </Space>
      <Progress
        percent={Math.round(value * 100)}
        size="small"
        showInfo={false}
        strokeColor={value >= 0.7 ? "#52c41a" : value >= 0.4 ? "#faad14" : "#ff4d4f"}
      />
    </div>
  );
}

interface PlanComparisonProps {
  alternatives: PlanAlternative[];
  selectedId?: string;
  onSelect: (planId: string) => void;
  loading?: boolean;
}

export default function PlanComparison({
  alternatives,
  selectedId,
  onSelect,
  loading,
}: PlanComparisonProps) {
  const bestId = alternatives.reduce((best, alt) => {
    if (!best) return alt.id;
    const bestScore = alternatives.find((a) => a.id === best)?.scores?.total ?? 0;
    return (alt.scores?.total ?? 0) > bestScore ? alt.id : best;
  }, "");

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
      {alternatives.map((alt) => {
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
            hoverable
            style={{
              border: isSelected ? "2px solid #1677ff" : isRecommended ? "2px solid #52c41a" : undefined,
            }}
            title={
              <Space>
                <Tag color={config.color} icon={config.icon}>
                  {config.label}
                </Tag>
                <Text strong>{alt.title}</Text>
                {isRecommended && <Tag color="gold">Recommended</Tag>}
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

            {alt.scores && <ScoreSection scores={alt.scores} />}

            <Button
              type={isSelected ? "primary" : "default"}
              block
              onClick={() => onSelect(alt.id)}
              loading={loading}
              disabled={isSelected}
            >
              {isSelected ? "Selected" : "Select This Plan"}
            </Button>
          </Card>
        );
      })}
    </div>
  );
}

function ScoreSection({ scores }: { scores: PlanScores }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <ScoreBar label="Price" value={scores.price} icon={<DollarOutlined />} />
      <ScoreBar label="Rating" value={scores.rating} icon={<TrophyOutlined />} />
      <ScoreBar
        label="Convenience"
        value={scores.convenience}
        icon={<ThunderboltOutlined />}
      />
      <ScoreBar label="Diversity" value={scores.diversity} icon={<AppstoreOutlined />} />
      <div style={{ marginTop: 8, textAlign: "center" }}>
        <Text strong style={{ fontSize: 16 }}>
          Total: {Math.round(scores.total * 100)}
        </Text>
      </div>
    </div>
  );
}
