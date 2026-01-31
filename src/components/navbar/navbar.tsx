import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

interface User {
  id: number;
  username: string;
  role: string;
  email: string;
}

interface NavbarProps {
  language: string;
  toggleLanguage: () => void;
  user?: User | null;
  onLogout?: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ language, toggleLanguage, user, onLogout }) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('user');
    if (onLogout) onLogout();
    window.location.reload();
  };

  return (
    <div className="navbar">
      <img src="/GenG.jpg" className="GenG-logo" alt="GenG Logo" />
      {user?.role === 'admin' && <Link to="/admin">Admin</Link>}
      {(user?.role === 'employee' || user?.role === 'admin') && <Link to="/">Chatbot</Link>}
      {(user?.role === 'employee' || user?.role === 'admin') && <Link to="/detect">Nhận diện ảnh</Link>}
      <Link to="/guest">Guest Chat</Link>
      
      {user && (
        <div className="user-menu" ref={dropdownRef}>
          <button 
            className="user-icon-btn"
            onClick={() => setShowDropdown(!showDropdown)}
            aria-label="User menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </button>
          
          {showDropdown && (
            <div className="user-dropdown">
              <div className="dropdown-header">
                <div className="user-avatar">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                </div>
                <div className="user-info-dropdown">
                  <div className="user-name">{user.username}</div>
                  <div className="user-email">{user.email}</div>
                  <div className="user-role-badge">{user.role}</div>
                </div>
              </div>
              <div className="dropdown-divider"></div>
              <button className="logout-btn-dropdown" onClick={handleLogout}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
                Đăng xuất
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Navbar;