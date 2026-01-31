import React from 'react';
import './NodePanel.css';

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

// Interface for node type configuration
interface NodeTypeConfig {
  type: NodeType;
  label: string;
}

// Interface for component props
interface NodePanelProps {
  nodeTypes: NodeTypeConfig[];
  workflowType: 'data' | 'chatbot';
}

const NodePanel: React.FC<NodePanelProps> = ({ nodeTypes, workflowType }) => {
  // Handle drag start event
  const onDragStart = (event: React.DragEvent<HTMLDivElement>, nodeType: NodeType, nodeName: string) => {
    console.log('Starting drag:', nodeType, nodeName);

    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('nodeName', nodeName);
    event.dataTransfer.setData('text/plain', nodeType);

    event.dataTransfer.effectAllowed = 'move';
  };

  // Determine node types to display based on workflow type
  const getNodeTypesToDisplay = (): NodeTypeConfig[] => {
    console.log('workflowType:', workflowType);
    console.log('nodeTypes:', nodeTypes);

    if (workflowType === 'data') {
      return [
        { type: 'InputNode', label: 'Dữ liệu' },
        { type: 'ConditionalNode', label: 'Điều kiện' },
        { type: 'IntentClassifierNode', label: 'Dự đoán ngữ cảnh' },
        { type: 'RAGNode', label: 'Lưu trong vector DB' },
        { type: 'OutputNode', label: 'Lưu vào file JSON' },
        { type: 'DatabaseNode', label: 'Kho dữ liệu' },
      ];
    } else {
      return [
        { type: 'InputNode', label: 'Đầu vào' },
        { type: 'OutputNode', label: 'Đầu ra' },
        { type: 'IntentClassifierNode', label: 'Phân loại ý định' },
        { type: 'RAGNode', label: 'RAG' },
        { type: 'SQLNode', label: 'SQL' },
        { type: 'FHIRPatientNode', label: 'Thông tin bệnh nhân' },
      ];
    }
  };

  const displayNodeTypes = getNodeTypesToDisplay();

  // Get panel title based on workflow type
  const getPanelTitle = (): string => {
    return workflowType === 'data' ? 'Nodes xử lý dữ liệu' : 'Nodes chatbot';
  };

  return (
    <div className="node-panel">
      <div className="node-panel-header">{getPanelTitle()}</div>
      <div className="node-list">
        {displayNodeTypes.map((type) => (
          <div
            key={type.type}
            className="node-item"
            onDragStart={(event) => onDragStart(event, type.type, type.label)}
            draggable
          >
            {type.label || type.type}
          </div>
        ))}
      </div>
    </div>
  );
};

export default NodePanel;