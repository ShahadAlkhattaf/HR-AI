import { useState, useCallback, useRef, useEffect } from 'react';
import './App.css';

// --- Types -----------------------------------------------------------------

interface CandidateProfile {
  full_name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  summary: string | null;
  github: string | null;
  linkedin: string | null;
  portfolio: string | null;
  skills: string[];
  years_of_experience: number | null;
  languages: string[];
  detected_source_language: string | null;
  education: Education[];
  work_experience: WorkExperience[];
  certificates: Certificate[];
  projects: Project[];
}

interface Education {
  degree: string | null;
  institution: string | null;
  start_year: number | null;
  end_year: number | null;
  gpa: number | null;
}

interface WorkExperience {
  company: string | null;
  role: string | null;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
}

interface Certificate {
  name: string | null;
  issuer: string | null;
  issue_date: string | null;
  expiry_date: string | null;
}

interface Project {
  name: string | null;
  link: string | null;
  description: string | null;
}

interface ApiModelsResponse {
  models: string[];
}

// --- Helpers ---------------------------------------------------------------

function formatDate(val: string | null | undefined): string {
  if (!val) return '—';
  const d = new Date(val);
  if (!isNaN(d.getTime())) return d.toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
  return val;
}

function formatYear(val: number | null | undefined): string {
  if (val === null || val === undefined) return '—';
  return String(val);
}

function downloadJson(data: CandidateProfile, filename: string): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function truncateMiddle(str: string | null | undefined, max = 60): string {
  if (!str) return '—';
  if (str.length <= max) return str;
  const half = Math.floor((max - 3) / 2);
  return str.slice(0, half) + '…' + str.slice(-half);
}

function skillColor(skill: string): string {
  const colors = [
    'bg-emerald-100 text-emerald-800 border-emerald-200',
    'bg-sky-100 text-sky-800 border-sky-200',
    'bg-violet-100 text-violet-800 border-violet-200',
    'bg-amber-100 text-amber-800 border-amber-200',
    'bg-rose-100 text-rose-800 border-rose-200',
    'bg-cyan-100 text-cyan-800 border-cyan-200',
    'bg-orange-100 text-orange-800 border-orange-200',
    'bg-teal-100 text-teal-800 border-teal-200',
  ];
  let hash = 0;
  for (let i = 0; i < skill.length; i++) hash = (hash * 31 + skill.charCodeAt(i)) | 0;
  return colors[Math.abs(hash) % colors.length];
}

// --- Icons (inline SVG) ---------------------------------------------------

const UploadIcon = () => (
  <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
  </svg>
);

const FileSvg = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
);

const DownloadIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
  </svg>
);

const ReloadIcon = () => (
  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const AlertIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
  </svg>
);

const CloseIcon = () => (
  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
  </svg>
);

// --- Component: Education Card ------------------------------------------

function EducationCard({ item }: { item: Education }) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-900 text-sm">{item.degree ?? '—'}</p>
          <p className="text-slate-500 text-xs mt-0.5">{item.institution ?? '—'}</p>
        </div>
        <div className="text-right">
          <p className="text-xs font-medium text-slate-600">
            {formatYear(item.start_year)} – {formatYear(item.end_year)}
          </p>
          {item.gpa != null && (
            <p className="text-xs text-slate-400 mt-0.5">GPA: {item.gpa.toFixed(2)}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function ExperienceCard({ item }: { item: WorkExperience }) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-slate-900 text-sm">{item.role ?? '—'}</p>
          <p className="text-slate-500 text-xs mt-0.5">{item.company ?? '—'}</p>
          {item.description && (
            <p className="text-slate-400 text-xs mt-2 line-clamp-3 leading-relaxed">{item.description}</p>
          )}
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-xs font-medium text-slate-600">
            {truncateMiddle(item.start_date)} – {truncateMiddle(item.end_date)}
          </p>
        </div>
      </div>
    </div>
  );
}

function CertificateCard({ item }: { item: Certificate }) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors">
      <p className="font-semibold text-slate-900 text-sm">{item.name ?? '—'}</p>
      <p className="text-slate-500 text-xs mt-1">{item.issuer ?? '—'}</p>
      <div className="flex gap-3 mt-2 text-xs text-slate-400">
        <span>Issued: {formatDate(item.issue_date)}</span>
        {item.expiry_date && <span>Expires: {formatDate(item.expiry_date)}</span>}
      </div>
    </div>
  );
}

function ProjectCard({ item }: { item: Project }) {
  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:border-slate-300 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <p className="font-semibold text-slate-900 text-sm">{item.name ?? '—'}</p>
        {item.link && (
          <a
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-hr-600 hover:text-hr-700 font-medium flex items-center gap-1 flex-shrink-0"
          >
            View
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5a2.25 2.25 0 00-2.25-2.25H13.5m0 0L16 13.25m-4-4l4 4" />
            </svg>
          </a>
        )}
      </div>
      {item.description && (
        <p className="text-slate-400 text-xs mt-2 line-clamp-3 leading-relaxed">{item.description}</p>
      )}
    </div>
  );
}

// --- Component: Toast ------------------------------------------------------

type ToastType = 'success' | 'error' | 'info';

interface ToastData {
  id: number;
  type: ToastType;
  message: string;
}

function Toast({ toast, onClose }: { toast: ToastData; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);

  const bg = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  }[toast.type];

  const icon = {
    success: <CheckIcon />,
    error: <AlertIcon />,
    info: <AlertIcon />,
  }[toast.type];

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3 rounded-xl border shadow-lg ${bg} animate-slide-up max-w-sm`}
    >
      {icon}
      <p className="text-sm font-medium flex-1">{toast.message}</p>
      <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
        <CloseIcon />
      </button>
    </div>
  );
}

// --- Component: Skills pill ----------------------------------------------

function SkillPill({ skill }: { skill: string }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 text-xs font-medium rounded-lg border ${skillColor(skill)}`}
    >
      {skill}
    </span>
  );
}

// --- Main App --------------------------------------------------------------

function App() {
  // API configuration
  const [apiUrl, setApiUrl] = useState(() => {
    const saved = localStorage.getItem('hr-ai-api-url');
    return saved ?? 'http://127.0.0.1:8000';
  });
  const [model, setModel] = useState('mock');
  const [availableModels, setAvailableModels] = useState<string[]>(['mock']);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);

  // Upload state
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Parse state
  const [parsing, setParsing] = useState(false);
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [responseTime, setResponseTime] = useState<number | null>(null);

  // Toasts
  const [toasts, setToasts] = useState<ToastData[]>([]);
  const toastIdRef = useRef(0);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = ++toastIdRef.current;
    setToasts(prev => [...prev, { id, type, message }]);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Save API URL
  useEffect(() => {
    localStorage.setItem('hr-ai-api-url', apiUrl);
  }, [apiUrl]);

  // Fetch available models
  const fetchModels = useCallback(async () => {
    setModelsLoading(true);
    setModelsError(null);
    try {
      const res = await fetch(`${apiUrl}/v1/models`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ApiModelsResponse = await res.json();
      if (!Array.isArray(data.models)) throw new Error('Unexpected response shape');
      setAvailableModels(data.models);
      if (data.models.length > 0) setModel(data.models[0]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch models';
      setModelsError(msg);
    } finally {
      setModelsLoading(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  // Drag-and-drop handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) validateAndSetFile(droppedFile);
  }, []);

  const validateAndSetFile = (f: File) => {
    const ext = f.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      addToast('error', `Unsupported file type: .${ext}. Please upload PDF or DOCX.`);
      return;
    }
    if (f.size > 20 * 1024 * 1024) {
      addToast('error', 'File too large. Maximum size is 20 MB.');
      return;
    }
    setFile(f);
    setParseError(null);
    setProfile(null);
    addToast('info', `Selected: ${f.name}`);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) validateAndSetFile(selected);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const clearFile = () => {
    setFile(null);
    setParseError(null);
    setProfile(null);
    setResponseTime(null);
  };

  const handleParse = async () => {
    if (!file) {
      addToast('error', 'Please select a resume file first.');
      return;
    }
    setParsing(true);
    setParseError(null);
    setProfile(null);
    setResponseTime(null);

    const formData = new FormData();
    formData.append('file', file);

    const start = performance.now();

    try {
      const res = await fetch(
        `${apiUrl}/v1/resumes/parse?model=${encodeURIComponent(model)}`,
        {
          method: 'POST',
          body: formData,
        }
      );
      const elapsed = Math.round(performance.now() - start);
      setResponseTime(elapsed);

      if (!res.ok) {
        let errBody: string;
        try {
          errBody = await res.text();
        } catch {
          errBody = res.statusText;
        }
        throw new Error(`Server error ${res.status}: ${errBody.slice(0, 300)}`);
      }

      const data: CandidateProfile = await res.json();
      setProfile(data);
      addToast('success', `Parsed ${data.full_name ?? 'resume'} in ${elapsed}ms`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Request failed';
      setParseError(msg);
      addToast('error', msg);
    } finally {
      setParsing(false);
    }
  };

  // ---------------------------------------------------------------- HEADER
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-hr-50/30">
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-5 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-hr-500 to-hr-700 flex items-center justify-center shadow-sm">
              <svg className="w-4.5 h-4.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.105a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.582-7.499-1.548z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 leading-tight">HR AI</h1>
              <p className="text-[10px] text-slate-400 font-medium leading-tight -mt-0.5">Resume Parser</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="hidden sm:inline">Bilingual EN / AR</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-5 py-8">
        {/* API Config */}
        <section className="mb-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="flex-1">
                <label htmlFor="api-url" className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                  API Endpoint
                </label>
                <div className="flex items-center gap-2">
                  <input
                    id="api-url"
                    type="url"
                    value={apiUrl}
                    onChange={e => setApiUrl(e.target.value)}
                    placeholder="http://127.0.0.1:8000"
                    className="flex-1 px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-hr-500/30 focus:border-hr-500 text-slate-800 placeholder-slate-300 transition-shadow"
                  />
                  <button
                    onClick={fetchModels}
                    disabled={modelsLoading}
                    className="px-3 py-2 text-xs font-medium bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                  >
                    {modelsLoading ? (
                      <>
                        <ReloadIcon />
                        Refreshing…
                      </>
                    ) : (
                      <>
                        <ReloadIcon />
                        Refresh
                      </>
                    )}
                  </button>
                </div>
                {modelsError && (
                  <p className="text-xs text-red-500 mt-1.5 flex items-center gap-1">
                    <AlertIcon />
                    {modelsError}
                  </p>
                )}
              </div>
              <div className="sm:border-t sm:border-slate-200 sm:pt-3 w-full sm:w-auto">
                <label htmlFor="model-select" className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">
                  Model
                </label>
                <select
                  id="model-select"
                  value={model}
                  onChange={e => setModel(e.target.value)}
                  className="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-hr-500/30 focus:border-hr-500 text-slate-800 cursor-pointer"
                >
                  {availableModels.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </section>

        {/* Upload + Parse */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Upload Area */}
          <section className="lg:col-span-3">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 pt-5 pb-3 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-800">Upload Resume</h2>
                <p className="text-xs text-slate-400 mt-0.5">PDF or DOCX — max 20 MB</p>
              </div>

              {/* Drop Zone */}
              <div
                className={`relative m-4 rounded-xl border-2 transition-all duration-200 cursor-pointer ${
                  isDragging
                    ? 'border-hr-500 bg-hr-50/60 scale-[1.01] shadow-lg shadow-hr-500/10'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50/40'
                } ${file ? 'border-emerald-300 bg-emerald-50/30' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => !file && fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileInputChange}
                  className="hidden"
                />

                <div className="flex flex-col items-center justify-center py-10 text-center pointer-events-none select-none">
                  {isDragging ? (
                    <div className="animate-bounce">
                      <UploadIcon />
                    </div>
                  ) : (
                    <div className="text-slate-300">
                      <UploadIcon />
                    </div>
                  )}
                  <p className={`text-sm font-medium mt-4 ${isDragging ? 'text-hr-700' : 'text-slate-500'}`}>
                    {isDragging ? 'Drop your resume here' : file ? 'File selected — click to change' : 'Drag & drop or click to browse'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1.5">
                    Supports PDF and DOCX files
                  </p>
                </div>
              </div>

              {/* File Info */}
              {file && (
                <div className="mx-4 mb-4 flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="w-9 h-9 rounded-lg bg-hr-100 text-hr-700 flex items-center justify-center flex-shrink-0">
                    <FileSvg />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{file.name}</p>
                    <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                  <button
                    onClick={clearFile}
                    className="text-slate-400 hover:text-red-500 transition-colors p-1"
                    title="Remove file"
                  >
                    <CloseIcon />
                  </button>
                </div>
              )}

              {/* Parse Button */}
              <div className="px-5 pb-5">
                <button
                  onClick={handleParse}
                  disabled={!file || parsing}
                  className={`w-full py-3 px-5 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center justify-center gap-2 ${
                    !file
                      ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                      : parsing
                      ? 'bg-hr-600 text-white cursor-wait shadow-md shadow-hr-500/20'
                      : 'bg-gradient-to-r from-hr-600 to-hr-700 hover:from-hr-700 hover:to-hr-800 text-white shadow-md shadow-hr-500/20 hover:shadow-lg hover:shadow-hr-500/30 active:scale-[0.99]'
                  }`}
                >
                  {parsing ? (
                    <>
                      <ReloadIcon />
                      Parsing…
                    </>
                  ) : (
                    <>
                      <UploadIcon />
                      Parse Resume
                    </>
                  )}
                </button>

                {responseTime != null && !parsing && (
                  <p className="text-center text-xs text-slate-400 mt-3">
                    Completed in {responseTime} ms
                  </p>
                )}
              </div>
            </div>
          </section>

          {/* Result */}
          <section className="lg:col-span-2">
            {!profile ? (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm h-full flex flex-col">
                <div className="px-5 pt-5 pb-3 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">Parsed Profile</h2>
                  <p className="text-xs text-slate-400 mt-0.5">Upload and parse a resume to view results</p>
                </div>
                <div className="flex-1 flex items-center justify-center p-6">
                  <div className="text-center max-w-[200px]">
                    <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-slate-100 flex items-center justify-center">
                      <svg className="w-6 h-6 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                    </div>
                    <p className="text-xs text-slate-400">Waiting for a parsed resume</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                {/* Result header */}
                <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-slate-100">
                  <div>
                    <h2 className="text-sm font-semibold text-slate-800">Parsed Profile</h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {profile.detected_source_language ? (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-500">
                          {profile.detected_source_language.toUpperCase()}
                        </span>
                      ) : (
                        'Language detected automatically'
                      )}
                    </p>
                  </div>
                  <button
                    onClick={() => profile && downloadJson(profile, 'candidate-profile.json')}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-hr-700 bg-hr-50 hover:bg-hr-100 border border-hr-200 rounded-lg transition-colors"
                  >
                    <DownloadIcon />
                    Download JSON
                  </button>
                </div>

                {/* Candidate info card */}
                <div className="px-5 py-4 bg-gradient-to-r from-hr-50 to-white border-b border-slate-100">
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 rounded-full bg-gradient-to-br from-hr-500 to-hr-700 flex items-center justify-center text-white font-bold text-lg shadow-sm flex-shrink-0">
                      {(profile.full_name ?? '?')[0].toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-base font-bold text-slate-900 truncate">
                        {profile.full_name ?? 'Unknown'}
                      </h3>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-xs text-slate-500">
                        {profile.email && (
                          <a href={`mailto:${profile.email}`} className="text-hr-600 hover:text-hr-700 truncate">
                            {profile.email}
                          </a>
                        )}
                        {profile.phone && <span className="truncate">{profile.phone}</span>}
                        {profile.location && <span className="truncate">{profile.location}</span>}
                      </div>
                      {profile.summary && (
                        <p className="text-xs text-slate-400 mt-2 line-clamp-2 leading-relaxed">{profile.summary}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Body: sections */}
                <div className="divide-y divide-slate-100">
                  {/* Skills */}
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-6.364-6.364L2.25 12l2.846.813a4.5 4.5 0 006.364 0l2.846-.813a4.5 4.5 0 00.813-6.364L12 2.25l.813 2.846a4.5 4.5 0 006.364 6.364L15.75 12l-2.846-.813a4.5 4.5 0 00-6.364 0l-2.846.813a4.5 4.5 0 00-.813 6.364z" />
                      </svg>
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Skills</span>
                      <span className="ml-auto text-xs text-slate-400">{profile.skills.length}</span>
                    </div>
                    {profile.skills.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {profile.skills.map(skill => (
                          <SkillPill key={skill} skill={skill} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No skills extracted</p>
                    )}
                  </div>

                  {/* Experience */}
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.24-4.091.24-6.187.24S2.47 18.48.383 18.24A2.12 2.12 0 01.125 15.03v-4.25c0-1.094.787-2.036 1.872-2.18 2.087-.24 4.09-.24 6.186-.24s4.098.24 6.187.24c1.085.144 1.872.986 1.872 2.18v4.25zM16.872 10.5c.396.712.787 1.472 1.128 2.25 1.306 2.86 2.083 6.123 2.083 9.375a1.125 1.125 0 01-1.125 1.125h-6.75a1.125 1.125 0 01-1.125-1.125c0-3.252.777-6.514 2.084-9.374.341-.778.732-1.538 1.128-2.25H16.872z" />
                      </svg>
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Experience</span>
                      <span className="ml-auto text-xs text-slate-400">{profile.work_experience.length}</span>
                    </div>
                    {profile.work_experience.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.work_experience.map((exp, i) => (
                          <ExperienceCard key={i} item={exp} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No work experience extracted</p>
                    )}
                  </div>

                  {/* Education */}
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.216 0 4.228.812 6 2.255V6.517A8.968 8.968 0 0018 3.75c-2.217 0-4.228.812-6 2.255v14.493A8.967 8.967 0 016 18c-2.216 0-4.227-.812-6-2.255V6.042z" />
                      </svg>
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Education</span>
                      <span className="ml-auto text-xs text-slate-400">{profile.education.length}</span>
                    </div>
                    {profile.education.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.education.map((edu, i) => (
                          <EducationCard key={i} item={edu} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No education extracted</p>
                    )}
                  </div>

                  {/* Certificates */}
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9.53 15.477c.184-.217.43-.39.736-.501l-1.947-1.947c.354-.433.766-.814 1.234-1.12a1.25 1.25 0 111.672 1.671c-.382.376-.856.702-1.358.955l-1.625-1.625a1.25 1.25 0 111.671-1.672c.308.5.687.98 1.12 1.234l1.948 1.947c-.217.184-.39.43-.501.736s-.217.527-.217.778v.405a1.25 1.25 0 01-1.12 1.234l-1.947 1.948c-.184.217-.43.39-.736.501l1.947 1.947c-.354.433-.766.814-1.234 1.12a1.25 1.25 0 11-1.672-1.671c.382-.376.856-.702 1.358-.955l1.625 1.625a1.25 1.25 0 11-1.671 1.672c-.308-.5-.687-.98-1.12-1.234l-1.948-1.947c.217-.184.39-.43.501-.736s.217-.527.217-.778V12.34a1.25 1.25 0 011.12-1.234l1.947-1.948c.184-.217.43-.39.736-.501l-1.947-1.947c.354-.433.766-.814 1.234-1.12a1.25 1.25 0 111.672 1.671c-.382.376-.856.702-1.358.955l-1.625-1.625a1.25 1.25 0 111.671-1.672c.308.5.687.98 1.12 1.234l1.948 1.947c-.217.184-.39.43-.501.736z" />
                      </svg>
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Certifications</span>
                      <span className="ml-auto text-xs text-slate-400">{profile.certificates.length}</span>
                    </div>
                    {profile.certificates.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.certificates.map((cert, i) => (
                          <CertificateCard key={i} item={cert} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No certifications extracted</p>
                    )}
                  </div>

                  {/* Projects */}
                  <div className="px-5 py-4">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-7.5 0m3.75 2.383a14.406 14.406 0 01-9 0M14.25 18v-.192c0-.983.658-1.823 1.5-2.316a7.5 7.5 0 10-7.5-7.5 7.5 7.5 0 007.5 7.5c.841 0 1.5-.83 1.5-1.818V13.5m1.5.192v.192c0 .983-.658 1.823-1.5 2.316a7.5 7.5 0 107.5 7.5 7.5 7.5 0 00-7.5-7.5c-.841 0-1.5.83-1.5 1.818z" />
                      </svg>
                      <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Projects</span>
                      <span className="ml-auto text-xs text-slate-400">{profile.projects.length}</span>
                    </div>
                    {profile.projects.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.projects.map((proj, i) => (
                          <ProjectCard key={i} item={proj} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400">No projects extracted</p>
                    )}
                  </div>

                  {/* Languages */}
                  {profile.languages.length > 0 && (
                    <div className="px-5 py-4">
                      <div className="flex items-center gap-2 mb-3">
                        <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016.562 0M3 5.621l4.125 10.5mA3 3 0 01-3 3m0 0v2.121m0 0h2.121m-3 3L3 15M3 5.621l5.25 13.125" />
                        </svg>
                        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Languages</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {profile.languages.map(lang => (
                          <span
                            key={lang}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-100 text-slate-700 border border-slate-200"
                          >
                            <span className="w-2 h-2 rounded-full bg-slate-400" />
                            {lang}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Years of experience */}
                  {profile.years_of_experience != null && (
                    <div className="px-5 py-4">
                      <div className="flex items-center gap-2 mb-2">
                        <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Experience</span>
                      </div>
                      <p className="text-sm text-slate-700">
                        {profile.years_of_experience} {profile.years_of_experience === 1 ? 'year' : 'years'} of experience
                      </p>
                    </div>
                  )}

                  {/* Links */}
                  {(profile.github || profile.linkedin || profile.portfolio) && (
                    <div className="px-5 py-4">
                      <div className="flex items-center gap-2 mb-3">
                        <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5a2.25 2.25 0 00-2.25-2.25H13.5m0 0L16 13.25m-4-4l4 4" />
                        </svg>
                        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Links</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {profile.github && (
                          <a
                            href={profile.github}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 text-white hover:bg-slate-900 transition-colors"
                          >
                            GitHub
                          </a>
                        )}
                        {profile.linkedin && (
                          <a
                            href={profile.linkedin}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                          >
                            LinkedIn
                          </a>
                        )}
                        {profile.portfolio && (
                          <a
                            href={profile.portfolio}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                          >
                            Portfolio
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>

        {/* Error display */}
        {parseError && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
            <AlertIcon />
            <div>
              <p className="text-sm font-semibold text-red-800">Parse failed</p>
              <p className="text-sm text-red-600 mt-1 break-words">{parseError}</p>
            </div>
            <button
              onClick={clearFile}
              className="ml-auto text-xs text-red-600 hover:text-red-800 font-medium"
            >
              Clear
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-10">
        <div className="max-w-5xl mx-auto px-5 py-4 flex items-center justify-between text-xs text-slate-400">
          <span>HR AI — Bilingual Resume Parser</span>
          <span>Built for Beamdata SDA Capstone</span>
        </div>
      </footer>

      {/* Toasts */}
      {toasts.map(t => (
        <Toast key={t.id} toast={t} onClose={() => removeToast(t.id)} />
      ))}

      {/* Inline keyframe animation */}
      <style>{`
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(12px) scale(0.96); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-slide-up {
          animation: slide-up 0.25s ease-out;
        }
      `}</style>
    </div>
  );
}

export default App;
