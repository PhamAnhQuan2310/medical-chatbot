
import React, { useState, useEffect } from 'react';
import './WorkflowSidebar.css';
import type { Node } from 'reactflow';

// Define node types supported
type NodeType =
  | 'InputNode'
  | 'OutputNode'
  | 'IntentClassifierNode'
  | 'RAGNode'
  | 'SQLNode'
  | 'FHIRPatientNode'
  | 'ConditionalNode'
  | 'DatabaseNode';

// Interface for node data
interface NodeData {
  label: string;
  nodeType: NodeType;
  parameters: Record<string, string | number | boolean | undefined>;
}

// Interface for parameter field configuration
interface ParamField {
  key: string;
  label: string;
  type: 'text' | 'checkbox' | 'select';
  options?: string[];
}

// Interface for component props
interface WorkflowSidebarProps {
  selectedNode: Node<NodeData> | null;
  updateNodeParameters: (id: string, parameters: Record<string, string | number | boolean | undefined>) => void;
  deleteNode: (id: string) => void;
}

const WorkflowSidebar: React.FC<WorkflowSidebarProps> = ({ selectedNode, updateNodeParameters, deleteNode }) => {
  const [parameters, setParameters] = useState<Record<string, string | number | boolean | undefined>>({});

  useEffect(() => {
    if (selectedNode && selectedNode.data.parameters) {
      setParameters(selectedNode.data.parameters);
    } else {
      setParameters({});
    }
  }, [selectedNode]);

  const handleParameterChange = (key: string, value: string | number | boolean | undefined) => {
    const updatedParameters = {
      ...parameters,
      [key]: value,
    };

    setParameters(updatedParameters);

    if (selectedNode) {
      updateNodeParameters(selectedNode.id, updatedParameters);
    }
  };

  const handleDeleteNode = () => {
    if (selectedNode && window.confirm('Bạn có chắc chắn muốn xóa node này?')) {
      deleteNode(selectedNode.id);
    }
  };

  // If no node is selected
  if (!selectedNode) {
    return (
      <div className="workflow-sidebar">
        <div className="sidebar-header">Thuộc tính</div>
        <div className="sidebar-content empty">
          <p>Chọn một node để xem và chỉnh sửa thuộc tính</p>
        </div>
      </div>
    );
  }

  // Default parameters based on node type
  let paramFields: ParamField[] = [];

  switch (selectedNode.data.nodeType) {
    case 'InputNode':
      paramFields = [{ key: 'default_value', label: 'Giá trị mặc định', type: 'text' }];
      break;
    case 'OutputNode':
      paramFields = [{ key: 'output_key', label: 'Khóa đầu ra', type: 'text' }];
      break;
    case 'IntentClassifierNode':
      paramFields = [
        { key: 'use_gemini', label: 'Sử dụng Gemini', type: 'checkbox' },
        { key: 'gemini_api_url', label: 'URL API Gemini', type: 'text' },
        { key: 'gemini_api_key', label: 'Khóa API Gemini', type: 'text' },
      ];
      break;
    case 'SQLNode':
      paramFields = [{ key: 'db_path', label: 'Đường dẫn database', type: 'text' }];
      break;
    case 'RAGNode':
      paramFields = [
        { key: 'collection_name', label: 'Tên bộ sưu tập', type: 'text' },
        { key: 'top_k', label: 'Số kết quả trả về', type: 'text' },
      ];
      break;
    case 'FHIRPatientNode':
      paramFields = [
        { key: 'fhir_server', label: 'URL máy chủ FHIR', type: 'text' },
        { key: 'use_real_data', label: 'Dùng dữ liệu thực', type: 'checkbox' },
      ];
      break;
    case 'ConditionalNode':
      paramFields = [
        {
          key: 'condition_type',
          label: 'Loại điều kiện',
          type: 'select',
          options: ['equals', 'contains', 'greater_than', 'less_than'],
        },
        { key: 'value_path', label: 'Đường dẫn giá trị', type: 'text' },
        { key: 'comparison_value', label: 'Giá trị so sánh', type: 'text' },
      ];
      break;
    case 'DatabaseNode':
      paramFields = [
        {
          key: 'db_type',
          label: 'Loại DB',
          type: 'select',
          options: ['vector', 'sql', 'json', 'mysql'],
        },
        { key: 'collection_name', label: 'Tên bộ sưu tập', type: 'text' },
        { key: 'connection_string', label: 'Chuỗi kết nối', type: 'text' },
      ];
      break;
    default:
      paramFields = [];
  }

  return (
    <div className="workflow-sidebar">
      <div className="sidebar-header">Thuộc tính node</div>
      <div className="sidebar-content">
        <div className="property-group">
          <label className="property-label">Loại node</label>
          <div className="property-value">{selectedNode.data.nodeType}</div>
        </div>
        <div className="property-group">
          <label className="property-label">Nhãn</label>
          <input
            type="text"
            value={selectedNode.data.label || ''}
            onChange={(e) => handleParameterChange('label', e.target.value)}
            className="property-input"
          />
        </div>
        {paramFields.map((field) => (
          <div className="property-group" key={field.key}>
            <label className="property-label">{field.label}</label>
            {field.type === 'text' && (
              <input
                type="text"
                value={parameters[field.key] != null ? String(parameters[field.key]) : ''}
                onChange={(e) => handleParameterChange(field.key, e.target.value)}
                className="property-input"
              />
            )}
            {field.type === 'checkbox' && (
              <input
                type="checkbox"
                checked={!!parameters[field.key]}
                onChange={(e) => handleParameterChange(field.key, e.target.checked)}
                className="property-checkbox"
              />
            )}
            {field.type === 'select' && (
              <select
                value={parameters[field.key] != null ? String(parameters[field.key]) : ''}
                onChange={(e) => handleParameterChange(field.key, e.target.value)}
                className="property-select"
              >
                <option value="">Chọn...</option>
                {field.options?.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            )}
          </div>
        ))}
        <div className="property-group">
          <button
            onClick={handleDeleteNode}
            className="delete-node-btn"
          >
            Xóa node
          </button>
        </div>
      </div>
    </div>
  );
};

export default WorkflowSidebar;
