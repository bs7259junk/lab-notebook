import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, FlaskConical } from 'lucide-react';
import { getExperiment } from '../api/endpoints';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import OverviewTab from './experiment/OverviewTab';
import LabEntriesTab from './experiment/LabEntriesTab';
import MaterialsTab from './experiment/MaterialsTab';
import AttachmentsTab from './experiment/AttachmentsTab';
import CommentsTab from './experiment/CommentsTab';
import ReviewsTab from './experiment/ReviewsTab';
import SignaturesTab from './experiment/SignaturesTab';
import AuditTab from './experiment/AuditTab';

const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'entries', label: 'Lab Entries' },
  { key: 'materials', label: 'Materials' },
  { key: 'attachments', label: 'Attachments' },
  { key: 'comments', label: 'Comments' },
  { key: 'reviews', label: 'Reviews' },
  { key: 'signatures', label: 'Signatures' },
  { key: 'audit', label: 'Audit' },
];

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();
  const experimentId = Number(id);
  const [activeTab, setActiveTab] = useState('overview');

  const { data: experiment, isLoading, error } = useQuery({
    queryKey: ['experiment', experimentId],
    queryFn: () => getExperiment(experimentId),
    enabled: !isNaN(experimentId),
    refetchOnWindowFocus: false,
  });

  if (isLoading) {
    return <div className="p-8"><LoadingSpinner size="lg" className="mt-16" /></div>;
  }

  if (error) {
    return <div className="p-8"><ErrorMessage message={(error as Error).message} /></div>;
  }

  if (!experiment) {
    return <div className="p-8"><ErrorMessage message="Experiment not found" /></div>;
  }

  return (
    <div className="p-8">
      {/* Back */}
      <Link
        to="/experiments"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 mb-6 transition-colors"
      >
        <ArrowLeft size={14} />
        Back to Experiments
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-start gap-4">
          <div className="bg-indigo-100 rounded-xl p-3 flex-shrink-0">
            <FlaskConical size={22} className="text-indigo-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-bold text-gray-900 mb-1">{experiment.title}</h1>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-400 font-mono">{experiment.experiment_id}</span>
                  <StatusBadge status={experiment.status} size="sm" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-1 -mb-px overflow-x-auto">
          {TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && <OverviewTab experiment={experiment} />}
      {activeTab === 'entries' && <LabEntriesTab experiment={experiment} />}
      {activeTab === 'materials' && <MaterialsTab experiment={experiment} />}
      {activeTab === 'attachments' && <AttachmentsTab experimentId={experiment.id} />}
      {activeTab === 'comments' && <CommentsTab experimentId={experiment.id} />}
      {activeTab === 'reviews' && <ReviewsTab experimentId={experiment.id} />}
      {activeTab === 'signatures' && <SignaturesTab experimentId={experiment.id} />}
      {activeTab === 'audit' && <AuditTab experimentId={experiment.id} />}
    </div>
  );
}
