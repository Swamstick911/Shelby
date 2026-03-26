# src/wifi_manager.py
import rtc
import time

class WifiManager:
    def __init__(self, secrets):
        self.secrets = secrets
        self.requests = None
        self.pool = None

    def connect(self):
        # If the firmware doesn't have wifi built in, this will throw
        # an ImportError which code.py catches gracefully
        import wifi
        import adafruit_connection_manager
        import adafruit_requests

        print(f"Connecting to {self.secrets['ssid']}...")
        try:
            wifi.radio.connect(self.secrets['ssid'], self.secrets['password'])
            print("Connected!")
        except Exception as e:
            print(f"WiFi connect failed: {e}")
            return False

        self.pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
        self.requests = adafruit_requests.Session(self.pool, ssl_context)
        return True

    def sync_time(self):
        if not self.requests:
            return

        tz = self.secrets.get("timezone", "Asia/Kolkata")
        url = f"http://worldtimeapi.org/api/timezone/{tz}"

        try:
            print("Syncing time...")
            response = self.requests.get(url)
            data = response.json()
            dt = data["datetime"]
            year   = int(dt[0:4])
            month  = int(dt[5:7])
            day    = int(dt[8:10])
            hour   = int(dt[11:13])
            minute = int(dt[14:16])
            second = int(dt[17:19])
            r = rtc.RTC()
            r.datetime = time.struct_time(
                (year, month, day, hour, minute, second, 0, 0, -1)
            )
            print(f"Time synced: {hour:02d}:{minute:02d}")
            response.close()
        except Exception as e:
            print(f"Time sync failed: {e}")