import React, { useRef, useState } from 'react';
import { FaCloudUploadAlt } from 'react-icons/fa';
import './styles/UploadTabThuoc.css';

interface DrugDraft {
  drug_name: string;
  concentration?: string | null;
  dosage_form?: string | null;
  manufacturer?: string | null;
  exp_date?: string | null;
  indication?: string | null;
  warning?: string | null;
  raw_text: string;
}

const UploadThuocTab: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [scanning, setScanning] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const [draft, setDraft] = useState<DrugDraft | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // chỉ cho phép ảnh
  const handleFiles = (fileList: FileList) => {
    const img = Array.from(fileList).find((f) =>
      f.type === 'image/jpeg' ||
      f.type === 'image/png' ||
      f.name.toLowerCase().endsWith('.jpg') ||
      f.name.toLowerCase().endsWith('.jpeg') ||
      f.name.toLowerCase().endsWith('.png')
    );
    if (!img) {
      setMessage('Vui lòng chọn file ảnh (.jpg, .jpeg, .png).');
      return;
    }
    setFile(img);
    setDraft(null);
    setMessage('');
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

  // Gửi ảnh lên backend để OCR + parse
  const handleScan = async () => {
    if (!file) {
      setMessage('Vui lòng chọn 1 ảnh thuốc trước.');
      return;
    }
    setScanning(true);
    setMessage('');
    setDraft(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/thuoc_ocr/ocr-image', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'OCR failed');
      }

      const data: DrugDraft = await res.json();
      setDraft(data);
      setMessage('Đã đọc OCR, kiểm tra lại thông tin bên dưới rồi bấm Lưu.');
    } catch (err: any) {
      setMessage(`Lỗi OCR: ${err.message || 'Không rõ nguyên nhân.'}`);
    } finally {
      setScanning(false);
    }
  };

  // Lưu thuốc vào DB
  const handleSave = async () => {
    if (!draft) {
      setMessage('Chưa có dữ liệu thuốc để lưu.');
      return;
    }
    if (!draft.drug_name || draft.drug_name.trim() === '') {
      setMessage('Tên thuốc đang trống, vui lòng nhập.');
      return;
    }

    setSaving(true);
    setMessage('');

    try {
      const res = await fetch('http://localhost:8000/thuoc_ocr/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(draft),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Save failed');
      }

      const data = await res.json();
      setMessage(`Lưu thuốc thành công (id = ${data.id}).`);
      // reset nếu muốn
      // setFile(null);
      // setDraft(null);
    } catch (err: any) {
      setMessage(`Lưu thất bại: ${err.message || 'Không rõ nguyên nhân.'}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="upload-main">
      <div className="upload-header">
        <h2 className="upload-title">Upload Ảnh Thuốc (Admin)</h2>
      </div>

      {/* KHU VỰC CHỌN ẢNH */}
      <div
        className={`upload-dropzone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <FaCloudUploadAlt className="upload-icon" />
        <div className="upload-label">
          Kéo thả ảnh thuốc vào đây, hoặc click để chọn
        </div>
        <div className="upload-sub-label">
          (Hỗ trợ: .jpg, .jpeg, .png)
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".jpg,.jpeg,.png"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </div>

      {file && (
        <div className="upload-filelist">
          <div className="upload-filelist-title">Ảnh đã chọn:</div>
          <div className="upload-filelist-grid">
            <div className="upload-file-item">
              <span className="upload-file-name">{file.name}</span>
            </div>
          </div>
        </div>
      )}

      {file && (
        <div className="image-preview">
          <img src={URL.createObjectURL(file)} alt="preview" />
        </div>
      )}


      {/* NÚT SCAN OCR */}
      <button
        className="upload-submit-btn"
        onClick={handleScan}
        disabled={scanning || !file}
      >
        {scanning ? 'Đang đọc OCR...' : 'Scan từ ảnh'}
      </button>

      {/* FORM CHỈNH SỬA THUỐC */}
      {draft && (
        <div className="thuoc-card">
          <h3>🧾 Thông tin thuốc</h3>

          {/* THÔNG TIN CHÍNH */}
          <div className="thuoc-section">
            <div className="field">
              <label>Tên thuốc</label>
              <input
                className="input-main"
                value={draft.drug_name ?? ''}
                onChange={(e) =>
                  setDraft(d => d ? { ...d, drug_name: e.target.value } : d)
                }
              />
            </div>

            <div className="field-row">
              <div className="field">
                <label>Hàm lượng</label>
                <input
                  value={draft.concentration ?? ''}
                  onChange={(e) =>
                    setDraft(d => d ? { ...d, concentration: e.target.value } : d)
                  }
                />
              </div>

              <div className="field">
                <label>Dạng bào chế</label>
                <input
                  value={draft.dosage_form ?? ''}
                  onChange={(e) =>
                    setDraft(d => d ? { ...d, dosage_form: e.target.value } : d)
                  }
                />
              </div>
            </div>
          </div>

          {/* THÔNG TIN PHỤ */}
          <div className="thuoc-section">
            <div className="field">
              <label>Nhà sản xuất</label>
              <input
                value={draft.manufacturer ?? ''}
                onChange={(e) =>
                  setDraft(d => d ? { ...d, manufacturer: e.target.value } : d)
                }
              />
            </div>

            <div className="field">
              <label>Hạn dùng</label>
              <input
                value={draft.exp_date ?? ''}
                onChange={(e) =>
                  setDraft(d => d ? { ...d, exp_date: e.target.value } : d)
                }
              />
            </div>
          </div>

          {/* TEXTAREA */}
          <div className="thuoc-section">
            <div className="field">
              <label>Công dụng</label>
              <textarea
                rows={3}
                value={draft.indication ?? ''}
                onChange={(e) =>
                  setDraft(d => d ? { ...d, indication: e.target.value } : d)
                }
              />
            </div>

            <div className="field">
              <label>Cảnh báo</label>
              <textarea
                rows={3}
                value={draft.warning ?? ''}
                onChange={(e) =>
                  setDraft(d => d ? { ...d, warning: e.target.value } : d)
                }
              />
            </div>
          </div>

          {/* RAW OCR */}
          <details className="raw-ocr">
            <summary>Xem văn bản OCR gốc</summary>
            <textarea
              rows={6}
              value={draft.raw_text}
              onChange={(e) =>
                setDraft(d => d ? { ...d, raw_text: e.target.value } : d)
              }
            />
          </details>

          <button
            className="upload-submit-btn primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Đang lưu...' : 'Lưu thuốc'}
          </button>
        </div>
      )}

      {message && (
        <div
          className={`upload-message ${
            message.toLowerCase().includes('thành công') ? 'success' : 'error'
          }`}
        >
          {message}
        </div>
      )}
    </div>
  );
};

export default UploadThuocTab;
