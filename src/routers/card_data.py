from fastapi import BackgroundTasks, Request, APIRouter
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from src.models import supabase_models as sp
from src.common.helper.card_data_helper import (
    generate_card_recommendations,
    fetch_all_messages_by_session,
    fetch_brands,
    fetch_brand_info,
    insert_brand_details,
    create_custom_card,
    generate_image,
    insert_custom_card)

router = APIRouter(prefix="/card-data")

@router.get("/generate-image")
async def create_image(color: str):
    if not color.startswith('#') or len(color) != 7:
        raise HTTPException(status_code=400, detail="Invalid color format. Please provide a hex color code (e.g., #FFFFFF)")
    
    try:
        image_bytes = generate_image(color)
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating the image: {str(e)}")


@router.post("/generate-brands-and-custom-cards")
async def generate_brands_and_custom_cards(request:Request, background_tasks: BackgroundTasks):
    body = await request.json()
    
    access_token = body.get('access_token', None)
    session_id = body.get('session_id', None)
    supabase_authorisation_token = body.get("supabase_authorisation", None)
    
    if not session_id:
        return {"message": "Invalid session!"}
    
    user_id = sp.AuthUser_Validator(supabase_authorisation_token)
    if not user_id:
        return {"message": "User Unauthenticated!"}
    
    if access_token is None : return {"message":"Access token Invalid ! Try Again!"}

    # fetch all the messages bases on the session_id using fetch_all_messages_by_session(session_id)
    messages = fetch_all_messages_by_session(session_id)
    
    # unique_domains = get list of unique domains (brands_details_response map each elem['domain'])
    unique_domains = list(set(message['company'] for message in messages))
    
    # already_created_brands = fetch all the brands where domain is in unique_domains using fetch_brands(unique_domains) map for each elem['domain'] as list
    already_created_brands = fetch_brands(unique_domains)
    existing_domains = {brand['domain'] for brand in already_created_brands}  # Set of existing domains
    
    # remove all the domains returned by already_created_brands from the unique brands
    unique_domains = [domain for domain in unique_domains if domain not in existing_domains and domain != ""]  # Filter unique domains
    
    if None in unique_domains:
        unique_domains.remove(None)
    
    print(f"unique_domains:::{unique_domains}")
    
    # loop through remaining unique_domains list 
    for domain in unique_domains:
        # Fetch brand details
        brand_details = fetch_brand_info(domain)
        
        print(f"brand_details:::{brand_details}")
        
        if brand_details:
            # Insert brand details and get ID
            brand_id = insert_brand_details(brand_details)
            
            if brand_id:
                # Create brand card
                card_details = create_custom_card(brand_id, brand_details) 
                
                # insert custom card
                insert_custom_card(card_details)
        
    background_tasks.add_task(generate_card_recommendations, user_id)
    
    return {"message": "Brands and custom cards generated successfully!"}