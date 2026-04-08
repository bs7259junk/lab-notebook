import type { ExperimentStatus } from '../types';

const STATUS_STYLES: Record<ExperimentStatus, string> = {
  draft: 'bg-slate-100 text-slate-700 border-slate-200',
  active: 'bg-blue-100 text-blue-700 border-blue-200',
  completed: 'bg-green-100 text-green-700 border-green-200',
  signed: 'bg-purple-100 text-purple-700 border-purple-200',
  in_review: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  approved: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  archived: 'bg-gray-100 text-gray-600 border-gray-200',
};

const STATUS_LABELS: Record<ExperimentStatus, string> = {
  draft: 'Draft',
  active: 'Active',
  completed: 'Completed',
  signed: 'Signed',
  in_review: 'In Review',
  approved: 'Approved',
  archived: 'Archived',
};

interface Props {
  status: ExperimentStatus | string;
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, size = 'md' }: Props) {
  const styles = STATUS_STYLES[status as ExperimentStatus] ?? 'bg-gray-100 text-gray-600 border-gray-200';
  const label = STATUS_LABELS[status as ExperimentStatus] ?? status;
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1';

  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${styles} ${sizeClass}`}>
      {label}
    </span>
  );
}
