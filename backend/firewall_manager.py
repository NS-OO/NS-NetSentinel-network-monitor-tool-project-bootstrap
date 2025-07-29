import subprocess
import platform
import json
import os
from database import DatabaseManager

class FirewallManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.is_windows = platform.system().lower() == "windows"
        
    def is_admin(self):
        """Check if running with administrator privileges"""
        try:
            if self.is_windows:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def block_ip(self, ip_address):
        """Block an IP address using Windows Firewall"""
        if not self.is_windows:
            return False, "Windows-only feature"
        
        if not self.is_admin():
            return False, "Administrator privileges required"
        
        try:
            # Create firewall rule to block IP
            rule_name = f"NetworkMonitor_Block_{ip_address}"
            
            # Add outbound rule
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_out",
                "dir=out",
                "action=block",
                f"remoteip={ip_address}",
                "enable=yes"
            ], check=True, capture_output=True)
            
            # Add inbound rule
            subprocess.run([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_in",
                "dir=in",
                "action=block",
                f"remoteip={ip_address}",
                "enable=yes"
            ], check=True, capture_output=True)
            
            # Update database
            self.db_manager.block_device(ip_address, True)
            
            return True, f"Successfully blocked IP: {ip_address}"
            
        except subprocess.CalledProcessError as e:
            return False, f"Failed to block IP: {e.stderr.decode()}"
        except Exception as e:
            return False, f"Error blocking IP: {str(e)}"
    
    def unblock_ip(self, ip_address):
        """Unblock an IP address from Windows Firewall"""
        if not self.is_windows:
            return False, "Windows-only feature"
        
        if not self.is_admin():
            return False, "Administrator privileges required"
        
        try:
            rule_name_out = f"NetworkMonitor_Block_{ip_address}_out"
            rule_name_in = f"NetworkMonitor_Block_{ip_address}_in"
            
            # Remove outbound rule
            subprocess.run([
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name_out}"
            ], check=True, capture_output=True)
            
            # Remove inbound rule
            subprocess.run([
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name_in}"
            ], check=True, capture_output=True)
            
            # Update database
            self.db_manager.block_device(ip_address, False)
            
            return True, f"Successfully unblocked IP: {ip_address}"
            
        except subprocess.CalledProcessError as e:
            return False, f"Failed to unblock IP: {e.stderr.decode()}"
        except Exception as e:
            return False, f"Error unblocking IP: {str(e)}"
    
    def list_blocked_ips(self):
        """List all blocked IP addresses"""
        if not self.is_windows:
            return []
        
        try:
            result = subprocess.run([
                "netsh", "advfirewall", "firewall", "show", "rule", "name=all"
            ], capture_output=True, text=True)
            
            blocked_ips = []
            lines = result.stdout.split('\n')
            
            current_rule = None
            for line in lines:
                line = line.strip()
                if line.startswith('Rule Name:'):
                    current_rule = line.split(':', 1)[1].strip()
                elif line.startswith('RemoteIP:') and current_rule and 'NetworkMonitor_Block_' in current_rule:
                    ip = line.split(':', 1)[1].strip()
                    if ip not in blocked_ips:
                        blocked_ips.append(ip)
            
            return blocked_ips
            
        except Exception as e:
            print(f"Error listing blocked IPs: {e}")
            return []
    
    def get_firewall_status(self):
        """Get current firewall status"""
        if not self.is_windows:
            return {"enabled": False, "message": "Windows-only feature"}
        
        try:
            result = subprocess.run([
                "netsh", "advfirewall", "show", "currentprofile"
            ], capture_output=True, text=True)
            
            if "State" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "State" in line:
                        state = line.split(':', 1)[1].strip().lower()
                        return {
                            "enabled": state == "on",
                            "message": f"Firewall is {state}"
                        }
            
            return {"enabled": False, "message": "Unable to determine firewall status"}
            
        except Exception as e:
            return {"enabled": False, "message": f"Error checking firewall: {str(e)}"}
    
    def test_firewall_rule(self, ip_address):
        """Test if a firewall rule exists for an IP"""
        if not self.is_windows:
            return False
        
        try:
            rule_name_out = f"NetworkMonitor_Block_{ip_address}_out"
            rule_name_in = f"NetworkMonitor_Block_{ip_address}_in"
            
            # Check if rule exists
            result = subprocess.run([
                "netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name_out}"
            ], capture_output=True, text=True)
            
            return "No rules" not in result.stdout
            
        except:
            return False
    
    def clear_all_rules(self):
        """Clear all NetworkMonitor firewall rules (admin only)"""
        if not self.is_windows:
            return False, "Windows-only feature"
        
        if not self.is_admin():
            return False, "Administrator privileges required"
        
        try:
            # Get all NetworkMonitor rules
            result = subprocess.run([
                "netsh", "advfirewall", "firewall", "show", "rule", "name=all"
            ], capture_output=True, text=True)
            
            lines = result.stdout.split('\n')
            rules_to_delete = []
            
            for line in lines:
                if line.strip().startswith('Rule Name:') and 'NetworkMonitor_Block_' in line:
                    rule_name = line.split(':', 1)[1].strip()
                    rules_to_delete.append(rule_name)
            
            # Delete each rule
            for rule_name in rules_to_delete:
                subprocess.run([
                    "netsh", "advfirewall", "firewall", "delete", "rule",
                    f"name={rule_name}"
                ], check=True, capture_output=True)
            
            return True, f"Cleared {len(rules_to_delete)} firewall rules"
            
        except Exception as e:
            return False, f"Error clearing rules: {str(e)}"
