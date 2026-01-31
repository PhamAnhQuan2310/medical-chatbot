import React, { useRef, useState } from 'react';
import { FaCloudUploadAlt } from 'react-icons/fa';
import { FaFileAlt } from 'react-icons/fa';
import './styles/UploadTab.css';

interface FileWithType extends File {
  type: string;
  name: string;
}

const allowedTypes: string[] = [
  'application/json',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'text/plain',
  'text/csv',
];

const UploadTab: React.FC = () => {
  const [files, setFiles] = useState<FileWithType[]>([]);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (fileList: FileList) => {
    const validFiles = Array.from(fileList).filter((file: FileWithType) =>
      allowedTypes.includes(file.type) ||
      file.name.endsWith('.json') ||
      file.name.endsWith('.docx') ||
      file.name.endsWith('.xlsx') ||
      file.name.endsWith('.txt') ||
      file.name.endsWith('.csv')
    );
    setFiles(validFiles);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else setDragActive(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  const handleUpload = async () => {
    if (!files.length) {
      setMessage('Please select at least one file.');
      return;
    }
    setUploading(true);
    setMessage('');
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    try {
      await fetch('http://localhost:8000/upload_rag_files/', { method: 'POST', body: formData });
      for (const file of files) {
        if (file.name.endsWith('.docx') || file.name.endsWith('.xlsx') || file.name.endsWith('.txt') || file.name.endsWith('.pdf') || file.name.endsWith('.json')) {
          await fetch('http://localhost:8000/ingest_to_vector/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: file.name }),
          });
        } else if (file.name.endsWith('.csv')) {
          const tableName = file.name.replace(/\.csv$/i, '');
          await fetch('http://localhost:8000/import_csv_to_db/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: file.name, table_name: tableName }),
          });
        }
      }
      setMessage('Upload & import/ingest successful!');
      setFiles([]);
    } catch {
      setMessage('Upload failed. Please try again.');
    }
    setUploading(false);
  };

  return (
    <div className="upload-main">
      <div className="upload-header">
        <h2 className="upload-title">Upload Data Files</h2>
      </div>
      <div
        className={`upload-dropzone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <FaCloudUploadAlt className="upload-icon" />
        <div className="upload-label">Drag & drop files here, or click to select</div>
        <div className="upload-sub-label">(Supported: .json, .docx, .xlsx, .txt, .csv)</div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".json,.docx,.xlsx,.txt,.csv"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </div>
      {files.length > 0 && (
        <div className="upload-filelist">
          <div className="upload-filelist-title">Selected files:</div>
          <div className="upload-filelist-grid">
            {files.map((file, idx) => (
              <div key={file.name + idx} className="upload-file-item">
                <FaFileAlt className="upload-file-icon" />
                <span className="upload-file-name">{file.name}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      <button className="upload-submit-btn" onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Uploading...' : 'Submit'}
      </button>
      {message && <div className={`upload-message ${message.includes('success') ? 'success' : 'error'}`}>{message}</div>}
    </div>
  );
};

export default UploadTab;