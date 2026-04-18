import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Table, Button, Popconfirm, Typography, message } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { listTrips, deleteTrip, type TripSummary } from "../api/client";

const { Title } = Typography;

const TripsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTrips = async () => {
    setLoading(true);
    try {
      const data = await listTrips();
      setTrips(data);
    } catch {
      // error handled by interceptor
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteTrip(id);
      message.success("Trip deleted");
      setTrips((prev) => prev.filter((t) => t.id !== id));
    } catch {
      // error handled by interceptor
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <Title level={2}>My Trips</Title>
      <Table
        dataSource={trips}
        loading={loading}
        rowKey="id"
        onRow={(record) => ({
          onClick: () => navigate(`/trips/${record.id}`),
          style: { cursor: "pointer" },
        })}
        columns={[
          {
            title: "City",
            dataIndex: "city",
            key: "city",
          },
          {
            title: "Dates",
            key: "dates",
            render: (_, record) => `${record.start_date} — ${record.end_date}`,
          },
          {
            title: "Created",
            dataIndex: "created_at",
            key: "created",
            render: (val: string | null) =>
              val ? new Date(val).toLocaleDateString() : "-",
          },
          {
            title: "",
            key: "actions",
            render: (_, record) => (
              <Popconfirm
                title="Delete this trip?"
                onConfirm={(e) => {
                  e?.stopPropagation();
                  handleDelete(record.id);
                }}
                onCancel={(e) => e?.stopPropagation()}
              >
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  size="small"
                  onClick={(e) => e.stopPropagation()}
                />
              </Popconfirm>
            ),
          },
        ]}
        locale={{ emptyText: "No trips yet. Plan your first trip!" }}
      />
    </div>
  );
};

export default TripsListPage;
