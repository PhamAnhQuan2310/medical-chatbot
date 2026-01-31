import React from 'react';
import WorkflowDesigner from '../workflow/WorkflowDesigner';
import './styles/WorkflowTab.css';
const WorkflowTab: React.FC = () => {
  return (
    <div className="admin-workflow-container">
      <WorkflowDesigner />
    </div>
  );
};

export default WorkflowTab;