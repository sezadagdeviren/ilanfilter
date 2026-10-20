import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Yerelde (npm run dev) çalışırken bilgisayardaki dosyayı, 
    // canlıda (GitHub Pages vb.) çalışırken GitHub sunucusundaki dosyayı çeker.
    const url = import.meta.env.DEV 
      ? `/jobs.json?v=${Date.now()}`
      : `https://raw.githubusercontent.com/sezadagdeviren/ilanfilter/main/public/jobs.json?v=${Date.now()}`;
      
    fetch(url)
      .then(res => res.json())
      .then(data => {
        setJobs(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching jobs:", err);
        setLoading(false);
      });
  }, []);

  const filteredJobs = jobs.filter(job => {
    if (filter === 'suitable') return job.isSuitable;
    if (filter === 'unsuitable') return !job.isSuitable;
    return true;
  });

  const suitableCount = jobs.filter(j => j.isSuitable).length;
  const unsuitableCount = jobs.filter(j => !j.isSuitable).length;

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Kariyer Kapısı AI Filtresi</h1>
        <p>Yapay zeka, ilanları okur ve "Yeni Mezun, Bilgisayar Mühendisi, 2026 KPSS" profilinize uygunluğunu analiz eder.</p>
      </header>

      <div className="filters">
        <button
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          Tümü ({jobs.length})
        </button>
        <button
          className={`filter-btn ${filter === 'suitable' ? 'active suitable-btn' : ''}`}
          onClick={() => setFilter('suitable')}
        >
          ✅ Bana Uygun ({suitableCount})
        </button>
        <button
          className={`filter-btn ${filter === 'unsuitable' ? 'active unsuitable-btn' : ''}`}
          onClick={() => setFilter('unsuitable')}
        >
          ❌ Uygun Değil ({unsuitableCount})
        </button>
      </div>

      {loading ? (
        <div className="loading">İlanlar yükleniyor...</div>
      ) : filteredJobs.length === 0 ? (
        <div className="loading">Bu kategoride ilan bulunamadı.</div>
      ) : (
        <div className="jobs-grid">
          {filteredJobs.map(job => (
            <div key={job.id} className={`job-card ${job.isSuitable ? 'card-suitable' : 'card-unsuitable'}`}>
              <div className="job-header">
                <div>
                  <h2 className="job-title">{job.title}</h2>
                  <div className="job-inst">🏢 {job.institution}</div>
                  {job.department && <div className="job-dept">📂 {job.department}</div>}
                </div>
              </div>

              <div className="job-badges">
                {job.city && <span className="badge badge-city">📍 {job.city}</span>}
                <span className="badge badge-type">💼 {job.type}</span>
                {job.endDate && (
                  <span className="badge badge-date">📅 Son: {formatDate(job.endDate)}</span>
                )}
                <span className={`badge ${job.aiScanned ? 'badge-ai-scanned' : 'badge-ai-pending'}`}>
                  {job.aiScanned ? '🤖 AI Tarandı' : '⏳ AI Bekliyor'}
                </span>
                <span className={`badge ${job.isSuitable ? 'badge-suitable' : 'badge-unsuitable'}`}>
                  {job.isSuitable ? '✅ Uygun' : '❌ Uygun Değil'}
                </span>
              </div>

              <div className={`ai-analysis ${job.isSuitable ? 'suitable' : 'unsuitable'}`}>
                <span className="ai-icon">{job.isSuitable ? '✨' : '⚠️'}</span>
                <div>
                  <strong>AI Yorumu:</strong> {job.aiExplanation}
                </div>
              </div>

              {job.detailLink && (
                <a href={job.detailLink} target="_blank" rel="noopener noreferrer" className="detail-link">
                  🔗 İlana Git →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
