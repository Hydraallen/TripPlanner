import React, { useState } from "react";
import { Form, Input, DatePicker, Select, Switch, Button, Space } from "antd";
import { RocketOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import type { Dayjs } from "dayjs";

export interface TripFormValues {
  city: string;
  startDate: Dayjs;
  endDate: Dayjs;
  interests: string[];
  transportMode: string;
  useLLM: boolean;
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
  { value: "religion", label: "Religious Sites" },
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
  const [useLLM, setUseLLM] = useState(initialValues?.useLLM ?? false);

  const handleFinish = (values: Record<string, unknown>) => {
    const range = values.dateRange as [Dayjs, Dayjs];
    onSubmit({
      city: values.city as string,
      startDate: range[0],
      endDate: range[1],
      interests: (values.interests as string[]) || ["interesting_places"],
      transportMode: values.transportMode as string,
      useLLM,
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
        interests: initialValues?.interests || ["interesting_places"],
        transportMode: initialValues?.transportMode || "walking",
      }}
    >
      <Form.Item
        name="city"
        label="Destination"
        rules={[{ required: true, message: "Please enter a destination" }]}
      >
        <Input placeholder="e.g. Tokyo, Beijing, Paris" size="large" />
      </Form.Item>

      <Form.Item
        name="dateRange"
        label="Travel Dates"
        rules={[{ required: true, message: "Please select dates" }]}
      >
        <DatePicker.RangePicker
          size="large"
          style={{ width: "100%" }}
          disabledDate={(d) => d && d < dayjs().startOf("day")}
        />
      </Form.Item>

      <Form.Item name="interests" label="Interests">
        <Select
          mode="multiple"
          options={INTEREST_OPTIONS}
          size="large"
          placeholder="Select interests"
        />
      </Form.Item>

      <Form.Item name="transportMode" label="Transport Mode">
        <Select options={TRANSPORT_OPTIONS} size="large" />
      </Form.Item>

      <Space align="center" style={{ marginBottom: 16 }}>
        <Switch checked={useLLM} onChange={setUseLLM} />
        <span>AI-Powered (uses LLM for generation)</span>
      </Space>

      {useLLM && (
        <Form.Item name="preferences" label="Additional Preferences">
          <Input.TextArea
            rows={2}
            placeholder="e.g. budget-friendly, prefer local cuisine, avoid crowds..."
          />
        </Form.Item>
      )}

      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          icon={<RocketOutlined />}
          loading={loading}
          size="large"
          block
        >
          Generate Plan
        </Button>
      </Form.Item>
    </Form>
  );
};

export default TripForm;
