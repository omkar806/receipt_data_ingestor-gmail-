import binascii
from typing import List
import logging, base64
from src.constants import *
from src.models.message import Message
from src.models.supabase_models import Supabase_Client
import httpx
from urllib.parse import quote


def fetch_emails(brand_name: str, page_token: int, access_token: str):
    g_query = G_QUERY
    if brand_name is not None:
        g_query = G_BRAND_QUERY(brand_name)
    
    gmail_url = f"https://www.googleapis.com/gmail/v1/users/me/messages?q={g_query}&maxResults=20"
    if page_token:
        gmail_url += f"&pageToken={page_token}"
    
    # gmail_response = requests.get(gmail_url, headers={"Authorization": f"Bearer {access_token}"})
    # gmail_data = gmail_response.json()

    gmail_data = make_request(gmail_url, headers={"Authorization": f"Bearer {access_token}"})

    
    if "messages" in gmail_data:
        return gmail_data['messages'], gmail_data.get("nextPageToken", None)
    
    return [], gmail_data.get("nextPageToken", None)

def store_message_data(message: Message):
    attachments = message.attachments
    if attachments:
        for attachment in attachments:
            extension = attachment.filename.split(".")[-1]
            file_name = f"{message.id}_{attachment.attachment_id}.{extension}"
            print(f"file_name: {file_name}")
            supabase = Supabase_Client().instance
            base64_data = attachment.data
            try:
                decoded_data = base64.urlsafe_b64decode(base64_data)
                supabase.storage.from_('receipt_radar').upload(file_name, decoded_data)
            except binascii.Error as e:
                print(f"Error decoding base64 data: {e}")
            except Exception as e:
                print(f"Error uploading file: {e}")

def insert_message(message:Message, session_id, user_id):
    logging.info("inserting message")
    supabase = Supabase_Client().instance
    print("to_json")
    data = message.to_json(session_id, user_id)
    print(data)
    try:
        if data:
            response = (
                supabase.table("receipt_radar_structured_data_duplicate")
                .insert(data)
                .execute()
            )
            print("response:")
            print(response)
        else:
            print("error: Unable to store receipt because of value being null")
    except Exception as e:
        print("error: Unable to store receipt because of ", e)

def fetch_message(message_id: str, access_token: str):
    
    message_url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{message_id}"
    # message_response = requests.get(message_url, headers={"Authorization": f"Bearer {access_token}"})
    # message_data = message_response.json()
    message_data = make_request(message_url, headers={"Authorization": f"Bearer {access_token}"})
    return message_data

def filter_messages(messages: List[Message], hushh_id: str):
    logging.info("filtering messages")
    supabase = Supabase_Client().instance
    existing_ids = [
        record['message_id'] 
        for record in supabase.table("receipt_radar_structured_data_duplicate")
        .select("message_id")
        .eq("user_id", hushh_id)
        .execute()
        .data
    ]
    messages = [message for message in messages if message['id'] not in existing_ids]
    return messages


def update_total_messages_count(session_id: str, total_messages_count: int):
    try:
        supabase = Supabase_Client().instance
        supabase.table("receipt_radar_history").update({"total_receipts": total_messages_count}).eq("id", int(session_id)).execute()
    except Exception as e:
        print(f"error: unable to update total messages count :: {e}")
        pass

def update_receipt_radar_history_status(session_id: str, status: str, total_processed_receipts: int = None):
    print(f"updating receipt radar history status for session_id: {session_id} with status: {status} and total_processed_receipts: {total_processed_receipts}")
    try:
        supabase = Supabase_Client().instance
        if total_processed_receipts:
            res = supabase.table("receipt_radar_history").update({"status": status, "total_processed_receipts": total_processed_receipts}).eq("id", int(session_id)).execute()
        else:
            res = supabase.table("receipt_radar_history").update({"status": status}).eq("id", int(session_id)).execute()
        print(f"response from update receipt radar history status: {res}")
    except Exception as e:
        print(f"error: unable to update receipt radar history status :: {e}")
        pass


def make_request(url, headers, method='GET', data=None):
    try:
        # Make the request based on the method
        if method.upper() == 'GET':
            response = httpx.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = httpx.post(url, headers=headers, json=data)
        elif method.upper() == 'PUT':
            response = httpx.put(url, headers=headers, json=data)
        elif method.upper() == 'DELETE':
            response = httpx.delete(url, headers=headers)
        else:
            logging.error(f"Unsupported HTTP method: {method}")
            return None

        # Raise an exception if the request was unsuccessful
        response.raise_for_status()

        # Return the JSON response
        return response.json()

    except httpx.RequestError as e:
        # Handle network-related errors
        logging.error(f"Request error occurred: {e}")
    except httpx.HTTPStatusError as e:
        # Handle HTTP status errors (e.g., 4xx, 5xx responses)
        logging.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        # Catch-all for any other exceptions
        logging.error(f"An unexpected error occurred: {e}")

    # Return None if an error occurs
    return None
