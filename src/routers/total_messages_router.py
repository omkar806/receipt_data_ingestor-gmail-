import asyncio
from fastapi import Request,APIRouter
from src.models import supabase_models as sp
from src.common.helper.helper import update_total_messages_count
from src.common.helper.helper import fetch_emails, filter_messages
router = APIRouter(prefix="/gmail")

@router.post("/total_messages")
async def get_total_messages(request:Request):
    body = await request.json()

    access_token = body.get('access_token', None)
    supabase_token = body.get('supabase_token', None)
    session_id = body.get('session_id', None)

    if access_token is None : return {"message":"Access token Invalid ! Try Again!"}

    if supabase_token is None : return {"message":"Supabase token Invalid ! Try Again!"}

    if session_id is None : return {"message":"Session id Invalid ! Try Again!"}

    brand_name = body.get('brand_name') if body.get('brand_name') is not None else None

    user_id = sp.AuthUser_Validator(access_token)

    

    total_messages = []
    page_token = None

    while True:
        messages, next_page_token = fetch_emails(
            brand_name=brand_name,
            page_token=page_token,
            access_token=access_token,
        )

        total_messages.extend(messages)

        if next_page_token:
            page_token = next_page_token
        else:
            break

    total_messages = filter_messages(total_messages, user_id)

    async def delayed_update():
        await asyncio.sleep(2.5)
        update_total_messages_count(session_id, len(total_messages))
    
    asyncio.create_task(delayed_update())

    return {"total_messages": len(total_messages)}