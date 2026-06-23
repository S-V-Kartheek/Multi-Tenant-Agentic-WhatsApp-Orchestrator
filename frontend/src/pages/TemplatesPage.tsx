// pages/TemplatesPage.tsx — Browse registered WhatsApp templates

import { useEffect, useState } from 'react';
import { FileText } from 'lucide-react';
import { Header } from '../components/layout/Header';
import { templatesApi } from '../api/client';
import type { BroadcastTemplate } from '../types';

export function TemplatesPage() {
  const [templates, setTemplates] = useState<BroadcastTemplate[]>([]);
  const [selected, setSelected] = useState<BroadcastTemplate | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    templatesApi
      .getAll()
      .then((res) => {
        setTemplates(res.data);
        if (res.data.length > 0) setSelected(res.data[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Header title="Templates" subtitle="Approved WhatsApp message templates" />

      <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
        <div className="md:w-80 border-b md:border-b-0 md:border-r border-surface-border overflow-y-auto p-4 space-y-2">
          {loading && (
            <div className="flex justify-center py-8">
              <div className="w-6 h-6 rounded-full border-2 border-brand-primary border-t-transparent animate-spin" />
            </div>
          )}
          {templates.map((t) => (
            <button
              key={t.name}
              onClick={() => setSelected(t)}
              className={`w-full p-3 rounded-xl text-left border transition-all ${
                selected?.name === t.name
                  ? 'border-brand-primary bg-brand-primary/10'
                  : 'border-surface-border bg-surface-card hover:border-gray-600'
              }`}
            >
              <p className="text-sm font-medium text-white">{t.label}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">{t.name}</p>
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {selected ? (
            <div className="max-w-lg">
              <div className="flex items-center gap-2 mb-4">
                <FileText size={18} className="text-brand-primary" />
                <h2 className="text-lg font-semibold text-white">{selected.label}</h2>
              </div>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-gray-500 text-xs uppercase mb-1">Meta name</dt>
                  <dd className="text-white font-mono">{selected.name}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase mb-1">Category</dt>
                  <dd className="text-white">{selected.category}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase mb-1">Language</dt>
                  <dd className="text-white">{selected.language}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase mb-1">Description</dt>
                  <dd className="text-gray-300">{selected.description}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 text-xs uppercase mb-1">Body preview</dt>
                  <dd className="bg-surface-card border border-surface-border rounded-xl p-4 text-gray-200 whitespace-pre-wrap">
                    {selected.body_preview}
                  </dd>
                </div>
              </dl>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Select a template to preview.</p>
          )}
        </div>
      </div>
    </div>
  );
}
