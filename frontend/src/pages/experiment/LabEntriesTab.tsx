import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ChevronDown, ChevronRight, Save, Edit3, CheckCircle } from 'lucide-react';
import { updateLabEntry } from '../../api/endpoints';
import ErrorMessage from '../../components/ErrorMessage';
import type { ExperimentDetail, LabEntry } from '../../types';

const SECTIONS = [
  { key: 'hypothesis', label: 'Purpose', placeholder: 'State the purpose of this experiment…' },
  { key: 'protocol', label: 'Protocol', placeholder: 'Describe the experimental protocol and procedures…' },
  { key: 'results', label: 'Results', placeholder: 'Record the results and observations…' },
  { key: 'observations', label: 'Observations', placeholder: 'Note any observations made during the experiment…' },
  { key: 'conclusions', label: 'Conclusions', placeholder: 'Summarize the conclusions drawn from the results…' },
];

interface SectionEditorProps {
  experimentId: string;
  section: string;
  label: string;
  placeholder: string;
  entry?: LabEntry;
}

function SectionEditor({ experimentId, section, label, placeholder, entry }: SectionEditorProps) {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(entry?.content ?? '');
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  const mutation = useMutation({
    mutationFn: () => updateLabEntry(experimentId, section, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiment', experimentId] });
      setIsEditing(false);
      setSaved(true);
      setError('');
      setTimeout(() => setSaved(false), 2500);
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleEdit() {
    setContent(entry?.content ?? '');
    setIsEditing(true);
    setIsOpen(true);
  }

  function handleCancel() {
    setContent(entry?.content ?? '');
    setIsEditing(false);
    setError('');
  }

  const hasContent = !!(entry?.content?.trim());

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-4 bg-white hover:bg-gray-50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          {isOpen ? (
            <ChevronDown size={16} className="text-gray-400" />
          ) : (
            <ChevronRight size={16} className="text-gray-400" />
          )}
          <span className="font-semibold text-gray-900">{label}</span>
          {saved && (
            <span className="flex items-center gap-1 text-xs text-green-600">
              <CheckCircle size={12} />
              Saved
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {hasContent && (
            <span className="text-xs text-gray-400">
              v{entry?.version ?? 1}
            </span>
          )}
          {!hasContent && <span className="text-xs text-gray-400">Empty</span>}
        </div>
      </button>

      {/* Content */}
      {isOpen && (
        <div className="px-5 py-4 border-t border-gray-100 bg-white">
          {error && <ErrorMessage message={error} className="mb-3" />}

          {isEditing ? (
            <div className="space-y-3">
              <textarea
                value={content}
                onChange={e => setContent(e.target.value)}
                rows={8}
                autoFocus
                className="w-full px-3.5 py-3 rounded-lg border border-gray-300 text-gray-900 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-y font-mono"
                placeholder={placeholder}
              />
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={handleCancel}
                  className="px-3.5 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => mutation.mutate()}
                  disabled={mutation.isPending}
                  className="flex items-center gap-2 px-3.5 py-1.5 text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
                >
                  <Save size={14} />
                  {mutation.isPending ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          ) : (
            <div>
              {hasContent ? (
                <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap font-mono">
                  {entry?.content}
                </p>
              ) : (
                <p className="text-sm text-gray-400 italic">{placeholder}</p>
              )}
              <div className="mt-3 pt-3 border-t border-gray-50 flex justify-end">
                <button
                  onClick={handleEdit}
                  className="flex items-center gap-2 px-3.5 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Edit3 size={14} />
                  {hasContent ? 'Edit' : 'Add Content'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface Props {
  experiment: ExperimentDetail;
}

export default function LabEntriesTab({ experiment }: Props) {
  const entriesBySection = (experiment.entries ?? []).reduce<Record<string, LabEntry>>(
    (acc, e) => { acc[e.section] = e; return acc; },
    {}
  );

  return (
    <div className="space-y-3">
      {SECTIONS.map(s => (
        <SectionEditor
          key={s.key}
          experimentId={experiment.id}
          section={s.key}
          label={s.label}
          placeholder={s.placeholder}
          entry={entriesBySection[s.key]}
        />
      ))}
    </div>
  );
}
