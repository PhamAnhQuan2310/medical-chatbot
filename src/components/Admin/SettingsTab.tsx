import React, { useState, useEffect } from 'react';
import './styles/SettingsTab.css';

interface Workflow {
  id: string;
  name: string;
  nodes: Record<string, unknown>[];
  edges: Record<string, unknown>[];
}

const SettingsTab: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [dataWorkflows, setDataWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [selectedDataWorkflow, setSelectedDataWorkflow] = useState<string | null>(null);
  const [loadingWorkflows, setLoadingWorkflows] = useState<boolean>(false);
  const [settingsMsg, setSettingsMsg] = useState<string>('');

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    setLoadingWorkflows(true);
    try {
      const response = await fetch('http://localhost:8000/workflow/list');
      const data: { success: boolean; workflows?: Workflow[] } = await response.json();
      if (data.success && data.workflows) {
        const chatbotWorkflows = data.workflows.filter(
          (w) => !w.name.toLowerCase().includes('data') && !w.name.toLowerCase().includes('dữ liệu')
        );
        const dataWorkflows = data.workflows.filter(
          (w) => w.name.toLowerCase().includes('data') || w.name.toLowerCase().includes('dữ liệu')
        );
        setWorkflows(chatbotWorkflows);
        setDataWorkflows(dataWorkflows);
      }
    } catch (error) {
      console.error('Error fetching workflows:', error);
    } finally {
      setLoadingWorkflows(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      const workflowSettings = {
        default_workflow_id: selectedWorkflow,
        default_data_workflow_id: selectedDataWorkflow,
      };
      await fetch('http://localhost:8000/settings/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow_settings: workflowSettings }),
      });
      setSettingsMsg('Settings saved successfully!');
    } catch (error) {
      console.error('Error saving settings:', error);
      setSettingsMsg('Failed to save settings. Please try again.');
    }
    setTimeout(() => setSettingsMsg(''), 3000);
  };

  return (
    <div className="settings-main">
      <div className="settings-header">
        <h2 className="settings-title">Settings</h2>
      </div>
      <div className="settings-content">
        <div className="settings-section">
          <label className="settings-label">Default Chatbot Workflow:</label>
          <div className="settings-input-group">
            <select
              value={selectedWorkflow || ''}
              onChange={(e) => setSelectedWorkflow(e.target.value)}
              className="settings-select"
            >
              <option value="">-- Select a workflow --</option>
              {workflows.map((workflow) => (
                <option key={workflow.id} value={workflow.id}>{workflow.name}</option>
              ))}
            </select>
            <button
              className="settings-refresh-btn"
              onClick={fetchWorkflows}
              disabled={loadingWorkflows}
              title="Refresh workflows"
            >
              {loadingWorkflows ? '...' : '⟳'}
            </button>
          </div>
        </div>
        <div className="settings-section">
          <label className="settings-label">Default Data Processing Workflow:</label>
          <div className="settings-input-group">
            <select
              value={selectedDataWorkflow || ''}
              onChange={(e) => setSelectedDataWorkflow(e.target.value)}
              className="settings-select"
            >
              <option value="">-- Select a data workflow --</option>
              {dataWorkflows.map((workflow) => (
                <option key={workflow.id} value={workflow.id}>{workflow.name}</option>
              ))}
            </select>
          </div>
        </div>
        <button className="settings-save-btn" onClick={handleSaveSettings}>
          Save Settings
        </button>
        {settingsMsg && (
          <div className={`settings-message ${settingsMsg.includes('success') ? 'success' : 'error'}`}>
            {settingsMsg}
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsTab;