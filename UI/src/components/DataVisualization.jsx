import { useState, useMemo } from "react";
import { Tabs, Select, Switch, Row, Col } from "antd";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart,
} from "recharts";
import moment from "moment";

const { TabPane } = Tabs;
const { Option } = Select;

const DataVisualization = ({ data, faultData }) => {
  const [selectedChart, setSelectedChart] = useState("energy");
  const [selectedInverter, setSelectedInverter] = useState("all");
  const [showFaults, setShowFaults] = useState(true);
  const [aggregationType, setAggregationType] = useState("daily");

  const colors = {
    ac: "#1890ff",
    dc: "#52c41a",
    fault: "#f5222d",
    normal: "#d9d9d9",
    performance: "#722ed1",
    capacity: "#fa8c16",
  };

  const faultColors = {
    normal: "#52c41a",
    disconnected_string: "#faad14",
    performance_degradation: "#fa8c16",
    soiling: "#1890ff",
    inverter_shutdown: "#f5222d",
    grid_curtailment: "#722ed1",
  };

  // Process data for charts
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];

    let filteredData = data;
    if (selectedInverter !== "all") {
      filteredData = data.filter((d) => d.inverter_id === selectedInverter);
    }

    // Group by date and aggregate
    const groupedData = filteredData.reduce((acc, item) => {
      const date = moment(item.datetime).format("YYYY-MM-DD");
      if (!acc[date]) {
        acc[date] = {
          date,
          datetime: item.datetime,
          daily_energy_yield_ac: 0,
          daily_energy_yield_dc: 0,
          performance_ratio_ac: 0,
          performance_ratio_dc: 0,
          capacity_utilization_factor_ac: 0,
          capacity_utilization_factor_dc: 0,
          daily_specific_yield_ac: 0,
          daily_specific_yield_dc: 0,
          count: 0,
          faults: [],
        };
      }

      acc[date].daily_energy_yield_ac += item.daily_energy_yield_ac;
      acc[date].daily_energy_yield_dc += item.daily_energy_yield_dc;
      acc[date].performance_ratio_ac += item.performance_ratio_ac;
      acc[date].performance_ratio_dc += item.performance_ratio_dc;
      acc[date].capacity_utilization_factor_ac +=
        item.capacity_utilization_factor_ac;
      acc[date].capacity_utilization_factor_dc +=
        item.capacity_utilization_factor_dc;
      acc[date].daily_specific_yield_ac += item.daily_specific_yield_ac;
      acc[date].daily_specific_yield_dc += item.daily_specific_yield_dc;
      acc[date].count++;

      if (item.fault_type && item.fault_type !== "normal") {
        acc[date].faults.push(item.fault_type);
      }

      return acc;
    }, {});

    // Calculate averages
    return Object.values(groupedData)
      .map((item) => ({
        ...item,
        performance_ratio_ac: item.performance_ratio_ac / item.count,
        performance_ratio_dc: item.performance_ratio_dc / item.count,
        capacity_utilization_factor_ac:
          item.capacity_utilization_factor_ac / item.count,
        capacity_utilization_factor_dc:
          item.capacity_utilization_factor_dc / item.count,
        daily_specific_yield_ac: item.daily_specific_yield_ac / item.count,
        daily_specific_yield_dc: item.daily_specific_yield_dc / item.count,
        hasFaults: item.faults.length > 0,
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [data, selectedInverter]);

  // Get unique inverters
  const inverterOptions = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.map((d) => d.inverter_id))].sort();
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;

      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{`Date: ${label}`}</p>
          {payload.map((entry, index) => (
            <p
              key={index}
              className="tooltip-value"
              style={{ color: entry.color }}
            >
              {`${entry.name}: ${
                typeof entry.value === "number"
                  ? entry.value.toFixed(2)
                  : entry.value
              }`}
            </p>
          ))}
          {data.hasFaults && (
            <p className="tooltip-faults">Faults: {data.faults.join(", ")}</p>
          )}
        </div>
      );
    }
    return null;
  };

  const renderEnergyChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={processedData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => moment(value).format("MM/DD")}
        />
        <YAxis />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="daily_energy_yield_ac"
          stroke={colors.ac}
          name="Energy AC (kWh)"
          strokeWidth={2}
          dot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="daily_energy_yield_dc"
          stroke={colors.dc}
          name="Energy DC (kWh)"
          strokeWidth={2}
          dot={{ r: 4 }}
        />
        {showFaults && (
          <Line
            type="monotone"
            dataKey="hasFaults"
            stroke={colors.fault}
            name="Faults"
            strokeWidth={3}
            dot={{ r: 6 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );

  const renderPerformanceChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart data={processedData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => moment(value).format("MM/DD")}
        />
        <YAxis />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Area
          type="monotone"
          dataKey="performance_ratio_ac"
          stackId="1"
          stroke={colors.performance}
          fill={colors.performance}
          name="Performance Ratio AC (%)"
        />
        <Area
          type="monotone"
          dataKey="capacity_utilization_factor_ac"
          stackId="2"
          stroke={colors.capacity}
          fill={colors.capacity}
          name="Capacity Utilization AC (%)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );

  const renderFaultDistributionChart = () => {
    const faultCounts = faultData.reduce((acc, fault) => {
      acc[fault.fault_type] = (acc[fault.fault_type] || 0) + 1;
      return acc;
    }, {});

    const pieData = Object.entries(faultCounts).map(([type, count]) => ({
      name: type.replace("_", " "),
      value: count,
      color: faultColors[type],
    }));

    return (
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) =>
              `${name} ${(percent * 100).toFixed(0)}%`
            }
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderComparisonChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={processedData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(value) => moment(value).format("MM/DD")}
        />
        <YAxis />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Bar
          dataKey="daily_energy_yield_ac"
          fill={colors.ac}
          name="Energy AC (kWh)"
        />
        <Bar
          dataKey="daily_energy_yield_dc"
          fill={colors.dc}
          name="Energy DC (kWh)"
        />
      </BarChart>
    </ResponsiveContainer>
  );

  return (
    <div className="data-visualization">
      <Row gutter={[16, 16]} className="chart-controls">
        <Col span={8}>
          <Select
            style={{ width: "100%" }}
            placeholder="Select Inverter"
            value={selectedInverter}
            onChange={setSelectedInverter}
          >
            <Option value="all">All Inverters</Option>
            {inverterOptions.map((inverter) => (
              <Option key={inverter} value={inverter}>
                {inverter}
              </Option>
            ))}
          </Select>
        </Col>
        <Col span={8}>
          <Select
            style={{ width: "100%" }}
            placeholder="Aggregation Type"
            value={aggregationType}
            onChange={setAggregationType}
          >
            <Option value="daily">Daily</Option>
            <Option value="weekly">Weekly</Option>
            <Option value="monthly">Monthly</Option>
          </Select>
        </Col>
        <Col span={8}>
          <Switch
            checked={showFaults}
            onChange={setShowFaults}
            checkedChildren="Show Faults"
            unCheckedChildren="Hide Faults"
          />
        </Col>
      </Row>

      <Tabs defaultActiveKey="energy" onChange={setSelectedChart}>
        <TabPane tab="Energy Production" key="energy">
          {renderEnergyChart()}
        </TabPane>
        <TabPane tab="Performance Metrics" key="performance">
          {renderPerformanceChart()}
        </TabPane>
        <TabPane tab="Fault Distribution" key="faults">
          {renderFaultDistributionChart()}
        </TabPane>
        <TabPane tab="Comparison" key="comparison">
          {renderComparisonChart()}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default DataVisualization;
