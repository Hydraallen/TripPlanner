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
      <Header style={{ display: "flex", alignItems: "center", gap: 24 }}>
        <Title level={4} style={{ color: "white", margin: 0, whiteSpace: "nowrap" }}>
          TripPlanner
        </Title>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={navItems}
          onClick={({ key }) => navigate(key)}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ padding: "24px 48px" }}>
        {children}
      </Content>
      <Footer style={{ textAlign: "center" }}>
        TripPlanner &copy; {new Date().getFullYear()}
      </Footer>
    </AntLayout>
  );
};

export default Layout;
