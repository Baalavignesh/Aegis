import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DemoPage from './pages/DemoPage';
import ChatPage from './pages/ChatPage';
import ScenarioPage from './pages/ScenarioPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface-alt">
        <Routes>
          <Route path="/" element={<DemoPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/scenario/:agentKey" element={<ScenarioPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
