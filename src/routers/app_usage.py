import logging
from fastapi import Request, APIRouter, BackgroundTasks
from typing import List
from src.models.app_usage_data import AppUsageData
from src.models.app_data import AppData
from src.common.helper.app_usage_helper import (
    insert_app_usage_data, 
    is_app_already_scraped, 
    scrape_app,
    fetch_app_category,
    insert_app_data)

router = APIRouter(prefix="/app-usage")

@router.post("/update-usage")
async def update_usage(request:Request):
    data = await request.json()
    app_usage_data = AppUsageData.from_dict(data)
    insert_app_usage_data(app_usage_data)
    return {"message": "Usage updated"}



@router.post("/after-usage-inserted")
async def after_usage_inserted(request:Request, background_tasks: BackgroundTasks):
    data = await request.json()
    app_usages = [AppUsageData(**item) for item in data]
    
    def process_app(app_usage: AppUsageData):
        logging.info(f"going process_app")
        is_app_scraped = is_app_already_scraped(app_usage.app_id)
        logging.info(f"is app scraped {app_usage.app_id}: {is_app_scraped}")
        if not is_app_scraped:
            google_app_json = scrape_app(app_usage.app_id)
            if not google_app_json:
                return {"message": "No information found"}
            app_name = google_app_json['title']
            summary = google_app_json['summary']
            app_developer = google_app_json['developer']
            app_categories = [category['name'] for category in google_app_json['categories']]
            app_data: AppData = AppData.from_dict(google_app_json, app_usage.hushh_id)
            category_id = fetch_app_category(
                app_data=app_data,
                app_name=app_name, 
                summary=summary, 
                app_categories=app_categories, 
                app_developer=app_developer)
            app_data.app_category_id = category_id
            insert_app_data(app_data)
    
    for app_usage in app_usages:
        background_tasks.add_task(process_app, app_usage)

    return {"message": "Processing in background"}

@router.post("/fetch-app-usage")
async def fetch_app_usage(request:Request):
    data = await request.json()
    hushh_id = data['hushh_id']
    percentage_change_timeline = data['percentage_change_timeline']

    app_usages: List[AppUsageData] = fetch_app_usage(hushh_id)

    # do some processing to get the categories from app usage and the %change in each category

    # filter all app usages based on app_id and create a set with unique app id and total time spend + the % change over {percentage_change_timeline}

    # last time fetched metric field

    return {}