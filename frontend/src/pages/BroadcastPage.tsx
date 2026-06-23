// pages/BroadcastPage.tsx — Full broadcast campaign page with dynamic templates + history

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Radio, Send, CheckCircle, AlertCircle, Upload, History } from 'lucide-react';
import { Header } from '../components/layout/Header';
import { useApp } from '../context/AppContext';
import { broadcastApi, templatesApi } from '../api/client';
import type { BroadcastCampaign, BroadcastTemplate } from '../types';

export function BroadcastPage() {
  const { activeTenant, sessions, refreshSessions } = useApp();
  const [templates, setTemplates] = useState<BroadcastTemplate[]>([]);
  const [history, setHistory] = useState<BroadcastCampaign[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [selectedPhones, setSelectedPhones] = useState<string[]>([]);
  const [csvInput, setCsvInput] = useState('');
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ sent: number; failed: number } | null>(null);
  const [showHistory, setShowHistory] = useState(false);

  const allPhones = sessions.map((s) => s.customer_phone);
  const activeTemplate = templates.find((t) => t.name === selectedTemplate);

  useEffect(() => {
    templatesApi.getAll().then((res) => setTemplates(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeTenant) return;
    broadcastApi.getHistory(activeTenant.id).then((res) => setHistory(res.data)).catch(() => {});
  }, [activeTenant, result]);

  const togglePhone = (phone: string) => {
    setSelectedPhones((prev) =>
      prev.includes(phone) ? prev.filter((p) => p !== phone) : [...prev, phone],
    );
  };

  const importCsv = () => {
    const phones = csvInput
      .split(/[\n,;]+/)
      .map((p) => p.trim())
      .filter((p) => p.length >= 8);
    setSelectedPhones((prev) => [...new Set([...prev, ...phones])]);
    setCsvInput('');
  };

  const handleSend = async () => {
    if (!activeTenant || !selectedTemplate || selectedPhones.length === 0) return;
    setSending(true);
    setResult(null);
    try {
      const res = await broadcastApi.send({
        tenant_id: activeTenant.id,
        template_name: selectedTemplate,
        phone_numbers: selectedPhones,
      });
      setResult({ sent: res.data.sent, failed: res.data.failed });
      refreshSessions();
    } catch {
      setResult({ sent: 0, failed: selectedPhones.length });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <Header title="Broadcast Campaigns" subtitle="Send approved WhatsApp templates" />

      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="flex gap-2">
            <button
              onClick={() => setShowHistory(false)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                !showHistory
                  ? 'bg-brand-primary/15 text-brand-glow border border-brand-primary/30'
                  : 'text-gray-500 border border-transparent'
              }`}
            >
              <Radio size={12} className="inline mr-1" />
              New Campaign
            </button>
            <button
              onClick={() => setShowHistory(true)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                showHistory
                  ? 'bg-brand-primary/15 text-brand-glow border border-brand-primary/30'
                  : 'text-gray-500 border border-transparent'
              }`}
            >
              <History size={12} className="inline mr-1" />
              History ({history.length})
            </button>
          </div>

          {showHistory ? (
            <div className="space-y-3">
              {history.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-12">No campaigns sent yet.</p>
              )}
              {history.map((c) => (
                <motion.div
                  key={c.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-surface-card border border-surface-border rounded-xl p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">{c.template_name}</span>
                    <span className="text-[10px] text-gray-500">
                      {new Date(c.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex gap-4 text-xs">
                    <span className="text-gray-400">
                      Recipients: <span className="text-white">{c.recipient_count}</span>
                    </span>
                    <span className="text-status-resolved">Sent: {c.sent}</span>
                    {c.failed > 0 && <span className="text-status-human">Failed: {c.failed}</span>}
                  </div>
                </motion.div>
              ))}
            </div>
          ) : (
            <>
              <div>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
                  Select Template
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {templates.map((t) => (
                    <button
                      key={t.name}
                      onClick={() => setSelectedTemplate(t.name)}
                      className={`p-3 rounded-xl text-left border transition-all ${
                        selectedTemplate === t.name
                          ? 'border-brand-primary bg-brand-primary/10'
                          : 'border-surface-border bg-surface-card hover:border-gray-600'
                      }`}
                    >
                      <p className="text-sm font-medium text-white">{t.label}</p>
                      <p className="text-[11px] text-gray-500 mt-0.5">{t.description}</p>
                      <span className="text-[9px] text-gray-600 mt-1 inline-block">{t.category}</span>
                    </button>
                  ))}
                </div>
              </div>

              {activeTemplate && (
                <div className="bg-surface-card border border-surface-border rounded-xl p-4">
                  <p className="text-xs text-gray-400 mb-2">Template Preview</p>
                  <p className="text-sm text-gray-200 whitespace-pre-wrap">{activeTemplate.body_preview}</p>
                </div>
              )}

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Recipients ({selectedPhones.length})
                  </p>
                  <button
                    onClick={() =>
                      setSelectedPhones(
                        selectedPhones.length === allPhones.length ? [] : [...allPhones],
                      )
                    }
                    className="text-xs text-brand-primary hover:text-brand-glow"
                  >
                    {selectedPhones.length === allPhones.length ? 'Deselect all' : 'Select all sessions'}
                  </button>
                </div>

                <div className="mb-3 flex gap-2">
                  <textarea
                    value={csvInput}
                    onChange={(e) => setCsvInput(e.target.value)}
                    placeholder="Paste phone numbers (comma or newline separated)"
                    rows={2}
                    className="flex-1 bg-surface-elevated border border-surface-border rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 outline-none resize-none"
                  />
                  <button
                    onClick={importCsv}
                    disabled={!csvInput.trim()}
                    className="px-3 rounded-xl bg-surface-elevated border border-surface-border text-gray-400 hover:text-white disabled:opacity-40 flex items-center gap-1 text-xs"
                  >
                    <Upload size={12} />
                    Import
                  </button>
                </div>

                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {allPhones.map((phone) => (
                    <button
                      key={phone}
                      onClick={() => togglePhone(phone)}
                      className={`w-full px-3 py-2 rounded-lg flex items-center justify-between text-sm ${
                        selectedPhones.includes(phone)
                          ? 'bg-brand-primary/15 border border-brand-primary/30 text-white'
                          : 'bg-surface-elevated border border-transparent text-gray-400'
                      }`}
                    >
                      <span className="font-mono text-xs">{phone}</span>
                      {selectedPhones.includes(phone) && (
                        <CheckCircle size={13} className="text-brand-primary" />
                      )}
                    </button>
                  ))}
                  {selectedPhones
                    .filter((p) => !allPhones.includes(p))
                    .map((phone) => (
                      <div
                        key={phone}
                        className="px-3 py-2 rounded-lg bg-brand-primary/10 border border-brand-primary/30 flex items-center justify-between"
                      >
                        <span className="font-mono text-xs text-white">{phone}</span>
                        <button
                          onClick={() => togglePhone(phone)}
                          className="text-[10px] text-gray-400 hover:text-white"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                </div>
              </div>

              {result && (
                <div
                  className={`p-3 rounded-xl border flex items-center gap-2 ${
                    result.failed === 0
                      ? 'bg-status-resolved/10 border-status-resolved/30'
                      : 'bg-status-human/10 border-status-human/30'
                  }`}
                >
                  {result.failed === 0 ? (
                    <CheckCircle size={14} className="text-status-resolved" />
                  ) : (
                    <AlertCircle size={14} className="text-status-human" />
                  )}
                  <p className="text-sm text-white">
                    Sent: {result.sent}
                    {result.failed > 0 && ` · Failed: ${result.failed}`}
                  </p>
                </div>
              )}

              <button
                onClick={handleSend}
                disabled={!selectedTemplate || selectedPhones.length === 0 || sending}
                className={`w-full h-11 rounded-xl flex items-center justify-center gap-2 text-sm font-semibold transition-all ${
                  !selectedTemplate || selectedPhones.length === 0 || sending
                    ? 'bg-surface-elevated text-gray-600 cursor-not-allowed'
                    : 'bg-gradient-to-r from-brand-primary to-brand-secondary text-white hover:opacity-90 glow-indigo'
                }`}
              >
                {sending ? (
                  <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                ) : (
                  <>
                    <Send size={14} />
                    Send to {selectedPhones.length} recipient{selectedPhones.length !== 1 ? 's' : ''}
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
