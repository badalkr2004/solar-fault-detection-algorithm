import React, { useState } from "react";
import { Button, Select, Card, Row, Col, Tag, Progress, Alert } from "antd";
import {
  PlayCircleOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  RobotOutlined,
  ExperimentOutlined,
} from "@ant-design/icons";

const { Option } = Select;

const FaultDetectionPanel = ({ onDetect, modelInfo, isLoading }) => {
  const [detectionType, setDetectionType] = useState("comprehensive");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const detectionOptions = [
    {
      value: "rule_based",
      label: "Rule-Based Detection",
      description: "Fast, threshold-based fault detection",
      icon: <SettingOutlined />,
    },
    {
      value: "ml_based",
      label: "ML-Based Detection",
      description: "Advanced machine learning anomaly detection",
      icon: <RobotOutlined />,
    },
    {
      value: "comprehensive",
      label: "Comprehensive Detection",
      description: "Combines both rule-based and ML methods",
      icon: <ExperimentOutlined />,
    },
  ];

  const handleDetection = () => {
    onDetect(detectionType);
  };

  const getDetectionTypeColor = (type) => {
    const colors = {
      rule_based: "blue",
      ml_based: "green",
      comprehensive: "purple",
    };
    return colors[type] || "default";
  };

  return (
    <div className="fault-detection-panel">
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title="Detection Method"
            size="small"
            extra={
              <Button
                type="link"
                onClick={() => setShowAdvanced(!showAdvanced)}
                icon={<InfoCircleOutlined />}
              >
                {showAdvanced ? "Hide" : "Show"} Details
              </Button>
            }
          >
            <Select
              style={{ width: "100%" }}
              value={detectionType}
              onChange={setDetectionType}
              size="large"
            >
              {detectionOptions.map((option) => (
                <Option key={option.value} value={option.value}>
                  <div style={{ display: "flex", alignItems: "center" }}>
                    {option.icon}
                    <span style={{ marginLeft: 8 }}>{option.label}</span>
                  </div>
                </Option>
              ))}
            </Select>

            {showAdvanced && (
              <div style={{ marginTop: 16 }}>
                <Alert
                  message={
                    detectionOptions.find((opt) => opt.value === detectionType)
                      ?.description
                  }
                  type="info"
                  showIcon
                />
              </div>
            )}
          </Card>
        </Col>

        <Col span={24}>
          <Card title="Detection Settings" size="small">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <div className="setting-item">
                  <label>Detection Type:</label>
                  <Tag color={getDetectionTypeColor(detectionType)}>
                    {detectionType.replace("_", " ").toUpperCase()}
                  </Tag>
                </div>
              </Col>
              <Col span={12}>
                <div className="setting-item">
                  <label>Model Status:</label>
                  <Tag color={modelInfo.is_trained ? "green" : "red"}>
                    {modelInfo.is_trained ? "TRAINED" : "NOT TRAINED"}
                  </Tag>
                </div>
              </Col>
            </Row>

            {modelInfo.is_trained && (
              <div style={{ marginTop: 16 }}>
                <Row gutter={[16, 8]}>
                  <Col span={24}>
                    <label>Supported Fault Types:</label>
                    <div style={{ marginTop: 8 }}>
                      {modelInfo.fault_types?.map((type) => (
                        <Tag
                          key={type}
                          color="blue"
                          style={{ marginBottom: 4 }}
                        >
                          {type.replace("_", " ")}
                        </Tag>
                      ))}
                    </div>
                  </Col>
                </Row>
              </div>
            )}
          </Card>
        </Col>

        <Col span={24}>
          <Card title="Detection Progress" size="small">
            {isLoading ? (
              <div>
                <Progress
                  percent={100}
                  status="active"
                  showInfo={false}
                  style={{ marginBottom: 16 }}
                />
                <div style={{ textAlign: "center" }}>
                  Analyzing solar plant data...
                </div>
              </div>
            ) : (
              <div style={{ textAlign: "center" }}>
                <Button
                  type="primary"
                  size="large"
                  icon={<PlayCircleOutlined />}
                  onClick={handleDetection}
                  disabled={isLoading}
                  block
                >
                  Run Fault Detection
                </Button>
              </div>
            )}
          </Card>
        </Col>

        {modelInfo.is_trained && (
          <Col span={24}>
            <Card title="Model Information" size="small">
              <Row gutter={[16, 8]}>
                <Col span={12}>
                  <div className="info-item">
                    <label>Features:</label>
                    <span>{modelInfo.feature_names?.length || 0}</span>
                  </div>
                </Col>
                <Col span={12}>
                  <div className="info-item">
                    <label>Fault Types:</label>
                    <span>{modelInfo.fault_types?.length || 0}</span>
                  </div>
                </Col>
              </Row>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default FaultDetectionPanel;
