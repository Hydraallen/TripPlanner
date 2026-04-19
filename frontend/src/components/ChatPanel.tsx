import React, { useState, useRef, useEffect } from "react";
import {
  FloatButton,
  Drawer,
  Input,
  Button,
  List,
  Typography,
  Space,
} from "antd";
import { MessageOutlined, SendOutlined, ClearOutlined } from "@ant-design/icons";
import Markdown from "react-markdown";
import { sendChat } from "../api/client";

const { Text } = Typography;

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  planContext?: string | null;
  externalOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  initialMessages?: Message[];
}

const ChatPanel: React.FC<Props> = ({ planContext, externalOpen, onOpenChange, initialMessages }) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = externalOpen ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;
  const [messages, setMessages] = useState<Message[]>(initialMessages ?? []);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const response = await sendChat(
        newMessages.map((m) => ({ role: m.role, content: m.content })),
        planContext || undefined,
      );
      setMessages([...newMessages, { role: "assistant", content: response }]);
    } catch {
      setMessages([...newMessages, { role: "assistant", content: "Sorry, something went wrong." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <FloatButton
        icon={<MessageOutlined />}
        type="primary"
        onClick={() => setOpen(true)}
        style={{ right: 24, bottom: 24 }}
        tooltip="Chat with AI Travel Advisor"
      />

      <Drawer
        title={
          <span style={{ fontWeight: 600, fontSize: 16 }}>
            <MessageOutlined style={{ marginRight: 8 }} />
            AI Travel Advisor
          </span>
        }
        placement="right"
        width={400}
        onClose={() => setOpen(false)}
        open={open}
        extra={
          <Button
            icon={<ClearOutlined />}
            size="small"
            onClick={() => setMessages([])}
            style={{ borderRadius: 6 }}
          >
            Clear
          </Button>
        }
      >
        <div
          ref={listRef}
          style={{
            height: "calc(100vh - 180px)",
            overflowY: "auto",
            marginBottom: 16,
          }}
        >
          {messages.length === 0 && (
            <div style={{ textAlign: "center", padding: 40, color: "#999" }}>
              <MessageOutlined style={{ fontSize: 32, marginBottom: 8 }} />
              <div>Ask me anything about your trip!</div>
            </div>
          )}
          <List
            dataSource={messages}
            renderItem={(msg, idx) => (
              <div
                className={msg.role === "user" ? "anim-slide-in-right" : "anim-slide-in-left"}
                style={{
                  marginBottom: 12,
                  textAlign: msg.role === "user" ? "right" : "left",
                  animationDelay: `${idx * 30}ms`,
                }}
              >
                <div
                  style={{
                    display: "inline-block",
                    maxWidth: "85%",
                    padding: "10px 14px",
                    borderRadius: 12,
                    background: msg.role === "user"
                      ? "linear-gradient(135deg, #1677ff, #722ed1)"
                      : "#f0f0f0",
                    color: msg.role === "user" ? "white" : "inherit",
                    textAlign: "left",
                    boxShadow: msg.role === "user"
                      ? "0 2px 8px rgba(22, 119, 255, 0.25)"
                      : "var(--shadow-sm)",
                    ...(msg.role === "user"
                      ? { borderTopRightRadius: 4 }
                      : { borderTopLeftRadius: 4 }),
                  }}
                >
                  {msg.role === "assistant" ? (
                    <Markdown>{msg.content}</Markdown>
                  ) : (
                    <Text style={{ color: "white" }}>{msg.content}</Text>
                  )}
                </div>
              </div>
            )}
          />
          {loading && (
            <div
              className="anim-slide-in-left"
              style={{ textAlign: "left", marginBottom: 12 }}
            >
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 4,
                  padding: "10px 14px",
                  borderRadius: 12,
                  borderTopLeftRadius: 4,
                  background: "#f0f0f0",
                  boxShadow: "var(--shadow-sm)",
                }}
              >
                <span className="typing-dot" />
                <span className="typing-dot" />
                <span className="typing-dot" />
              </div>
            </div>
          )}
        </div>

        <Space.Compact style={{ width: "100%" }}>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={handleSend}
            placeholder="Ask about your trip..."
            disabled={loading}
            style={{
              borderRadius: "8px 0 0 8px",
              boxShadow: "var(--shadow-sm)",
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            style={{
              borderRadius: "0 8px 8px 0",
              background: "linear-gradient(135deg, #1677ff, #722ed1)",
              border: "none",
            }}
          />
        </Space.Compact>
      </Drawer>
    </>
  );
};

export default ChatPanel;
