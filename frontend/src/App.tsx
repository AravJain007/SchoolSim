import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './layout';
import WelcomePage from './pages/WelcomePage';
import SetupPage from './pages/SetupPage';
import SimulationPage from './pages/SimulationPage';
import ResultsPage from './pages/ResultsPage';
import Dashboard from './pages/Dashboard';
import SimulationDetailPage from './pages/SimulationDetail';
import Analytics from './pages/Analytics';
import StudentBig5Page from './pages/StudentBig5Page';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route element={<Layout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="setup" element={<SetupPage />} />
          <Route path="simulation/:id" element={<SimulationPage />} />
          <Route path="simulation/:id/detail" element={<SimulationDetailPage />} />
          <Route path="results/:id" element={<ResultsPage />} />
          <Route path="big5" element={<StudentBig5Page />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
