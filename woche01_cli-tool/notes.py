from dataclasses import dataclass
from datetime import datetime

@dataclass
class Note:
    id: int
    titel: str
    inhalt: str
    erstellt_am: str = None

    def __post_init__(self):
        if self.erstellt_am is None:
            self.erstellt_am = datetime.now().isoformat()