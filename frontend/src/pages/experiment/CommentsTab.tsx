import { useState} from 'react';
import type { FormEvent } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MessageCircle, Send, User, CornerDownRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { getComments, addComment } from '../../api/endpoints';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';
import type { Comment } from '../../types';

interface CommentItemProps {
  comment: Comment;
  experimentId: number;
  depth?: number;
}

function CommentItem({ comment, experimentId, depth = 0 }: CommentItemProps) {
  const queryClient = useQueryClient();
  const [showReply, setShowReply] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [replyError, setReplyError] = useState('');

  const replyMutation = useMutation({
    mutationFn: () => addComment(experimentId, replyContent, comment.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', experimentId] });
      setReplyContent('');
      setShowReply(false);
      setReplyError('');
    },
    onError: (err: Error) => setReplyError(err.message),
  });

  return (
    <div className={depth > 0 ? 'ml-8 border-l-2 border-gray-100 pl-4' : ''}>
      <div className="py-3">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0">
            <User size={14} className="text-indigo-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium text-gray-900">
                {comment.author?.full_name || comment.author?.username || `User #${comment.author_id}`}
              </span>
              <span className="text-xs text-gray-400">
                {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}
              </span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed">{comment.content}</p>
            {depth < 2 && (
              <button
                onClick={() => setShowReply(r => !r)}
                className="mt-1.5 flex items-center gap-1 text-xs text-gray-400 hover:text-indigo-600 transition-colors"
              >
                <CornerDownRight size={12} />
                Reply
              </button>
            )}
          </div>
        </div>

        {showReply && (
          <div className="ml-11 mt-2">
            {replyError && <ErrorMessage message={replyError} className="mb-2" />}
            <div className="flex gap-2">
              <textarea
                value={replyContent}
                onChange={e => setReplyContent(e.target.value)}
                rows={2}
                autoFocus
                className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                placeholder="Write a reply…"
              />
              <div className="flex flex-col gap-1">
                <button
                  onClick={() => {
                    if (!replyContent.trim()) return;
                    replyMutation.mutate();
                  }}
                  disabled={replyMutation.isPending || !replyContent.trim()}
                  className="px-3 py-2 text-xs text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 rounded-lg transition-colors"
                >
                  <Send size={13} />
                </button>
                <button
                  onClick={() => { setShowReply(false); setReplyContent(''); }}
                  className="px-3 py-2 text-xs text-gray-500 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface Props {
  experimentId: number;
}

export default function CommentsTab({ experimentId }: Props) {
  const queryClient = useQueryClient();
  const [content, setContent] = useState('');
  const [error, setError] = useState('');

  const { data: comments = [], isLoading } = useQuery({
    queryKey: ['comments', experimentId],
    queryFn: () => getComments(experimentId),
  });

  const addMutation = useMutation({
    mutationFn: () => addComment(experimentId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', experimentId] });
      setContent('');
      setError('');
    },
    onError: (err: Error) => setError(err.message),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    addMutation.mutate();
  }

  // Build comment tree
  const topLevel = comments.filter(c => !c.parent_id);
  const replies = comments.filter(c => c.parent_id);

  function getReplies(parentId: number): Comment[] {
    return replies.filter(r => r.parent_id === parentId);
  }

  return (
    <div className="space-y-4">
      {/* Add Comment */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Add Comment</h3>
        {error && <ErrorMessage message={error} className="mb-3" />}
        <form onSubmit={handleSubmit}>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            rows={3}
            className="w-full px-3.5 py-3 rounded-lg border border-gray-300 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
            placeholder="Write a comment…"
          />
          <div className="flex justify-end mt-2">
            <button
              type="submit"
              disabled={addMutation.isPending || !content.trim()}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 rounded-lg transition-colors"
            >
              <Send size={14} />
              {addMutation.isPending ? 'Posting…' : 'Post Comment'}
            </button>
          </div>
        </form>
      </div>

      {/* Comments List */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-900">Comments ({comments.length})</h3>
        </div>

        {isLoading ? (
          <LoadingSpinner className="py-10" />
        ) : topLevel.length === 0 ? (
          <div className="py-10 text-center">
            <MessageCircle size={28} className="text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No comments yet</p>
          </div>
        ) : (
          <div className="px-5 divide-y divide-gray-50">
            {topLevel.map(comment => (
              <div key={comment.id}>
                <CommentItem comment={comment} experimentId={experimentId} depth={0} />
                {getReplies(comment.id).map(reply => (
                  <CommentItem key={reply.id} comment={reply} experimentId={experimentId} depth={1} />
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
