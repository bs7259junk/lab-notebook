import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, FolderOpen, ChevronRight, Pencil } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getProjects, createProject, updateProject } from '../api/endpoints';
import PageHeader from '../components/PageHeader';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import Modal from '../components/Modal';
import type { Project } from '../types';

export default function Projects() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [projectCode, setProjectCode] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState('');
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editError, setEditError] = useState('');

  const { data: projects = [], isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const createMutation = useMutation({
    mutationFn: () => createProject({ project_code: projectCode.toUpperCase(), title, description: description || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowCreate(false);
      setTitle('');
      setDescription('');
      setFormError('');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const editMutation = useMutation({
    mutationFn: () => updateProject(editingProject!.id, { title: editTitle, description: editDescription || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setEditingProject(null);
      setEditError('');
    },
    onError: (err: Error) => setEditError(err.message),
  });

  function openEdit(e: React.MouseEvent, project: Project) {
    e.preventDefault();
    e.stopPropagation();
    setEditingProject(project);
    setEditTitle(project.title);
    setEditDescription(project.description || '');
    setEditError('');
  }

  function handleEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editTitle.trim()) { setEditError('Title is required'); return; }
    editMutation.mutate();
  }

  function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!projectCode.trim()) { setFormError('Project code is required'); return; }
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
                <div className="flex items-center gap-2">
                  <button
                    onClick={e => openEdit(e, project)}
                    className="p-1.5 rounded-md text-gray-300 hover:text-indigo-500 hover:bg-indigo-50 transition-colors opacity-0 group-hover:opacity-100"
                    title="Edit project"
                  >
                    <Pencil size={14} />
                  </button>
                  <ChevronRight size={16} className="text-gray-300 group-hover:text-indigo-400 transition-colors mt-0.5" />
                </div>
              </div>
              <h3 className="font-semibold text-gray-900 text-base mb-1">{project.title}</h3>
              {project.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">{project.description}</p>
              )}
              <div className="flex items-center justify-between mt-auto pt-3 border-t border-gray-50">
                <span className="text-xs text-gray-400 font-mono">{project.project_code}</span>
                <span className="text-xs text-gray-400">
                  {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {editingProject && (
        <Modal title="Edit Project" onClose={() => setEditingProject(null)}>
          <form onSubmit={handleEdit} className="space-y-4">
            {editError && <ErrorMessage message={editError} />}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Title *</label>
              <input
                type="text"
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
                required
                autoFocus
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
              <textarea
                value={editDescription}
                onChange={e => setEditDescription(e.target.value)}
                rows={3}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setEditingProject(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={editMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
              >
                {editMutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {showCreate && (
        <Modal title="New Project" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            {formError && <ErrorMessage message={formError} />}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Project Code *</label>
              <input
                type="text"
                value={projectCode}
                onChange={e => setProjectCode(e.target.value)}
                required
                autoFocus
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 uppercase"
                placeholder="e.g. PROJ-001"
              />
            </div>
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
