import { ConfigProvider } from "antd";
import Dashboard from "./components/Dashboard";
import "antd/dist/reset.css";
import "./App.css";

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#1890ff",
          borderRadius: 4,
        },
      }}
    >
      <div className="App">
        <Dashboard />
      </div>
    </ConfigProvider>
  );
}

export default App;
