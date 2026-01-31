import React, { useState, useRef, useEffect, useContext } from 'react';
import { UserContext } from '../../contexts/UserContext';
import './guestchatbot.css';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  source?: 'qwen' | 'rule_based' | 'hybrid';
  decisionInfo?: {
    decision_reason?: string;
    similarity_score?: number;
    quality_scores?: {
      qwen: number;
      rule: number;
    };
  };
}

interface ChatSession {
  id: string;
  name: string;
  messageCount: number;
  messages: Message[];
  lastActivity?: Date;
  isActive?: boolean;
}

interface SystemInfo {
  qwen_info?: Record<string, unknown>;
  rule_base_info?: Record<string, unknown>;
  readiness?: {
    qwen_ready: boolean;
    rule_base_ready: boolean;
  };
  csv_exists?: boolean;
}

interface HybridSystemStatus {
  status: 'not_initialized' | 'loading' | 'ready' | 'partial' | 'error';
  readiness: {
    qwen_ready: boolean;
    rule_base_ready: boolean;
  };
  system_info?: SystemInfo;
}

// Define API response interfaces
interface GuestSessionResponse {
  id: string;
  session_name: string;
  message_count: number;
  last_activity: string;
  is_active: boolean;
}

interface GuestMessageResponse {
  id: number;
  message: string;
  response: string;
  timestamp: string;
  source?: string;
  decision_info?: {
    decision_reason?: string;
    similarity_score?: number;
    quality_scores?: {
      qwen: number;
      rule: number;
    };
  };
}

// API Base URL Configuration
const API_BASE_URL = 'http://localhost:8000/guest-chat';
const HISTORY_API_BASE_URL = 'http://localhost:8000/api/guest-chat';

const GuestChatbot: React.FC = () => {
  const userContext = useContext(UserContext);
  const user = userContext?.user;
  
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string>('');
  const [newMessage, setNewMessage] = useState<string>('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [systemStatus, setSystemStatus] = useState<HybridSystemStatus>({
    status: 'not_initialized',
    readiness: { qwen_ready: false, rule_base_ready: false }
  });
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  const [showAdvancedInfo, setShowAdvancedInfo] = useState<boolean>(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState<boolean>(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showImageModal, setShowImageModal] = useState<boolean>(false);
  const [isDraggingImage, setIsDraggingImage] = useState(false);


  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentChat = chatSessions.find(chat => chat.id === currentChatId);

  // Get authentication headers
  const getAuthHeaders = () => {
    if (!user?.id) {
      throw new Error('User not authenticated');
    }
    return {
      'Content-Type': 'application/json',
      'Authorization': `${user.id}`
    };
  };

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentChat?.messages]);

  useEffect(() => {
    if (!selectedImage) {
      setPreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(selectedImage);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [selectedImage]);

  useEffect(() => {
    initializeGuestChat();
  }, []);

  useEffect(() => {
    if (user?.id) {
      initializeGuestChat();
    }
  }, [user]);

  const initializeGuestChat = async () => {
    if (!user?.id) {
      console.log('User not authenticated, skipping chat initialization');
      return;
    }
    await loadGuestSessions();
    await initializeHybridSystem();
  };

  // Load guest sessions from history
  const loadGuestSessions = async (): Promise<void> => {
    try {
      setIsLoadingHistory(true);
      const response = await fetch(`${HISTORY_API_BASE_URL}/sessions`, {
        method: 'GET',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const sessions: GuestSessionResponse[] = await response.json();
        if (sessions && sessions.length > 0) {
          const formattedSessions: ChatSession[] = sessions.map((session) => ({
            id: session.id,
            name: session.session_name,
            messageCount: session.message_count,
            messages: [],
            lastActivity: new Date(session.last_activity),
            isActive: session.is_active
          }));
          
          setChatSessions(formattedSessions);
          setCurrentChatId(formattedSessions[0].id);
          
          // Load messages for the first session
          await loadSessionMessages(formattedSessions[0].id);
        } else {
          // Create first session if none exist
          await createNewChat();
        }
      }
    } catch (error) {
      console.error('Error loading guest sessions:', error);
      // Create a default session if loading fails
      await createNewChat();
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Load messages for a specific session
  const loadSessionMessages = async (sessionId: string): Promise<void> => {
    try {
      const response = await fetch(`${HISTORY_API_BASE_URL}/history/${sessionId}`, {
        method: 'GET',
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const history: GuestMessageResponse[] = await response.json();
        const messages: Message[] = [];

        history.forEach((item) => {
          // Add user message
          messages.push({
            id: `${item.id}-user`,
            text: item.message,
            isUser: true,
            timestamp: new Date(item.timestamp)
          });

          // Add bot response
          messages.push({
            id: `${item.id}-bot`,
            text: item.response,
            isUser: false,
            timestamp: new Date(item.timestamp),
            source: item.source as 'qwen' | 'rule_based' | 'hybrid',
            decisionInfo: item.decision_info
          });
        });

        setChatSessions(prevSessions =>
          prevSessions.map(session =>
            session.id === sessionId
              ? { ...session, messages }
              : session
          )
        );
      }
    } catch (error) {
      console.error('Error loading session messages:', error);
    }
  };

  // Save message to history
  const saveMessageToHistory = async (
    sessionId: string, 
    userMessage: string, 
    botResponse: string, 
    source: string, 
    decisionInfo?: Record<string, unknown>
  ): Promise<boolean> => {
    if (!user?.id) {
      console.error('User not authenticated for saving message');
      return false;
    }
    
    try {
      const response = await fetch(`${HISTORY_API_BASE_URL}/save`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
          response: botResponse,
          source: source,
          decision_info: decisionInfo
        })
      });
      
      if (response.ok) {
        console.log('✅ Message saved to history');
        return true;
      } else {
        const errorData = await response.json();
        console.error('Error saving message:', errorData);
        return false;
      }
    } catch (error) {
      console.error('Error saving message to history:', error);
      return false;
    }
  };

  // Generate session name from first message
  const generateSessionName = (firstMessage: string): string => {
    const words = firstMessage.trim().split(' ');
    const preview = words.slice(0, 4).join(' ');
    return preview.length > 20 ? preview.substring(0, 20) + '...' : preview;
  };

  const initializeHybridSystem = async (): Promise<void> => {
    try {
      console.log('🔄 Bắt đầu khởi tạo hybrid system...');
      setIsInitializing(true);
      setSystemStatus(prev => ({ ...prev, status: 'loading' }));
      
      const response = await fetch(`${API_BASE_URL}/initialize`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      console.log('📡 Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('📦 Response data:', data);
      
      setSystemStatus({
        status: data.status,
        readiness: data.readiness,
        system_info: data.system_info
      });

      if (data.success && data.status === 'ready') {
        console.log('✅ Hybrid system sẵn sàng');
      } else if (data.status === 'partial') {
        console.log('⚠️ System một phần sẵn sàng:', data.message);
      } else {
        console.log('⚠️ System chưa sẵn sàng:', data.message);
        // Retry sau 3 giây nếu đang loading
        if (data.status === 'loading') {
          setTimeout(() => {
            initializeHybridSystem();
          }, 3000);
        }
      }
    } catch (error) {
      console.error('💥 Lỗi network khi khởi tạo hybrid system:', error);
      setSystemStatus(prev => ({ ...prev, status: 'error' }));
      
      // Retry sau 5 giây
      setTimeout(() => {
        console.log('🔄 Retry khởi tạo hybrid system...');
        initializeHybridSystem();
      }, 5000);
    } finally {
      setIsInitializing(false);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDraggingImage(true);
  };

  const handleDragLeave = () => {
    setIsDraggingImage(false);
  };

  const handleDropImage = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDraggingImage(false);

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Chỉ hỗ trợ file ảnh");
      return;
    }

    setSelectedImage(file);
  };


  const handleSendMessage = async (): Promise<void> => {
    if ((newMessage.trim() === '' && !selectedImage) || !isSystemReady()) return;

    const userMessage = newMessage;
    const currentSession = chatSessions.find(session => session.id === currentChatId);
    const isFirstMessage = !currentSession || currentSession.messages.length === 0;

    const message: Message = {
      id: Date.now().toString(),
      text: selectedImage ? `[Đã gửi ảnh] ${newMessage || ""}` : newMessage,
      isUser: true,
      timestamp: new Date()
    };

    // add tin nhắn user vào UI
    setChatSessions(prevSessions =>
      prevSessions.map(session =>
        session.id === currentChatId
          ? {
              ...session,
              messages: [...session.messages, message],
              messageCount: session.messageCount + 1
            }
          : session
      )
    );

    setNewMessage('');

    // ======================= MULTIMODAL (IMAGE) BLOCK =======================
    if (selectedImage) {
      const fd = new FormData();
      fd.append("image", selectedImage);
      fd.append("message", userMessage);
      fd.append("session_key", currentChatId);

      // reset preview
      setSelectedImage(null);

      try {
        const res = await fetch("http://localhost:8000/chat/multimodal", {
          method: "POST",
          body: fd,
        });

        const data = await res.json();

        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.answer ?? "",
          isUser: false,
          timestamp: new Date(),
          source: "hybrid",
          decisionInfo: undefined,
          ...(data.diagnosis && { diagnosis: data.diagnosis }),
          ...(data.drug_message && { drug_message: data.drug_message }),
          ...(data.drug_suggestions && { drug_suggestions: data.drug_suggestions }),
        } as any;

        // add bot message vào UI
        setChatSessions(prev =>
          prev.map(session =>
            session.id === currentChatId
              ? {
                  ...session,
                  messages: [...session.messages, botMessage],
                  messageCount: session.messageCount + 1,
                  lastActivity: new Date()
                }
              : session
          )
        );

        // Lưu vào lịch sử chat
        await saveMessageToHistory(
          currentChatId,
          userMessage,
          botMessage.text,
          "hybrid",
          botMessage.decisionInfo
        );

        // cập nhật tên session nếu là tin đầu
        if (isFirstMessage) {
          const sessionName = generateSessionName(userMessage);
          await updateSessionName(currentChatId, sessionName);
        }

        return; // NGỪNG TẠI ĐÂY → KHÔNG chạy xuống phần xử lý text
      } catch (err) {
        console.error("Lỗi gửi ảnh:", err);

        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: 'Không thể xử lý ảnh. Vui lòng thử lại.',
          isUser: false,
          timestamp: new Date()
        };

        setChatSessions(prev =>
          prev.map(session =>
            session.id === currentChatId
              ? {
                  ...session,
                  messages: [...session.messages, errorMessage],
                  messageCount: session.messageCount + 1
                }
              : session
          )
        );

        return;
      }
    }
    // ======================= END MULTIMODAL BLOCK =======================


    // ======================= TEXT CHAT (GỐC) =======================
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: currentChatId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          isUser: false,
          timestamp: new Date(),
          source: data.source,
          decisionInfo: data.decision_info
        };

        setChatSessions(prevSessions =>
          prevSessions.map(session =>
            session.id === currentChatId
              ? {
                  ...session,
                  messages: [...session.messages, botMessage],
                  messageCount: session.messageCount + 1,
                  lastActivity: new Date()
                }
              : session
          )
        );

        // save history
        await saveMessageToHistory(currentChatId, userMessage, data.response, data.source, data.decision_info);

        // đổi tên session nếu là tin đầu
        if (isFirstMessage) {
          const sessionName = generateSessionName(userMessage);
          await updateSessionName(currentChatId, sessionName);
        }

      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.error || 'Có lỗi xảy ra khi xử lý tin nhắn.',
          isUser: false,
          timestamp: new Date()
        };

        setChatSessions(prevSessions =>
          prevSessions.map(session =>
            session.id === currentChatId
              ? {
                  ...session,
                  messages: [...session.messages, errorMessage],
                  messageCount: session.messageCount + 1
                }
              : session
          )
        );
      }
    } catch (error) {
      console.error('Lỗi gửi tin nhắn:', error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Không thể kết nối đến server. Vui lòng thử lại sau.',
        isUser: false,
        timestamp: new Date()
      };

      setChatSessions(prevSessions =>
        prevSessions.map(session =>
          session.id === currentChatId
            ? {
                ...session,
                messages: [...session.messages, errorMessage],
                messageCount: session.messageCount + 1
              }
            : session
        )
      );
    }
  };


  const handleKeyPress = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Update session name
  const updateSessionName = async (sessionId: string, newName: string): Promise<void> => {
    if (!user?.id) {
      console.error('User not authenticated for updating session name');
      return;
    }
    
    try {
      const response = await fetch(`${HISTORY_API_BASE_URL}/session/${sessionId}/name?name=${encodeURIComponent(newName)}`, {
        method: 'PATCH',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        // Update UI immediately
        setChatSessions(prevSessions =>
          prevSessions.map(session =>
            session.id === sessionId
              ? { ...session, name: newName }
              : session
          )
        );
        console.log('✅ Session name updated:', newName);
      } else {
        const errorData = await response.json();
        console.error('Error updating session name:', errorData);
      }
    } catch (error) {
      console.error('Error updating session name:', error);
    }
  };

  // Switch to session and load its messages
  const switchToSession = async (sessionId: string): Promise<void> => {
    setCurrentChatId(sessionId);
    const session = chatSessions.find(s => s.id === sessionId);
    
    // Load messages if not already loaded
    if (session && session.messages.length === 0 && session.messageCount > 0) {
      await loadSessionMessages(sessionId);
    }
  };

  const createNewChat = async (): Promise<void> => {
    if (!user?.id) {
      console.error('User not authenticated');
      return;
    }
    
    try {
      const sessionName = `Medical Chat ${new Date().toLocaleDateString()}`;
      const response = await fetch(`${HISTORY_API_BASE_URL}/session`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          session_name: sessionName
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newChat: ChatSession = {
          id: data.session_id,
          name: data.session_name,
          messageCount: 0,
          messages: [],
          lastActivity: new Date(),
          isActive: true
        };

        setChatSessions(prev => [newChat, ...prev]);
        setCurrentChatId(data.session_id);
        console.log('✅ New chat session created:', data.session_id);
      } else {
        const errorData = await response.json();
        console.error('Error creating chat:', errorData);
      }
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  };

  const deleteChat = async (chatId: string): Promise<void> => {
    if (chatSessions.length === 1) return;

    try {
      await fetch(`${HISTORY_API_BASE_URL}/session/${chatId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      setChatSessions(prevSessions => prevSessions.filter(session => session.id !== chatId));
      
      if (currentChatId === chatId) {
        const remainingSessions = chatSessions.filter(session => session.id !== chatId);
        setCurrentChatId(remainingSessions[0]?.id || '');
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  const checkSystemStatus = async (): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSystemStatus({
          status: data.status,
          readiness: data.readiness,
          system_info: data.system_info
        });
      }
    } catch (error) {
      console.error('Error checking system status:', error);
      setSystemStatus(prev => ({ ...prev, status: 'error' }));
    }
  };

  const isSystemReady = (): boolean => {
    return systemStatus.status === 'ready' || 
           (systemStatus.status === 'partial' && 
            (systemStatus.readiness.qwen_ready || systemStatus.readiness.rule_base_ready));
  };

  const getSystemStatusText = (): string => {
    switch (systemStatus.status) {
      case 'ready': {
        return 'Hệ thống sẵn sàng (Hybrid)';
      }
      case 'partial': {
        const readyComponents = [];
        if (systemStatus.readiness.qwen_ready) readyComponents.push('AI');
        if (systemStatus.readiness.rule_base_ready) readyComponents.push('Rule-base');
        return `Một phần sẵn sàng (${readyComponents.join(', ')})`;
      }
      case 'loading': {
        return 'Đang khởi tạo...';
      }
      case 'error': {
        return 'Lỗi hệ thống';
      }
      default: {
        return 'Chưa khởi tạo';
      }
    }
  };

  const getSystemStatusClass = (): string => {
    if (isSystemReady()) return 'ready';
    if (systemStatus.status === 'loading') return 'loading';
    return 'error';
  };

  const renderMessageSource = (message: Message): React.ReactElement | null => {
    if (!message.source || !showAdvancedInfo) return null;

    const sourceLabels: Record<string, string> = {
      qwen: '🤖 AI Model',
      rule_based: '📚 Rule-based',
      hybrid: '🔬 Hybrid'
    };

    return (
      <div className="message-metadata">
        <div className="source-indicator">
          <span className={`source-label ${message.source}`}>
            {sourceLabels[message.source]}
          </span>
        </div>
        
        {message.decisionInfo && (
          <div className="decision-info">
            {message.decisionInfo.similarity_score !== undefined && (
              <div className="metric">
                Độ tương đồng: {(message.decisionInfo.similarity_score * 100).toFixed(1)}%
              </div>
            )}
            {message.decisionInfo.quality_scores && (
              <div className="quality-scores">
                AI: {message.decisionInfo.quality_scores.qwen.toFixed(2)} | 
                Rule: {message.decisionInfo.quality_scores.rule.toFixed(2)}
              </div>
            )}
            {message.decisionInfo.decision_reason && (
              <div className="decision-reason" title={message.decisionInfo.decision_reason}>
                💡 {message.decisionInfo.decision_reason}
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  useEffect(() => {
    let intervalId: number;
    
    if (systemStatus.status === 'loading' || systemStatus.status === 'not_initialized') {
      intervalId = setInterval(checkSystemStatus, 3000);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [systemStatus.status]);

  // Show loading state if user is not authenticated yet
  if (!userContext) {
    return (
      <div className="guest-chatbot">
        <div className="authentication-required">
          <h3>Authentication Required</h3>
          <p>Please log in to access Guest Chat features.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="guest-chatbot">
      {/* Sidebar */}
      <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <h3>Medical Chats</h3>
          <div className="sidebar-controls">
            <button 
              className="collapse-btn"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              {sidebarCollapsed ? '→' : '←'}
            </button>
            <button className="menu-btn">≡</button>
          </div>
        </div>

        {sidebarCollapsed ? (
          <div className="sidebar-collapsed-content">
            <button 
              className="new-chat-collapsed-btn" 
              onClick={createNewChat}
              title="New Medical Chat"
            >
              +
            </button>
            <div className="chat-count-collapsed" title={`${chatSessions.length} chats`}>
              {chatSessions.length}
            </div>
          </div>
        ) : (
          <>
            <div className="new-chat-section">
              <button className="new-chat-btn" onClick={createNewChat}>
                <span className="new-chat-icon">+</span>
                <span>New Medical Chat</span>
              </button>
            </div>

            <div className="system-info">
              <div className="system-status">
                <div className={`status-indicator ${getSystemStatusClass()}`}></div>
                <span className="status-text">{getSystemStatusText()}</span>
              </div>
              
              <div className="readiness-details">
                <div className={`component-status ${systemStatus.readiness.qwen_ready ? 'ready' : 'not-ready'}`}>
                  🤖 AI Model: {systemStatus.readiness.qwen_ready ? 'Ready' : 'Not Ready'}
                </div>
                <div className={`component-status ${systemStatus.readiness.rule_base_ready ? 'ready' : 'not-ready'}`}>
                  📚 Rule-base: {systemStatus.readiness.rule_base_ready ? 'Ready' : 'Not Ready'}
                </div>
              </div>

              <button 
                className="toggle-advanced-btn"
                onClick={() => setShowAdvancedInfo(!showAdvancedInfo)}
              >
                {showAdvancedInfo ? 'Hide' : 'Show'} Decision Info
              </button>
            </div>

            <div className="chat-history-section">
              <div className="section-title">
                <span>📜 Chat History</span>
                <span className="chat-count">({chatSessions.length})</span>
              </div>
              <div className="chat-list">
              {isLoadingHistory ? (
                <div className="loading-sessions">Loading sessions...</div>
              ) : (
                chatSessions.map((chat) => (
                  <div
                    key={chat.id}
                    className={`chat-item ${currentChatId === chat.id ? 'active' : ''}`}
                    onClick={() => switchToSession(chat.id)}
                  >
                    <div className="chat-info">
                      <span className="chat-name">{chat.name} ({chat.messageCount})</span>
                      {chat.lastActivity && (
                        <span className="last-activity">
                          {new Date(chat.lastActivity).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                    <button 
                      className="delete-chat-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(chat.id);
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))
              )}
            </div>
            </div>
          </>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        <div className="chat-header">
          <div className="header-left">
            <span>🏥 Medical AI Assistant</span>
            {currentChat && (
              <span className="current-session">{currentChat.name}</span>
            )}
          </div>
          <div className="header-right">
            <span className={`model-status ${getSystemStatusClass()}`}>
              {getSystemStatusText()}
            </span>
          </div>
        </div>

        {/* Loading overlay */}
        {isInitializing && (
          <div className="initialization-overlay">
            <div className="loading-spinner"></div>
            <p>Đang khởi tạo Medical Hybrid AI system...</p>
            <div className="initialization-details">
              <div>🤖 Loading AI Model...</div>
              <div>📚 Loading Medical Database...</div>
              <div>🔬 Setting up Hybrid Logic...</div>
            </div>
          </div>
        )}

        {/* Messages area */}
        {!currentChat && chatSessions.length === 0 && !isLoadingHistory ? (
          <div className="empty-state">
            <div className="empty-content">
              <div className="empty-icon">💬</div>
              <h3>Start Your First Medical Consultation</h3>
              <p>Ask me about your health concerns, symptoms, or medical questions.</p>
              <button className="start-chat-btn" onClick={createNewChat}>
                Start New Chat
              </button>
            </div>
          </div>
        ) : (
          <div className="messages-container">
            {currentChat?.messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.isUser ? 'user-message' : 'bot-message'}`}
              >
                {!message.isUser && (
                  <div className="bot-avatar">
                    <img src="/api/placeholder/32/32" alt="Medical AI" />
                  </div>
                )}
                <div className="message-content">
                  <div className="message-text">
                    <p>{message.text}</p>
                    {(message as any).diagnosis && (
                      <div className="card">
                        <b>🩻 Kết quả nhận diện ảnh</b>
                        <pre className="json-pre">{JSON.stringify((message as any).diagnosis, null, 2)}</pre>
                      </div>
                    )}

                    {/* {(message as any).drug_message && (
                      <div className="card">
                        <b>💊 Thông báo thuốc</b>
                        <div>{(message as any).drug_message}</div>
                      </div>
                    )}

                    {Array.isArray((message as any).drug_suggestions) &&
                    (message as any).drug_suggestions.length > 0 && (
                      <div className="card">
                        <b>Gợi ý thuốc</b>
                        <ul>
                          {(message as any).drug_suggestions.map((d: any) => (
                            <li key={d.id ?? d.drug_name}>
                              <b>{d.drug_name}</b> — score: {Number(d.score).toFixed(3)}
                              <div>{d.search_indication}</div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )} */}

                  </div>
                  {!message.isUser && renderMessageSource(message)}
                </div>
                {message.isUser && (
                  <div className="user-avatar">
                    <img src="/api/placeholder/32/32" alt="User" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}

        <div
          className={`input-container ${isDraggingImage ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDropImage}
        >


          {/* Button thêm ảnh */}
          <label className={`upload-btn ${previewUrl ? 'has-image' : ''}`} title="Tải ảnh y tế">
            <span className="upload-icon">
              {previewUrl ? '🖼️' : '📷'}
            </span>
            <input
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={(e) => {
                const f = e.target.files?.[0] ?? null;
                setSelectedImage(f);
              }}
            />
          </label>

          {previewUrl && (
            <div className="image-preview-thumb">
              <img
                src={previewUrl}
                alt="preview"
                onClick={() => setShowImageModal(true)}
              />
              <button
                className="remove-image-btn"
                onClick={() => setSelectedImage(null)}
                type="button"
              >
                ✕
              </button>
            </div>
          )}


          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              isSystemReady() 
                ? "Đặt câu hỏi y tế của bạn..." 
                : "Vui lòng đợi hệ thống khởi tạo..."
            }
            className="message-input"
            disabled={!isSystemReady() || !currentChat}
          />
          <button 
            onClick={handleSendMessage} 
            className="send-btn"
            disabled={!isSystemReady() || !currentChat}
          >
            Gửi
          </button>
        </div>
      </div>

      {showImageModal && previewUrl && (
        <div
          className="image-modal"
          onClick={() => setShowImageModal(false)}
        >
          <img src={previewUrl} alt="full-preview" />
        </div>
      )}


    </div>
  );
};

export default GuestChatbot;

