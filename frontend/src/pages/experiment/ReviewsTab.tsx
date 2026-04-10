import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { UserCheck, CheckCircle, XCircle, Plus } from 'lucide-react';
import { format } from 'date-fns';
import { getUsers, createReview, updateReview, getReviews } from '../../api/endpoints';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import Modal from '../../components/Modal';
import type { Review } from '../../types';

const REVIEW_STATUS_STYLES: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  in_review: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-emerald-100 text-emerald-700',
  returned: 'bg-red-100 text-red-700',
};

interface Props {
  experimentId: string;
}

export default function ReviewsTab({ experimentId }: Props) {
  const queryClient = useQueryClient();
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [selectedReviewerId, setSelectedReviewerId] = useState('');
  const [requestError, setRequestError] = useState('');
  const [actionError, setActionError] = useState('');
  const [reviewComments, setReviewComments] = useState<Record<string, string>>({});

  const { data: reviews = [], isLoading } = useQuery({
    queryKey: ['reviews', experimentId],
    queryFn: () => getReviews(experimentId),
  });

  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  });

  const requestMutation = useMutation({
    mutationFn: () => createReview(experimentId, selectedReviewerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews', experimentId] });
      setShowRequestModal(false);
      setSelectedReviewerId('');
      setRequestError('');
    },
    onError: (err: Error) => setRequestError(err.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ reviewId, status, comments }: { reviewId: string; status: string; comments?: string }) =>
      updateReview(reviewId, { status, comments }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews', experimentId] });
      queryClient.invalidateQueries({ queryKey: ['experiment', experimentId] });
      setActionError('');
    },
    onError: (err: Error) => setActionError(err.message),
  });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Reviews</h3>
        <button
          onClick={() => setShowRequestModal(true)}
          className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
        >
          <Plus size={16} />
          Request Review
        </button>
      </div>

      {actionError && <ErrorMessage message={actionError} />}

      {/* Reviews List */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {isLoading ? (
          <LoadingSpinner className="py-10" />
        ) : reviews.length === 0 ? (
          <div className="py-10 text-center">
            <UserCheck size={28} className="text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No reviews yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {reviews.map(review => {
              const reviewer = users.find(u => u.id === review.reviewer_id);
              return (
                <div key={review.id} className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-gray-900">
                          {reviewer?.full_name || reviewer?.username || `Reviewer #${review.reviewer_id}`}
                        </p>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${REVIEW_STATUS_STYLES[review.status] ?? 'bg-gray-100 text-gray-600'}`}>
                          {review.status.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400">
                        Requested {format(new Date(review.created_at), 'MMM d, yyyy')}
                      </p>
                      {review.comments && (
                        <p className="mt-2 text-sm text-gray-600 italic">"{review.comments}"</p>
                      )}
                    </div>
                  </div>

                  {/* Review Actions */}
                  {review.status === 'pending' || review.status === 'in_review' ? (
                    <div className="mt-3 space-y-2">
                      <textarea
                        value={reviewComments[review.id] ?? ''}
                        onChange={e => setReviewComments(prev => ({ ...prev, [review.id]: e.target.value }))}
                        rows={2}
                        placeholder="Add review comments (optional)…"
                        className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                      />
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() =>
                            updateMutation.mutate({
                              reviewId: review.id,
                              status: 'approved',
                              comments: reviewComments[review.id],
                            })
                          }
                          disabled={updateMutation.isPending}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-white bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 rounded-lg transition-colors"
                        >
                          <CheckCircle size={14} />
                          Approve
                        </button>
                        <button
                          onClick={() =>
                            updateMutation.mutate({
                              reviewId: review.id,
                              status: 'returned',
                              comments: reviewComments[review.id],
                            })
                          }
                          disabled={updateMutation.isPending}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-white bg-red-600 hover:bg-red-700 disabled:bg-red-400 rounded-lg transition-colors"
                        >
                          <XCircle size={14} />
                          Return
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Request Review Modal */}
      {showRequestModal && (
        <Modal title="Request Review" onClose={() => setShowRequestModal(false)}>
          <div className="space-y-4">
            {requestError && <ErrorMessage message={requestError} />}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Select Reviewer</label>
              <select
                value={selectedReviewerId}
                onChange={e => setSelectedReviewerId(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-gray-300 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">Choose a reviewer…</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>
                    {u.full_name || u.username} ({u.email})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowRequestModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => requestMutation.mutate()}
                disabled={requestMutation.isPending || !selectedReviewerId}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
              >
                {requestMutation.isPending ? 'Requesting…' : 'Request Review'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
