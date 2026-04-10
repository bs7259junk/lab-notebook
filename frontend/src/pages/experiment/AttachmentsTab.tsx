import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, Download, Paperclip } from 'lucide-react';
import { format } from 'date-fns';
import { getAttachments, uploadAttachment, downloadAttachmentUrl } from '../../api/endpoints';
import { getAccessToken } from '../../auth';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorMessage from '../../components/ErrorMessage';

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

interface Props {
  experimentId: string;
}

export default function AttachmentsTab({ experimentId }: Props) {
  const queryClient = useQueryClient();
  const [dragOver, setDragOver] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const { data: attachments = [], isLoading } = useQuery({
    queryKey: ['attachments', experimentId],
    queryFn: () => getAttachments(experimentId),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadAttachment(experimentId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attachments', experimentId] });
      setUploadError('');
    },
    onError: (err: Error) => setUploadError(err.message),
  });

  function handleFiles(files: FileList | null) {
    if (!files) return;
    Array.from(files).forEach(f => uploadMutation.mutate(f));
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  }

  function handleDownload(attachmentId: string, filename: string) {
    const url = downloadAttachmentUrl(attachmentId);
    const token = getAccessToken();
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(res => res.blob())
      .then(blob => {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = filename;
        a.click();
        URL.revokeObjectURL(a.href);
      });
  }

  return (
    <div className="space-y-4">
      {/* Upload Zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 bg-white hover:border-indigo-300'
        }`}
      >
        <input
          type="file"
          multiple
          onChange={e => handleFiles(e.target.files)}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        {uploadMutation.isPending ? (
          <div className="flex flex-col items-center gap-2">
            <LoadingSpinner size="md" />
            <p className="text-sm text-gray-500">Uploading…</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="bg-indigo-100 rounded-full p-3">
              <Upload size={20} className="text-indigo-600" />
            </div>
            <p className="text-sm font-medium text-gray-700">
              Drop files here or <span className="text-indigo-600">browse</span>
            </p>
            <p className="text-xs text-gray-400">Any file type supported</p>
          </div>
        )}
      </div>

      {uploadError && <ErrorMessage message={uploadError} />}

      {/* File List */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-900">
            Attachments ({attachments.length})
          </h3>
        </div>

        {isLoading ? (
          <LoadingSpinner className="py-10" />
        ) : attachments.length === 0 ? (
          <div className="py-10 text-center">
            <Paperclip size={28} className="text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No attachments yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {attachments.map(att => (
              <div key={att.id} className="flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="bg-gray-100 rounded-lg p-2">
                    <FileText size={16} className="text-gray-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{att.filename}</p>
                    <p className="text-xs text-gray-400">
                      {formatBytes(att.file_size_bytes)} · {format(new Date(att.uploaded_at), 'MMM d, yyyy')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDownload(att.id, att.filename)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-indigo-600 hover:text-indigo-700 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
                >
                  <Download size={13} />
                  Download
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
