import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FlaskConical, ArrowLeft, PlusCircle, FolderOpen } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getProject, getExperiments } from '../api/endpoints';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = id ?? '';

  const { data: project, isLoading: projLoading, error: projError } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId),
    enabled: !!projectId,
  });

  const { data: experiments = [], isLoading: expsLoading } = useQuery({
    queryKey: ['experiments', { project_id: projectId }],
    queryFn: () => getExperiments({ project_id: projectId }),
    enabled: !!projectId,
  });

  if (projLoading || expsLoading) {
    return <div className="p-8"><LoadingSpinner size="lg" className="mt-16" /></div>;
  }

  if (projError) {
    return <div className="p-8"><ErrorMessage message={(projError as Error).message} /></div>;
  }

  if (!project) {
    return <div className="p-8"><ErrorMessage message="Project not found" /></div>;
  }

  return (
    <div className="p-8">
      {/* Back link */}
      <Link
        to="/projects"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 mb-6 transition-colors"
      >
        <ArrowLeft size={14} />
        Back to Projects
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="bg-indigo-100 rounded-xl p-3">
            <FolderOpen size={24} className="text-indigo-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-gray-900">{project.title}</h1>
              <span className="text-sm text-gray-400 font-mono">{project.project_code}</span>
            </div>
            {project.description && (
              <p className="text-gray-600 mb-3">{project.description}</p>
            )}
            <div className="flex items-center gap-4 text-xs text-gray-400">
              <span>Created {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}</span>
              <span>Updated {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}</span>
            </div>
          </div>
          <Link
            to={`/experiments/new?project_id=${project.id}`}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <PlusCircle size={16} />
            New Experiment
          </Link>
        </div>
      </div>

      {/* Experiments */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            Experiments ({experiments.length})
          </h2>
        </div>

        {experiments.length === 0 ? (
          <div className="p-16 text-center">
            <FlaskConical size={36} className="text-gray-300 mx-auto mb-3" />
            <h3 className="text-sm font-medium text-gray-600 mb-1">No experiments in this project</h3>
            <p className="text-sm text-gray-400 mb-4">Start by creating a new experiment</p>
            <Link
              to={`/experiments/new?project_id=${project.id}`}
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              <PlusCircle size={16} />
              New Experiment
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  <th className="text-left px-6 py-3">ID</th>
                  <th className="text-left px-6 py-3">Title</th>
                  <th className="text-left px-6 py-3">Status</th>
                  <th className="text-left px-6 py-3">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {experiments.map(exp => (
                  <tr key={exp.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-3.5 font-mono text-gray-500">{exp.experiment_id}</td>
                    <td className="px-6 py-3.5">
                      <Link
                        to={`/experiments/${exp.id}`}
                        className="font-medium text-gray-900 hover:text-indigo-600 transition-colors"
                      >
                        {exp.title}
                      </Link>
                    </td>
                    <td className="px-6 py-3.5">
                      <StatusBadge status={exp.status} size="sm" />
                    </td>
                    <td className="px-6 py-3.5 text-gray-500">
                      {formatDistanceToNow(new Date(exp.updated_at), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
