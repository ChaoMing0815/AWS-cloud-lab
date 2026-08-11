from datetime import datetime

from app.application.ports import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now()
