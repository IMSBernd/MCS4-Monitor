from datetime import datetime


class AlarmManager:
    LIMITS = {
        1: {"warn_low": 0, "warn_high": 90, "alarm_low": -10, "alarm_high": 95},
        2: {"warn_low": 4.5, "warn_high": 6.0, "alarm_low": 4.0, "alarm_high": 6.5},
        3: {"warn_low": 500, "warn_high": 1900, "alarm_low": 300, "alarm_high": 2100},
        4: {"warn_low": 0, "warn_high": 88, "alarm_low": -10, "alarm_high": 95},
        5: {"warn_low": 0, "warn_high": 520, "alarm_low": -10, "alarm_high": 560},
    }

    def __init__(self):
        self.active = {}

    def evaluate(self, decoded):
        limits = self.LIMITS.get(decoded.channel)
        if not limits:
            return "OK", "", None
        value = decoded.value
        text = ""
        if value <= limits["alarm_low"] or value >= limits["alarm_high"]:
            state = "ALARM"
            text = f"{decoded.name}: {value:.2f} {decoded.unit} außerhalb Alarmgrenze"
        elif value <= limits["warn_low"] or value >= limits["warn_high"]:
            state = "WARNUNG"
            text = f"{decoded.name}: {value:.2f} {decoded.unit} außerhalb Warngrenze"
        else:
            state = "OK"
        event = None
        if state in {"WARNUNG", "ALARM"}:
            if self.active.get(decoded.channel) != text:
                self.active[decoded.channel] = text
                event = f"{datetime.now():%H:%M:%S} [{state}] {text}"
        else:
            if decoded.channel in self.active:
                del self.active[decoded.channel]
                event = f"{datetime.now():%H:%M:%S} [OK] {decoded.name}: Wert wieder normal"
        return state, text, event
