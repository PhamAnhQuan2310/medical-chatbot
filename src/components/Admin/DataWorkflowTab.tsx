import React from 'react';
import DataWorkflowDesigner from '../workflow/DataWorkflowDesigner';
import './styles/DataWorkflowTab.css';

const DataWorkflowTab: React.FC = () => {
  return (
    <div className="admin-workflow-container">
      <DataWorkflowDesigner />
    </div>
  );
};

export default DataWorkflowTab;