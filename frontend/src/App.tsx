import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Nav from './components/Nav';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Regulations from './pages/Regulations';
import RegulationDetail from './pages/RegulationDetail';
import Assessments from './pages/Assessments';
import AssessmentDetail from './pages/AssessmentDetail';
import Alerts from './pages/Alerts';
import AIAnalyzeRegulation from './pages/AIAnalyzeRegulation';
import AIRiskAssessment from './pages/AIRiskAssessment';
import AIGapAnalysis from './pages/AIGapAnalysis';
import AIGeneratePolicy from './pages/AIGeneratePolicy';
import AIHistory from './pages/AIHistory';
import AIChat from './pages/AIChat';
import AIBacklogTools from './pages/AIBacklogTools';
import CalendarPage from './pages/CalendarPage';
import Profile from './pages/Profile';
import ControlAttestationQueue from './pages/ControlAttestationQueue';

import CodexCustomVizFeature from './pages/CodexCustomVizFeature';
import CodexOperationsFeature from './pages/CodexOperationsFeature';

import TimelineView from './pages/TimelineView';

function Protected({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="container">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <>
      <Nav />
      <Routes>
        <Route path="/insights/timeline" element={<TimelineView />} />
        <Route path="/codex/custom-viz" element={<CodexCustomVizFeature />} />
        <Route path="/codex/operations" element={<CodexOperationsFeature />} />

        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Protected><Dashboard /></Protected>} />
        <Route path="/regulations" element={<Protected><Regulations /></Protected>} />
        <Route path="/regulations/:id" element={<Protected><RegulationDetail /></Protected>} />
        <Route path="/assessments" element={<Protected><Assessments /></Protected>} />
        <Route path="/assessments/:id" element={<Protected><AssessmentDetail /></Protected>} />
        <Route path="/alerts" element={<Protected><Alerts /></Protected>} />
        <Route path="/ai/analyze" element={<Protected><AIAnalyzeRegulation /></Protected>} />
        <Route path="/ai/risk" element={<Protected><AIRiskAssessment /></Protected>} />
        <Route path="/ai/gap" element={<Protected><AIGapAnalysis /></Protected>} />
        <Route path="/ai/policy" element={<Protected><AIGeneratePolicy /></Protected>} />
        <Route path="/ai/history" element={<Protected><AIHistory /></Protected>} />
        <Route path="/ai/chat" element={<Protected><AIChat /></Protected>} />
        <Route path="/ai/backlog-tools" element={<Protected><AIBacklogTools /></Protected>} />
        <Route path="/calendar" element={<Protected><CalendarPage /></Protected>} />
        <Route path="/profile" element={<Protected><Profile /></Protected>} />
        <Route path="/control-attestation-queue" element={<Protected><ControlAttestationQueue /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
