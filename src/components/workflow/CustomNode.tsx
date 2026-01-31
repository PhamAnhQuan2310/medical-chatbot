import React, { memo } from 'react';
import { Handle, Position} from 'reactflow';
import type { NodeProps } from 'reactflow';
import './CustomNode.css';

// Define the node types supported
type NodeType =
  | 'InputNode'
  | 'OutputNode'
  | 'IntentClassifierNode'
  | 'RAGNode'
  | 'SQLNode'
  | 'FHIRPatientNode'
  | 'ConditionalNode'
  | 'DatabaseNode';

// Define the shape of the data prop
interface CustomNodeData {
  nodeType?: NodeType;
  label: string;
}

// Extend NodeProps from reactflow to type the props
interface CustomNodeProps extends NodeProps<CustomNodeData> {
  isConnectable: boolean;
}

function CustomNode({ data, isConnectable }: CustomNodeProps) {
  // Determine color based on node type
  let headerColor: string = '#6366F1'; // Default color

  switch (data.nodeType) {
    // Common nodes for both workflows
    case 'InputNode':
      headerColor = '#10B981'; // Green
      break;
    case 'OutputNode':
      headerColor = '#F43F5E'; // Red
      break;
    case 'IntentClassifierNode':
      headerColor = '#EC4899'; // Pink
      break;
    case 'RAGNode':
      headerColor = '#3B82F6'; // Blue
      break;

    // Nodes for regular workflow
    case 'SQLNode':
      headerColor = '#6366F1'; // Purple
      break;
    case 'FHIRPatientNode':
      headerColor = '#14B8A6'; // Teal
      break;

    // Nodes for Data Workflow
    case 'ConditionalNode':
      headerColor = '#F59E0B'; // Orange
      break;
    case 'DatabaseNode':
      headerColor = '#8B5CF6'; // Deep Purple
      break;

    default:
      headerColor = '#6366F1'; // Default color
  }

  return (
    <div className="custom-node">
      <div className="custom-node-header" style={{ background: headerColor }}>
        {data.nodeType || 'Node'}
      </div>
      <div className="custom-node-content">
        {data.label}
      </div>

      <Handle
        type="target"
        position={Position.Left}
        id="input"
        style={{ background: '#555' }}
        isConnectable={isConnectable}
      />

      <Handle
        type="source"
        position={Position.Right}
        id="output"
        style={{ background: '#555' }}
        isConnectable={isConnectable}
      />
    </div>
  );
}

export default memo(CustomNode);