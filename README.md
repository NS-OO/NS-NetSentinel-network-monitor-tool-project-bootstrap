# Network Monitoring System

A comprehensive network monitoring solution with real-time monitoring, device management, and alerting capabilities.

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
# Backend runs on http://localhost:5000
```

### 2. Frontend Setup
```bash
npm install
npm run dev
# Frontend runs on http://localhost:8000
```

### 3. Default Login
- **Username**: admin
- **Password**: admin123

## 📋 Features

### ✅ Network Monitoring
- Real-time network speed monitoring
- Device discovery and tracking
- Bandwidth usage per device
- 24/7 continuous monitoring

### ✅ Device Management
- IP, MAC, vendor detection
- Connection type identification (LAN/Wi-Fi)
- Block/unblock devices via Windows firewall
- Device status tracking

### ✅ Alert System
- Network down detection (>15 seconds)
- Automatic notifications
- Alert history and management

### ✅ User Management
- SuperAdmin vs Normal user roles
- Secure JWT authentication
- User registration and management

### ✅ Dashboard
- Real-time network graphs
- Device count and status
- Alert notifications
- Responsive modern UI

## 🛠️ Technical Stack

### Backend
- **Python Flask** - REST API
- **SQLite** - Database
- **Socket.IO** - Real-time updates
- **Windows Firewall** - Device blocking

### Frontend
- **Next.js** - React framework
- **Tailwind CSS** - Styling
- **Shadcn/UI** - Components
- **Recharts** - Charts and graphs
- **Socket.IO Client** - Real-time updates

## 📁 Project Structure

```
network-monitor/
├── backend/
│   ├── app.py              # Flask application
│   ├── database.py         # Database models
│   ├── network_monitor.py  # Network monitoring
│   ├── firewall_manager.py # Windows firewall
│   └── requirements.txt    # Python dependencies
├── src/
│   ├── app/
│   │   ├── login/         # Login page
│   │   ├── dashboard/     # Main dashboard
│   │   ├── devices/       # Device management
│   │   └── page.tsx       # Home redirect
│   └── hooks/             # Custom hooks
└── README.md              # This file
```

## 🔧 Requirements

- **Windows OS** (for firewall integration)
- **Administrator privileges** (for device blocking)
- **Python 3.7+**
- **Node.js 16+**

## 🎯 Usage

1. **Login** with admin/admin123
2. **View Dashboard** for network overview
3. **Manage Devices** to block/unblock
4. **Monitor Alerts** for network issues

## 🚨 Security Notes

- Change default admin password after first login
- Run with administrator privileges for full functionality
- Use HTTPS in production environments
