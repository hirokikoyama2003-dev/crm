from datetime import date, timedelta, datetime
from calendar import monthrange
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Customer, Rank, ContactHistory

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    week_later = today + timedelta(days=7)

    overdue = (
        db.query(Customer)
        .filter(Customer.next_contact_date < today)
        .order_by(Customer.next_contact_date)
        .all()
    )
    due_today = (
        db.query(Customer)
        .filter(Customer.next_contact_date == today)
        .order_by(Customer.name)
        .all()
    )
    due_week = (
        db.query(Customer)
        .filter(Customer.next_contact_date > today, Customer.next_contact_date <= week_later)
        .order_by(Customer.next_contact_date)
        .all()
    )

    ranks = db.query(Rank).order_by(Rank.priority).all()
    rank_counts = {r.id: 0 for r in ranks}
    for row in db.query(Customer.rank_id, func.count()).group_by(Customer.rank_id).all():
        if row[0] is not None:
            rank_counts[row[0]] = row[1]

    total_customers = db.query(func.count(Customer.id)).scalar()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "overdue": overdue,
        "due_today": due_today,
        "due_week": due_week,
        "ranks": ranks,
        "rank_counts": rank_counts,
        "total_customers": total_customers,
        "today": today,
    })


@router.get("/report", response_class=HTMLResponse)
def report(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    month_start = today.replace(day=1)
    _, last_day = monthrange(today.year, today.month)
    month_end = today.replace(day=last_day)

    # 今月のコンタクト件数（履歴ベース）
    month_contacts = (
        db.query(func.count(ContactHistory.id))
        .filter(
            func.date(ContactHistory.contacted_at) >= month_start,
            func.date(ContactHistory.contacted_at) <= today,
        )
        .scalar()
    )

    # 種別ごと
    contact_by_type = {}
    for row in (
        db.query(ContactHistory.contact_type, func.count())
        .filter(
            func.date(ContactHistory.contacted_at) >= month_start,
            func.date(ContactHistory.contacted_at) <= today,
        )
        .group_by(ContactHistory.contact_type)
        .all()
    ):
        contact_by_type[row[0]] = row[1]

    # ランク別件数
    ranks = db.query(Rank).order_by(Rank.priority).all()
    rank_counts = {r.id: 0 for r in ranks}
    for row in db.query(Customer.rank_id, func.count()).group_by(Customer.rank_id).all():
        if row[0] is not None:
            rank_counts[row[0]] = row[1]

    # 今月の成約件数・金額（status が existing になった顧客は contract_amount で判断）
    total_customers = db.query(func.count(Customer.id)).scalar()
    existing_customers = db.query(func.count(Customer.id)).filter(Customer.status == "existing").scalar()
    lost_customers = db.query(func.count(Customer.id)).filter(Customer.status == "lost").scalar()

    # 今月コンタクトした顧客数（ユニーク）
    unique_contacted = (
        db.query(func.count(func.distinct(ContactHistory.customer_id)))
        .filter(
            func.date(ContactHistory.contacted_at) >= month_start,
            func.date(ContactHistory.contacted_at) <= today,
        )
        .scalar()
    )

    type_labels = {"phone": "📞 電話", "email": "✉️ メール", "meeting": "🤝 商談", "visit": "🏠 現地案内", "other": "📝 その他"}

    return templates.TemplateResponse("report.html", {
        "request": request,
        "today": today,
        "month_start": month_start,
        "month_contacts": month_contacts,
        "unique_contacted": unique_contacted,
        "contact_by_type": contact_by_type,
        "type_labels": type_labels,
        "ranks": ranks,
        "rank_counts": rank_counts,
        "total_customers": total_customers,
        "existing_customers": existing_customers,
        "lost_customers": lost_customers,
    })
