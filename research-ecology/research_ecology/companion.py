"""Isolated study companion state. Not UNDERBYTE; no game saves or rewards."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

@dataclass
class Companion:
    name: str = 'Mote'
    mood: str = 'observing'
    visible: bool = True
    quiet_until: datetime | None = None
    notes: int = 0

    def react(self, event: str, moment: datetime | None = None) -> str:
        moment = moment or datetime.now(timezone.utc)
        if self.quiet_until and moment < self.quiet_until:
            return ''
        if event == 'insight':
            self.mood='curious';self.notes+=1
            return 'An idea worth keeping.'
        if event == 'source':
            self.mood='reading'
            return 'Source pinned to the session.'
        if event == 'start':
            self.mood='focused'
            return 'Research session ready.'
        self.mood='observing';return ''

    def quiet(self, minutes: int = 10, moment: datetime | None = None):
        if minutes < 3 or minutes > 120: raise ValueError('Quiet time must be 3–120 minutes')
        self.quiet_until=(moment or datetime.now(timezone.utc))+timedelta(minutes=minutes)
        self.mood='quiet'

    def status(self, moment: datetime | None = None) -> str:
        moment = moment or datetime.now(timezone.utc)
        return 'quiet' if self.quiet_until and moment < self.quiet_until else self.mood
