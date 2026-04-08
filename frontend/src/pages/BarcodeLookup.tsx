import { useState} from 'react';
import type { FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { ScanBarcode, Search, ArrowRight, FlaskConical } from 'lucide-react';
import { lookupBarcode } from '../api/endpoints';
import StatusBadge from '../components/StatusBadge';
import ErrorMessage from '../components/ErrorMessage';
import PageHeader from '../components/PageHeader';
import type { Experiment } from '../types';

export default function BarcodeLookup() {
  const [barcode, setBarcode] = useState('');
  const [result, setResult] = useState<Experiment | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!barcode.trim()) return;

    setLoading(true);
    setError('');
    setResult(null);
    setSearched(false);

    try {
      const exp = await lookupBarcode(barcode.trim());
      setResult(exp);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lookup failed');
      setSearched(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <PageHeader
        title="Barcode Lookup"
        subtitle="Find an experiment by its barcode"
      />

      {/* Search Form */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <form onSubmit={handleSubmit}>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Experiment Barcode
          </label>
          <div className="flex gap-3">
            <div className="relative flex-1">
              <ScanBarcode size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={barcode}
                onChange={e => setBarcode(e.target.value)}
                autoFocus
                className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter or scan barcode…"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !barcode.trim()}
              className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
            >
              {loading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <Search size={16} />
              )}
              {loading ? 'Looking up…' : 'Look Up'}
            </button>
          </div>
        </form>
      </div>

      {/* Result */}
      {searched && (
        <>
          {error && <ErrorMessage message={error} />}

          {result && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-start gap-4">
                <div className="bg-indigo-100 rounded-xl p-3 flex-shrink-0">
                  <FlaskConical size={22} className="text-indigo-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h2 className="text-lg font-bold text-gray-900">{result.title}</h2>
                    <StatusBadge status={result.status} size="sm" />
                  </div>
                  <p className="text-sm text-gray-400 font-mono mb-2">{result.experiment_id}</p>
                  {result.purpose && (
                    <p className="text-sm text-gray-600 mb-3">{result.purpose}</p>
                  )}
                  {result.barcode && (
                    <div className="flex items-center gap-2 mb-4">
                      <ScanBarcode size={14} className="text-gray-400" />
                      <span className="text-sm text-gray-500 font-mono">{result.barcode}</span>
                    </div>
                  )}
                  <Link
                    to={`/experiments/${result.id}`}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
                  >
                    View Experiment
                    <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Help text */}
      {!searched && (
        <div className="bg-gray-50 rounded-xl border border-gray-100 p-5">
          <h3 className="text-sm font-medium text-gray-700 mb-2">How to use</h3>
          <ul className="space-y-1.5 text-sm text-gray-500">
            <li className="flex items-start gap-2">
              <span className="text-gray-300 mt-0.5">•</span>
              Enter the barcode printed on the experiment label
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gray-300 mt-0.5">•</span>
              Use a barcode scanner to scan directly into the field
            </li>
            <li className="flex items-start gap-2">
              <span className="text-gray-300 mt-0.5">•</span>
              The experiment record will be displayed if found
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
