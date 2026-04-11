import urequests
import time 
import gc

_DEFAULT_LAT = 26.45
_DEFAULT_LON = 80.35

def _decode(code):
    if code == 0:  return "CLEAR"
    if code in (1, 2, 3):  return "CLOUDY"
    if code in (45, 48):  return "FOG"
    if 51 <= code <= 67:  return "RAIN"
    if 71 <= code <= 77:  return "SNOW"
    if 80 <= code <= 82:  return "RAIN"
    if 85 <= code <= 86:  return "SNOW"
    if 95 <= code <= 99:  return "STORM"
    return "CLEAR"

class WeatherManager:
    REFRESH_MS = 900_000 

    def __init__(self, secrets):
        self.lat = secrets.get("lat", _DEFAULT_LAT)
        self.lon = secrets.get("lon", _DEFAULT_LON)
        self.condition = "CLEAR"
        self.temp_c = None
        self._last_fetch = -self.REFRESH_MS

    def update(self):
        """Returns True if conditions changed"""
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_fetch) < self.REFRESH_MS:
            return False
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.lat}&longitude={self.lon}"
                "&current_weather=true"
            )
            gc.collect()
            r = urequests.get(url, timeout=8)
            if r.status_code == 200:
                cw = r.json()["current_weather"]
                self.condition = _decode(int(cw["weathercode"]))
                self.temp_c = cw.get("temperature")
            r.close()
            gc.collect()
            self._last_fetch = time.ticks_ms()
            return True
        except Exception as e:
            print(f"Weather fetch error: {e}")
            return False