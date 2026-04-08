import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Experiments from './pages/Experiments';
import NewExperiment from './pages/NewExperiment';
import ExperimentDetail from './pages/ExperimentDetail';
import Users from './pages/Users';
import BarcodeLookup from './pages/BarcodeLookup';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/experiments/new" element={<NewExperiment />} />
            <Route path="/experiments/:id" element={<ExperimentDetail />} />
            <Route path="/users" element={<Users />} />
            <Route path="/barcode" element={<BarcodeLookup />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
