import React, { useState } from "react";
import {
  Button,
  Card,
  InputNumber,
  Switch,
  Row,
  Col,
  Progress,
  Alert,
  Divider,
} from "antd";
import {
  DatabaseOutlined,
  ExperimentOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";

const TestingPanel = ({ onDataGenerate, onModelRetrain, isLoading }) => {
  const [numDays, setNumDays] = useState(30);
  const [numInverters, setNumInverters] = useState(5);
  const [includeFaults, setIncludeFaults] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [retraining, setRetraining] = useState(false);

  const handleDataGeneration = async () => {
    setGenerating(true);
    try {
      await onDataGenerate({
        num_days: numDays,
        num_inverters: numInverters,
        include_faults: includeFaults,
      });
    } catch (error) {
      console.error("Error generating data:", error);
    } finally {
      setGenerating(false);
    }
  };

  const handleModelRetraining = async () => {
    setRetraining(true);
    try {
      await onModelRetrain();
    } catch (error) {
      console.error("Error retraining model:", error);
    } finally {
      setRetraining(false);
    }
  };

  return (
    <div className="testing-panel">
      <Card title="Data Generation" className="generation-card">
        <Alert
          message="Generate synthetic solar plant data for testing"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <div className="input-group">
              <label>Number of Days:</label>
              <InputNumber
                min={1}
                max={365}
                value={numDays}
                onChange={setNumDays}
                style={{ width: "100%" }}
              />
            </div>
          </Col>
          <Col span={12}>
            <div className="input-group">
              <label>Number of Inverters:</label>
              <InputNumber
                min={1}
                max={50}
                value={numInverters}
                onChange={setNumInverters}
                style={{ width: "100%" }}
              />
            </div>
          </Col>
          <Col span={24}>
            <div className="input-group">
              <label>Include Faults:</label>
              <Switch
                checked={includeFaults}
                onChange={setIncludeFaults}
                checkedChildren="Yes"
                unCheckedChildren="No"
              />
            </div>
          </Col>
        </Row>

        <Divider />

        <div className="generation-info">
          <p>
            <strong>Data Points to Generate:</strong>{" "}
            {numDays * numInverters * 8}
          </p>
          <p>
            <strong>Estimated Size:</strong> ~
            {Math.round(numDays * numInverters * 8 * 0.001)} KB
          </p>
        </div>

        {generating && (
          <div style={{ marginBottom: 16 }}>
            <Progress percent={100} status="active" showInfo={false} />
            <div style={{ textAlign: "center", marginTop: 8 }}>
              Generating synthetic data...
            </div>
          </div>
        )}

        <Button
          type="primary"
          icon={<DatabaseOutlined />}
          onClick={handleDataGeneration}
          loading={generating}
          disabled={isLoading}
          block
          size="large"
        >
          Generate Test Data
        </Button>
      </Card>

      <Card title="Model Management" className="model-card">
        <Alert
          message="Retrain fault detection models with new data"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <div className="model-info">
          <p>
            <strong>Current Model:</strong> Isolation Forest + Random Forest
          </p>
          <p>
            <strong>Training Time:</strong> ~2-5 minutes
          </p>
          <p>
            <strong>Status:</strong> Ready for retraining
          </p>
        </div>

        {retraining && (
          <div style={{ marginBottom: 16 }}>
            <Progress percent={100} status="active" showInfo={false} />
            <div style={{ textAlign: "center", marginTop: 8 }}>
              Retraining models in background...
            </div>
          </div>
        )}

        <Button
          type="default"
          icon={<ExperimentOutlined />}
          onClick={handleModelRetraining}
          loading={retraining}
          disabled={isLoading}
          block
          size="large"
        >
          Retrain Models
        </Button>
      </Card>

      <Card title="Quick Actions" className="actions-card">
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Button
              type="dashed"
              icon={<ReloadOutlined />}
              onClick={() => window.location.reload()}
              block
            >
              Reload Page
            </Button>
          </Col>
          <Col span={12}>
            <Button
              type="dashed"
              icon={<PlayCircleOutlined />}
              onClick={() => {
                handleDataGeneration();
                setTimeout(() => {
                  // Auto-trigger fault detection after data generation
                  window.dispatchEvent(new CustomEvent("autoDetectFaults"));
                }, 2000);
              }}
              loading={generating}
              disabled={isLoading}
              block
            >
              Quick Test
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default TestingPanel;
