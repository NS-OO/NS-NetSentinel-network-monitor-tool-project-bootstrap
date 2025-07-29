import sqlite3
import bcrypt
import json
from datetime import datetime
import uuid

class DatabaseManager:
    def __init__(self, db_path='network_monitor.db'):
        self.db_path = db_path
        self.init_database()
        self.create_default_admin()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'normal',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Devices table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                mac_address TEXT,
                vendor TEXT,
                hostname TEXT,
                connection_type TEXT,
                is_blocked BOOLEAN DEFAULT 0,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_bandwidth REAL DEFAULT 0,
                is_online BOOLEAN DEFAULT 1
            )
        ''')
        
        # Network stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                download_speed REAL,
                upload_speed REAL,
                total_devices INTEGER,
                active_devices INTEGER,
                network_usage REAL,
                ping_latency REAL
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                device_ip TEXT,
                additional_data TEXT
            )
        ''')
        
        # Bandwidth usage table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bandwidth_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_ip TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bytes_sent REAL,
                bytes_received REAL,
                packets_sent INTEGER,
                packets_received INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_default_admin(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            # Create default admin user
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            ''', ('admin', password_hash.decode('utf-8'), 'superadmin'))
            conn.commit()
            print("Default admin user created: username='admin', password='admin123'")
        
        conn.close()
    
    # User management methods
    def create_user(self, username, password, role='normal'):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            ''', (username, password_hash.decode('utf-8'), role))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def authenticate_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, role, is_active
            FROM users WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and user[4]:  # is_active
            if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[3]
                }
        return None
    
    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, role, created_at, last_login, is_active
            FROM users ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'created_at': user[3],
                'last_login': user[4],
                'is_active': bool(user[5])
            }
            for user in users
        ]
    
    # Device management methods
    def add_or_update_device(self, ip, mac=None, vendor=None, hostname=None, connection_type=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO devices 
            (ip_address, mac_address, vendor, hostname, connection_type, last_seen, is_online)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        ''', (ip, mac, vendor, hostname, connection_type))
        
        conn.commit()
        conn.close()
    
    def get_all_devices(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ip_address, mac_address, vendor, hostname, connection_type,
                   is_blocked, first_seen, last_seen, total_bandwidth, is_online
            FROM devices ORDER BY last_seen DESC
        ''')
        
        devices = cursor.fetchall()
        conn.close()
        
        return [
            {
                'ip': device[0],
                'mac': device[1],
                'vendor': device[2],
                'hostname': device[3],
                'connection_type': device[4],
                'is_blocked': bool(device[5]),
                'first_seen': device[6],
                'last_seen': device[7],
                'total_bandwidth': device[8],
                'is_online': bool(device[9])
            }
            for device in devices
        ]
    
    def block_device(self, ip_address, block=True):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE devices SET is_blocked = ? WHERE ip_address = ?
        ''', (block, ip_address))
        
        conn.commit()
        conn.close()
    
    # Network stats methods
    def add_network_stats(self, download_speed, upload_speed, total_devices, active_devices, network_usage, ping_latency):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO network_stats 
            (download_speed, upload_speed, total_devices, active_devices, network_usage, ping_latency)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (download_speed, upload_speed, total_devices, active_devices, network_usage, ping_latency))
        
        conn.commit()
        conn.close()
    
    def get_recent_network_stats(self, limit=100):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, download_speed, upload_speed, total_devices, 
                   active_devices, network_usage, ping_latency
            FROM network_stats 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        stats = cursor.fetchall()
        conn.close()
        
        return [
            {
                'timestamp': stat[0],
                'download_speed': stat[1],
                'upload_speed': stat[2],
                'total_devices': stat[3],
                'active_devices': stat[4],
                'network_usage': stat[5],
                'ping_latency': stat[6]
            }
            for stat in stats
        ]
    
    # Alert methods
    def add_alert(self, alert_type, message, severity='info', device_ip=None, additional_data=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (alert_type, message, severity, device_ip, additional_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (alert_type, message, severity, device_ip, json.dumps(additional_data) if additional_data else None))
        
        conn.commit()
        conn.close()
    
    def get_recent_alerts(self, limit=50):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, alert_type, message, severity, timestamp, is_read, device_ip, additional_data
            FROM alerts 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        alerts = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': alert[0],
                'type': alert[1],
                'message': alert[2],
                'severity': alert[3],
                'timestamp': alert[4],
                'is_read': bool(alert[5]),
                'device_ip': alert[6],
                'additional_data': json.loads(alert[7]) if alert[7] else None
            }
            for alert in alerts
        ]
    
    def mark_alert_read(self, alert_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE alerts SET is_read = 1 WHERE id = ?', (alert_id,))
        conn.commit()
        conn.close()
