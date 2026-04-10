import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import { User, Calendar, Hash, Barcode, ChevronRight } from 'lucide-react';
import { transitionStatus, signExperiment } from '../../api/endpoints';
import StatusBadge from '../../components/StatusBadge';
import Modal from '../../components/Modal';
import ErrorMessage from '../../components/ErrorMessage';
import type { ExperimentDetail, ExperimentStatus } from '../../types';

interface StatusTransition {
  targetStatus: ExperimentStatus;
  label: string;
  style: string;
  requiresSignature?: boolean;
}

function getTransitions(status: ExperimentStatus): StatusTransition[] {
  switch (status) {
    case 'draft':
      return [{ targetStatus: 'active', label: 'Start Experiment', style: 'bg-blue-600 hover:bg-blue-700 text-white' }];
    case 'active':
      return [{ targetStatus: 'completed', label: 'Mark Complete', style: 'bg-green-600 hover:bg-green-700 text-white' }];
    case 'completed':
      return [{ targetStatus: 'signed', label: 'Sign Experiment', style: 'bg-purple-600 hover:bg-purple-700 text-white', requiresSignature: true }];
    case 'signed':
      return [{ targetStatus: 'in_review', label: 'Submit for Review', style: 'bg-yellow-600 hover:bg-yellow-700 text-white' }];
    case 'in_review':
      return [
        { targetStatus: 'approved', label: 'Approve', style: 'bg-emerald-600 hover:bg-emerald-700 text-white' },
        { targetStatus: 'draft', label: 'Return', style: 'bg-red-100 hover:bg-red-200 text-red-700' },
      ];
    case 'approved':
      return [{ targetStatus: 'archived', label: 'Archive', style: 'bg-gray-600 hover:bg-gray-700 text-white' }];
    default:
      return [];
  }
}

interface MetaRowProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}

function MetaRow({ icon, label, value }: MetaRowProps) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-gray-50 last:border-0">
      <div className="text-gray-400 mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 mb-0.5">{label}</p>
        <div className="text-sm font-medium text-gray-900">{value}</div>
      </div>
    </div>
  );
}

interface Props {
  experiment: ExperimentDetail;
}

export default function OverviewTab({ experiment }: Props) {
  const queryClient = useQueryClient();
  const [showSignModal, setShowSignModal] = useState(false);
  const [signMeaning, setSignMeaning] = useState('');
  const [transitionComment, setTransitionComment] = useState('');
  const [pendingTransition, setPendingTransition] = useState<StatusTransition | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [transitionError, setTransitionError] = useState('');

  const transitions = getTransitions(experiment.status as ExperimentStatus);

  const transitionMutation = useMutation({
    mutationFn: ({ target, comment }: { target: string; comment?: string }) =>
      transitionStatus(experiment.id, target, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiment', experiment.id] });
      setShowConfirm(false);
      setPendingTransition(null);
      setTransitionComment('');
      setTransitionError('');
    },
    onError: (err: Error) => setTransitionError(err.message),
  });

  const signMutation = useMutation({
    mutationFn: () =>
      signExperiment(experiment.id, 'electronic', signMeaning || 'I certify this experiment is accurate'),
    onSuccess: () => {
      // After signing, transition to signed status
      transitionMutation.mutate({ target: 'signed' });
      setShowSignModal(false);
      setSignMeaning('');
    },
    onError: (err: Error) => setTransitionError(err.message),
  });

  function handleTransitionClick(t: StatusTransition) {
    setTransitionError('');
    if (t.requiresSignature) {
      setShowSignModal(true);
    } else {
      setPendingTransition(t);
      setShowConfirm(true);
    }
  }

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* Metadata */}
      <div className="col-span-2 space-y-4">
        {/* Purpose */}
        {experiment.purpose && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Purpose</h3>
            <p className="text-gray-700 text-sm leading-relaxed">{experiment.purpose}</p>
          </div>
        )}

        {/* Details */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Details</h3>
          <MetaRow
            icon={<Hash size={16} />}
            label="Experiment ID"
            value={<span className="font-mono">{experiment.experiment_id}</span>}
          />
          <MetaRow
            icon={<Calendar size={16} />}
            label="Created"
            value={format(new Date(experiment.created_at), 'PPP p')}
          />
          <MetaRow
            icon={<Calendar size={16} />}
            label="Last Updated"
            value={format(new Date(experiment.updated_at), 'PPP p')}
          />
          {experiment.barcode && (
            <MetaRow
              icon={<Barcode size={16} />}
              label="Inventory Barcode"
              value={<span className="font-mono">{experiment.barcode}</span>}
            />
          )}
          <MetaRow
            icon={<Hash size={16} />}
            label="Version"
            value={`v${experiment.version}`}
          />
        </div>

        {/* Participants */}
        {experiment.participants && experiment.participants.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Participants</h3>
            <div className="space-y-2">
              {experiment.participants.map(p => (
                <div key={p.id} className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center">
                    <User size={14} className="text-indigo-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {p.role}
                    </p>
                    <p className="text-xs text-gray-400">User {p.user_id.slice(0, 8)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Status panel */}
      <div className="space-y-4">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Status</h3>
          <StatusBadge status={experiment.status} />

          {transitions.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs text-gray-500 mb-2">Available Actions</p>
              {transitions.map(t => (
                <button
                  key={t.targetStatus}
                  onClick={() => handleTransitionClick(t)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${t.style}`}
                >
                  {t.label}
                  <ChevronRight size={14} />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Sign Modal */}
      {showSignModal && (
        <Modal title="Sign Experiment" onClose={() => setShowSignModal(false)}>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              By signing, you certify that the information in this experiment record is accurate and complete.
            </p>
            {transitionError && <ErrorMessage message={transitionError} />}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Signature Meaning</label>
              <input
                type="text"
                value={signMeaning}
                onChange={e => setSignMeaning(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="e.g. I certify this experiment is accurate"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowSignModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => signMutation.mutate()}
                disabled={signMutation.isPending || transitionMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 rounded-lg transition-colors"
              >
                {signMutation.isPending || transitionMutation.isPending ? 'Signing…' : 'Sign & Submit'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Confirm Transition Modal */}
      {showConfirm && pendingTransition && (
        <Modal title="Confirm Status Change" onClose={() => setShowConfirm(false)}>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Are you sure you want to change the status to{' '}
              <strong>{pendingTransition.targetStatus.replace('_', ' ')}</strong>?
            </p>
            {transitionError && <ErrorMessage message={transitionError} />}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Comment (optional)</label>
              <textarea
                value={transitionComment}
                onChange={e => setTransitionComment(e.target.value)}
                rows={2}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                placeholder="Add a comment about this status change…"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  transitionMutation.mutate({
                    target: pendingTransition.targetStatus,
                    comment: transitionComment || undefined,
                  })
                }
                disabled={transitionMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
              >
                {transitionMutation.isPending ? 'Updating…' : 'Confirm'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
