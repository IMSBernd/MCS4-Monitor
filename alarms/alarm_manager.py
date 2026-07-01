from datetime import datetime


class AlarmManager:
    def __init__(self):
        self.limits = {
            1: {"warn_low": 0, "warn_high": 90, "alarm_low": -10, "alarm_high": 95},
            2: {"warn_low": 4.5, "warn_high": 6.0, "alarm_low": 4.0, "alarm_high": 6.5},
            3: {"warn_low": 500, "warn_high": 1900, "alarm_low": 300, "alarm_high": 2100},
            4: {"warn_low": 0, "warn_high": 88, "alarm_low": -10, "alarm_high": 95},
            5: {"warn_low": 0, "warn_high": 520, "alarm_low": -10, "alarm_high": 560},
        }
        self.active = {}

    def evaluate(self, sensor: dict):
        channel = sensor["id"]
        limits = self.limits.get(channel)
        if not limits:
            return None
        value = sensor["value"]
        name = sensor["name"]
        unit = sensor["unit"]
        if value <= limits["alarm_low"] or value >= limits["alarm_high"]:
            state = "ALARM"
            text = f"{name}: {value:.2f} {unit} außerhalb Alarmgrenze"
        elif value <= limits["warn_low"] or value >= limits["warn_high"]:
            state = "WARNUNG"
            text = f"{name}: {value:.2f} {unit} außerhalb Warngrenze"
        else:
            state = "OK"
            text = ""

        sensor["status"] = state
        sensor["alarm"] = text

        if state in {"WARNUNG", "ALARM"}:
            if self.active.get(channel) != text:
                self.active[channel] = text
                return f"{datetime.now():%H:%M:%S} [{state}] {text}"
        else:
            if channel in self.active:
                del self.active[channel]
                return f"{datetime.now():%H:%M:%S} [OK] {name}: Wert wieder normal"
        return None
