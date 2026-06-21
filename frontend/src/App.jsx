import { useState, useRef, useEffect } from 'react'
import './index.css'

function App() {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('idle') // idle, uploading, processing, completed, error
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')
  
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelection(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelection(e.target.files[0])
    }
  }

  const handleFileSelection = async (selectedFile) => {
    if (selectedFile.type !== 'application/pdf') {
      alert('Please upload a PDF file.')
      return
    }
    setFile(selectedFile)
    setStatus('uploading')
    setMessage('Uploading file...')
    setProgress(5)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (data.job_id) {
        setJobId(data.job_id)
        setStatus('processing')
      } else {
        setStatus('error')
        setMessage('Failed to start processing.')
      }
    } catch (err) {
      setStatus('error')
      setMessage('Network error during upload.')
    }
  }

  useEffect(() => {
    if (jobId && status === 'processing') {
      const eventSource = new EventSource(`http://localhost:8000/api/progress/${jobId}`)
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setProgress(data.progress)
        setMessage(data.message)

        if (data.status === 'completed') {
          setStatus('completed')
          const url = `http://localhost:8000/api/download/${jobId}`
          setDownloadUrl(url)
          eventSource.close()
          
          // Auto-trigger the download
          const a = document.createElement('a')
          a.href = url
          a.download = 'Voter_List.xlsx'
          document.body.appendChild(a)
          a.click()
          document.body.removeChild(a)
        } else if (data.status === 'error') {
          setStatus('error')
          setMessage(data.message)
          eventSource.close()
        }
      }

      eventSource.onerror = () => {
        setStatus((prevStatus) => {
          if (prevStatus !== 'completed') {
            setMessage('Lost connection to server.')
            return 'error'
          }
          return prevStatus
        })
        eventSource.close()
      }

      return () => eventSource.close()
    }
  }, [jobId, status])

  return (
    <div className="app-container">
      <div className="hero">
        <h1>Voter List Extractor</h1>
        <p>AI-Powered PDF to Excel Conversion</p>
      </div>

      <div className="glass-card">
        {status === 'idle' && (
          <div 
            className={`upload-zone ${isDragging ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="upload-icon">📄</div>
            <div className="upload-text">Drag & Drop your Telugu Voter PDF here</div>
            <div className="upload-subtext">or click to browse files</div>
            <input 
              type="file" 
              className="file-input" 
              accept=".pdf" 
              onChange={handleFileInput}
              ref={fileInputRef}
            />
          </div>
        )}

        {(status === 'uploading' || status === 'processing') && (
          <div className="progress-container">
            <div className="upload-icon">⚙️</div>
            <div className="status-text">{message}</div>
            <div className="progress-bar-bg" style={{ marginTop: '20px' }}>
              <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{progress}%</div>
          </div>
        )}

        {status === 'completed' && (
          <div className="progress-container">
            <div className="upload-icon" style={{ color: 'var(--success-color)' }}>✨</div>
            <div className="status-text" style={{ fontSize: '1.5rem', marginBottom: '10px' }}>Extraction Complete!</div>
            <div style={{ color: 'var(--text-muted)' }}>{file.name} has been processed successfully.</div>
            <a href={downloadUrl} className="btn btn-success" download>
              Download Excel
            </a>
            <div style={{ marginTop: '2rem' }}>
              <button 
                onClick={() => { setStatus('idle'); setFile(null); setJobId(null); setProgress(0); }}
                style={{ background: 'none', border: 'none', color: 'var(--primary-color)', cursor: 'pointer', textDecoration: 'underline' }}
              >
                Convert Another File
              </button>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="progress-container">
            <div className="upload-icon" style={{ color: '#ef4444' }}>❌</div>
            <div className="status-text" style={{ color: '#ef4444' }}>Error: {message}</div>
            <button 
              className="btn" 
              onClick={() => { setStatus('idle'); setFile(null); setJobId(null); }}
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
