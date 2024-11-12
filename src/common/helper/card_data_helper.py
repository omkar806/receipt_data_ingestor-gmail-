import os
from PIL import Image, ImageDraw, ImageOps
import io
from datetime import datetime
from typing import List, Optional
from colorthief import ColorThief
import requests
from src.models.supabase_models import Supabase_Client
import logging


def fetch_all_messages_by_session(session_id: str):
    logging.info(f"fetching messages for session_id: {session_id}")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("receipt_radar_structured_data_duplicate").select("*").eq("session_id", session_id).execute()
        logging.info(f"fetched messages: {response.data}")
        return response.data
    except Exception as e:
        logging.error(f"error: unable to fetch messages for session_id {session_id} because of ", e)
        return []
    
def fetch_all_messages_by_user_id(user_id: str):
    logging.info(f"fetching messages for user_id: {user_id}")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("receipt_radar_structured_data_duplicate").select("*").eq("user_id", user_id).execute()
        logging.info(f"fetched messages: {response.data}")
        return response.data
    except Exception as e:
        logging.error(f"error: unable to fetch messages for user_id {user_id} because of ", e)
        return []

def fetch_brands(unique_domains: List[str], columns: Optional[str] = '*'):
    logging.info(f"fetching brands for domains: {unique_domains}")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("brand_details").select(columns).in_("domain", unique_domains).execute()
        logging.info(f"fetched brands: {response.data}")
        return response.data
    except Exception as e:
        logging.error(f"error: unable to fetch brands because of ", e)
        return []
    
def fetch_cards(unique_domains: List[str]):
    logging.info(f"fetching cards for domains: {unique_domains}")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("card_market").select("*, brand_categories(brand_category)").in_("domain", unique_domains).execute()
        logging.info(f"fetched cards: {response.data}")
        return response.data
    except Exception as e:
        logging.error(f"error: unable to fetch cards because of ", e)
        return []

def fetch_brand_info(domain: str):
    supabase = Supabase_Client().instance
    
    API_KEY = "live_6a1a28fd-6420-4492-aeb0-b297461d9de2"
    file_name = f"{domain}_{datetime.utcnow():%Y%m%d_%H%M%S}.jpg"
    try:
        domain_info_api_response = requests.get(f"https://search.logo.dev/?query={domain}").json()
        print(f"domain_info_api_response for {domain}:::{domain_info_api_response}")
        if domain_info_api_response:
            brand_name = domain_info_api_response[0]['name']
        else:
            brand_name = '.'.join(domain.split('.')[0:-1])
        
        response = requests.get(f"https://img.logo.dev/{domain}?token={API_KEY}&size=100&format=jpg")
        supabase.storage.from_('receipt_radar').upload(file_name, response.content)
        res = supabase.storage.from_('receipt_radar').get_public_url(file_name)
        return {
            "domain": domain,
            "brand_name": brand_name,
            "brand_category_id": 1,
            "brand_logo": res,
        }
    except Exception as e:
        print(f"Unable to create brand {domain} because {e}")
        return None

def insert_brand_details(brand_details: dict):
    logging.info("inserting brand details")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("brand_details").insert(brand_details).execute()
        logging.info(f"inserted brand details: {response.data}")
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        logging.error("error: unable to insert brand details because of ", e)
        return None
    
def insert_recommendation(user_id: str, card_ids: List[int]):
    logging.info("inserting recommendation")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("recommended_cards").insert({
            'user_id': user_id,
            'card_ids': card_ids
        }).execute()
        logging.info(f"inserted recommendation: {response.data}")
        return None
    except Exception as e:
        logging.error("error: unable to insert recommendation because of ", e)
        return None
    
def create_custom_card(brand_id: int, brand_details: dict):
    return {
        'brand_name': brand_details['brand_name'],
        'image': brand_details['brand_logo'], # This is the icon in card market
        'category': '', # category will be empty string for custom cards
        'category_id': brand_details['brand_category_id'],
        'brandId': brand_id,
        'type': 3,
        'domain': brand_details['domain'],
        'audio_url': None,
        'body_image': None, # custom cards will not have any body
        'logo': brand_details['brand_logo'], # This is the brand logo in bottom left of every card
        'featured': 1,
    }

def insert_custom_card(card_details: dict):
    logging.info(f"creating brand card for: {card_details}")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("card_market").insert(card_details).execute()
        logging.info(f"created brand card: {response.data}")
    except Exception as e:
        logging.error("error: unable to create brand card because of ", e)
        
def analyze_purchase_patterns(receipts: dict):
    brand_spending = {}
    category_spending = {}

    for receipt in receipts:
        brand_domain = receipt['company']
        brand_category = receipt['brand_category']
        amount = receipt.get('total_cost', 0)

        # Update brand spending data
        brand_spending[brand_domain] = brand_spending.get(brand_domain, 0) + amount

        # Update category spending data
        category_spending[brand_category] = category_spending.get(brand_category, 0) + amount
        
    min_brand_spending = min(brand_spending.values())
    max_brand_spending = max(brand_spending.values())
    
    min_category_spending = min(brand_spending.values())
    max_category_spending = max(brand_spending.values())

    return brand_spending, category_spending, min_brand_spending, max_brand_spending, min_category_spending, max_category_spending

def calculate_card_score(
    brand_spending,
    category_spending,
    min_brand_spending,
    max_brand_spending,
    min_category_spending,
    max_category_spending,
    card,
):
    """
    brand_spending: How much is spent by user on this brand/card.
    category_speaking: How much is spent by user on this brand/card's category.
    """
    alpha = 0.0  # Weight for brand-specific spending
    beta = 1.0   # Weight for category-specific spending
    
    card_brand = card['domain']
    card_category = card['brand_categories']['brand_category']

    if card_brand in brand_spending:
        user_brand_spending = brand_spending[card_brand]
        brand_score = (user_brand_spending - min_brand_spending) / (max_brand_spending - min_brand_spending)
    else:
        brand_score = 0

    if card_category in category_spending:
        user_category_spending = category_spending[card_category]
        category_score = (user_category_spending - min_category_spending) / (max_category_spending - min_category_spending)
    else:
        category_score = 0

    brand_score = max(0, min(brand_score, 1))
    category_score = max(0, min(category_score, 1))

    final_score = alpha * brand_score + beta * category_score
    return final_score

def recommend_cards(
        brand_spending,
        category_spending,
        min_brand_spending,
        max_brand_spending,
        min_category_spending,
        max_category_spending,
        cards
    ):
    recommended_cards = []

    for brand_domain, spending in brand_spending.items():
        custom_cards = [c for c in cards if c['domain'] == brand_domain]
        if custom_cards:
            card = custom_cards[0]
            print(f"card:::::{card}")
            
            if not card['brand_categories']:
                score = 0
            else:
                # Calculate a score based on relevance to the user's spending
                score = calculate_card_score(
                    brand_spending,
                    category_spending,
                    min_brand_spending,
                    max_brand_spending,
                    min_category_spending,
                    max_category_spending,
                    card
                )
            recommended_cards.append((custom_cards[0], score))

    return recommended_cards

def limit_cards(recommended_cards, limit=3):
    # sorting based on score
    recommended_cards.sort(key=lambda x: x[1], reverse=True)
    top_cards = recommended_cards[:limit]
    return top_cards

def get_dominant_color(logo_url):
    response = requests.get(logo_url)
    image_bytes = io.BytesIO(response.content)
    color_thief = ColorThief(image_bytes)
    dominant_color = color_thief.get_color(quality=1)
    dominant_color_hex = '#{:02x}{:02x}{:02x}'.format(*dominant_color)
    return dominant_color_hex

def generate_image(dominant_color: str) -> bytes:
    # Set the parameters
    width = 596
    height = 363
    radius = 30

    # Create the base image with the dominant color
    base_image = Image.new("RGB", (width, height), dominant_color)

    # Apply rounded corners
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
    base_image = ImageOps.fit(base_image, mask.size, centering=(0.5, 0.5))
    base_image.putalpha(mask)

    # Load the overlay image
    current_directory = os.path.dirname(__file__)
    image_path = os.path.join(current_directory, 'overlay.png')
    overlay_image = Image.open(image_path)

    # Resize overlay image width to match the base image width
    overlay_image = overlay_image.resize((width, int(overlay_image.height * (width / overlay_image.width))))

    # Calculate the position to paste the overlay image (aligned to the bottom)
    position = (0, height - overlay_image.height)

    # Paste the overlay image on the base image
    base_image.paste(overlay_image, position, overlay_image)

    # Save the final image to a bytes buffer
    img_byte_arr = io.BytesIO()
    base_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    return img_byte_arr.getvalue()

def upload_image_to_supabase_storage(image_bytes: bytes) -> str:
    supabase = Supabase_Client().instance
    file_name = f"image_{datetime.utcnow():%Y%m%d_%H%M%S}.png"  # Generate a unique file name

    try:
        # Upload the image to Supabase storage
        supabase.storage.from_('dump').upload(file_name, image_bytes)
        # Get the public URL of the uploaded image
        url = supabase.storage.from_('dump').get_public_url(file_name)
        return url
    except Exception as e:
        logging.error(f"Error uploading image to Supabase: {e}")
        return ""

def update_card_url_in_card_market(card_id: int, url: str):
    logging.info(f"Updating card with ID {card_id} to set body_image to {url}")
    supabase = Supabase_Client().instance
    try:
        response = supabase.table("card_market").update({"body_image": url}).eq("id", card_id).execute()
        logging.info(f"Updated card: {response.data}")
    except Exception as e:
        logging.error(f"Error updating card {card_id}: {e}")

def generate_card_recommendations(user_id: str):
    # Fetch all receipts
    receipts = fetch_all_messages_by_user_id(user_id)
    unique_domains = list(set(message['company'] for message in receipts))
    
    # Fetch cards based on receipt domain
    cards = fetch_cards(unique_domains=unique_domains)
    print(f"Total fetched cards are {cards.__len__()}")
    
    # Extract user's purchase patterns
    (
        brand_spending,
        category_spending,
        min_brand_spending,
        max_brand_spending,
        min_category_spending,
        max_category_spending
    ) = analyze_purchase_patterns(
        receipts=receipts,
        # NOTE: Add more data sources/user patterns here
    )
    
    # Extract cards based on user patterns
    recommended_cards = recommend_cards(
        brand_spending,
        category_spending,
        min_brand_spending,
        max_brand_spending,
        min_category_spending,
        max_category_spending,
        cards
    )

    # Extract top n recommendations
    recommendations = limit_cards(recommended_cards, limit=3)
    print(f"full recommendations: {recommendations}")
    
    card_ids = [recommendation[0]['id'] for recommendation in recommendations]
    
    print(f"recommendations::::{recommendations}")
    
    insert_recommendation(user_id=user_id, card_ids=card_ids)
    
    recommended_cards_without_body_image = [recommendation[0] for recommendation in recommendations if recommendation[0]['body_image'] == "" or recommendation[0]['body_image'] == None]
    print(f"recommended_cards_without_body_image:{recommended_cards_without_body_image.__len__()}")
    
    for card in recommended_cards_without_body_image:
        logo_url = card['logo'];
        print(f"logo url: {logo_url}")
        dominant_color = get_dominant_color(logo_url)
        print(f"dominant color: {dominant_color}")
        image_bytes = generate_image(dominant_color)
        url = upload_image_to_supabase_storage(image_bytes)
        print(f"uploaded url: {url}")
        update_card_url_in_card_market(card['id'], url)
        print(f"card body image updated: {card['id']} {url}")
    
