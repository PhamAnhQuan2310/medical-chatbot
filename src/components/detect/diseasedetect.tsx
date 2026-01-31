import React, { useState } from "react";
import "./diseasedetect.css";

interface DiagnosisResponse {
  domain: string;
  router_confidence: number;
  diagnosis: string;
}

const API_URL = "http://localhost:8000/api/disease-image";

const domainLabel: Record<string, string> = {
  chest_xray: "Ảnh X-quang phổi",
  retina_oct: "Ảnh OCT mắt",
  skin_derm: "Ảnh bệnh da",
  teeth_cavity: "Ảnh răng / sâu răng",
};

const DiseaseDetect: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiagnosisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;

    setFile(f);
    setError(null);
    setResult(null);
    setPreview(URL.createObjectURL(f));
  };

  const analyzeImage = async () => {
    if (!file) {
      setError("⚠ Vui lòng chọn một ảnh.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const form = new FormData();
      form.append("file", file);

      const res = await fetch(API_URL, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        const dt = await res.json().catch(() => ({}));
        throw new Error(dt.detail || "Lỗi server.");
      }

      const data: DiagnosisResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Lỗi không xác định.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-detect">
      <div className="detect-wrapper">
        <h1 className="detect-title">🩺 Chẩn đoán hình ảnh y khoa</h1>

        <div className="upload-section">
          <p>Chọn ảnh X-ray phổi, OCT mắt, ảnh da hoặc ảnh răng</p>
          <input type="file" accept="image/*" onChange={handleFileSelect} />
        </div>

        {preview && (
          <div className="preview-container">
            <img src={preview} className="preview-img" alt="preview" />
          </div>
        )}

        <button
          className="detect-button"
          onClick={analyzeImage}
          disabled={loading}
        >
          {loading ? "Đang phân tích..." : "Phân tích ảnh"}
        </button>

        {error && (
          <p style={{ color: "red", marginTop: "10px" }}>{error}</p>
        )}

        {result && (
          <div className="result-box">
            <div className="result-title">Kết quả</div>
            <div className="result-line">
              <b>Loại ảnh:</b> {domainLabel[result.domain]}
            </div>
            <div className="result-line">
              <b>Xác suất router:</b> {result.router_confidence.toFixed(3)}
            </div>
            <div className="result-line">
              <b>Chẩn đoán:</b> {result.diagnosis}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DiseaseDetect;
