import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import AgentsPage from './pages/AgentsPage';
import AgentDetailPage from './pages/AgentDetailPage';
import ActivityPage from './pages/ActivityPage';
import ApprovalsPage from './pages/ApprovalsPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface-alt">
        <Navbar />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/agents/:name" element={<AgentDetailPage />} />
          <Route path="/activity" element={<ActivityPage />} />
          <Route path="/approvals" element={<ApprovalsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
