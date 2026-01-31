# Dashboard API Endpoints

Dashboard API đã được cập nhật để lấy dữ liệu từ `accounts/Database/account.db` thay vì `Data/Data.db`.

## Các Endpoint Mới

### 1. Dashboard Overview
```
GET /dashboard/overview
```
Lấy tổng quan về hệ thống:
- Tổng số sessions
- Tổng số messages
- Sessions gần đây (7 ngày)
- Tổng số users
- Phân bố loại tin nhắn
- Hoạt động hàng ngày (7 ngày)
- Top 10 users có nhiều tin nhắn nhất

### 2. Recent Sessions
```
GET /dashboard/sessions/recent?limit=10
```
Lấy danh sách các sessions gần đây với thông tin:
- Session ID
- Tiêu đề
- Username và role
- Thời gian tạo và hoạt động cuối
- Số lượng tin nhắn
- Tin nhắn cuối cùng

### 3. Session History (MỚI)
```
GET /dashboard/sessions/{session_id}/history
```
Lấy toàn bộ lịch sử chat của một session cụ thể:
- Thông tin session (user, thời gian)
- Danh sách tất cả tin nhắn trong session
- Chi tiết từng tin nhắn (message, response, timestamp)

**Sử dụng**: Khi người dùng bấm vào một session trong dashboard để xem chi tiết

### 4. User Statistics (MỚI)
```
GET /dashboard/users/stats
```
Lấy thống kê của tất cả users:
- Username, role, email
- Tổng số sessions
- Tổng số messages
- Hoạt động cuối cùng

### 5. User History (MỚI)
```
GET /dashboard/users/{user_id}/history?limit=50
```
Lấy lịch sử chat của một user cụ thể:
- Thông tin user
- Danh sách sessions
- Tổng số tin nhắn

### 6. Performance Analytics
```
GET /dashboard/analytics/performance
```
Lấy phân tích hiệu suất:
- Tỷ lệ engagement
- Tin nhắn theo ngày (30 ngày)
- Trung bình tin nhắn/session

## Thay Đổi Chính

1. **Database**: Đổi từ `Data/Data.db` sang `accounts/Database/account.db`
2. **Bảng dữ liệu**: Sử dụng `chat_history` và `chat_sessions` thay vì `Sessions`
3. **Endpoint mới**: Thêm 3 endpoints để xem chi tiết session và user
4. **Loại bỏ**: Xóa các endpoint Q-Learning không còn dùng

## Frontend Integration

Để hiển thị lịch sử khi bấm vào session:
```typescript
// Fetch session history
const response = await axios.get(`/dashboard/sessions/${sessionId}/history`);
const { session_info, messages } = response.data;

// Display messages in UI
messages.forEach(msg => {
  console.log(`User: ${msg.message}`);
  console.log(`Bot: ${msg.response}`);
});
```
