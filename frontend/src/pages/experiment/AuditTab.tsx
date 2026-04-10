import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { Activity, ChevronRight } from 'lucide-react';
import { getAuditLog } from '../../api/endpoints';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';

const ACTION_STYLES: Record<string, string> = {
  create: 'bg-green-100 text-green-700',
  update: 'bg-blue-100 text-blue-700',
  delete: 'bg-red-100 text-red-700',
  status_change: 'bg-purple-100 text-purple-700',
  sign: 'bg-indigo-100 text-indigo-700',
  login: 'bg-gray-100 text-gray-600',
};

interface Props {
  experimentId: string;
}

export default function AuditTab({ experimentId }: Props) {
  const { data: logs = [], isLoading, error } = useQuery({
    queryKey: ['audit', experimentId],
    queryFn: () => getAuditLog(experimentId),
  });

  if (isLoading) return <LoadingSpinner className="py-10" />;
  if (error) return <ErrorMessage message={(error as Error).message} />;

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-900">Audit Log ({logs.length})</h3>
      </div>

      {logs.length === 0 ? (
        <div className="py-10 text-center">
          <Activity size={28} className="text-gray-300 mx-auto mb-2" />
          <p className="text-sm text-gray-400">No audit entries</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-50">
          {logs.map(log => (
            <div key={log.id} className="px-5 py-3.5 flex items-start gap-4">
              <div className="w-1.5 h-1.5 rounded-full bg-gray-300 mt-2 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-gray-900">{log.actor_username}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${ACTION_STYLES[log.action] ?? 'bg-gray-100 text-gray-600'}`}
                  >
                    {log.action.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-gray-500">{log.entity_type}</span>
                  {log.new_value && (
                    <span className="flex items-center gap-1 text-xs text-gray-400">
                      <ChevronRight size={12} />
                      {JSON.stringify(log.new_value).slice(0, 80)}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-0.5">
                  {log.old_value && (
                    <span className="text-xs text-gray-400 line-through">
                      {JSON.stringify(log.old_value).slice(0, 60)}
                    </span>
                  )}
                  <span className="text-xs text-gray-400">
                    {format(new Date(log.timestamp), 'MMM d, yyyy HH:mm')}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
