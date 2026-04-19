import React from "react";
import { Form, Input, DatePicker, Select, Button, Collapse } from "antd";
import { RocketOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";

export interface TripFormValues {
  city: string;
  startDate: Dayjs;
  endDate: Dayjs;
  interests?: string[];
  transportMode?: string;
  preferences?: string;
}

interface Props {
  onSubmit: (values: TripFormValues) => void;
  loading?: boolean;
  initialValues?: Partial<TripFormValues>;
}

const INTEREST_OPTIONS = [
  { value: "museums", label: "Museums" },
  { value: "food", label: "Food & Dining" },
  { value: "historic", label: "Historic Sites" },
  { value: "nature", label: "Nature & Parks" },
  { value: "shopping", label: "Shopping" },
  { value: "nightlife", label: "Nightlife" },
  { value: "beaches", label: "Beaches" },
  { value: "architecture", label: "Architecture" },
  { value: "interesting_places", label: "General" },
];

const TRANSPORT_OPTIONS = [
  { value: "walking", label: "Walking" },
  { value: "transit", label: "Public Transit" },
  { value: "driving", label: "Driving" },
];

const TripForm: React.FC<Props> = ({ onSubmit, loading, initialValues }) => {
  const [form] = Form.useForm();

  const handleFinish = (values: Record<string, unknown>) => {
    const range = values.dateRange as [Dayjs, Dayjs];
    const interests = values.interests as string[] | undefined;
    const transportMode = values.transportMode as string | undefined;
    onSubmit({
      city: values.city as string,
      startDate: range[0],
      endDate: range[1],
      interests: interests && interests.length > 0 ? interests : undefined,
      transportMode: transportMode && transportMode !== "auto" ? transportMode : undefined,
      preferences: values.preferences as string | undefined,
    });
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      initialValues={{
        city: initialValues?.city || "",
      }}
      className="focus-glow"
    >
      <Form.Item
        name="city"
        label="Destination"
        rules={[{ required: true, message: "Please enter a destination" }]}
      >
        <Input
          placeholder="e.g. Tokyo, Beijing, Paris"
          size="large"
          style={{ borderRadius: 8 }}
        />
      </Form.Item>

      <Form.Item
        name="dateRange"
        label="Travel Dates"
        rules={[{ required: true, message: "Please select dates" }]}
      >
        <DatePicker.RangePicker
          size="large"
          style={{ width: "100%", borderRadius: 8 }}
          disabledDate={(d) => d && d < dayjs().startOf("day")}
        />
      </Form.Item>

      <Collapse
        ghost
        items={[
          {
            key: "advanced",
            label: "Advanced options",
            children: (
              <>
                <Form.Item name="interests" label="Interests">
                  <Select
                    mode="multiple"
                    options={INTEREST_OPTIONS}
                    size="large"
                    placeholder="Leave empty for AI to decide"
                    style={{ borderRadius: 8 }}
                    allowClear
                  />
                </Form.Item>

                <Form.Item name="transportMode" label="Transport Mode">
                  <Select
                    size="large"
                    style={{ borderRadius: 8 }}
                    allowClear
                    placeholder="Leave empty for AI to decide"
                  >
                    {TRANSPORT_OPTIONS.map((opt) => (
                      <Select.Option key={opt.value} value={opt.value}>
                        {opt.label}
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>

                <Form.Item name="preferences" label="Additional Preferences">
                  <Input.TextArea
                    rows={2}
                    placeholder="e.g. budget-friendly, prefer local cuisine, avoid crowds..."
                    style={{ borderRadius: 8 }}
                  />
                </Form.Item>
              </>
            ),
          },
        ]}
      />

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          icon={<RocketOutlined />}
          loading={loading}
          size="large"
          block
          style={{
            height: 48,
            fontSize: 16,
            borderRadius: 8,
            background: "linear-gradient(135deg, #1677ff 0%, #722ed1 100%)",
            border: "none",
          }}
        >
          Generate Plan
        </Button>
      </Form.Item>
    </Form>
  );
};

export default TripForm;
