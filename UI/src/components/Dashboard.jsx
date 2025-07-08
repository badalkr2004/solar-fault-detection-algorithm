import React, { useState, useEffect } from "react";
import { Layout, Row, Col, Card, Spin, notification } from "antd";
import PlantOverview from "./PlantOverview";
import DataVisualization from "./DataVisualization";
import FaultDetectionPanel from "./FaultDetectionPanel";
import FaultAlerts from "./FaultAlerts";
import TestingPanel from "./TestingPanel";
import { solarAPI } from "../services/api";
import "../styles/Dashboard.css";

const { Header, Content } = Layout;

const Dashboard = () => {
  const [loading, setLoading] = useState(false);
  const [solarData, setSolarData] = useState([]);
  const [faultData, setFaultData] = useState([]);
  const [plantStats, setPlantStats] = useState({});
  const [modelInfo, setModelInfo] = useState({});
  const [selectedDateRange, setSelectedDateRange] = useState([]);
  const [selectedInverters, setSelectedInverters] = useState([]);

  // Load initial data
  useEffect(() => {
    loadInitialData();
    loadModelInfo();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const response = await solarAPI.generateSampleData({
        num_days: 30,
        num_inverters: 8,
        include_faults: true,
      });

      setSolarData(response.data.data);
      calculatePlantStats(response.data.data);

      notification.success({
        message: "Data Loaded",
        description: `Loaded ${response.data.data.length} data points`,
      });
    } catch (error) {
      console.error("Error loading initial data:", error);
      notification.error({
        message: "Error",
        description: "Failed to load initial data",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadModelInfo = async () => {
    try {
      const response = await solarAPI.getModelInfo();
      setModelInfo(response.data);
    } catch (error) {
      console.error("Error loading model info:", error);
    }
  };

  const calculatePlantStats = (data) => {
    if (!data || data.length === 0) return;

    const stats = {
      totalInverters: new Set(data.map((d) => d.inverter_id)).size,
      totalStrings: new Set(data.map((d) => d.string_id)).size,
      totalEnergyAC: data.reduce((sum, d) => sum + d.daily_energy_yield_ac, 0),
      totalEnergyDC: data.reduce((sum, d) => sum + d.daily_energy_yield_dc, 0),
      avgPerformanceRatio:
        data.reduce((sum, d) => sum + d.performance_ratio_ac, 0) / data.length,
      avgCapacityUtilization:
        data.reduce((sum, d) => sum + d.capacity_utilization_factor_ac, 0) /
        data.length,
      faultDistribution: data.reduce((acc, d) => {
        acc[d.fault_type] = (acc[d.fault_type] || 0) + 1;
        return acc;
      }, {}),
    };

    setPlantStats(stats);
  };

  const handleFaultDetection = async (detectionType = "comprehensive") => {
    if (!solarData || solarData.length === 0) {
      notification.warning({
        message: "No Data",
        description: "Please load sample data first",
      });
      return;
    }

    setLoading(true);
    try {
      const response = await solarAPI.detectFaults(solarData, detectionType);
      setFaultData(response.data.faults);

      notification.success({
        message: "Fault Detection Complete",
        description: `Detected ${response.data.total_faults} faults`,
      });
    } catch (error) {
      console.error("Error detecting faults:", error);
      notification.error({
        message: "Error",
        description: "Failed to detect faults",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDataRefresh = () => {
    loadInitialData();
  };

  const handleDateRangeChange = (dates) => {
    setSelectedDateRange(dates);
  };

  const handleInverterSelection = (inverters) => {
    setSelectedInverters(inverters);
  };

  // Filter data based on selections
  const filteredData = solarData.filter((item) => {
    const dateInRange =
      selectedDateRange.length === 0 ||
      (new Date(item.datetime) >= selectedDateRange[0] &&
        new Date(item.datetime) <= selectedDateRange[1]);

    const inverterSelected =
      selectedInverters.length === 0 ||
      selectedInverters.includes(item.inverter_id);

    return dateInRange && inverterSelected;
  });

  return (
    <Layout className="dashboard-layout">
      <Header className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">
            Solar Plant Monitoring & Fault Detection
          </h1>
          <div className="header-stats">
            <span className="stat-item">
              Inverters: {plantStats.totalInverters || 0}
            </span>
            <span className="stat-item">
              Strings: {plantStats.totalStrings || 0}
            </span>
            <span className="stat-item">
              Total Energy: {(plantStats.totalEnergyAC || 0).toFixed(2)} kWh
            </span>
          </div>
        </div>
      </Header>

      <Content className="dashboard-content">
        <Spin spinning={loading} size="large">
          <Row gutter={[16, 16]}>
            {/* Plant Overview */}
            <Col span={24}>
              <Card title="Plant Overview" className="overview-card">
                <PlantOverview
                  data={filteredData}
                  stats={plantStats}
                  onDateRangeChange={handleDateRangeChange}
                  onInverterSelection={handleInverterSelection}
                />
              </Card>
            </Col>

            {/* Data Visualization */}
            <Col span={16}>
              <Card
                title="Performance Analytics"
                className="visualization-card"
              >
                <DataVisualization data={filteredData} faultData={faultData} />
              </Card>
            </Col>

            {/* Fault Alerts */}
            <Col span={8}>
              <Card title="Fault Alerts" className="alerts-card">
                <FaultAlerts
                  faults={faultData}
                  onRefresh={() => handleFaultDetection()}
                />
              </Card>
            </Col>

            {/* Fault Detection Panel */}
            <Col span={12}>
              <Card title="Fault Detection" className="detection-card">
                <FaultDetectionPanel
                  onDetect={handleFaultDetection}
                  modelInfo={modelInfo}
                  isLoading={loading}
                />
              </Card>
            </Col>

            {/* Testing Panel */}
            <Col span={12}>
              <Card title="Testing & Data Generation" className="testing-card">
                <TestingPanel
                  onDataGenerate={handleDataRefresh}
                  onModelRetrain={loadModelInfo}
                  isLoading={loading}
                />
              </Card>
            </Col>
          </Row>
        </Spin>
      </Content>
    </Layout>
  );
};

export default Dashboard;
