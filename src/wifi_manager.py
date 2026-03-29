import network
import socket
import struct
import time
import machine

class WifiManager:
    def __init__(self, secrets):
        self.secrets = secrets
        self.wlan = network.WLAN(network.STA_IF)

    def connect(self):
        self.wlan.active(True)
        if self.wlan.isconnected():
            print("Already connected!")
            return True
        
        print(f"Connecting to {self.secrets['ssid']}...")
        self.wlan.connect(self.secrets['ssid'], self.secrets['password'])

        #wait for upto 15 sec
        for _ in range(15):
            if self.wlan.isconnected():
                print(f"Connected! IP: {self.wlan.ifconfig()[0]}")
                return True
            time.sleep(1)
        
        print("WiFi connection failed")
        return False
    
    def sync_time(self):
        NTP_HOSTS = ["time.google.com", "pool.ntp.org", "time.cloudflare.com"]
        NTP_DELTA = 3155673600

        for host in NTP_HOSTS:
            try:
                print("Syncing time via NTP...", host)
                NTP_QUERY = bytearray(48)
                NTP_QUERY[0] = 0x1B
                addr = socket.getaddrinfo(host, 123)[0][-1]
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(5)
                s.sendto(NTP_QUERY, addr)
                msg = s.recv(48)
                s.close()

                utc = struct.unpack("!I", msg[40:44])[0] - NTP_DELTA
                offset_seconds = int(float(self.secrets.get("timezone_offset", 5.5)) * 3600)
                local_time = utc + offset_seconds

                t = time.gmtime(local_time)
                machine.RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))
                print(f"Time synced: {t[3]:02d}:{t[4]:02d}")
                return True
            except Exception as e:
                print("NTP sync failed from", host, ":", e)

        return False
