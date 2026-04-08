import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FlaskConical, FolderOpen, CheckCircle2, Clock, ArrowRight, PlusCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getExperiments } from '../api/endpoints';
import { getProjects } from '../api/endpoints';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import type { ExperimentStatus } from '../types';

const STATUS_ORDER: ExperimentStatus[] = [
  'draft', 'active', 'completed', 'signed', 'in_review', 'approved', 'archived',
];

const STATUS_COLORS: Record<ExperimentStatus, string> = {
  draft: 'bg-slate-50 border-slate-200',
  active: 'bg-blue-50 border-blue-200',
  completed: 'bg-green-50 border-green-200',
  signed: 'bg-purple-50 border-purple-200',
  in_review: 'bg-yellow-50 border-yellow-200',
  approved: 'bg-emerald-50 border-emerald-200',
  archived: 'bg-gray-50 border-gray-200',
};

const STATUS_ICON_COLORS: Record<ExperimentStatus, string> = {
  draft: 'text-slate-500',
  active: 'text-blue-500',
  completed: 'text-green-500',
  signed: 'text-purple-500',
  in_review: 'text-yellow-500',
  approved: 'text-emerald-500',
  archived: 'text-gray-400',
};

export default function Dashboard() {
  const { data: experiments = [], isLoading: expsLoading } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => getExperiments(),
  });

  const { data: projects = [], isLoading: projLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const statusCounts = STATUS_ORDER.reduce<Record<string, number>>((acc, s) => {
    acc[s] = experiments.filter(e => e.status === s).length;
    return acc;
  }, {});

  const recentExperiments = [...experiments]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 10);

  const activeCount = experiments.filter(e => e.status === 'active').length;
  const pendingReviewCount = experiments.filter(e => e.status === 'in_review').length;

  if (expsLoading || projLoading) {
    return (
      <div className="p-8">
        <LoadingSpinner size="lg" className="mt-16" />
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Overview of your laboratory notebook</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 rounded-lg p-2.5">
              <FlaskConical size={20} className="text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{experiments.length}</p>
              <p className="text-sm text-gray-500">Total Experiments</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-100 rounded-lg p-2.5">
              <Clock size={20} className="text-indigo-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{activeCount}</p>
              <p className="text-sm text-gray-500">Active Experiments</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3">
            <div className="bg-green-100 rounded-lg p-2.5">
              <FolderOpen size={20} className="text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">{projects.length}</p>
              <p className="text-sm text-gray-500">Projects</p>
            </div>
          </div>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Experiments by Status</h2>
        <div className="grid grid-cols-4 gap-3">
          {STATUS_ORDER.map(status => (
            <Link
              key={status}
              to={`/experiments?status=${status}`}
              className={`rounded-lg border p-4 transition-shadow hover:shadow-sm ${STATUS_COLORS[status]}`}
            >
              <p className={`text-2xl font-bold ${STATUS_ICON_COLORS[status]}`}>
                {statusCounts[status] || 0}
              </p>
              <p className="text-xs text-gray-600 mt-0.5 capitalize">{status.replace('_', ' ')}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Recent Experiments */}
        <div className="col-span-2 bg-white rounded-xl border border-gray-200">
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <h2 className="text-base font-semibold text-gray-900">Recent Experiments</h2>
            <Link
              to="/experiments"
              className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              View all <ArrowRight size={14} />
            </Link>
          </div>
          <div className="divide-y divide-gray-50">
            {recentExperiments.length === 0 ? (
              <p className="px-6 py-8 text-sm text-gray-400 text-center">No experiments yet</p>
            ) : (
              recentExperiments.map(exp => (
                <Link
                  key={exp.id}
                  to={`/experiments/${exp.id}`}
                  className="flex items-center justify-between px-6 py-3.5 hover:bg-gray-50 transition-colors"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{exp.title}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {exp.experiment_id} · Updated {formatDistanceToNow(new Date(exp.updated_at), { addSuffix: true })}
                    </p>
                  </div>
                  <StatusBadge status={exp.status} size="sm" />
                </Link>
              ))
            )}
          </div>
        </div>

        {/* Quick Links */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="text-base font-semibold text-gray-900 mb-3">Quick Actions</h2>
            <div className="space-y-2">
              <Link
                to="/experiments/new"
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors"
              >
                <PlusCircle size={16} />
                New Experiment
              </Link>
              <Link
                to="/projects"
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <FolderOpen size={16} />
                Manage Projects
              </Link>
              <Link
                to="/barcode"
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <CheckCircle2 size={16} />
                Barcode Lookup
              </Link>
            </div>
          </div>

          {pendingReviewCount > 0 && (
            <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-5">
              <h2 className="text-sm font-semibold text-yellow-800 mb-1">Pending Reviews</h2>
              <p className="text-2xl font-bold text-yellow-700">{pendingReviewCount}</p>
              <p className="text-xs text-yellow-600 mt-1">experiments waiting for review</p>
              <Link
                to="/experiments?status=in_review"
                className="mt-3 text-xs font-medium text-yellow-700 hover:text-yellow-800 flex items-center gap-1"
              >
                View experiments <ArrowRight size={12} />
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
