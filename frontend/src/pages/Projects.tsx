import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, FolderOpen, ChevronRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getProjects, createProject } from '../api/endpoints';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Modal from '../components/Modal';

export default function Projects() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState('');

  const { data: projects = [], isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const createMutation = useMutation({
    mutationFn: () => createProject({ title, description: description || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowCreate(false);
      setTitle('');
      setDescription('');
      setFormError('');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) { setFormError('Title is required'); return; }
    createMutation.mutate();
  }

  if (isLoading) return <div className="p-8"><LoadingSpinner size="lg" className="mt-16" /></div>;
  if (error) return <div className="p-8"><ErrorMessage message={(error as Error).message} /></div>;

  return (
    <div className="p-8">
      <PageHeader
        title="Projects"
        subtitle={`${projects.length} project${projects.length !== 1 ? 's' : ''}`}
        actions={
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} />
            New Project
          </button>
        }
      />

      {projects.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <FolderOpen size={40} className="text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-medium text-gray-700 mb-1">No projects yet</h3>
          <p className="text-sm text-gray-400 mb-4">Create a project to organize your experiments</p>
          <button
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} />
            New Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map(project => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow group"
            >
              <div className="flex items-start justify-between">
                <div className="bg-indigo-100 rounded-lg p-2 mb-3">
                  <FolderOpen size={18} className="text-indigo-600" />
                </div>
                <ChevronRight size={16} className="text-gray-300 group-hover:text-indigo-400 transition-colors mt-1" />
              </div>
              <h3 className="font-semibold text-gray-900 text-base mb-1">{project.title}</h3>
              {project.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">{project.description}</p>
              )}
              <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-50">
                <span className="text-xs text-gray-400 font-mono">{project.project_id}</span>
                <span className="text-xs text-gray-400">
                  {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {showCreate && (
        <Modal title="New Project" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            {formError && <ErrorMessage message={formError} />}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Title *</label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                required
                autoFocus
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Project title"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={3}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                placeholder="Optional project description"
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
              >
                {createMutation.isPending ? 'Creating…' : 'Create Project'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
