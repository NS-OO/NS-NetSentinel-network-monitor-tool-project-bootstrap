import psutil
import socket
import subprocess
import platform
import time
import threading
from datetime import datetime
import json
import sqlite3
from database import DatabaseManager

class NetworkMonitor:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.monitoring = False
        self.monitor_thread = None
        self.last_network_status = True
        self.network_down_time = None
        
    def get_network_interfaces(self):
        """Get all network interfaces with their details"""
        interfaces = {}
        for interface, addrs in psutil.net_if_addrs().items():
            interface_info = {
                'name': interface,
                'ip': None,
                'mac': None,
                'netmask': None,
                'is_up': psutil.net_if_stats()[interface].isup
            }
            
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    interface_info['ip'] = addr.address
                    interface_info['netmask'] = addr.netmask
                elif addr.family == psutil.AF_LINK:
                    interface_info['mac'] = addr.address
            
            interfaces[interface] = interface_info
        
        return interfaces
    
    def get_network_speed(self):
        """Get current network speed (upload/download)"""
        try:
            # Get initial stats
            initial_stats = psutil.net_io_counters()
            time.sleep(1)
            final_stats = psutil.net_io_counters()
            
            # Calculate speed in bytes per second
            download_speed = final_stats.bytes_recv - initial_stats.bytes_recv
            upload_speed = final_stats.bytes_sent - initial_stats.bytes_sent
            
            return {
                'download_speed': max(0, download_speed),
                'upload_speed': max(0, upload_speed),
                'bytes_sent': final_stats.bytes_sent,
                'bytes_recv': final_stats.bytes_recv,
                'packets_sent': final_stats.packets_sent,
                'packets_recv': final_stats.packets_recv
            }
        except Exception as e:
            print(f"Error getting network speed: {e}")
            return {
                'download_speed': 0,
                'upload_speed': 0,
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0
            }
    
    def ping_test(self, host="8.8.8.8", timeout=3):
        """Test network connectivity by pinging a host"""
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            command = ["ping", param, "1", "-w", str(timeout * 1000), host]
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 1)
            return result.returncode == 0
        except:
            return False
    
    def get_connected_devices(self):
        """Scan network for connected devices"""
        devices = []
        try:
            # Get local network range
            local_ip = None
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                        local_ip = addr.address
                        break
                if local_ip:
                    break
            
            if not local_ip:
                return devices
            
            # Simple ARP scan for Windows
            if platform.system().lower() == "windows":
                try:
                    # Use arp -a to get devices
                    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    
                    for line in lines:
                        if "dynamic" in line.lower() or "static" in line.lower():
                            parts = line.split()
                            if len(parts) >= 2:
                                ip = parts[0].strip()
                                mac = parts[1].strip()
                                
                                # Get vendor info
                                vendor = self.get_vendor_from_mac(mac)
                                
                                # Try to get hostname
                                hostname = self.get_hostname(ip)
                                
                                devices.append({
                                    'ip': ip,
                                    'mac': mac,
                                    'vendor': vendor,
                                    'hostname': hostname,
                                    'connection_type': 'LAN',
                                    'is_online': self.ping_test(ip, timeout=1)
                                })
                except:
                    pass
            
            # Fallback: use socket to detect active connections
            active_connections = psutil.net_connections()
            unique_ips = set()
            
            for conn in active_connections:
                if conn.status == 'ESTABLISHED':
                    if conn.raddr:
                        unique_ips.add(conn.raddr.ip)
            
            for ip in unique_ips:
                if not ip.startswith('127.') and not ip.startswith('192.168.'):
                    continue
                    
                devices.append({
                    'ip': ip,
                    'mac': 'Unknown',
                    'vendor': 'Unknown',
                    'hostname': self.get_hostname(ip),
                    'connection_type': 'LAN',
                    'is_online': self.ping_test(ip, timeout=1)
                })
                
        except Exception as e:
            print(f"Error scanning devices: {e}")
        
        return devices
    
    def get_vendor_from_mac(self, mac):
        """Get vendor information from MAC address"""
        try:
            # Simple MAC vendor lookup (you can enhance this with a MAC vendor database)
            mac_prefix = mac.replace(':', '').replace('-', '').upper()[:6]
            # This is a simplified version - in production, use a proper MAC vendor database
            vendor_map = {
                '00:1A:79': 'Apple',
                'B8:27:EB': 'Raspberry Pi',
                'DC:A6:32': 'Raspberry Pi',
                '00:0D:4B': 'Intel',
                '00:50:56': 'VMware',
                '08:00:27': 'VirtualBox',
                '00:15:5D': 'Microsoft',
                '00:25:90': 'Microsoft',
                '00:1F:3B': 'Dell',
                '00:1B:63': 'Dell',
                '00:22:19': 'Hewlett-Packard',
                '00:26:55': 'Hewlett-Packard',
                '00:1E:65': 'Netgear',
                '00:1F:33': 'Netgear',
                '00:0F:B5': 'Linksys',
                '00:14:BF': 'Linksys',
                '00:1C:10': 'ASUS',
                '00:22:15': 'ASUS',
                '00:1E:58': 'TP-Link',
                '00:25:86': 'TP-Link',
                '00:1F:A7': 'Samsung',
                '00:26:CB': 'Samsung',
                '00:1B:77': 'Sony',
                '00:26:F2': 'Sony',
                '00:1F:5B': 'LG Electronics',
                '00:26:9E': 'LG Electronics',
                '00:1A:E8': 'Nintendo',
                '00:23:CC': 'Nintendo',
                '00:1F:AF': 'Amazon Technologies',
                '00:26:82': 'Amazon Technologies',
                '00:1B:EA': 'Google',
                '00:26:BB': 'Google',
                '00:1F:F3': 'Facebook',
                '00:26:F3': 'Facebook',
                '00:1A:11': 'Cisco',
                '00:1B:D4': 'Cisco',
                '00:1F:CA': 'Juniper Networks',
                '00:26:99': 'Juniper Networks',
                '00:1B:21': 'Aruba Networks',
                '00:26:73': 'Aruba Networks',
                '00:1F:45': 'Ubiquiti Networks',
                '00:26:AC': 'Ubiquiti Networks',
                '00:1A:2B': 'Ruckus Wireless',
                '00:26:5A': 'Ruckus Wireless',
                '00:1F:6C': 'Aerohive Networks',
                '00:26:E8': 'Aerohive Networks',
                '00:1B:63': 'Dell',
                '00:26:55': 'Hewlett-Packard',
                '00:1F:33': 'Netgear',
                '00:14:BF': 'Linksys',
                '00:22:15': 'ASUS',
                '00:25:86': 'TP-Link',
                '00:26:CB': 'Samsung',
                '00:26:F2': 'Sony',
                '00:26:9E': 'LG Electronics',
                '00:23:CC': 'Nintendo',
                '00:26:82': 'Amazon Technologies',
                '00:26:BB': 'Google',
                '00:26:F3': 'Facebook',
                '00:26:99': 'Juniper Networks',
                '00:26:73': 'Aruba Networks',
                '00:26:AC': 'Ubiquiti Networks',
                '00:26:5A': 'Ruckus Wireless',
                '00:26:E8': 'Aerohive Networks'
            }
            
            for prefix, vendor in vendor_map.items():
                if mac.upper().startswith(prefix):
                    return vendor
            
            return 'Unknown'
        except:
            return 'Unknown'
    
    def get_hostname(self, ip):
        """Get hostname for an IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return ip
    
    def get_bandwidth_usage_by_device(self):
        """Get bandwidth usage per device"""
        # This is a simplified version - in production, use packet sniffing
        usage = {}
        
        try:
            # Get network connections
            connections = psutil.net_connections()
            
            for conn in connections:
                if conn.raddr and conn.status == 'ESTABLISHED':
                    ip = conn.raddr.ip
                    if ip not in usage:
                        usage[ip] = {
                            'bytes_sent': 0,
                            'bytes_received': 0,
                            'packets_sent': 0,
                            'packets_received': 0
                        }
                    
                    # This is approximate - real implementation would use packet capture
                    usage[ip]['bytes_sent'] += conn.raddr.port if conn.raddr else 0
                    usage[ip]['bytes_received'] += conn.laddr.port if conn.laddr else 0
        
        except Exception as e:
            print(f"Error getting bandwidth usage: {e}")
        
        return usage
    
    def start_monitoring(self):
        """Start continuous network monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop network monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Get network stats
                network_stats = self.get_network_speed()
                
                # Check network connectivity
                is_online = self.ping_test()
                
                # Handle network status changes
                if is_online != self.last_network_status:
                    if not is_online and self.last_network_status:
                        # Network went down
                        self.network_down_time = datetime.now()
                        self.db_manager.add_alert(
                            'network_down',
                            'Network connectivity lost',
                            'critical'
                        )
                    elif is_online and not self.last_network_status:
                        # Network came back up
                        downtime = None
                        if self.network_down_time:
                            downtime = (datetime.now() - self.network_down_time).total_seconds()
                        
                        self.db_manager.add_alert(
                            'network_up',
                            f'Network connectivity restored (downtime: {downtime:.1f}s)' if downtime else 'Network connectivity restored',
                            'info'
                        )
                        self.network_down_time = None
                
                self.last_network_status = is_online
                
                # Get connected devices
                devices = self.get_connected_devices()
                
                # Update database
                self.db_manager.add_network_stats(
                    network_stats['download_speed'],
                    network_stats['upload_speed'],
                    len(devices),
                    sum(1 for d in devices if d['is_online']),
                    network_stats['bytes_sent'] + network_stats['bytes_recv'],
                    0  # ping_latency - would need actual ping measurement
                )
                
                # Update device information
                for device in devices:
                    self.db_manager.add_or_update_device(
                        device['ip'],
                        device['mac'],
                        device['vendor'],
                        device['hostname'],
                        device['connection_type']
                    )
                
                # Wait before next check
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def get_current_status(self):
        """Get current network status summary"""
        devices = self.get_connected_devices()
        network_stats = self.get_network_speed()
        
        return {
            'is_online': self.ping_test(),
            'download_speed': network_stats['download_speed'],
            'upload_speed': network_stats['upload_speed'],
            'total_devices': len(devices),
            'active_devices': sum(1 for d in devices if d['is_online']),
            'devices': devices
        }
