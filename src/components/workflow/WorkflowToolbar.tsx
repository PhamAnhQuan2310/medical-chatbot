import React from 'react';
import './WorkflowToolbar.css';

// Interface for node and edge (replace with actual structure if known)
interface Node {
  id: string;
  // Add other node properties
}

interface Edge {
  id: string;
  // Add other edge properties
}

// Interface for workflow object
interface Workflow {
  id: string | null; // Still allowing null here, but could be refined
  name: string;
  nodes: Node[];
  edges: Edge[];
}

// Interface for component props
interface WorkflowToolbarProps {
  workflowName: string;
  setWorkflowName: (name: string) => void;
  saveWorkflow: () => void;
  createNewWorkflow: () => void;
  isLoading: boolean;
  workflows?: Workflow[];
  loadWorkflow: (workflowId: string) => void;
  currentWorkflowId: string | null; // Will handle null in the select
}

const WorkflowToolbar: React.FC<WorkflowToolbarProps> = ({
  workflowName,
  setWorkflowName,
  saveWorkflow,
  createNewWorkflow,
  isLoading,
  workflows = [], // Default to empty array
  loadWorkflow,
  currentWorkflowId,
}) => {
  return (
    <div className="workflow-toolbar">
      <div className="workflow-name">
        <input
          type="text"
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          placeholder="Workflow Name"
        />
      </div>

      <div className="workflow-actions">
        <button
          className="workflow-button new"
          onClick={createNewWorkflow}
          disabled={isLoading}
        >
          New
        </button>

        <button
          className="workflow-button save"
          onClick={saveWorkflow}
          disabled={isLoading}
        >
          {isLoading ? 'Saving...' : 'Save'}
        </button>

        <select
          className="workflow-select"
          onChange={(e) => e.target.value && loadWorkflow(e.target.value)}
          value={currentWorkflowId ?? ''} // Convert null to empty string
          disabled={isLoading}
        >
          <option value="">Load Workflow...</option>
          {Array.isArray(workflows) &&
            workflows.map((workflow) => (
              <option key={workflow.id ?? ''} value={workflow.id ?? ''}>
                {workflow.name}
              </option>
            ))}
        </select>

        <button
          className="workflow-button run"
          disabled={isLoading || !currentWorkflowId}
        >
          Run
        </button>
      </div>
    </div>
  );
};

export default WorkflowToolbar;