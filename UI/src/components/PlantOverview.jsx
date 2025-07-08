import React from "react";
import { Row, Col, Statistic, DatePicker, Select, Card } from "antd";
import {
  ThunderboltOutlined,
  DashboardOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";

const { RangePicker } = DatePicker;
const { Option } = Select;

const PlantOverview = ({
  data,
  stats,
  onDateRangeChange,
  onInverterSelection,
}) => {
  const inverterOptions = data
    ? [...new Set(data.map((d) => d.inverter_id))].sort()
    : [];

  const getFaultSeverityColor = (faultType) => {
    const severityColors = {
      normal: "#52c41a",
      disconnected_string: "#faad14",
      performance_degradation: "#fa8c16",
      soiling: "#1890ff",
      inverter_shutdown: "#f5222d",
      grid_curtailment: "#722ed1",
    };
    return severityColors[faultType] || "#d9d9d9";
  };

  const formatNumber = (num) => {
    return num ? num.toFixed(2) : "0.00";
  };

  return (
    <div className="plant-overview">
      <Row gutter={[16, 16]} className="controls-row">
        <Col span={12}>
          <RangePicker
            style={{ width: "100%" }}
            onChange={onDateRangeChange}
            placeholder={["Start Date", "End Date"]}
          />
        </Col>
        <Col span={12}>
          <Select
            mode="multiple"
            style={{ width: "100%" }}
            placeholder="Select Inverters"
            onChange={onInverterSelection}
            allowClear
          >
            {inverterOptions.map((inverter) => (
              <Option key={inverter} value={inverter}>
                {inverter}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="stats-row">
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Energy AC"
              value={formatNumber(stats.totalEnergyAC)}
              suffix="kWh"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: "#3f8600" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Energy DC"
              value={formatNumber(stats.totalEnergyDC)}
              suffix="kWh"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Performance Ratio"
              value={formatNumber(stats.avgPerformanceRatio)}
              suffix="%"
              prefix={<DashboardOutlined />}
              valueStyle={{ color: "#722ed1" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Capacity Utilization"
              value={formatNumber(stats.avgCapacityUtilization)}
              suffix="%"
              prefix={<DashboardOutlined />}
              valueStyle={{ color: "#fa8c16" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="fault-distribution-row">
        <Col span={24}>
          <Card title="Fault Distribution" size="small">
            <div className="fault-distribution">
              {stats.faultDistribution &&
                Object.entries(stats.faultDistribution).map(
                  ([faultType, count]) => (
                    <div key={faultType} className="fault-item">
                      <div
                        className="fault-indicator"
                        style={{
                          backgroundColor: getFaultSeverityColor(faultType),
                        }}
                      />
                      <span className="fault-type">
                        {faultType.replace("_", " ")}
                      </span>
                      <span className="fault-count">{count}</span>
                    </div>
                  )
                )}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default PlantOverview;
