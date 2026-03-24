import wifi
import rtc
import time
import adafruit_connection_manager
import adafruit_requests

class WifiManager:
    def __init__(self, secrets):
        self.secrets = secrets
        self.requests = None
        self.pool = None

    def connect(self):
        print(f"Connecting to {self.secrets['ssid']}...")
        try:
            wifi.radio.connect(self.secrets['ssid'], self.secrets['password'])
            print("Connected to WiFi!")
        except Exception as e:
            print(f"WiFi failed: {e}")
            return False
        
        #network setup
        self.pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
        self.requests = adafruit_requests.Session(self.pool, ssl_context)
        return True
    
    def sync_time(self):
        print("Syncing time...")
        tz = self.secrets.get("timezone", "Asia/Kolkata")
        url = f"http://worldtimeapi.org/api/timezone/{tz}"

        try:
            response = self.requests.get(url)
            data = response.json()
            #Parse ISO 8601 string: 2026-03-24T21:02:00.000+05:30
            dt = data["datetime"]
            year = int(dt[0:4])
            month = int(dt[5:7])
            day = int(dt[8:10])
            hour = int(dt[11:13])
            minute = int(dt[14:16])
            second = int(dt[17:19])

            #set RTC
            r = rtc.RTC()
            r.datetime = time_struct_time((year, month, day, hour, minute, second, 0, 0, -1))
            print("Time synced successfully!")
        except Exception as e:
            print(f"Time sync failed: {e}")