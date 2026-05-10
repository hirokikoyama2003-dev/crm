from __future__ import annotations
from datetime import date as date_type
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
from models import Customer, Rank, LifecycleStage

router = APIRouter(prefix="/customers")
templates = Jinja2Templates(directory="templates")

STATUS_LABELS = {"prospect": "見込み", "existing": "既存", "lost": "失注"}
CONTACT_TYPE_LABELS = {
    "tel":     "📞 TEL（架電）",
    "tel_in":  "📲 TEL（受電）",
    "sms":     "💬 SMS",
    "email":   "✉️ メール",
    "meeting": "🤝 商談",
    "visit":   "🏠 現地案内",
    "other":   "📝 その他",
}

PROPERTY_TYPES = ["一戸建て", "マンション", "土地", "土地+建物", "投資用", "その他"]
FLOOR_PLANS = ["1K", "1DK", "1LDK", "2LDK", "3LDK", "4LDK", "4LDK以上"]
RESIDENCE_TYPES = ["自己所有マンション", "自己所有戸建", "賃貸マンション", "賃貸アパート", "賃貸戸建"]
PURCHASE_PURPOSES = ["自己居住", "投資", "親族用", "その他"]
PLANNED_PERIODS = ["3ヶ月以内", "6ヶ月以内", "1年以内", "2年以内", "未定"]
INFLOW_SOURCES = ["ポータルサイト", "チラシ", "紹介", "看板", "SNS", "電話問い合わせ", "来店", "その他"]
RESPONSE_TYPES = ["会員登録", "物件リクエスト", "土地リクエスト", "未公開", "メルマガ登録", "プレミアムクラブ", "電話", "メール", "紹介", "その他"]


def _parse_date(val: str) -> Optional[date_type]:
    return date_type.fromisoformat(val) if val else None


def _parse_int(val: str) -> Optional[int]:
    return int(val) if val else None


def _customer_from_form(
    name, email, phone, birth_date, best_contact_time,
    postal_code, prefecture, city, address, current_residence_type,
    first_contact_date, first_inflow_source, first_response_type,
    referral_agency, inquiry_property_name, inquiry_property_price,
    rank_id, lifecycle_stage, status, assigned_to,
    last_email_reply_date, rental_renewal_date, sale_activity_status, next_contact_date,
    purchase_purpose, purchase_motivation, planned_purchase_period,
    desired_property_type, desired_area, desired_area_memo,
    desired_rail_line, desired_rail_line_memo, max_station_distance,
    budget_max, desired_land_area_max, desired_floor_area_max,
    desired_floor_plan, purchase_conditions_memo,
    num_adults, num_children, child_age_1, child_age_2, child_age_3, num_cars,
    household_company, household_industry, household_income,
    spouse_company, spouse_industry, spouse_income,
    contract_amount, memo,
) -> dict:
    return dict(
        name=name, email=email, phone=phone,
        birth_date=_parse_date(birth_date), best_contact_time=best_contact_time,
        postal_code=postal_code, prefecture=prefecture, city=city, address=address,
        current_residence_type=current_residence_type,
        first_contact_date=_parse_date(first_contact_date),
        first_inflow_source=first_inflow_source, first_response_type=first_response_type,
        referral_agency=referral_agency, inquiry_property_name=inquiry_property_name,
        inquiry_property_price=_parse_int(inquiry_property_price),
        rank_id=_parse_int(rank_id), lifecycle_stage=lifecycle_stage,
        status=status, assigned_to=assigned_to,
        last_email_reply_date=_parse_date(last_email_reply_date),
        rental_renewal_date=_parse_date(rental_renewal_date),
        sale_activity_status=sale_activity_status,
        next_contact_date=_parse_date(next_contact_date),
        purchase_purpose=purchase_purpose, purchase_motivation=purchase_motivation,
        planned_purchase_period=planned_purchase_period,
        desired_property_type=desired_property_type,
        desired_area=desired_area, desired_area_memo=desired_area_memo,
        desired_rail_line=desired_rail_line, desired_rail_line_memo=desired_rail_line_memo,
        max_station_distance=_parse_int(max_station_distance),
        budget_max=_parse_int(budget_max),
        desired_land_area_max=_parse_int(desired_land_area_max),
        desired_floor_area_max=_parse_int(desired_floor_area_max),
        desired_floor_plan=desired_floor_plan, purchase_conditions_memo=purchase_conditions_memo,
        num_adults=_parse_int(num_adults), num_children=_parse_int(num_children),
        child_age_1=_parse_int(child_age_1), child_age_2=_parse_int(child_age_2),
        child_age_3=_parse_int(child_age_3), num_cars=_parse_int(num_cars),
        household_company=household_company, household_industry=household_industry,
        household_income=_parse_int(household_income),
        spouse_company=spouse_company, spouse_industry=spouse_industry,
        spouse_income=_parse_int(spouse_income),
        contract_amount=_parse_int(contract_amount), memo=memo,
    )


FORM_DEFAULTS = dict(
    name="", email="", phone="", birth_date="", best_contact_time="",
    postal_code="", prefecture="", city="", address="", current_residence_type="",
    first_contact_date="", first_inflow_source="", first_response_type="",
    referral_agency="", inquiry_property_name="", inquiry_property_price="",
    rank_id="", lifecycle_stage="", status="prospect", assigned_to="",
    last_email_reply_date="", rental_renewal_date="", sale_activity_status="", next_contact_date="",
    purchase_purpose="", purchase_motivation="", planned_purchase_period="",
    desired_property_type="", desired_area="", desired_area_memo="",
    desired_rail_line="", desired_rail_line_memo="", max_station_distance="",
    budget_max="", desired_land_area_max="", desired_floor_area_max="",
    desired_floor_plan="", purchase_conditions_memo="",
    num_adults="", num_children="", child_age_1="", child_age_2="", child_age_3="", num_cars="",
    household_company="", household_industry="", household_income="",
    spouse_company="", spouse_industry="", spouse_income="",
    contract_amount="", memo="",
)


def _ctx(db: Session) -> dict:
    return dict(
        ranks=db.query(Rank).order_by(Rank.priority).all(),
        lifecycle_stages=[s.name for s in db.query(LifecycleStage).order_by(LifecycleStage.priority).all()],
        status_labels=STATUS_LABELS,
        contact_type_labels=CONTACT_TYPE_LABELS,
        property_types=PROPERTY_TYPES,
        floor_plans=FLOOR_PLANS,
        residence_types=RESIDENCE_TYPES,
        purchase_purposes=PURCHASE_PURPOSES,
        planned_periods=PLANNED_PERIODS,
        inflow_sources=INFLOW_SOURCES,
        response_types=RESPONSE_TYPES,
        today=date_type.today(),
    )


@router.get("/", response_class=HTMLResponse)
def list_customers(
    request: Request,
    q: str = "",
    rank_id: Optional[int] = None,
    status: str = "",
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
                Customer.desired_area.ilike(like),
                Customer.household_company.ilike(like),
            )
        )
    if rank_id:
        query = query.filter(Customer.rank_id == rank_id)
    if status:
        query = query.filter(Customer.status == status)

    customers = query.order_by(Customer.next_contact_date.asc().nullslast(), Customer.name).all()

    return templates.TemplateResponse("customers/list.html", {
        "request": request,
        "customers": customers,
        **_ctx(db),
        "q": q,
        "selected_rank_id": rank_id,
        "selected_status": status,
    })


@router.get("/new", response_class=HTMLResponse)
def new_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("customers/form.html", {
        "request": request, "customer": None, **_ctx(db),
    })


@router.post("/new")
async def create_customer(
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()
    data = {k: form.get(k, "") for k in FORM_DEFAULTS}
    fields = _customer_from_form(**data)
    customer = Customer(**fields)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return RedirectResponse(url=f"/customers/{customer.id}", status_code=303)


@router.get("/{customer_id}", response_class=HTMLResponse)
def customer_detail(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")

    email_template = None
    if customer.rank_id:
        from models import EmailTemplate
        email_template = db.query(EmailTemplate).filter(EmailTemplate.rank_id == customer.rank_id).first()

    return templates.TemplateResponse("customers/detail.html", {
        "request": request,
        "customer": customer,
        "email_template": email_template,
        **_ctx(db),
    })


@router.get("/{customer_id}/edit", response_class=HTMLResponse)
def edit_form(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    return templates.TemplateResponse("customers/form.html", {
        "request": request, "customer": customer, **_ctx(db),
    })


@router.post("/{customer_id}/edit")
async def update_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    form = await request.form()
    data = {k: form.get(k, "") for k in FORM_DEFAULTS}
    for k, v in _customer_from_form(**data).items():
        setattr(customer, k, v)
    db.commit()
    return RedirectResponse(url=f"/customers/{customer_id}", status_code=303)


@router.post("/{customer_id}/delete")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    db.delete(customer)
    db.commit()
    return RedirectResponse(url="/customers/", status_code=303)


@router.post("/{customer_id}/next-contact")
async def update_next_contact(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    form = await request.form()
    val = form.get("next_contact_date", "")
    customer.next_contact_date = _parse_date(val)
    db.commit()
    return RedirectResponse(url=f"/customers/{customer_id}", status_code=303)


@router.get("/{customer_id}/print", response_class=HTMLResponse)
def print_customer(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")
    return templates.TemplateResponse("customers/print.html", {
        "request": request,
        "customer": customer,
        "contact_type_labels": CONTACT_TYPE_LABELS,
        "today": date_type.today(),
    })
