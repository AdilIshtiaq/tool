import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Message
from app.schemas import MessageOut
from app.services.ai_reply_classifier import ReplyClassificationError
from app.services.imap_reply_fetcher import IMAPFetchError, fetch_and_process_replies
from app.services.reply_execution import classify_message

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.post("/fetch-inbound")
def fetch_inbound_replies(db: Session = Depends(get_db)):
    """Called by n8n's schedule trigger (Workflow G) to poll the mailbox for new replies."""
    settings = get_settings()
    try:
        return fetch_and_process_replies(
            db,
            imap_host=settings.imap_host,
            imap_port=settings.imap_port,
            imap_user=settings.smtp_user,
            imap_password=settings.smtp_password,
        )
    except IMAPFetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[MessageOut])
def list_messages(direction: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    query = select(Message).order_by(Message.created_at.desc()).limit(limit)
    if direction:
        query = query.where(Message.direction == direction)
    return db.scalars(query).all()


@router.post("/{message_id}/classify", response_model=MessageOut)
def classify_message_endpoint(message_id: uuid.UUID, db: Session = Depends(get_db)):
    message = db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.direction != "inbound":
        raise HTTPException(status_code=422, detail="Only inbound messages can be classified")

    try:
        return classify_message(db, message)
    except ReplyClassificationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
