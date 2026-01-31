import React, { useState } from 'react';
import { FaFileAlt } from 'react-icons/fa';
import './styles/ViewDataTab.css';

function isTextFile(filename: string): boolean {
  return filename.endsWith('.json') || filename.endsWith('.txt') || filename.endsWith('.csv');
}

const ViewDataTab: React.FC = () => {
  const [dataList, setDataList] = useState<string[]>([]);
  const [loadingData, setLoadingData] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [loadingContent, setLoadingContent] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');

  const fetchDataList = async () => {
    setLoadingData(true);
    setDataList([]);
    try {
      const res = await fetch('http://localhost:8000/list_rag_files/');
      const data: { files?: string[] } = await res.json();
      setDataList(data.files || []);
    } catch {
      setDataList([]);
    }
    setLoadingData(false);
  };

  const handleShowFile = async (filename: string) => {
    setSelectedFile(filename);
    setFileContent('');
    setLoadingContent(true);
    try {
      const res = await fetch(`http://localhost:8000/get_rag_file/?filename=${encodeURIComponent(filename)}`);
      const text = await res.text();
      setFileContent(text);
    } catch {
      setFileContent('Error loading file content.');
    }
    setLoadingContent(false);
  };

  const handleDeleteFile = async (filename: string) => {
    if (!window.confirm(`Delete file "${filename}" and its table/vector?`)) return;
    try {
      await fetch('http://localhost:8000/delete_rag_file/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });
      setMessage('Deleted!');
      setSelectedFile(null);
      fetchDataList();
    } catch {
      setMessage('Delete failed!');
    }
  };

  return (
    <div className="view-main">
      <div className="view-header">
        <h2 className="view-title">Uploaded Files</h2>
        <button className="view-refresh-btn" onClick={fetchDataList} disabled={loadingData}>
          {loadingData ? 'Loading...' : 'Refresh'}
        </button>
      </div>
      <div className="view-content">
        <div className="view-file-list">
          {dataList.length === 0 && !loadingData && <div className="view-no-data">No files found.</div>}
          {dataList.length > 0 && (
            <ul className="view-file-grid">
              {dataList.map((file, idx) => (
                <li
                  key={file + idx}
                  className={`view-file-item ${selectedFile === file ? 'selected' : ''}`}
                  onClick={() => handleShowFile(file)}
                >
                  <FaFileAlt className="view-file-icon" />
                  <span className="view-file-name">{file}</span>
                  <button
                    className="view-delete-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteFile(file);
                    }}
                    title="Delete"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        {selectedFile && (
          <div className="view-file-content">
            <div className="view-file-header">
              <h3 className="view-file-title">{selectedFile}</h3>
            </div>
            {isTextFile(selectedFile) ? (
              loadingContent ? (
                <div className="view-loading">Loading...</div>
              ) : (
                <pre className="view-text-content">{fileContent}</pre>
              )
            ) : (
              <a
                href={`http://localhost:8000/get_rag_file/?filename=${encodeURIComponent(selectedFile)}`}
                download={selectedFile}
                className="view-download-link"
              >
                Download file
              </a>
            )}
          </div>
        )}
        {message && <div className={`view-message ${message.includes('success') ? 'success' : 'error'}`}>{message}</div>}
      </div>
    </div>
  );
};

export default ViewDataTab;