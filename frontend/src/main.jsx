import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AlertTriangle, CheckCircle2, RefreshCw, Search, Shield, Zap } from 'lucide-react'
import './index.css'

const EMPTY_FEATURES = Object.fromEntries(
  Array.from({ length: 28 }, (_, index) => [`V${index + 1}`, 0])
)

function riskClasses(level) {
  if (level === 'fraud') return 'border-risk-fraud/30 bg-risk-fraudBg text-risk-fraud'
  if (level === 'review') return 'border-risk-review/30 bg-risk-reviewBg text-risk-review'
  return 'border-risk-safe/30 bg-risk-safeBg text-risk-safe'
}

function App() {
  const [amount, setAmount] = useState('249.50')
  const [time, setTime] = useState('86400')
  const [features, setFeatures] = useState(EMPTY_FEATURES)
  const [result, setResult] = useState(null)
  const [metadata, setMetadata] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/metadata')
      .then((response) => response.ok ? response.json() : null)
      .then(setMetadata)
      .catch(() => null)
  }, [])

  async function analyze(event) {
    event?.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          Time: Number(time),
          Amount: Number(amount),
          features,
        }),
      })
      if (!response.ok) throw new Error(await response.text())
      setResult(await response.json())
    } catch (caught) {
      setError(caught.message || 'Unable to analyze transaction')
    } finally {
      setLoading(false)
    }
  }

  async function loadSample() {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/sample')
      if (!response.ok) throw new Error(await response.text())
      const sample = await response.json()
      setAmount(String(sample.Amount))
      setTime(String(sample.Time))
      setFeatures({ ...EMPTY_FEATURES, ...sample.features })
      setResult(null)
    } catch (caught) {
      setError(caught.message || 'Unable to load a sample')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-ink-50 px-4 py-8 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl bg-ink-900 text-white shadow-sm">
              <Shield size={22} />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-ink-900">Radar</h1>
              <p className="text-sm text-ink-500">Fraud intelligence</p>
            </div>
          </div>
          <div className="hidden items-center gap-2 rounded-full border border-ink-200 bg-white px-3 py-2 text-xs font-medium text-ink-600 sm:flex">
            <span className="h-2 w-2 rounded-full bg-risk-safe" />
            Model online
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
          <section className="rounded-2xl border border-ink-200 bg-white shadow-sm">
            <div className="border-b border-ink-200 px-5 py-4 sm:px-6">
              <h2 className="font-semibold text-ink-900">Transaction analysis</h2>
              <p className="mt-1 text-sm text-ink-500">Enter transaction details or load a dataset sample.</p>
            </div>

            <form onSubmit={analyze} className="p-5 sm:p-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-ink-700">Amount</span>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400">$</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={amount}
                      onChange={(event) => setAmount(event.target.value)}
                      className="h-11 w-full rounded-lg border border-ink-200 bg-white pl-7 pr-3 text-sm tabular outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                    />
                  </div>
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-ink-700">Time since first transaction (seconds)</span>
                  <input
                    type="number"
                    min="0"
                    value={time}
                    onChange={(event) => setTime(event.target.value)}
                    className="h-11 w-full rounded-lg border border-ink-200 bg-white px-3 text-sm tabular outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                  />
                </label>
              </div>

              <details className="mt-5 rounded-lg border border-ink-200">
                <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-ink-700">
                  PCA transaction features
                </summary>
                <div className="grid max-h-72 grid-cols-2 gap-3 overflow-y-auto border-t border-ink-200 p-4 md:grid-cols-4">
                  {Object.keys(features).map((name) => (
                    <label key={name} className="text-xs font-medium text-ink-500">
                      {name}
                      <input
                        type="number"
                        step="0.0001"
                        value={features[name]}
                        onChange={(event) => setFeatures((current) => ({
                          ...current,
                          [name]: Number(event.target.value),
                        }))}
                        className="mt-1 h-9 w-full rounded-md border border-ink-200 px-2 text-sm tabular text-ink-800 outline-none focus:border-brand-500"
                      />
                    </label>
                  ))}
                </div>
              </details>

              {error && (
                <div className="mt-4 rounded-lg border border-risk-fraud/20 bg-risk-fraudBg px-4 py-3 text-sm text-risk-fraud">
                  {error}
                </div>
              )}

              <div className="mt-6 flex flex-wrap gap-3">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex h-11 items-center gap-2 rounded-lg bg-ink-900 px-5 text-sm font-semibold text-white transition hover:bg-ink-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? <RefreshCw className="animate-spin" size={16} /> : <Search size={16} />}
                  Analyze transaction
                </button>
                <button
                  type="button"
                  onClick={loadSample}
                  disabled={loading}
                  className="inline-flex h-11 items-center gap-2 rounded-lg border border-ink-200 bg-white px-4 text-sm font-semibold text-ink-700 transition hover:bg-ink-100 disabled:opacity-60"
                >
                  <Zap size={16} />
                  Load random sample
                </button>
              </div>
            </form>
          </section>

          <aside className="space-y-6">
            <section className="rounded-2xl border border-ink-200 bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-ink-500">Risk assessment</p>
              {!result ? (
                <div className="mt-6 text-center">
                  <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-ink-100 text-ink-400">
                    <Shield size={28} />
                  </div>
                  <p className="mt-4 text-sm text-ink-500">Waiting for a transaction</p>
                </div>
              ) : (
                <div className="mt-5">
                  <div className={`rounded-xl border p-4 ${riskClasses(result.riskLevel)}`}>
                    <div className="flex items-start gap-3">
                      {result.riskLevel === 'safe'
                        ? <CheckCircle2 className="mt-0.5 shrink-0" size={20} />
                        : <AlertTriangle className="mt-0.5 shrink-0" size={20} />}
                      <div>
                        <p className="font-semibold">{result.summary}</p>
                        <p className="mt-1 text-3xl font-bold tabular">{result.score}%</p>
                      </div>
                    </div>
                  </div>

                  <div className="mt-5">
                    <p className="text-xs font-semibold uppercase tracking-wider text-ink-400">Key signals</p>
                    <ul className="mt-2 space-y-2">
                      {result.triggers.map((trigger) => (
                        <li key={trigger} className="rounded-lg bg-ink-50 px-3 py-2 text-sm text-ink-700">
                          {trigger}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </section>

            {metadata && (
              <section className="rounded-2xl border border-ink-200 bg-white p-5 shadow-sm">
                <p className="text-sm font-medium text-ink-500">Model metrics</p>
                <dl className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <dt className="text-xs text-ink-400">AUC</dt>
                    <dd className="mt-1 font-semibold tabular text-ink-900">{metadata.auc?.toFixed(4)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-ink-400">Avg precision</dt>
                    <dd className="mt-1 font-semibold tabular text-ink-900">{metadata.avg_precision?.toFixed(4)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-ink-400">Transactions</dt>
                    <dd className="mt-1 font-semibold tabular text-ink-900">{metadata.n_samples?.toLocaleString()}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-ink-400">Fraud cases</dt>
                    <dd className="mt-1 font-semibold tabular text-ink-900">{metadata.n_fraud?.toLocaleString()}</dd>
                  </div>
                </dl>
              </section>
            )}
          </aside>
        </div>
      </div>
    </main>
  )
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
