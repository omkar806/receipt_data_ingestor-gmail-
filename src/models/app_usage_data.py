from datetime import datetime

class AppUsageData:
    def __init__(self, hushh_id: str, created_at: datetime, start_data: datetime, end_data: datetime, app_id: str, usage: int, last_foreground: datetime):
        self.hushh_id = hushh_id
        self.created_at = created_at
        self.start_data = start_data
        self.end_data = end_data
        self.app_id = app_id
        self.usage = usage
        self.last_foreground = last_foreground

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
    
    def to_dict(self):
        return self.__dict__