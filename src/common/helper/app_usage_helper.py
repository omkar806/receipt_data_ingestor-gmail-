import csv
from io import StringIO
import json
import os
from typing import List
from google_play_scraper import app
from functools import lru_cache
from src.models.app_usage_data import AppUsageData
from src.models.app_data import AppData
from src.models.supabase_models import Supabase_Client
from src.common.helper.helper import make_request
from src.constants import TEMPERATURE, MAX_TOKENS, APP_CATEGORIES
import logging


def insert_app_usage_data(app_usage_data: AppUsageData):
    logging.info("inserting app usage data")
    supabase = Supabase_Client().instance
    data = app_usage_data.to_dict()
    try:
        _ = (
            supabase.table("app_usage")
            .insert(data)
            .execute()
        )
    except Exception as e:
        print("error: Unable to store app usage data because of ", e)

def is_app_already_scraped(app_id: str):
    logging.info(f"checking if {app_id} is scraped")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("user_apps").select("*").eq("app_id", app_id).execute()
        logging.info(f"response::::{response.data}")
        return bool(response.data)
    except Exception as e:
        logging.error(f"error: error occurred in checking if {app_id} is scraped because of ", e)

def scrape_app(app_id: str) -> dict:
    try:
        result = app(
            app_id,
            lang='en', # defaults to 'en'
            country='us' # defaults to 'us'
        )
        return result
    except:
        return None
    

def fetch_app_category(app_data: AppData, app_name: str, summary: str, app_categories: List[str], app_developer: str) -> int:
    prompt = f"""Your job is to analyze the app information provided below and return {{"category_id": INT ID OF THE CATEGORY BASED ON THE PRE DEFINED LIST WHICH MATCH WITH APP INFORMATION}} by checking the provided app information.

App Information
App Name: {app_name}
App Summary: {summary}
App Identified: {app_data.app_id}
App Categories: {app_categories}
App Developer: {app_developer}

Pre Defined Categories: {fetch_pre_defined_categories()}

Your output should only contain a json 
{{"category_id": CATEGORY INT ID FROM PRE DEFINED CATEGORIES}}
"""

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        "OpenAI-Organization": os.environ['ORG_ID']
    }
    data = {
        "model": "gpt-4o-mini",
        "max_tokens": MAX_TOKENS, 
        "messages": [{"role": "user", "content": f"{prompt}"}],
        "temperature": TEMPERATURE
    }
    logging.info(f"GPT prompt: {prompt}")
    output = make_request(url, headers=headers, data=data, method='POST')
    try:
        content = output['choices'][0]['message']['content']
        data = json.loads(content)['category_id']
        return int(data)
    except:
        print(f"error: unable to fetch category_id for {app_data.app_id}")
        return None

def insert_app_data(app_data: AppData):
    logging.info("inserting app data")
    supabase = Supabase_Client().instance
    data = app_data.to_dict()
    try:
        _ = (
            supabase.table("user_apps")
            .insert(data)
            .execute()
        )
    except Exception as e:
        print("error: Unable to store app data because of ", e)

def fetch_pre_defined_categories():
    csv_file = StringIO(APP_CATEGORIES)
    id_to_name = {}
    reader = csv.DictReader(csv_file)

    for row in reader:
        id_to_name[int(row['id'])] = row['category_name']

    return id_to_name
    
