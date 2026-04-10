import { useState} from 'react';
import type { FormEvent } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { createExperiment, getProjects } from '../api/endpoints';
import PageHeader from '../components/PageHeader';
import ErrorMessage from '../components/ErrorMessage';

export default function NewExperiment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedProject = searchParams.get('project_id');

  const [title, setTitle] = useState('');
  const [purpose, setPurpose] = useState('');
  const [projectId, setProjectId] = useState(preselectedProject || '');
  const [formError, setFormError] = useState('');

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const mutation = useMutation({
    mutationFn: () =>
      createExperiment({
        title,
        purpose: purpose || undefined,
        project_id: projectId || undefined,
      }),
    onSuccess: (exp) => {
      navigate(`/experiments/${exp.id}`);
    },
    onError: (err: Error) => setFormError(err.message),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!title.trim()) { setFormError('Title is required'); return; }
    setFormError('');
    mutation.mutate();
  }

  return (
    <div className="p-8 max-w-2xl">
      <Link
        to="/experiments"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 mb-6 transition-colors"
      >
        <ArrowLeft size={14} />
        Back to Experiments
      </Link>

      <PageHeader title="New Experiment" subtitle="Create a new laboratory experiment" />

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        {formError && <ErrorMessage message={formError} className="mb-4" />}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
              autoFocus
              className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter experiment title"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Purpose</label>
            <textarea
              value={purpose}
              onChange={e => setPurpose(e.target.value)}
              rows={4}
              className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
              placeholder="Describe the purpose of this experiment…"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Project</label>
            <select
              value={projectId}
              onChange={e => setProjectId(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">No project</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-100">
            <Link
              to="/experiments"
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
            >
              {mutation.isPending ? 'Creating…' : 'Create Experiment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
