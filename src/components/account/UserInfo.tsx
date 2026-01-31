import React from 'react';
import './UserInfo.css';

interface User {
  id: number;
  username: string;
  role: string;
  email: string;
}

interface UserInfoProps {
  user: User;
  onLogout: () => void;
}

const UserInfo: React.FC<UserInfoProps> = ({ user, onLogout }) => {
  const handleLogout = () => {
    localStorage.removeItem('user');
    onLogout();
    window.location.reload();
  };

  return (
    <div className="user-info">
      <div className="user-details">
        <span className="username">👋 {user.username}</span>
        <span className="user-role">({user.role})</span>
      </div>
      <button className="logout-btn" onClick={handleLogout}>
        Đăng xuất
      </button>
    </div>
  );
};

export default UserInfo;