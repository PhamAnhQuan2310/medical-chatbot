import React, { useState } from 'react';
import { FaCloudUploadAlt,  FaCog, FaTable, FaDatabase, FaComment, FaChartLine, FaUser } from 'react-icons/fa';
import './styles/Admin.css';
import DashboardTab from './DashboardTab';
import UploadTab from './UploadTab';
import UploadThuocTab from './UploadThuocTab';
import ViewDataTab from './ViewDataTab';
import DbTablesTab from './DbTablesTab';
import WorkflowTab from './WorkflowTab';
import DataWorkflowTab from './DataWorkflowTab';
import SettingsTab from './SettingsTab';
import ChatDetailTab from './ChatDetailTab';
import ManageUserTab from './ManageUserTab';
const SIDEBAR_BUTTONS = [
  { label: 'Dashboard', icon: <FaChartLine /> },
  { label: 'Upload File', icon: <FaCloudUploadAlt /> },
  { label: 'Upload Thuoc', icon: <FaCloudUploadAlt /> },
  { label: 'View Data', icon: <FaTable /> },
  { label: 'View Database Tables', icon: <FaTable /> },
  { label: 'WorkFlow', icon: <FaCog /> },
  { label: 'Data WorkFlow', icon: <FaDatabase /> },
  { label: 'Settings', icon: <FaCog /> },
  { label: 'Chat Detail', icon: <FaComment /> },
  { label: 'Manage Users', icon: <FaUser /> },
];

const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<number>(0);

  return (
    <div className="admin-root">
      <nav className="admin-navbar">
        <div className="admin-navbar-title">Admin Dashboard</div>
        <div className="admin-navbar-links">
          <a href="/" className="admin-navbar-link">Chatbot</a>
        </div>
      </nav>
      <aside className="admin-sidebar">
        <div className="admin-sidebar-title">RAG Admin</div>
        <div className="admin-sidebar-btns">
          {SIDEBAR_BUTTONS.map((btn, idx) => (
            <button
              key={btn.label}
              className={`admin-sidebar-btn${activeTab === idx ? ' active' : ''}`}
              onClick={() => setActiveTab(idx)}
            >
              <span className="admin-sidebar-btn-icon">{btn.icon}</span>
              {btn.label}
            </button>
          ))}
        </div>
      </aside>
      <main className="admin-main">
        {activeTab === 0 && <DashboardTab />}
        {activeTab === 1 && <UploadTab />}
        {activeTab === 2 && <UploadThuocTab />}
        {activeTab === 3 && <ViewDataTab />}
        {activeTab === 4 && <DbTablesTab />}
        {activeTab === 5 && <WorkflowTab />}
        {activeTab === 6 && <DataWorkflowTab />}
        {activeTab === 7 && <SettingsTab />}
        {activeTab === 8 && <ChatDetailTab />}
        {activeTab === 9 && <ManageUserTab />}
      </main>
    </div>
  );
};

export default AdminPage;