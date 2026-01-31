import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './styles/ManageUserTab.css';

axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.withCredentials = true;

interface User {
  id?: number; // Làm id thành optional vì API hiện tại không trả về id
  username: string;
  email: string;
  role: string;
}

// Simple Error Boundary Component
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  state = { hasError: false };

  static getDerivedStateFromError(error: unknown) {
    console.error("Error occurred:", error);
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <h2 className="role-error">Something went wrong. Please try refreshing the page.</h2>;
    }
    return this.props.children;
  }
}

const ChangeRole: React.FC = () => {
  const [users, setUsers] = useState<User[] | null>(null);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedUsername, setSelectedUsername] = useState<string>('');
  const [newRole, setNewRole] = useState<string>('user');

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('/users/', {
          validateStatus: (status) => status < 500,
        });
        console.log('API Response Status:', response.status);
        console.log('API Response Data:', JSON.stringify(response.data, null, 2)); // Pretty print for clarity
        if (Array.isArray(response.data)) {
          const validUsers = response.data.filter((item: User) =>
            item && typeof item === 'object' && 'username' in item && 'role' in item
          );
          setUsers(validUsers.length > 0 ? validUsers : []);
        } else if (response.data && typeof response.data === 'object' && 'users' in response.data && Array.isArray(response.data.users)) {
          const validUsers = response.data.users.filter((item: User) =>
            item && typeof item === 'object' && 'username' in item && 'role' in item
          );
          setUsers(validUsers.length > 0 ? validUsers : []);
        } else if (response.data && typeof response.data === 'object' && 'detail' in response.data) {
          setError(`Server error: ${response.data.detail}`);
        } else {
          setError(`Unexpected data format from server. Received: ${JSON.stringify(response.data, null, 2)}`);
        }
      } catch (err: unknown) {
        if (axios.isAxiosError(err)) {
          const errorMsg = err.response?.data?.detail || err.message || 'Failed to fetch users.';
          setError(`Network error: ${errorMsg}`);
          console.error('Fetch Error:', err);
        } else {
          setError('Failed to fetch users. Please try again.');
        }
      } finally {
        setIsLoading(false);
      }
    };
    fetchUsers();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await axios.put('/change-role/', {
        username: selectedUsername,
        new_role: newRole,
      }, {
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.data.status === 'success') {
        setSuccess(`Successfully changed role for ${response.data.username} to ${response.data.new_role}`);
        if (users) {
          setUsers(users.map(user =>
            user.username === selectedUsername ? { ...user, role: newRole } : user
          ));
        }
        setSelectedUsername('');
        setNewRole('user');
      }
    } catch (err: unknown) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Failed to change role. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ErrorBoundary>
      <div className="role-container">
        <div className="role-content">
          <h2 className="role-title">Change User Role</h2>
          {error && <div className="role-error">{error}</div>}
          {success && <div className="role-success">{success}</div>}
          {isLoading ? (
            <div className="role-loading">Loading users...</div>
          ) : users === null || users.length === 0 ? (
            <div className="role-error">
              {users === null ? 'Failed to load users.' : 'No users found in the database.'}
            </div>
          ) : (
            <>
              <div className="role-table">
                <table>
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Current Role</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.username}> {/* Sử dụng username làm key vì id không có */}
                        <td>{user.username}</td>
                        <td>{user.role}</td>
                        <td>
                          <button
                            className="action-button"
                            onClick={() => {
                              setSelectedUsername(user.username);
                              setNewRole(user.role);
                            }}
                          >
                            Change Role
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {selectedUsername && (
                <form onSubmit={handleSubmit} className="role-form">
                  <div className="form-group">
                    <label htmlFor="username" className="form-label">
                      Username
                    </label>
                    <input
                      id="username"
                      type="text"
                      value={selectedUsername}
                      onChange={(e) => setSelectedUsername(e.target.value)}
                      className="form-input"
                      readOnly
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="newRole" className="form-label">
                      New Role
                    </label>
                    <select
                      id="newRole"
                      value={newRole}
                      onChange={(e) => setNewRole(e.target.value)}
                      className="form-input"
                      required
                    >
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                      <option value="customer_service">Customer Service</option>
                      <option value="employee">Employee</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    className={`role-button ${isLoading ? 'loading' : ''}`}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <svg
                        className="spinner"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <circle
                          className="spinner-path"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                      </svg>
                    ) : (
                      'Change Role'
                    )}
                  </button>
                </form>
              )}
            </>
          )}
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default ChangeRole;