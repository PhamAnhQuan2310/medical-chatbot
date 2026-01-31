import React, { useState, useEffect } from 'react';
import './styles/ChatDetailTab.css';

interface ChatHistoryItem {
  id: string;
  timestamp: string;
  message_count: number;
  q_score: number;
}

interface ChatDetail {
  summary?: string;
  avg_q_score?: number;
  max_q_score?: number;
  action_count?: number;
  q_history?: { timestamp: string; action: string; state: string; score: number }[];
  messages?: { isUser: boolean; content: string; timestamp: string }[];
}

const ChatDetailTab: React.FC = () => {
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);
  const [loadingChatHistory, setLoadingChatHistory] = useState<boolean>(false);
  const [selectedChat, setSelectedChat] = useState<string | null>(null);
  const [chatDetail, setChatDetail] = useState<ChatDetail | null>(null);
  const [loadingChatDetail, setLoadingChatDetail] = useState<boolean>(false);

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const fetchChatHistory = async () => {
    setLoadingChatHistory(true);
    setChatHistory([]);
    try {
      const response = await fetch('http://localhost:8000/chat/history');
      const data: { success: boolean; history?: ChatHistoryItem[] } = await response.json();
      if (data.success) {
        setChatHistory(data.history || []);
      } else {
        console.error('Failed to fetch chat history: No history data returned');
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
    }
    setLoadingChatHistory(false);
  };

  const fetchChatDetail = async (conversationId: string) => {
    setSelectedChat(conversationId);
    setLoadingChatDetail(true);
    setChatDetail(null);
    try {
      const response = await fetch(`http://localhost:8000/chat/detail/${conversationId}`);
      const data: { success: boolean; detail?: ChatDetail } = await response.json();
      if (data.success) {
        setChatDetail(data.detail || null);
      } else {
        console.error('Failed to fetch chat detail: No detail data returned');
      }
    } catch (error) {
      console.error('Error fetching chat detail:', error);
    }
    setLoadingChatDetail(false);
  };

  return (
    <div className="chat-main">
      <div className="chat-header">
        <h2 className="chat-title">Chi tiết đoạn chat</h2>
        <button className="chat-refresh-btn" onClick={fetchChatHistory} disabled={loadingChatHistory}>
          {loadingChatHistory ? 'Đang tải...' : 'Tải lại'}
        </button>
      </div>
      <div className="chat-content">
        <div className="chat-history">
          {chatHistory.length === 0 && !loadingChatHistory && (
            <div className="chat-no-data">Không tìm thấy lịch sử chat.</div>
          )}
          {chatHistory.length > 0 && (
            <div className="chat-history-grid">
              <div className="chat-history-header">
                <div>ID</div>
                <div>Thời gian</div>
                <div>Số tin nhắn</div>
                <div>Điểm Q</div>
              </div>
              {chatHistory.map((chat) => (
                <div
                  key={chat.id}
                  className={`chat-history-item ${selectedChat === chat.id ? 'selected' : ''}`}
                  onClick={() => fetchChatDetail(chat.id)}
                >
                  <div>{String(chat.id).substring(0, 8)}...</div>
                  <div>{chat.timestamp ? new Date(chat.timestamp).toLocaleString() : 'N/A'}</div>
                  <div>{chat.message_count || 0}</div>
                  <div className="q-score">{Number(chat.q_score || 0).toFixed(2)}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        {selectedChat && (
          <div className="chat-detail-section">
            {loadingChatDetail ? (
              <div className="chat-loading">Đang tải chi tiết...</div>
            ) : chatDetail ? (
              <>
                <div className="chat-summary">
                  <h3>Tóm tắt</h3>
                  <p>{chatDetail.summary || 'Không có tóm tắt'}</p>
                </div>
                <div className="q-learning-details">
                  <h3>Phân tích Q-Learning</h3>
                  <div className="q-stats">
                    <div className="q-stat">
                      <span>Điểm trung bình:</span>
                      <span>{Number(chatDetail.avg_q_score || 0).toFixed(2)}</span>
                    </div>
                    <div className="q-stat">
                      <span>Điểm cao nhất:</span>
                      <span>{Number(chatDetail.max_q_score || 0).toFixed(2)}</span>
                    </div>
                    <div className="q-stat">
                      <span>Số hành động:</span>
                      <span>{chatDetail.action_count || 0}</span>
                    </div>
                  </div>
                  <div className="q-learning-chart">
                    <h4>Biểu đồ điểm Q-Learning</h4>
                    <div className="chart-container">
                      {chatDetail.q_history && chatDetail.q_history.length > 0 ? (
                        chatDetail.q_history.map((point, index) => (
                          <div
                            key={index}
                            className="chart-bar"
                            style={{
                              height: `${(Number(point.score || 0) / 10) * 100}%`,
                              left: `${(index / ((chatDetail.q_history?.length ?? 1) - 1 || 1)) * 100}%`
                            }}
                            title={`${point.timestamp ? new Date(point.timestamp).toLocaleTimeString() : 'N/A'}: ${Number(point.score || 0).toFixed(2)}`}
                          ></div>
                        ))
                      ) : (
                        <div className="chat-no-data">Không có dữ liệu Q-Learning</div>
                      )}
                    </div>
                  </div>
                  <table className="q-learning-table">
                    <thead>
                      <tr>
                        <th>Thời điểm</th>
                        <th>Hành động</th>
                        <th>Trạng thái</th>
                        <th>Điểm</th>
                      </tr>
                    </thead>
                    <tbody>
                      {chatDetail.q_history && chatDetail.q_history.length > 0 ? (
                        chatDetail.q_history.map((item, index) => (
                          <tr key={index}>
                            <td>{item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : 'N/A'}</td>
                            <td>{String(item.action || 'N/A')}</td>
                            <td>{String(item.state || 'N/A')}</td>
                            <td>{Number(item.score || 0).toFixed(2)}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4}>Không có dữ liệu Q-Learning</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                <div className="conversation-messages">
                  <h3>Nội dung hội thoại</h3>
                  {chatDetail.messages && chatDetail.messages.length > 0 ? (
                    chatDetail.messages.map((msg, index) => (
                      <div key={index} className={`chat-message ${msg.isUser ? 'user' : 'bot'}`}>
                        <div className="message-header">
                          <span className="message-sender">{msg.isUser ? 'User' : 'Bot'}</span>
                          <span className="message-time">{msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : 'N/A'}</span>
                        </div>
                        <div className="message-content">{String(msg.content || '')}</div>
                      </div>
                    ))
                  ) : (
                    <div className="chat-no-data">Không có tin nhắn nào</div>
                  )}
                </div>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatDetailTab;