import { AlertCircle } from 'lucide-react';

interface Props {
  message: string;
  className?: string;
}

export default function ErrorMessage({ message, className = '' }: Props) {
  return (
    <div className={`flex items-start gap-3 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-red-700 ${className}`}>
      <AlertCircle size={18} className="mt-0.5 flex-shrink-0" />
      <p className="text-sm">{message}</p>
    </div>
  );
}
