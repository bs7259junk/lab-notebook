import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { Plus, FlaskConical, Search, X } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getExperiments, getProjects } from '../api/endpoints';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import PageHeader from '../components/PageHeader';
import type { ExperimentStatus } from '../types';

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'active', label: 'Active' },
  { value: 'completed', label: 'Completed' },
  { value: 'signed', label: 'Signed' },
  { value: 'in_review', label: 'In Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'archived', label: 'Archived' },
];

export default function Experiments() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [status, setStatus] = useState(searchParams.get('status') || '');
  const [projectId, setProjectId] = useState(searchParams.get('project_id') || '');
  const [debouncedSearch, setDebouncedSearch] = useState(search);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  // Keep URL params in sync
  useEffect(() => {
    const params: Record<string, string> = {};
    if (debouncedSearch) params.search = debouncedSearch;
    if (status) params.status = status;
    if (projectId) params.project_id = projectId;
    setSearchParams(params, { replace: true });
  }, [debouncedSearch, status, projectId, setSearchParams]);

  const { data: experiments = [], isLoading, error } = useQuery({
    queryKey: ['experiments', { search: debouncedSearch, status, project_id: projectId }],
    queryFn: () =>
      getExperiments({
        search: debouncedSearch || undefined,
        status: status || undefined,
        project_id: projectId || undefined,
      }),
  });

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  function clearFilters() {
    setSearch('');
    setStatus('');
    setProjectId('');
    setDebouncedSearch('');
  }

  const hasFilters = !!(debouncedSearch || status || projectId);

  if (error) return <div className="p-8"><ErrorMessage message={(error as Error).message} /></div>;

  return (
    <div className="p-8">
      <PageHeader
        title="Experiments"
        subtitle={`${experiments.length} experiment${experiments.length !== 1 ? 's' : ''}`}
        actions={
          <Link
            to="/experiments/new"
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} />
            New Experiment
          </Link>
        }
      />

      {/* Filters */}
      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search experiments…"
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <select
          value={status}
          onChange={e => setStatus(e.target.value)}
          className="px-3.5 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          {STATUS_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <select
          value={projectId}
          onChange={e => setProjectId(e.target.value)}
          className="px-3.5 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">All Projects</option>
          {projects.map(p => (
            <option key={p.id} value={p.id}>{p.title}</option>
          ))}
        </select>

        {hasFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <X size={14} /> Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner size="lg" className="py-16" />
        ) : experiments.length === 0 ? (
          <div className="py-16 text-center">
            <FlaskConical size={36} className="text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-medium text-gray-600 mb-1">
              {hasFilters ? 'No matching experiments' : 'No experiments yet'}
            </h3>
            {hasFilters ? (
              <button
                onClick={clearFilters}
                className="text-sm text-indigo-600 hover:text-indigo-700 mt-1"
              >
                Clear filters
              </button>
            ) : (
              <Link
                to="/experiments/new"
                className="text-sm text-indigo-600 hover:text-indigo-700 mt-1 inline-block"
              >
                Create your first experiment
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium text-gray-500 uppercase tracking-wide bg-gray-50">
                  <th className="text-left px-6 py-3">Experiment ID</th>
                  <th className="text-left px-6 py-3">Title</th>
                  <th className="text-left px-6 py-3">Project</th>
                  <th className="text-left px-6 py-3">Status</th>
                  <th className="text-left px-6 py-3">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {experiments.map(exp => {
                  const project = projects.find(p => p.id === exp.project_id);
                  return (
                    <tr key={exp.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-3.5 font-mono text-xs text-gray-500">{exp.experiment_id}</td>
                      <td className="px-6 py-3.5">
                        <Link
                          to={`/experiments/${exp.id}`}
                          className="font-medium text-gray-900 hover:text-indigo-600 transition-colors"
                        >
                          {exp.title}
                        </Link>
                      </td>
                      <td className="px-6 py-3.5 text-gray-500">
                        {project ? (
                          <Link
                            to={`/projects/${project.id}`}
                            className="hover:text-indigo-600 transition-colors"
                          >
                            {project.title}
                          </Link>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-6 py-3.5">
                        <StatusBadge status={exp.status as ExperimentStatus} size="sm" />
                      </td>
                      <td className="px-6 py-3.5 text-gray-500">
                        {formatDistanceToNow(new Date(exp.updated_at), { addSuffix: true })}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
