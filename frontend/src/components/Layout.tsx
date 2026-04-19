import React from "react";
import { Layout as AntLayout, Menu, Typography } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import type { MenuProps } from "antd";

const { Header, Content, Footer } = AntLayout;
const { Title } = Typography;

const navItems: MenuProps["items"] = [
  { key: "/", label: "Home" },
  { key: "/plan", label: "Plan Trip" },
  { key: "/trips", label: "My Trips" },
];

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          display: "flex",
          alignItems: "center",
          gap: 24,
          background: "linear-gradient(90deg, #1a1a2e 0%, #16213e 100%)",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}
      >
        <Title
          level={4}
          style={{
            color: "white",
            margin: 0,
            whiteSpace: "nowrap",
            fontWeight: 600,
            letterSpacing: "0.5px",
          }}
        >
          TripPlanner
        </Title>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={navItems}
          onClick={({ key }) => navigate(key)}
          style={{
            flex: 1,
            minWidth: 0,
            background: "transparent",
            borderBottom: "none",
          }}
        />
      </Header>
      <Content style={{ padding: "24px 48px" }}>
        {children}
      </Content>
      <Footer
        style={{
          textAlign: "center",
          background: "rgba(255, 255, 255, 0.7)",
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
          borderTop: "1px solid rgba(0, 0, 0, 0.06)",
          color: "#666",
        }}
      >
        TripPlanner &copy; {new Date().getFullYear()}
      </Footer>
    </AntLayout>
  );
};

export default Layout;
