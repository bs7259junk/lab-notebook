import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { PenLine, Shield } from 'lucide-react';
import { format } from 'date-fns';
import { signExperiment, getSignatures } from '../../api/endpoints';
import { useQuery } from '@tanstack/react-query';
import ErrorMessage from '../../components/ErrorMessage';
import Modal from '../../components/Modal';
import LoadingSpinner from '../../components/LoadingSpinner';
import type { Signature } from '../../types';

interface Props {
  experimentId: number;
}

export default function SignaturesTab({ experimentId }: Props) {
  const queryClient = useQueryClient();
  const [showSignModal, setShowSignModal] = useState(false);
  const [signType, setSignType] = useState('electronic');
  const [meaning, setMeaning] = useState('');
  const [signError, setSignError] = useState('');

  const { data: signatures = [], isLoading } = useQuery({
    queryKey: ['signatures', experimentId],
    queryFn: () => getSignatures(experimentId),
  });

  const signMutation = useMutation({
    mutationFn: () =>
      signExperiment(
        experimentId,
        signType,
        meaning || 'I certify this record is accurate and complete'
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signatures', experimentId] });
      queryClient.invalidateQueries({ queryKey: ['experiment', experimentId] });
      setShowSignModal(false);
      setMeaning('');
      setSignError('');
    },
    onError: (err: Error) => setSignError(err.message),
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Signatures</h3>
        <button
          onClick={() => setShowSignModal(true)}
          className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
        >
          <PenLine size={16} />
          Sign
        </button>
      </div>

      {/* Signatures List */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner className="py-10" />
        ) : signatures.length === 0 ? (
          <div className="py-10 text-center">
            <Shield size={28} className="text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No signatures yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {signatures.map(sig => (
              <div key={sig.id} className="p-5 flex items-start gap-4">
                <div className="bg-purple-100 rounded-full p-2 flex-shrink-0">
                  <PenLine size={16} className="text-purple-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {sig.signer?.full_name || sig.signer?.username || `User #${sig.signer_id}`}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">{sig.meaning}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-400">
                      {format(new Date(sig.signed_at), 'PPP p')}
                    </span>
                    <span className="text-xs text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100">
                      {sig.signature_type}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sign Modal */}
      {showSignModal && (
        <Modal title="Sign Experiment" onClose={() => setShowSignModal(false)}>
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                By applying your signature, you are confirming the authenticity and accuracy of this record.
              </p>
            </div>
            {signError && <ErrorMessage message={signError} />}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Signature Type</label>
              <select
                value={signType}
                onChange={e => setSignType(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="electronic">Electronic Signature</option>
                <option value="witness">Witness Signature</option>
                <option value="review">Reviewer Signature</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Meaning</label>
              <input
                type="text"
                value={meaning}
                onChange={e => setMeaning(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="I certify this record is accurate and complete"
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
                disabled={signMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 rounded-lg transition-colors"
              >
                <PenLine size={14} />
                {signMutation.isPending ? 'Signing…' : 'Apply Signature'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
