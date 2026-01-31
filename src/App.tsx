import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import { useSearchParams, Navigate } from 'react-router-dom';
import './App.css';
import AdminPage from './components/Admin/AdminPage';
import Navbar from './components/navbar/navbar';
import Auth from './components/account/Auth';
import Guest from './components/guest_chatbot/guestchatbot';
import { Routes, Route } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import CustomerService from './components/customerservice/customerservice';
import DiseaseDetect from './components/detect/diseasedetect';
import { UserContext, type User } from './contexts/UserContext';

axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.withCredentials = true;

// ...existing code...
interface TableMessage {
  columns?: string[];
  rows?: (string | number)[][];
  sql?: string;
  answer?: string;
}
type MessageContent = string | TableMessage;

interface Message {
  message: MessageContent;
  is_user: boolean;
  sentiment?: string | null;
}
// ...existing code...

interface Session {
  session_id: string;
  title: string;
  created_at: string;
  last_activity: string;
  message_count: number;
  is_active: boolean;
}

interface ChatHistoryItem {
  id: number;
  user_id: number;
  message: string;
  response: string;
  timestamp: string;
  session_id: string | null;
  is_private: boolean;
  status: string;
  message_type: string;
}

interface ParseTextAndSQLResult {
  text: string;
  sql: string | null;
}

function ShowSQLButtonText({ sql }: { sql: string | null }) {
  const [show, setShow] = React.useState(false);
  if (!sql) return null;
  return (
    <div>
      <button
        className="show-sql-btn"
        onClick={() => setShow(s => !s)}
      >
        {show ? "Ẩn SQL" : "Hiện SQL"}
      </button>
      {show && (
        <div className="sql-block">
          <b>Câu lệnh SQL đã dùng:</b>
          <pre className="sql-pre">{sql}</pre>
        </div>
      )}
    </div>
  );
}

function parseTextAndSQL(message: unknown): ParseTextAndSQLResult {
  if (typeof message !== "string") {
    return { text: JSON.stringify(message), sql: null };
  }
  const sqlIndex = message.indexOf("Câu lệnh SQL đã dùng:");
  if (sqlIndex === -1) return { text: message, sql: null };
  const text = message.slice(0, sqlIndex).trim();
  const sql = message.slice(sqlIndex + "Câu lệnh SQL đã dùng:".length).trim();
  return { text, sql };
}

function ShowSQLButton({ sql }: { sql: string | null }) {
  const [show, setShow] = React.useState(false);
  if (!sql) return null;
  return (
    <div>
      <button
        className="show-sql-btn"
        onClick={() => setShow(s => !s)}
      >
        {show ? "Ẩn SQL" : "Hiện SQL"}
      </button>
      {show && (
        <div className="sql-block">
          <b>Câu lệnh SQL đã dùng:</b>
          <pre className="sql-pre">{sql}</pre>
        </div>
      )}
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [language, setLanguage] = useState<string>('vi');
  const [sidebarActive, setSidebarActive] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const chatboxRef = useRef<HTMLDivElement>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const getCsrfToken = (): string => {
    const el = document.querySelector('[name=csrfmiddlewaretoken]') as HTMLInputElement | null;
    return el?.value || '';
  };

  const getAuthHeaders = useCallback(() => {
    if (!user) return {};
    return {
      'Authorization': `Bearer ${user.id}`,
      'Content-Type': 'application/json'
    };
  }, [user]);

  // Check authentication on app load
  useEffect(() => {
    const checkAuth = () => {
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        try {
          const parsedUser = JSON.parse(savedUser);
          setUser(parsedUser);
          setIsAuthenticated(true);
        } catch {
          // If user data is corrupted, clear it
          localStorage.removeItem('user');
        }
      }
    };
    checkAuth();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      if (!user || !isAuthenticated) {
        setMessages([]);
        setSessions([]);
        return;
      }

      const sessionId = searchParams.get('session_id');
      setCurrentSession(sessionId);

      try {
        // Fetch chat history for current session or all history
        const historyUrl = sessionId ? `/api/chat/history?session_id=${sessionId}` : '/api/chat/history?limit=20';
        const historyRes = await axios.get(historyUrl, { headers: getAuthHeaders() });
        
        // Convert API response to Message format
        const apiMessages: ChatHistoryItem[] = historyRes.data || [];
        const formattedMessages: Message[] = [];
        
        // Sort by timestamp to ensure correct order
        const sortedMessages = apiMessages.sort((a, b) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );
        
        sortedMessages.forEach(item => {
          // Add user message
          formattedMessages.push({
            message: item.message,
            is_user: true,
            sentiment: null
          });
          
          // Parse bot response to restore original structure
          let botResponse: MessageContent;
          try {
            // Try to parse as JSON first (for table/object data)
            const parsed = JSON.parse(item.response);
            
            // Handle array responses (backend sometimes wraps in array)
            let data = parsed;
            if (Array.isArray(parsed) && parsed.length > 0) {
              data = parsed[0];
            }
            
            if (data && typeof data === 'object') {
              // If it's an error response with message and sql, just use the message text
              if ('message' in data && typeof data.message === 'string' && 'sql' in data) {
                botResponse = data.message;
              } else {
                botResponse = data;
              }
            } else {
              botResponse = item.response;
            }
          } catch {
            // If not JSON, use as string
            botResponse = item.response;
          }
          
          // Add bot response
          formattedMessages.push({
            message: botResponse,
            is_user: false,
            sentiment: null
          });
        });
        
        setMessages(formattedMessages);
      } catch {
        // If error fetching history, just set empty messages
        setMessages([]);
      }

      try {
        // Fetch chat sessions
        const sessionsRes = await axios.get('/api/chat/sessions', { headers: getAuthHeaders() });
        // Filter out sessions with 0 messages
        const activeSessions = (sessionsRes.data || []).filter((session: Session) => session.message_count > 0);
        setSessions(activeSessions);
      } catch {
        // If error fetching sessions, just set empty array
        setSessions([]);
      }

      try {
        const res = await axios.get('/get_language/');
        setLanguage(res.data.language || 'vi');
      } catch {
        setLanguage('vi');
      }
    };
    fetchData();
  }, [searchParams, user, isAuthenticated, getAuthHeaders]);

  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || !user) return;
    
    const userMessage: Message = { message: input, is_user: true, sentiment: null };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    
    try {
      // Send message to chat API
      const res = await axios.post('/chat/', { message: currentInput });
      
      let botResponse: string;
      let botMsg: Message;
      
      if (
        res.data.type === "table" &&
        res.data.columns &&
        res.data.rows
      ) {
        botMsg = {
          message: {
            columns: res.data.columns,
            rows: res.data.rows,
            sql: res.data.sql
          },
          is_user: false
        };
        botResponse = `Table data with ${res.data.rows.length} rows`;
      } else if (
        res.data.response &&
        typeof res.data.response === 'object' &&
        res.data.response.answer
      ) {
        botMsg = {
          message: {
            answer: res.data.response.answer
          },
          is_user: false
        };
        botResponse = res.data.response.answer;
      } else if (
        res.data.response &&
        typeof res.data.response === 'object' &&
        res.data.response.message
      ) {
        // Handle error response with message and sql fields
        botMsg = { 
          message: res.data.response.message, 
          is_user: false 
        };
        botResponse = res.data.response.message;
      } else {
        botMsg = { message: res.data.response, is_user: false };
        botResponse = res.data.response;
      }
      
    // Update messages without sentiment
    setMessages((prev) => [
      ...prev.slice(0, -1),
      userMessage,
      botMsg
    ]);      // Save to chat history API
      try {
        // Serialize complex bot response properly
        let responseToSave: string;
        if (typeof botResponse === 'string') {
          responseToSave = botResponse;
        } else if (typeof botResponse === 'object') {
          responseToSave = JSON.stringify(botResponse);
        } else {
          responseToSave = String(botResponse);
        }
        
        const saveData = {
          message: currentInput,
          response: responseToSave,
          session_id: currentSession || `session_${Date.now()}`,
          is_private: true,
          message_type: 'text'
        };
        
        console.log('Saving chat data:', saveData);
        
        await axios.post('/api/chat/save', saveData, { 
          headers: getAuthHeaders() 
        });
        
        // Update session title if it's a new session
        if (!currentSession) {
          const newSessionId = `session_${Date.now()}`;
          setCurrentSession(newSessionId);
          setSearchParams({ session_id: newSessionId });
          
          // Set a meaningful session title like ChatGPT
          const words = currentInput.split(' ').slice(0, 4); // Take first 4 words
          let sessionTitle = words.join(' ');
          if (currentInput.split(' ').length > 4) {
            sessionTitle += '...';
          }
            
          try {
            await axios.patch(
              `/api/chat/session/${newSessionId}/title?title=${encodeURIComponent(sessionTitle)}`,
              {},
              { headers: getAuthHeaders() }
            );
            
            // Add new session to sessions list immediately
            const newSession = {
              session_id: newSessionId,
              title: sessionTitle,
              created_at: new Date().toISOString(),
              last_activity: new Date().toISOString(),
              message_count: 2, // User message + bot response
              is_active: true
            };
            setSessions(prev => [newSession, ...prev]);
            
          } catch {
            // Silently handle title update errors
          }
        } else {
          // Update message count for existing session
          setSessions(prev => prev.map(session => 
            session.session_id === currentSession 
              ? { ...session, message_count: session.message_count + 2, last_activity: new Date().toISOString() }
              : session
          ));
        }
        
        console.log('Chat saved successfully');
      } catch {
        // Silently handle save errors - don't show to user
        // The conversation continues normally even if save fails
      }
      
    } catch (error) {
      // Show friendly error message instead of raw error
      let errorMessage = 'Xin lỗi, không tìm thấy thông tin hoặc không thể xử lý yêu cầu của bạn. Vui lòng thử lại.';
      
      // Extract meaningful error message if available
      if (axios.isAxiosError(error) && error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      }
      
      setMessages((prev) => [
        ...prev,
        { message: errorMessage, is_user: false }
      ]);
    }
  };

  const toggleLanguage = async () => {
    const newLang = language === 'vi' ? 'en' : 'vi';
    try {
      await axios.post('/set_language/', { language: newLang }, {
        headers: { 'X-CSRFToken': getCsrfToken() }
      });
      setLanguage(newLang);
      window.location.reload();
    } catch {
      // If language toggle fails, just keep current language
    }
  };

  const startNewChat = async () => {
    if (!user) {
      alert('Please login to start a new chat');
      return;
    }
    
    const newSessionId = `session_${Date.now()}_${user.id}`;
    setSearchParams({ session_id: newSessionId });
    setMessages([]);
  };

  const loadChatSession = (sessionId: string) => {
    setSearchParams({ session_id: sessionId });
  };



  function renderChart(message: Message) {
    if (
      message &&
      typeof message.message === 'object' &&
      message.message !== null &&
      'columns' in message.message &&
      'rows' in message.message &&
      Array.isArray(message.message.columns) &&
      Array.isArray(message.message.rows) &&
      message.message.columns.length === 2
    ) {
      const columns = message.message.columns as string[];
      const rows = (message.message.rows ?? []) as (string | number)[][];
      const data = rows.map((row) => {
        const obj: Record<string, string | number> = {};
        columns.forEach((col, idx) => {
          obj[col] = row[idx];
        });
        return obj;
      });
      return (
        <div className="chart-wrapper">
          <ResponsiveContainer>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={columns[0]} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey={columns[1]} fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }
    return null;
  }

  const deleteChatSession = async (sessionId: string) => {
    if (!window.confirm('Bạn có chắc muốn xóa phiên chat này?') || !user) return;
    
    try {
      // Call API to delete session first
      await axios.delete(`/api/chat/session/${sessionId}`, {
        headers: getAuthHeaders()
      });
      
      // Remove from UI after successful API call
      setSessions(prev => prev.filter(session => session.session_id !== sessionId));
      
      // If deleted session was current, clear it
      if (sessionId === currentSession) {
        setSearchParams({});
        setMessages([]);
        setCurrentSession(null);
      }
      
      console.log('Session deleted successfully');
      
    } catch {
      // Show user-friendly error message
      alert('Không thể xóa phiên chat. Vui lòng thử lại.');
    }
  };

  // Show login if not authenticated
  if (!isAuthenticated || !user) {
    return (
      <UserContext.Provider value={{ user, setUser }}>
        <Routes>
          <Route path="/guest" element={<Guest />} />
          <Route path="/*" element={<Auth />} />
        </Routes>
      </UserContext.Provider>
    );
  }

  return (
    <UserContext.Provider value={{ user, setUser }}>
      <Navbar toggleLanguage={toggleLanguage} language={language} user={user} />

      <Routes>
        {user.role === 'admin' && <Route path="/admin" element={<AdminPage />} />}
        {(user.role === 'admin' || user.role === 'employee') && <Route path="/customerservice" element={<CustomerService />} />}
        {(user.role === 'admin' || user.role === 'employee') && <Route path="/detect" element={<DiseaseDetect />} />}
        <Route path="/guest" element={<Guest />} />

        {(user.role === 'admin' || user.role === 'employee') && <Route path="/" element={
          <div className="container">
            <div className={`sidebar${sidebarActive ? ' active' : ''}`}>
              <div className="sidebar-header">
                <h3>Chat History</h3>
                <span className="hamburger" onClick={() => setSidebarActive(false)}>✕</span>
              </div>
              <div className="sidebar-content">
                <button className="new-chat-btn" onClick={startNewChat}>New Chat</button>
                <div className="chat-sessions-container">
                  {sessions.map((session) => (
                    <div
                      key={session.session_id}
                      className={`chat-session${session.session_id === currentSession ? ' active' : ''}`}
                      onClick={() => loadChatSession(session.session_id)}
                    >
                      <span>{session.title} ({session.message_count} messages)</span>
                      <div className="session-meta">
                        <small>{new Date(session.last_activity).toLocaleDateString()}</small>
                      </div>
                      <div>
                        <span role="img" aria-label="chat">🗨️</span>
                        <button
                          className="delete-session-btn"
                          onClick={e => {
                            e.stopPropagation();
                            deleteChatSession(session.session_id);
                          }}
                        >✕</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="chat-container">
              <div className="chat-header">
                <span className="hamburger" onClick={() => setSidebarActive(!sidebarActive)}>☰</span>
                <span>Agy</span>
                <span></span>
              </div>
              <div id="chatbox" ref={chatboxRef}>
                <div className="welcome-message">
                  <img src="Agleae.jpg" className="avatar bot-avatar" alt="Bot Avatar" />
                  <div className="message">
                    {language === 'vi'
                      ? 'Xin chào, tôi là Agealea, tôi có thể giúp gì cho bạn?'
                      : "Hello, I'm Agealea. How can I help you?"}
                  </div>
                </div>
                {messages.map((message, idx) => (
                <div
                  key={idx}
                  className={`message-container${message.is_user ? ' user-message-container' : ''}`}
                >
                  {!message.is_user && (
                    <img src="Agleae.jpg" className="avatar bot-avatar" alt="Bot Avatar" />
                  )}
                  {(() => {
                    let msg = message.message;
                      if (
                        Array.isArray(msg) &&
                        msg.length > 0 &&
                        msg[0] &&
                        typeof msg[0] === 'object' &&
                        Array.isArray(msg[0].columns) &&
                        Array.isArray(msg[0].rows)
                      ) {
                        msg = msg[0];
                      }
                      if (
                        msg &&
                        typeof msg === 'object' &&
                        'columns' in msg &&
                        'rows' in msg &&
                        Array.isArray(msg.columns) &&
                        Array.isArray(msg.rows)
                      ) {
                        const columns: string[] = msg.columns;
                        const rows: (string | number)[][] = msg.rows;
                        return rows.length > 0 ? (
                          <>
                            <div className="table-wrapper">
                              <table className="result-table">
                                <thead>
                                  <tr>
                                    {columns.map((col, i) => (
                                      <th key={i}>{col}</th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {rows.map((row, i) => (
                                    <tr key={i}>
                                      {row.map((cell, j) => (
                                        <td key={j}>{cell}</td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                            {renderChart({ message: msg, is_user: false })}
                            <ShowSQLButton sql={msg.sql ?? null} />
                          </>
                        ) : (
                          <div>
                            <i>Không tìm thấy dữ liệu phù hợp.</i>
                            <ShowSQLButton sql={msg.sql ?? null} />
                          </div>
                        );
                      }
                      if (
                        message.message &&
                        typeof message.message === 'object' &&
                        'answer' in message.message
                      ) {
                        return (
                          <div className="message">{message.message.answer}</div>
                        );
                      }
                      // Handle error response with message and sql
                      if (
                        message.message &&
                        typeof message.message === 'object' &&
                        'message' in message.message &&
                        typeof message.message.message === 'string'
                      ) {
                        return (
                          <div className="message">{message.message.message}</div>
                        );
                      }
                      if (
                        message.message &&
                        typeof message.message === 'object'
                      ) {
                        // For any other object, try to extract meaningful text
                        // If it has a 'message' field, use it, otherwise stringify
                        const msgObj = message.message as Record<string, unknown>;
                        if (msgObj.message && typeof msgObj.message === 'string') {
                          return <div className="message">{msgObj.message}</div>;
                        }
                        return (
                          <div className="message">
                            <pre className="json-pre">
                              {JSON.stringify(message.message, null, 2)}
                            </pre>
                          </div>
                        );
                      }
                      const { text, sql } = parseTextAndSQL(message.message);
                      return (
                        <>
                          <div className={`message${message.is_user ? ' user-message' : ''}`}>
                            {text}
                            {sql && <ShowSQLButtonText sql={sql} />}
                          </div>
                          {message.is_user && (
                            <img src="Huey.jpg" className="avatar user-avatar" alt="User Avatar" />
                          )}
                        </>
                      );
                    })()}
                  </div>
                ))}
              </div>
              <div id="input-container">
                <input
                  id="input"
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                  placeholder="Nhập tin nhắn của bạn..."
                />
                <button onClick={sendMessage}>Gửi</button>
              </div>
            </div>
          </div>
        } />}
        
        {/* Redirect user role to /guest */}
        {user.role === 'user' && <Route path="/" element={<Navigate to="/guest" replace />} />}
        {user.role === 'user' && <Route path="/*" element={<Navigate to="/guest" replace />} />}
      </Routes>
    </UserContext.Provider>
  );
}

export default App;