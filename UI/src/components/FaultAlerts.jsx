import React, { useState, useMemo } from "react";
import {
  List,
  Tag,
  Badge,
  Button,
  Modal,
  Descriptions,
  Empty,
  Input,
  Select,
  Row,
  Col,
} from "antd";
import {
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import moment from "moment";

const { Search } = Input;
const { Option } = Select;

const FaultAlerts = ({ faults, onRefresh }) => {
  const [selectedFault, setSelectedFault] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  const getSeverityIcon = (severity) => {
    const icons = {
      critical: <CloseCircleOutlined style={{ color: "#f5222d" }} />,
      high: <ExclamationCircleOutlined style={{ color: "#fa8c16" }} />,
      medium: <WarningOutlined style={{ color: "#faad14" }} />,
      low: <InfoCircleOutlined style={{ color: "#1890ff" }} />,
    };
    return icons[severity] || icons.low;
  };

  const getSeverityColor = (severity) => {
    const colors = {
      critical: "red",
      high: "orange",
      medium: "gold",
      low: "blue",
    };
    return colors[severity] || "default";
  };

  const getFaultTypeColor = (faultType) => {
    const colors = {
      disconnected_string: "orange",
      inverter_shutdown: "red",
      performance_degradation: "purple",
      soiling: "blue",
      grid_curtailment: "green",
      unknown_anomaly: "gray",
    };
    return colors[faultType] || "default";
  };

  // Filter and sort faults
  const filteredFaults = useMemo(() => {
    let filtered = faults || [];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (fault) =>
          fault.fault_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
          fault.inverter_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          fault.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply severity filter
    if (severityFilter !== "all") {
      filtered = filtered.filter((fault) => fault.severity === severityFilter);
    }

    // Apply type filter
    if (typeFilter !== "all") {
      filtered = filtered.filter((fault) => fault.fault_type === typeFilter);
    }

    // Sort by severity and timestamp
    return filtered.sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
      const severityDiff =
        (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0);

      if (severityDiff !== 0) return severityDiff;

      return new Date(b.timestamp) - new Date(a.timestamp);
    });
  }, [faults, searchTerm, severityFilter, typeFilter]);

  const handleFaultClick = (fault) => {
    setSelectedFault(fault);
    setShowModal(true);
  };

  const handleModalClose = () => {
    setShowModal(false);
    setSelectedFault(null);
  };

  // Get unique fault types for filter
  const uniqueFaultTypes = useMemo(() => {
    if (!faults) return [];
    return [...new Set(faults.map((f) => f.fault_type))];
  }, [faults]);

  const faultSummary = useMemo(() => {
    if (!faults || faults.length === 0) return {};

    return faults.reduce((acc, fault) => {
      acc[fault.severity] = (acc[fault.severity] || 0) + 1;
      return acc;
    }, {});
  }, [faults]);

  return (
    <div className="fault-alerts">
      <Row gutter={[16, 16]} className="fault-controls">
        <Col span={24}>
          <div className="fault-summary">
            <Badge
              count={faultSummary.critical || 0}
              style={{ backgroundColor: "#f5222d" }}
            >
              <Tag color="red">Critical</Tag>
            </Badge>
            <Badge
              count={faultSummary.high || 0}
              style={{ backgroundColor: "#fa8c16" }}
            >
              <Tag color="orange">High</Tag>
            </Badge>
            <Badge
              count={faultSummary.medium || 0}
              style={{ backgroundColor: "#faad14" }}
            >
              <Tag color="gold">Medium</Tag>
            </Badge>
            <Badge
              count={faultSummary.low || 0}
              style={{ backgroundColor: "#1890ff" }}
            >
              <Tag color="blue">Low</Tag>
            </Badge>
          </div>
        </Col>

        <Col span={24}>
          <Search
            placeholder="Search faults..."
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ marginBottom: 8 }}
            prefix={<SearchOutlined />}
          />
        </Col>

        <Col span={12}>
          <Select
            style={{ width: "100%" }}
            placeholder="Filter by severity"
            value={severityFilter}
            onChange={setSeverityFilter}
          >
            <Option value="all">All Severities</Option>
            <Option value="critical">Critical</Option>
            <Option value="high">High</Option>
            <Option value="medium">Medium</Option>
            <Option value="low">Low</Option>
          </Select>
        </Col>

        <Col span={12}>
          <Select
            style={{ width: "100%" }}
            placeholder="Filter by type"
            value={typeFilter}
            onChange={setTypeFilter}
          >
            <Option value="all">All Types</Option>
            {uniqueFaultTypes.map((type) => (
              <Option key={type} value={type}>
                {type.replace("_", " ")}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      <div className="fault-list">
        {filteredFaults.length === 0 ? (
          <Empty
            description="No faults detected"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={filteredFaults}
            renderItem={(fault) => (
              <List.Item
                className="fault-item"
                onClick={() => handleFaultClick(fault)}
                style={{ cursor: "pointer" }}
              >
                <List.Item.Meta
                  avatar={getSeverityIcon(fault.severity)}
                  title={
                    <div>
                      <Tag color={getFaultTypeColor(fault.fault_type)}>
                        {fault.fault_type.replace("_", " ")}
                      </Tag>
                      <Tag color={getSeverityColor(fault.severity)}>
                        {fault.severity}
                      </Tag>
                      {fault.inverter_id && (
                        <Tag color="default">{fault.inverter_id}</Tag>
                      )}
                    </div>
                  }
                  description={
                    <div>
                      <div className="fault-description">
                        {fault.description}
                      </div>
                      <div className="fault-meta">
                        <span>{moment(fault.timestamp).fromNow()}</span>
                        <span>
                          Confidence: {(fault.confidence * 100).toFixed(1)}%
                        </span>
                        <span>Detected by: {fault.detected_by}</span>
                      </div>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </div>

      <div className="fault-actions">
        <Button
          type="primary"
          icon={<ReloadOutlined />}
          onClick={onRefresh}
          block
        >
          Refresh Faults
        </Button>
      </div>

      <Modal
        title="Fault Details"
        visible={showModal}
        onCancel={handleModalClose}
        footer={[
          <Button key="close" onClick={handleModalClose}>
            Close
          </Button>,
        ]}
        width={600}
      >
        {selectedFault && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="Fault Type" span={2}>
              <Tag color={getFaultTypeColor(selectedFault.fault_type)}>
                {selectedFault.fault_type.replace("_", " ")}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Severity">
              <Tag color={getSeverityColor(selectedFault.severity)}>
                {selectedFault.severity}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Confidence">
              {(selectedFault.confidence * 100).toFixed(1)}%
            </Descriptions.Item>
            <Descriptions.Item label="Timestamp" span={2}>
              {moment(selectedFault.timestamp).format("YYYY-MM-DD HH:mm:ss")}
            </Descriptions.Item>
            <Descriptions.Item label="Inverter ID">
              {selectedFault.inverter_id || "N/A"}
            </Descriptions.Item>
            <Descriptions.Item label="Plant ID">
              {selectedFault.plant_id || "N/A"}
            </Descriptions.Item>
            <Descriptions.Item label="Detection Method" span={2}>
              {selectedFault.detected_by}
            </Descriptions.Item>
            <Descriptions.Item label="Description" span={2}>
              {selectedFault.description}
            </Descriptions.Item>
            {selectedFault.anomaly_score && (
              <Descriptions.Item label="Anomaly Score" span={2}>
                {selectedFault.anomaly_score.toFixed(3)}
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default FaultAlerts;
