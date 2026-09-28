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
    'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
    'bg-sky-500/10 text-sky-300 border-sky-500/20',
    'bg-violet-500/10 text-violet-300 border-violet-500/20',
    'bg-amber-500/10 text-amber-300 border-amber-500/20',
    'bg-rose-500/10 text-rose-300 border-rose-500/20',
    'bg-cyan-500/10 text-cyan-300 border-cyan-500/20',
    'bg-orange-500/10 text-orange-300 border-orange-500/20',
    'bg-teal-500/10 text-teal-300 border-teal-500/20',
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

const SkillIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-6.364-6.364L2.25 12l2.846.813a4.5 4.5 0 006.364 0l2.846-.813a4.5 4.5 0 00.813-6.364L12 2.25l.813 2.846a4.5 4.5 0 006.364 6.364L15.75 12l-2.846-.813a4.5 4.5 0 00-6.364 0l-2.846.813a4.5 4.5 0 00-.813 6.364z" />
  </svg>
);

const BriefcaseIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.24-4.091.24-6.187.24S2.47 18.48.383 18.24A2.12 2.12 0 01.125 15.03v-4.25c0-1.094.787-2.036 1.872-2.18 2.087-.24 4.09-.24 6.186-.24s4.098.24 6.187.24c1.085.144 1.872.986 1.872 2.18v4.25zM16.872 10.5c.396.712.787 1.472 1.128 2.25 1.306 2.86 2.083 6.123 2.083 9.375a1.125 1.125 0 01-1.125 1.125h-6.75a1.125 1.125 0 01-1.125-1.125c0-3.252.777-6.514 2.084-9.374.341-.778.732-1.538 1.128-2.25H16.872z" />
  </svg>
);

const GraduationIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.216 0 4.228.812 6 2.255V6.517A8.968 8.968 0 0018 3.75c-2.217 0-4.228.812-6 2.255v14.493A8.967 8.967 0 016 18c-2.216 0-4.227-.812-6-2.255V6.042z" />
  </svg>
);

const AwardIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.53 15.477c.184-.217.43-.39.736-.501l-1.947-1.947c.354-.433.766-.814 1.234-1.12a1.25 1.25 0 111.672 1.671c-.382.376-.856.702-1.358.955l-1.625-1.625a1.25 1.25 0 111.671-1.672c.308.5.687.98 1.12 1.234l1.948 1.947c-.217.184-.39.43-.501.736s-.217.527-.217.778v.405a1.25 1.25 0 01-1.12 1.234l-1.947 1.948c-.184.217-.43.39-.736.501l1.947 1.947c-.354.433-.766.814-1.234 1.12a1.25 1.25 0 11-1.672-1.671c.382-.376.856-.702 1.358-.955l1.625 1.625a1.25 1.25 0 11-1.671 1.672c-.308-.5-.687-.98-1.12-1.234l-1.948-1.947c.217-.184.39-.43.501-.736s.217-.527.217-.778V12.34a1.25 1.25 0 011.12-1.234l1.947-1.948c.184-.217.43-.39.736-.501l-1.947-1.947c.354-.433.766-.814 1.234-1.12a1.25 1.25 0 111.672 1.671c-.382.376-.856.702-1.358.955l-1.625-1.625a1.25 1.25 0 111.671-1.672c.308.5.687.98 1.12 1.234l1.948 1.947c-.217.184-.39.43-.501.736z" />
  </svg>
);

const FolderIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-7.5 0m3.75 2.383a14.406 14.406 0 01-9 0M14.25 18v-.192c0-.983.658-1.823 1.5-2.316a7.5 7.5 0 10-7.5-7.5 7.5 7.5 0 007.5 7.5c.841 0 1.5-.83 1.5-1.818V13.5m1.5.192v.192c0 .983-.658 1.823-1.5 2.316a7.5 7.5 0 107.5 7.5 7.5 7.5 0 00-7.5-7.5c-.841 0-1.5.83-1.5 1.818z" />
  </svg>
);

const GlobeIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016.562 0M3 5.621l4.125 10.5mA3 3 0 01-3 3m0 0v2.121m0 0h2.121m-3 3L3 15M3 5.621l5.25 13.125" />
  </svg>
);

const ClockIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const LinkIcon = () => (
  <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5a2.25 2.25 0 00-2.25-2.25H13.5m0 0L16 13.25m-4-4l4 4" />
  </svg>
);

// --- Component: Empty state ----------------------------------------------

function EmptyProfile() {
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="text-center max-w-[200px]">
        <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gray-800/60 border border-gray-700/50 flex items-center justify-center">
          <FileSvg />
        </div>
        <p className="text-xs text-gray-500">Waiting for a parsed resume</p>
      </div>
    </div>
  );
}

// --- Component: Education Card --------------------------------------------

function EducationCard({ item }: { item: Education }) {
  return (
    <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] px-4 py-4 transition hover:border-gray-700/80">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{item.degree ?? '—'}</p>
          <p className="text-xs text-gray-400 mt-0.5">{item.institution ?? '—'}</p>
        </div>
        <div className="text-right">
          <p className="text-xs font-medium text-gray-300">
            {formatYear(item.start_year)} – {formatYear(item.end_year)}
          </p>
          {item.gpa != null && (
            <p className="text-xs text-gray-500 mt-0.5">GPA: {item.gpa.toFixed(2)}</p>
          )}
        </div>
      </div>
    </div>
  );
}

// --- Component: Experience Card ------------------------------------------

function ExperienceCard({ item }: { item: WorkExperience }) {
  return (
    <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] px-4 py-4 transition hover:border-gray-700/80">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{item.role ?? '—'}</p>
          <p className="text-xs text-gray-400 mt-0.5">{item.company ?? '—'}</p>
          {item.description && (
            <p className="text-xs text-gray-500 mt-2 leading-relaxed line-clamp-3">{item.description}</p>
          )}
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-xs font-medium text-gray-300">
            {truncateMiddle(item.start_date)} – {truncateMiddle(item.end_date)}
          </p>
        </div>
      </div>
    </div>
  );
}

// --- Component: Certificate Card -----------------------------------------

function CertificateCard({ item }: { item: Certificate }) {
  return (
    <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] px-4 py-4 transition hover:border-gray-700/80">
      <p className="text-sm font-semibold text-white">{item.name ?? '—'}</p>
      <p className="text-xs text-gray-400 mt-1">{item.issuer ?? '—'}</p>
      <div className="flex gap-3 mt-2 text-xs text-gray-500">
        <span>Issued: {formatDate(item.issue_date)}</span>
        {item.expiry_date && <span>Expires: {formatDate(item.expiry_date)}</span>}
      </div>
    </div>
  );
}

// --- Component: Project Card ---------------------------------------------

function ProjectCard({ item }: { item: Project }) {
  return (
    <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] px-4 py-4 transition hover:border-gray-700/80">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold text-white">{item.name ?? '—'}</p>
        {item.link && (
          <a
            href={item.link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-indigo-300 hover:text-white font-medium flex items-center gap-1 flex-shrink-0 transition"
          >
            View
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5a2.25 2.25 0 00-2.25-2.25H13.5m0 0L16 13.25m-4-4l4 4" />
            </svg>
          </a>
        )}
      </div>
      {item.description && (
        <p className="text-xs text-gray-500 mt-2 leading-relaxed line-clamp-3">{item.description}</p>
      )}
    </div>
  );
}

// --- Component: Section header -------------------------------------------

function SectionHead({ icon, title, count }: { icon: React.ReactNode; title: string; count?: number }) {
  return (
    <div className="mb-3 flex items-center gap-2">
      {icon}
      <span className="text-xs font-semibold uppercase tracking-[0.35em] text-indigo-300">{title}</span>
      {count != null && (
        <span className="ml-auto text-xs text-gray-500 font-medium">{count}</span>
      )}
    </div>
  );
}

// --- Component: Toast -----------------------------------------------------

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
    success: 'bg-[#101016] border-emerald-500/30 text-gray-100 shadow-emerald-900/30',
    error: 'bg-[#101016] border-rose-500/30 text-gray-100 shadow-rose-900/30',
    info: 'bg-[#101016] border-indigo-500/30 text-gray-100 shadow-indigo-900/30',
  }[toast.type];

  const icon = {
    success: '✅',
    error: '✕',
    info: '✕',
  }[toast.type];

  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl border px-5 py-3 text-sm shadow-lg ${bg} animate-slide-up max-w-sm`}>
      <span className="text-lg">{icon}</span>
      <p className="flex-1">{toast.message}</p>
      <button onClick={onClose} className="text-gray-400 transition hover:text-white" aria-label="Dismiss">
        ✕
      </button>
    </div>
  );
}

// --- Component: Skill pill -----------------------------------------------

function SkillPill({ skill }: { skill: string }) {
  return (
    <span className={`inline-flex items-center px-3 py-1 text-xs font-medium rounded-xl border ${skillColor(skill)}`}>
      {skill}
    </span>
  );
}

// --- Main App -------------------------------------------------------------

function App() {
  const [apiUrl, setApiUrl] = useState(() => {
    const saved = localStorage.getItem('hr-ai-api-url');
    return saved ?? 'http://127.0.0.1:8000';
  });
  const [model, setModel] = useState('mock');
  const [availableModels, setAvailableModels] = useState<string[]>(['mock']);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [parsing, setParsing] = useState(false);
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [responseTime, setResponseTime] = useState<number | null>(null);

  const [toasts, setToasts] = useState<ToastData[]>([]);
  const toastIdRef = useRef(0);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = ++toastIdRef.current;
    setToasts(prev => [...prev, { id, type, message }]);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  useEffect(() => {
    localStorage.setItem('hr-ai-api-url', apiUrl);
  }, [apiUrl]);

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

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setIsDragging(true);
    else if (e.type === 'dragleave') setIsDragging(false);
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
        { method: 'POST', body: formData }
      );
      const elapsed = Math.round(performance.now() - start);
      setResponseTime(elapsed);

      if (!res.ok) {
        let errBody: string;
        try { errBody = await res.text(); } catch { errBody = res.statusText; }
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

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------
  return (
    <div className="min-h-screen bg-[#0E0E10] font-inter text-gray-100 custom-scrollbar">
      {/* gradient glow top */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-gradient-to-b from-indigo-500/30 via-transparent to-transparent blur-3xl opacity-60" />

      <div className="relative z-10 max-w-6xl mx-auto px-4 md:px-8 py-8 space-y-8">

        {/* ---------------------------------------------------------------------
           HEADER
        ----------------------------------------------------------------------- */}
        <header className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs uppercase tracking-[0.35em] text-indigo-300">
              <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
              HR AI
            </div>
            <h1 className="text-3xl md:text-4xl font-semibold text-white">HR AI — Resume Parser</h1>
            <p className="text-gray-400 text-sm md:text-base">Bilingual · PDF / DOCX · EN / AR</p>
          </div>

          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
            <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
              <button className="flex-1 rounded-2xl border border-indigo-500/40 bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(79,70,229,0.25)] transition hover:-translate-y-0.5 hover:bg-indigo-500 sm:flex-none">
                Parse Resume
              </button>
              <button className="flex-1 rounded-2xl border border-indigo-500/40 bg-transparent px-5 py-3 text-sm font-semibold text-indigo-200 transition hover:border-indigo-400 hover:text-white sm:flex-none">
                History
              </button>
              <button className="flex-1 rounded-2xl border border-gray-700 bg-gray-900/70 px-5 py-3 text-sm font-medium text-gray-200 transition-all duration-300 hover:scale-[1.01] hover:bg-gray-800 sm:flex-none">
                Settings
              </button>
            </div>
          </div>
        </header>

        {/* ---------------------------------------------------------------------
           API CONFIG CARD
        ----------------------------------------------------------------------- */}
        <div className="relative isolate rounded-2xl border border-indigo-900/40 bg-[#0B0B0E]/90 px-6 py-5 shadow-lg shadow-black/30 backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex-1 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-[0.4em] text-gray-400">API Endpoint</span>
                <button
                  onClick={fetchModels}
                  disabled={modelsLoading}
                  className="text-xs text-indigo-300 transition hover:text-white disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
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
              <div className="flex items-center gap-2">
                <input
                  type="url"
                  value={apiUrl}
                  onChange={e => setApiUrl(e.target.value)}
                  placeholder="http://127.0.0.1:8000"
                  className="flex-1 rounded-2xl border border-indigo-900/30 bg-[#09090B] px-4 py-3 text-gray-100 placeholder-gray-600 focus:border-indigo-400 focus:outline-none transition"
                />
                <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-300 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  Live
                </div>
              </div>
              {modelsError && (
                <p className="text-xs text-rose-400 flex items-center gap-1">
                  <AlertIcon /> {modelsError}
                </p>
              )}
            </div>

            <div className="sm:border-l sm:border-indigo-900/40 sm:pl-4">
              <span className="text-xs font-semibold uppercase tracking-[0.4em] text-gray-400 block mb-2">Model</span>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                className="w-full rounded-2xl border border-indigo-900/30 bg-[#09090B] px-4 py-3 text-gray-100 focus:border-indigo-400 focus:outline-none transition cursor-pointer"
              >
                {availableModels.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* ---------------------------------------------------------------------
           BODY: UPLOAD + PROFILE SIDE BY SIDE
        ----------------------------------------------------------------------- */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* Upload panel */}
          <section className="lg:col-span-3 space-y-4">
            <div className="relative isolate rounded-2xl border border-indigo-900/40 bg-[#0B0B0E]/90 p-6 shadow-lg shadow-black/30 backdrop-blur-sm">
              <h2 className="text-sm font-semibold text-white">Upload Resume</h2>
              <p className="text-xs text-gray-400 mt-0.5">PDF or DOCX — max 20 MB</p>

              {/* Drop zone */}
              <div
                className={`relative mt-4 rounded-2xl border-2 transition-all duration-200 cursor-pointer ${
                  isDragging
                    ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01] shadow-lg shadow-indigo-500/20'
                    : 'border-gray-800 hover:border-gray-700 hover:bg-gray-800/30'
                } ${file ? 'border-emerald-500/40 bg-emerald-500/5' : ''}`}
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

                <div className="flex flex-col items-center justify-center py-12 text-center pointer-events-none select-none">
                  {isDragging ? (
                    <div className="animate-bounce text-indigo-300">
                      <UploadIcon />
                    </div>
                  ) : (
                    <div className="text-gray-500">
                      <UploadIcon />
                    </div>
                  )}
                  <p className={`text-sm font-medium mt-4 ${isDragging ? 'text-indigo-200' : 'text-gray-400'}`}>
                    {isDragging ? 'Drop your resume here' : file ? 'File selected — click to change' : 'Drag & drop or click to browse'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1.5">
                    Supports PDF and DOCX files
                  </p>
                </div>
              </div>

              {/* File info */}
              {file && (
                <div className="mt-4 flex items-center gap-3 rounded-2xl border border-gray-800 bg-[#09090B] px-4 py-3">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-300 flex items-center justify-center flex-shrink-0 border border-indigo-500/20">
                    <FileSvg />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{file.name}</p>
                    <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                  <button
                    onClick={clearFile}
                    className="text-gray-400 transition hover:text-rose-300"
                    title="Remove file"
                  >
                    <CloseIcon />
                  </button>
                </div>
              )}

              {/* Parse button */}
              <div className="mt-5">
                <button
                  onClick={handleParse}
                  disabled={!file || parsing}
                  className={`w-full rounded-2xl py-3.5 px-6 text-sm font-semibold transition-all duration-200 flex items-center justify-center gap-2 ${
                    !file || parsing
                      ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white shadow-[0_12px_30px_rgba(79,70,229,0.25)] hover:-translate-y-0.5'
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
                  <p className="text-center text-xs text-gray-500 mt-2">Completed in {responseTime} ms</p>
                )}
              </div>
            </div>
          </section>

          {/* Profile panel */}
          <section className="lg:col-span-2 space-y-4">
            {!profile ? (
              <div className="relative isolate rounded-2xl border border-indigo-900/40 bg-[#0B0B0E]/90 p-6 shadow-lg shadow-black/30 backdrop-blur-sm h-full flex flex-col">
                <div className="flex items-center justify-between pr-2">
                  <h2 className="text-sm font-semibold text-white">Parsed Profile</h2>
                  <span className="text-xs text-gray-500">en / ar</span>
                </div>
                <div className="mt-4 flex-1">
                  <EmptyProfile />
                </div>

                {/* quote */}
                <blockquote className="mt-4 rounded-xl border border-indigo-900/30 bg-indigo-500/5 px-5 py-3 text-center text-xs text-indigo-200/60">
                  Resume parsing
                </blockquote>
              </div>
            ) : (
              <div className="relative isolate rounded-2xl border border-indigo-900/40 bg-[#0B0B0E]/90 p-6 shadow-lg shadow-black/30 backdrop-blur-sm">
                {/* header */}
                <div className="flex items-center justify-between pr-2">
                  <div>
                    <h2 className="text-sm font-semibold text-white">Parsed Profile</h2>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {profile.detected_source_language ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-gray-800/80 px-1.5 py-0.5 text-[10px] font-medium text-gray-300">
                          {profile.detected_source_language.toUpperCase()}
                        </span>
                      ) : (
                        'language auto-detected'
                      )}
                    </p>
                  </div>
                  <button
                    onClick={() => profile && downloadJson(profile, 'candidate-profile.json')}
                    className="flex items-center gap-1.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 px-3 py-1.5 text-xs font-medium text-indigo-200 transition hover:border-indigo-400 hover:text-white hover:bg-indigo-500/20"
                  >
                    <DownloadIcon />
                    Download JSON
                  </button>
                </div>

                {/* avatar + name */}
                <div className="mt-5 flex items-start gap-4 rounded-xl border border-gray-800/80 bg-[#09090B] px-5 py-4">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-600 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-md flex-shrink-0 border border-indigo-400/30">
                    {(profile.full_name ?? '?')[0].toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-base font-bold text-white truncate">{profile.full_name ?? 'Unknown'}</h3>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mt-1.5 text-xs text-gray-400">
                      {profile.email && (
                        <a href={`mailto:${profile.email}`} className="text-indigo-300 hover:text-white truncate transition">
                          {profile.email}
                        </a>
                      )}
                      {profile.phone && <span className="truncate">{profile.phone}</span>}
                      {profile.location && <span className="truncate">{profile.location}</span>}
                    </div>
                    {profile.summary && (
                      <p className="text-xs text-gray-500 mt-2 leading-relaxed line-clamp-2">{profile.summary}</p>
                    )}
                  </div>
                </div>

                {/* sections */}
                <div className="mt-4 space-y-2">
                  {/* Skills */}
                  <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                    <SectionHead icon={<SkillIcon />} title="Skills" count={profile.skills.length} />
                    {profile.skills.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {profile.skills.map(skill => (
                          <SkillPill key={skill} skill={skill} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No skills extracted</p>
                    )}
                  </div>

                  {/* Experience */}
                  <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                    <SectionHead icon={<BriefcaseIcon />} title="Experience" count={profile.work_experience.length} />
                    {profile.work_experience.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.work_experience.map((exp, i) => (
                          <ExperienceCard key={i} item={exp} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No work experience extracted</p>
                    )}
                  </div>

                  {/* Education */}
                  <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                    <SectionHead icon={<GraduationIcon />} title="Education" count={profile.education.length} />
                    {profile.education.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.education.map((edu, i) => (
                          <EducationCard key={i} item={edu} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No education extracted</p>
                    )}
                  </div>

                  {/* Certificates */}
                  <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                    <SectionHead icon={<AwardIcon />} title="Certifications" count={profile.certificates.length} />
                    {profile.certificates.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.certificates.map((cert, i) => (
                          <CertificateCard key={i} item={cert} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No certifications extracted</p>
                    )}
                  </div>

                  {/* Projects */}
                  <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                    <SectionHead icon={<FolderIcon />} title="Projects" count={profile.projects.length} />
                    {profile.projects.length > 0 ? (
                      <div className="space-y-2.5">
                        {profile.projects.map((proj, i) => (
                          <ProjectCard key={i} item={proj} />
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-500">No projects extracted</p>
                    )}
                  </div>

                  {/* Languages */}
                  {profile.languages.length > 0 && (
                    <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                      <SectionHead icon={<GlobeIcon />} title="Languages" />
                      <div className="flex flex-wrap gap-2">
                        {profile.languages.map(lang => (
                          <span key={lang} className="inline-flex items-center gap-1.5 rounded-xl bg-gray-800/80 px-3 py-1 text-xs font-medium text-gray-300 border border-gray-700/50">
                            <span className="h-1.5 w-1.5 rounded-full bg-gray-500" />
                            {lang}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Years of experience */}
                  {profile.years_of_experience != null && (
                    <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                      <SectionHead icon={<ClockIcon />} title="Experience" />
                      <p className="text-sm text-gray-300">
                        {profile.years_of_experience} {profile.years_of_experience === 1 ? 'year' : 'years'} of experience
                      </p>
                    </div>
                  )}

                  {/* Links */}
                  {(profile.github || profile.linkedin || profile.portfolio) && (
                    <div className="rounded-xl border border-gray-800/80 bg-[#0B0B0E] p-4">
                      <SectionHead icon={<LinkIcon />} title="Links" />
                      <div className="flex flex-wrap gap-2">
                        {profile.github && (
                          <a href={profile.github} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-xl bg-gray-900/80 px-3.5 py-1.5 text-xs font-medium text-gray-200 border border-gray-700/50 hover:border-gray-600 hover:text-white transition">
                            GitHub
                          </a>
                        )}
                        {profile.linkedin && (
                          <a href={profile.linkedin} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-500/10 px-3.5 py-1.5 text-xs font-medium text-indigo-200 border border-indigo-500/20 hover:border-indigo-400 hover:text-white transition">
                            LinkedIn
                          </a>
                        )}
                        {profile.portfolio && (
                          <a href={profile.portfolio} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/10 px-3.5 py-1.5 text-xs font-medium text-emerald-300 border border-emerald-500/20 hover:border-emerald-400 hover:text-white transition">
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

        {/* parse error */}
        {parseError && (
          <div className="rounded-2xl border border-rose-500/30 bg-[#101016] px-5 py-4 flex items-start gap-3 shadow-lg shadow-rose-900/20">
            <AlertIcon />
            <div className="flex-1">
              <p className="text-sm font-semibold text-rose-300">Parse failed</p>
              <p className="text-sm text-gray-300 mt-1 break-words">{parseError}</p>
            </div>
            <button onClick={clearFile} className="ml-auto text-xs text-rose-300 hover:text-rose-200 transition font-medium">
              Clear
            </button>
          </div>
        )}

        {/* footer */}
        <footer className="rounded-2xl border border-indigo-900/40 bg-[#0B0B0E]/80 px-6 py-6 text-center text-gray-300 shadow-inner shadow-black/30">
          <p className="text-sm text-gray-200">HR AI — Bilingual Resume Parser</p>
          <p className="mt-1 text-xs text-gray-500">Built for Beamdata SDA Capstone</p>
        </footer>
      </div>

      {/* toast */}
      {toasts.map(t => (
        <Toast key={t.id} toast={t} onClose={() => removeToast(t.id)} />
      ))}

      {/* keyframe */}
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
