import React, { useState, useRef, useEffect } from 'react';
import './customerservice.css';

interface Ticket {
  id: string;
  userName: string;
  issue: string;
  status: 'open' | 'closed';
  priority: 'low' | 'medium' | 'high';
  createdAt: string;
}

interface Message {
  sender: 'user' | 'agent';
  content: string;
  timestamp: string;
}

const CustomerService: React.FC = () => {
  const [tickets] = useState<Ticket[]>([
    { 
      id: 'TICKET-1', 
      userName: 'Nguyễn Văn An', 
      issue: 'Không thể đăng nhập vào tài khoản', 
      status: 'open',
      priority: 'high',
      createdAt: '10:30'
    },
    { 
      id: 'TICKET-2', 
      userName: 'Trần Thị Bình', 
      issue: 'Lỗi thanh toán khi mua hàng', 
      status: 'open',
      priority: 'medium',
      createdAt: '09:15'
    },
    { 
      id: 'TICKET-3', 
      userName: 'Lê Minh Cường', 
      issue: 'Muốn thay đổi thông tin cá nhân', 
      status: 'open',
      priority: 'low',
      createdAt: '08:45'
    },
  ]);
  
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const chatBoxRef = useRef<HTMLDivElement>(null);

  const handleSelectTicket = (ticket: Ticket) => {
    setSelectedTicket(ticket);
    // Simulate initial conversation
    setMessages([
      {
        sender: 'user',
        content: ticket.issue,
        timestamp: ticket.createdAt,
      },
      {
        sender: 'agent',
        content: `Xin chào ${ticket.userName}, tôi đã nhận được yêu cầu hỗ trợ của bạn. Tôi sẽ giúp bạn giải quyết vấn đề này.`,
        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const handleSendMessage = (e: React.FormEvent | React.MouseEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedTicket) return;

    const message: Message = {
      sender: 'agent',
      content: newMessage,
      timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, message]);
    setNewMessage('');
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high': return 'Cao';
      case 'medium': return 'Trung bình';
      case 'low': return 'Thấp';
      default: return priority;
    }
  };

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="container">
      <h1>🎧 Hỗ Trợ Khách Hàng</h1>
      
      <div className="main-content">
        {/* Ticket List */}
        <div className="ticket-list">
          <h2>Danh sách Ticket</h2>
          
          {tickets.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <p>Chưa có ticket nào.</p>
            </div>
          ) : (
            <ul>
              {tickets.map((ticket) => (
                <li
                  key={ticket.id}
                  className={`ticket ${selectedTicket?.id === ticket.id ? 'active' : ''}`}
                  onClick={() => handleSelectTicket(ticket)}
                >
                  <div className="ticket-header">
                    <strong>{ticket.userName}</strong>
                    <div className="priority-indicator">
                      <span 
                        className="priority-dot"
                        style={{ backgroundColor: getPriorityColor(ticket.priority) }}
                      ></span>
                      <span className="priority-text">
                        {getPriorityText(ticket.priority)}
                      </span>
                    </div>
                  </div>
                  
                  <p className="ticket-issue">{ticket.issue}</p>
                  
                  <div className="ticket-footer">
                    <span className="ticket-time">{ticket.createdAt}</span>
                    <span className={`ticket-status ${ticket.status}`}>
                      {ticket.status === 'open' ? 'Đang xử lý' : 'Đã đóng'}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Chat Section */}
        <div className="chat-section">
          {selectedTicket ? (
            <>
              {/* Chat Header */}
              <div className="chat-header">
                <div className="chat-title">
                  <h2>💬 Chat với {selectedTicket.userName}</h2>
                  <p className="chat-subtitle">
                    Ticket: {selectedTicket.id} • Độ ưu tiên: {getPriorityText(selectedTicket.priority)}
                  </p>
                </div>
                <div className="online-status">
                  <div className="status-dot"></div>
                  <span>Online</span>
                </div>
              </div>

              {/* Chat Messages */}
              <div ref={chatBoxRef} className="chat-box">
                {messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`message ${msg.sender === 'agent' ? 'agent' : 'user'}`}
                  >
                    <p>{msg.content}</p>
                    <span>{msg.timestamp}</span>
                  </div>
                ))}
              </div>

              {/* Chat Form */}
              <div className="chat-form">
                <input
                  type="text"
                  placeholder="Nhập tin nhắn của bạn..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!newMessage.trim()}
                  className={!newMessage.trim() ? 'disabled' : ''}
                >
                  ✈️ Gửi
                </button>
              </div>
            </>
          ) : (
            <div className="empty-chat">
              <div className="empty-chat-icon">💬</div>
              <h3>Chọn một ticket để bắt đầu</h3>
              <p>Hãy chọn một ticket từ danh sách bên trái để bắt đầu cuộc hội thoại</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CustomerService;