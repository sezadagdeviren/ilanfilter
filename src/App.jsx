import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState('all'); // all, suitable, unsuitable
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In a real scenario, this would fetch from GitHub Pages or your backend API
    fetch('/jobs.json')
      .then(res => res.json())
      .then(data => {
        setJobs(data);
        setLoading(false);
      })
      .catch(err => console.error("Error fetching jobs:", err));
  }, []);

  const filteredJobs = jobs.filter(job => {
    if (filter === 'suitable') return job.isSuitable;
    if (filter === 'unsuitable') return !job.isSuitable;
    return true;
  });

  return (
    <div className="container">
      <header className="header">
        <h1>Kariyer Kapısı AI Filtresi</h1>
        <p>Yapay zeka, ilanları sizin için okur ve "Yeni Mezun, Bilgisayar Mühendisi, 2026 KPSS" profilinize uyup uymadığını analiz eder.</p>
      </header>

      <div className="filters">
        <button 
          className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          Tümü ({jobs.length})
        </button>
        <button 
          className={`filter-btn ${filter === 'suitable' ? 'active' : ''}`}
          onClick={() => setFilter('suitable')}
        >
          Bana Uygun ({jobs.filter(j => j.isSuitable).length})
        </button>
        <button 
          className={`filter-btn ${filter === 'unsuitable' ? 'active' : ''}`}
          onClick={() => setFilter('unsuitable')}
        >
          Uygun Değil ({jobs.filter(j => !j.isSuitable).length})
        </button>
      </div>

      {loading ? (
        <div className="loading">İlanlar analiz ediliyor...</div>
      ) : (
        <div className="jobs-grid">
          {filteredJobs.map(job => (
            <div key={job.id} className="job-card">
              <div className="job-header">
                <div>
                  <h2 className="job-title">{job.title}</h2>
                  <div className="job-inst">🏢 {job.institution}</div>
                </div>
              </div>
              
              <div className="job-badges">
                <span className="badge">📍 {job.city}</span>
                <span className="badge">💼 {job.type}</span>
              </div>
              
              <div className={`ai-analysis ${job.isSuitable ? 'suitable' : 'unsuitable'}`}>
                <span className="ai-icon">{job.isSuitable ? '✨' : '⚠️'}</span>
                <div>
                  <strong>AI Yorumu:</strong> {job.aiExplanation}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
