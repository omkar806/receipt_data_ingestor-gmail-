from datetime import datetime
from typing import List

class AppData:
    def __init__(
        self,
        app_id: str,
        added_by: str,
        scraped_on: datetime,
        icon_url: str,
        app_category_id: int,
        developer_name: str,
        ratings: float,
        downloads: int,
        app_support_website: str,
        app_support_number: str,
        app_support_email: str,
        app_support_address: str,
        app_privacy_policy: str,
        app_data_shared: List[str],
        app_data_collected: List[str],
        app_name: str
    ):
        self.app_id = app_id
        self.added_by = added_by
        self.scraped_on = scraped_on
        self.icon_url = icon_url
        self.app_category_id = app_category_id
        self.developer_name = developer_name
        self.ratings = ratings
        self.downloads = downloads
        self.app_support_website = app_support_website
        self.app_support_number = app_support_number
        self.app_support_email = app_support_email
        self.app_support_address = app_support_address
        self.app_privacy_policy = app_privacy_policy
        self.app_data_shared = app_data_shared
        self.app_data_collected = app_data_collected
        self.app_name = app_name

    @classmethod
    def from_dict(cls, data: dict, hushh_id: str):
        return cls(
            app_name=data.get('title'),
            app_id=data.get('appId'),
            added_by=hushh_id,
            scraped_on=datetime.now(),
            icon_url=data.get('icon'),
            app_category_id=None,
            developer_name=data.get('developer'),
            ratings=data.get('score'),
            downloads=data.get('realInstalls'),
            app_support_website=data.get('developerWebsite'),
            app_support_number=None,
            app_support_email=data.get('developerEmail'),
            app_support_address=data.get('developerAddress'),
            app_privacy_policy=data.get('privacyPolicy'),
            app_data_shared=[],
            app_data_collected=[]
        )

    def to_dict(self):
        return {
            'app_name': self.app_name,
            'app_id': self.app_id,
            'added_by': self.added_by,
            'scraped_on': self.scraped_on.isoformat() if self.scraped_on else None,
            'icon_url': self.icon_url,
            'app_category_id': self.app_category_id,
            'developer_name': self.developer_name,
            'ratings': self.ratings,
            'downloads': self.downloads,
            'app_support_website': self.app_support_website,
            'app_support_number': self.app_support_number,
            'app_support_email': self.app_support_email,
            'app_support_address': self.app_support_address,
            'app_privacy_policy': self.app_privacy_policy,
            'app_data_shared': self.app_data_shared,
            'app_data_collected': self.app_data_collected
        }