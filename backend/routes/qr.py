from io import BytesIO

import qrcode
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/businesses/{business_id}/feedback", tags=["feedback"])


@router.get("/qr")
def feedback_qr(business_id: str):
    # Feedback form is publicly accessible; business administrators can share this URL.
    public_url = f"{__import__('os').getenv('FRONTEND_URL', 'http://localhost:5173')}?feedback={business_id}"
    image = qrcode.make(public_url)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")
