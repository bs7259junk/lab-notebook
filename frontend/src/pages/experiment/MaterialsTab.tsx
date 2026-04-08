import { useState} from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Package, FlaskConical } from 'lucide-react';
import { addMaterial } from '../../api/endpoints';
import ErrorMessage from '../../components/ErrorMessage';
import type { ExperimentDetail } from '../../types';

interface Props {
  experiment: ExperimentDetail;
}

export default function MaterialsTab({ experiment }: Props) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formError, setFormError] = useState('');

  const [materialName, setMaterialName] = useState('');
  const [lotNumber, setLotNumber] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('');
  const [barcode, setBarcode] = useState('');

  const mutation = useMutation({
    mutationFn: () =>
      addMaterial(experiment.id, {
        material_name: materialName,
        lot_number: lotNumber || undefined,
        quantity_used: quantity ? Number(quantity) : undefined,
        unit: unit || undefined,
        barcode: barcode || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiment', experiment.id] });
      setShowForm(false);
      setMaterialName('');
      setLotNumber('');
      setQuantity('');
      setUnit('');
      setBarcode('');
      setFormError('');
    },
    onError: (err: Error) => setFormError(err.message),
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!materialName.trim()) { setFormError('Material name is required'); return; }
    setFormError('');
    mutation.mutate();
  }

  const materials = experiment.materials ?? [];

  return (
    <div className="space-y-4">
      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-900">
            Materials ({materials.length})
          </h3>
          <button
            onClick={() => setShowForm(f => !f)}
            className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            <Plus size={16} />
            Add Material
          </button>
        </div>

        {/* Add Material Form */}
        {showForm && (
          <div className="px-5 py-4 border-b border-gray-100 bg-indigo-50/50">
            {formError && <ErrorMessage message={formError} className="mb-3" />}
            <form onSubmit={handleSubmit}>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Material Name *</label>
                  <input
                    type="text"
                    value={materialName}
                    onChange={e => setMaterialName(e.target.value)}
                    required
                    autoFocus
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="e.g. Sodium chloride"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Lot Number</label>
                  <input
                    type="text"
                    value={lotNumber}
                    onChange={e => setLotNumber(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Lot #"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Quantity</label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={e => setQuantity(e.target.value)}
                    step="any"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="0.0"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Unit</label>
                  <input
                    type="text"
                    value={unit}
                    onChange={e => setUnit(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="g, mL, mg…"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">Barcode</label>
                  <input
                    type="text"
                    value={barcode}
                    onChange={e => setBarcode(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Optional barcode"
                  />
                </div>
              </div>
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => { setShowForm(false); setFormError(''); }}
                  className="px-3.5 py-1.5 text-sm text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={mutation.isPending}
                  className="px-3.5 py-1.5 text-sm text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 rounded-lg transition-colors"
                >
                  {mutation.isPending ? 'Adding…' : 'Add Material'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Materials Table */}
        {materials.length === 0 ? (
          <div className="py-12 text-center">
            <FlaskConical size={32} className="text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-400">No materials recorded</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs font-medium text-gray-500 uppercase tracking-wide bg-gray-50 border-b border-gray-100">
                  <th className="text-left px-5 py-3">Material</th>
                  <th className="text-left px-5 py-3">Lot Number</th>
                  <th className="text-left px-5 py-3">Quantity</th>
                  <th className="text-left px-5 py-3">Barcode</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {materials.map(m => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <Package size={14} className="text-gray-400" />
                        <span className="font-medium text-gray-900">{m.material_name}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-gray-500 font-mono">
                      {m.lot_number || '—'}
                    </td>
                    <td className="px-5 py-3 text-gray-500">
                      {m.quantity_used != null
                        ? `${m.quantity_used}${m.unit ? ` ${m.unit}` : ''}`
                        : '—'}
                    </td>
                    <td className="px-5 py-3 text-gray-500 font-mono">
                      {m.barcode || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
