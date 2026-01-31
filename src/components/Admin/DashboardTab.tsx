

import React, { useState, useEffect } from 'react';
import './styles/DashboardTab.css';

interface DashboardData {
  total_sessions?: number;
  total_messages?: number;
  recent_sessions?: number;
  q_learning_stats?: { total_logs: number; average_q_value: number };
  daily_activity?: { date: string; sessions: number }[];
  intent_distribution?: Record<string, number>;
}

interface PerformanceData {
  engagement_rate?: number;
  engaged_sessions?: number;
  total_sessions?: number;
  q_learning_performance?: { avg_q_value: number }[];
}

interface RecentSession {
  session_id: string;
  created_at: string;
  message_count: number;
  last_message?: string;
}

const DashboardTab: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState<boolean>(false);
  const [recentSessions, setRecentSessions] = useState<RecentSession[]>([]);
  const [performanceData, setPerformanceData] = useState<PerformanceData | null>(null);

  useEffect(() => {
    fetchDashboardData();
    fetchRecentSessions();
    fetchPerformanceData();
  }, []);

  const fetchDashboardData = async () => {
    setLoadingDashboard(true);
    try {
      const res = await fetch('http://localhost:8000/dashboard/overview');
      const data: DashboardData = await res.json();
      setDashboardData(data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setDashboardData(null);
    }
    setLoadingDashboard(false);
  };

  const fetchRecentSessions = async () => {
    try {
      const res = await fetch('http://localhost:8000/dashboard/sessions/recent?limit=10');
      const data: { sessions?: RecentSession[] } = await res.json();
      setRecentSessions(data.sessions || []);
    } catch (error) {
      console.error('Error fetching recent sessions:', error);
      setRecentSessions([]);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      const res = await fetch('http://localhost:8000/dashboard/analytics/performance');
      const data: PerformanceData = await res.json();
      setPerformanceData(data);
    } catch (error) {
      console.error('Error fetching performance data:', error);
      setPerformanceData(null);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="admin-upload-title">Tổng quan Dashboard</div>
        <button
          className="admin-upload-btn"
          onClick={() => {
            fetchDashboardData();
            fetchRecentSessions();
            fetchPerformanceData();
          }}
          disabled={loadingDashboard}
        >
          {loadingDashboard ? 'Đang tải...' : 'Làm mới dữ liệu'}
        </button>
      </div>
      {loadingDashboard ? (
        <div className="admin-loading-text">Đang tải dữ liệu dashboard...</div>
      ) : dashboardData ? (
        <>
          <div className="dashboard-cards">
            <div className="dashboard-card">
              <h3>Tổng số phiên chat</h3>
              <div className="dashboard-number">{dashboardData.total_sessions || 0}</div>
            </div>
            <div className="dashboard-card">
              <h3>Tổng số tin nhắn</h3>
              <div className="dashboard-number">{dashboardData.total_messages || 0}</div>
            </div>
            <div className="dashboard-card">
              <h3>Phiên gần đây (7 ngày)</h3>
              <div className="dashboard-number">{dashboardData.recent_sessions || 0}</div>
            </div>
            <div className="dashboard-card">
              <h3>Q-Learning Logs</h3>
              <div className="dashboard-number">{dashboardData.q_learning_stats?.total_logs || 0}</div>
              <div className="dashboard-subtitle">Q-Value TB: {dashboardData.q_learning_stats?.average_q_value || 0}</div>
            </div>
          </div>
          <div className="dashboard-charts">
            <div className="dashboard-chart-container">
              <h3>Hoạt động hàng ngày (7 ngày qua)</h3>
              <div className="dashboard-bar-chart">
                {dashboardData.daily_activity && dashboardData.daily_activity.length > 0 ? (
                  dashboardData.daily_activity.map((day, index) => {
                    // Tính phần trăm chiều cao cho bar chart
                    const maxSessions = Math.max(...(dashboardData.daily_activity?.map((d) => d.sessions) ?? [1]), 1);
                    const percent = Math.max((day.sessions / maxSessions) * 100, 5);
                    return (
                      <div key={index} className="chart-bar-container">
                        <div
                          className="chart-bar"
                          style={{ height: `${percent}%` }}
                        ></div>
                        <div className="chart-label">
                          {day.date
                            ? new Date(day.date).toLocaleDateString('vi-VN', { month: 'short', day: 'numeric' })
                            : 'N/A'}
                        </div>
                        <div className="chart-value">{day.sessions}</div>
                      </div>
                    );
                  })
                ) : (
                  <div className="admin-no-data">Chưa có dữ liệu hoạt động</div>
                )}
              </div>
            </div>
            <div className="dashboard-chart-container">
              <h3>Phân bố Intent</h3>
              <div className="dashboard-intent-list">
                {dashboardData.intent_distribution && Object.keys(dashboardData.intent_distribution).length > 0 ? (
                  Object.entries(dashboardData.intent_distribution)
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .slice(0, 10)
                    .map(([intent, count]) => {
                      // Tính phần trăm chiều rộng cho intent bar
                      const maxIntent = Math.max(...(Object.values(dashboardData.intent_distribution ?? {}) as number[]), 1);
                      const percent = ((count as number) / maxIntent) * 100;
                      return (
                        <div key={intent} className="intent-item">
                          <span className="intent-name">{intent}</span>
                          <span className="intent-count">{count}</span>
                          <div className="intent-bar">
                            <div
                              className="intent-bar-fill"
                              style={{ width: `${percent}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })
                ) : (
                  <div className="admin-no-data">Chưa có dữ liệu intent</div>
                )}
              </div>
            </div>
          </div>
          {performanceData && (
            <div className="dashboard-performance">
              <h3>Phân tích hiệu suất</h3>
              <div className="performance-cards">
                <div className="dashboard-card">
                  <h4>Tỷ lệ tương tác</h4>
                  <div className="dashboard-number">{performanceData.engagement_rate || 0}%</div>
                  <div className="dashboard-subtitle">
                    {performanceData.engaged_sessions || 0} / {performanceData.total_sessions || 0} phiên
                  </div>
                </div>
                {performanceData.q_learning_performance && performanceData.q_learning_performance.length > 0 && (
                  <div className="dashboard-card">
                    <h4>Xu hướng Q-Learning</h4>
                    <div className="dashboard-number">
                      {performanceData.q_learning_performance[performanceData.q_learning_performance.length - 1]?.avg_q_value || 0}
                    </div>
                    <div className="dashboard-subtitle">Q-value TB mới nhất</div>
                  </div>
                )}
              </div>
            </div>
          )}
          <div className="dashboard-recent-sessions">
            <h3>Phiên chat gần đây</h3>
            <div className="sessions-list">
              {recentSessions.length > 0 ? (
                recentSessions.slice(0, 5).map((session, index) => (
                  <div key={index} className="session-item">
                    <div className="session-id">Phiên: {session.session_id}</div>
                    <div className="session-time">
                      {session.created_at && session.created_at !== 'N/A'
                        ? new Date(session.created_at).toLocaleString('vi-VN')
                        : 'Không có thời gian'}
                    </div>
                    <div className="session-messages">{session.message_count || 0} tin nhắn</div>
                    {session.last_message && <div className="session-preview">{String(session.last_message)}</div>}
                  </div>
                ))
              ) : (
                <div className="admin-no-data">Chưa có phiên chat nào</div>
              )}
            </div>
          </div>
        </>
      ) : (
        <div className="admin-no-data">Nhấn "Làm mới dữ liệu" để tải dashboard</div>
      )}
    </div>
  );
};

export default DashboardTab;