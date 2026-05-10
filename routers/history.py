from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models import ContactHistory, Customer

router = APIRouter(prefix="/customers/{customer_id}/history")


@router.post("/add")
def add_history(
    customer_id: int,
    contact_type: str = Form("tel"),
    content: str = Form(""),
    contacted_at: str = Form(""),
    created_by: str = Form(""),
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")

    dt = datetime.fromisoformat(contacted_at) if contacted_at else datetime.now()
    history = ContactHistory(
        customer_id=customer_id,
        contact_type=contact_type,
        content=content,
        contacted_at=dt,
        created_by=created_by,
    )
    db.add(history)
    db.commit()
    return RedirectResponse(url=f"/customers/{customer_id}", status_code=303)


@router.post("/{history_id}/delete")
def delete_history(customer_id: int, history_id: int, db: Session = Depends(get_db)):
    history = db.get(ContactHistory, history_id)
    if not history or history.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="履歴が見つかりません")
    db.delete(history)
    db.commit()
    return RedirectResponse(url=f"/customers/{customer_id}", status_code=303)
