from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Rank, EmailTemplate, LifecycleStage

router = APIRouter(prefix="/settings")
templates = Jinja2Templates(directory="templates")

COLOR_OPTIONS = [
    ("danger",    "赤（緊急）"),
    ("warning",   "黄（注意）"),
    ("primary",   "青（通常）"),
    ("success",   "緑（良好）"),
    ("secondary", "グレー"),
    ("info",      "水色"),
]


# ── ランク設定 ────────────────────────────────────────
@router.get("/ranks", response_class=HTMLResponse)
def ranks_page(request: Request, db: Session = Depends(get_db)):
    ranks = db.query(Rank).order_by(Rank.priority).all()
    return templates.TemplateResponse("settings/ranks.html", {
        "request": request, "ranks": ranks, "color_options": COLOR_OPTIONS,
    })


@router.post("/ranks/{rank_id}/update")
def update_rank(
    rank_id: int,
    name: str = Form(...),
    description: str = Form(""),
    contact_frequency: str = Form(""),
    color: str = Form("secondary"),
    db: Session = Depends(get_db),
):
    rank = db.get(Rank, rank_id)
    if not rank:
        raise HTTPException(status_code=404)
    rank.name = name
    rank.description = description
    rank.contact_frequency = contact_frequency
    rank.color = color
    db.commit()
    return RedirectResponse(url="/settings/ranks", status_code=303)


# ── メールテンプレート ────────────────────────────────
@router.get("/templates", response_class=HTMLResponse)
def templates_page(request: Request, db: Session = Depends(get_db)):
    ranks = db.query(Rank).order_by(Rank.priority).all()
    email_templates = db.query(EmailTemplate).order_by(EmailTemplate.id).all()
    return templates.TemplateResponse("settings/templates.html", {
        "request": request,
        "ranks": ranks,
        "email_templates": email_templates,
    })


@router.post("/templates/new")
def create_template(
    name: str = Form(""),
    rank_id: str = Form(""),
    subject: str = Form(""),
    body: str = Form(""),
    db: Session = Depends(get_db),
):
    tmpl = EmailTemplate(
        name=name,
        rank_id=int(rank_id) if rank_id else None,
        subject=subject,
        body=body,
    )
    db.add(tmpl)
    db.commit()
    return RedirectResponse(url="/settings/templates", status_code=303)


@router.post("/templates/{tmpl_id}/update")
def update_template(
    tmpl_id: int,
    name: str = Form(""),
    rank_id: str = Form(""),
    subject: str = Form(""),
    body: str = Form(""),
    db: Session = Depends(get_db),
):
    tmpl = db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404)
    tmpl.name = name
    tmpl.rank_id = int(rank_id) if rank_id else None
    tmpl.subject = subject
    tmpl.body = body
    db.commit()
    return RedirectResponse(url="/settings/templates", status_code=303)


@router.post("/templates/{tmpl_id}/delete")
def delete_template(tmpl_id: int, db: Session = Depends(get_db)):
    tmpl = db.get(EmailTemplate, tmpl_id)
    if not tmpl:
        raise HTTPException(status_code=404)
    db.delete(tmpl)
    db.commit()
    return RedirectResponse(url="/settings/templates", status_code=303)


# ── ライフサイクルステージ ────────────────────────────
@router.get("/lifecycle", response_class=HTMLResponse)
def lifecycle_page(request: Request, db: Session = Depends(get_db)):
    stages = db.query(LifecycleStage).order_by(LifecycleStage.priority).all()
    return templates.TemplateResponse("settings/lifecycle.html", {
        "request": request, "stages": stages,
    })


@router.post("/lifecycle/new")
def create_stage(name: str = Form(...), db: Session = Depends(get_db)):
    max_priority = db.query(LifecycleStage).count()
    db.add(LifecycleStage(name=name, priority=max_priority + 1))
    db.commit()
    return RedirectResponse(url="/settings/lifecycle", status_code=303)


@router.post("/lifecycle/{stage_id}/update")
def update_stage(stage_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    stage = db.get(LifecycleStage, stage_id)
    if not stage:
        raise HTTPException(status_code=404)
    stage.name = name
    db.commit()
    return RedirectResponse(url="/settings/lifecycle", status_code=303)


@router.post("/lifecycle/{stage_id}/delete")
def delete_stage(stage_id: int, db: Session = Depends(get_db)):
    stage = db.get(LifecycleStage, stage_id)
    if not stage:
        raise HTTPException(status_code=404)
    db.delete(stage)
    db.commit()
    return RedirectResponse(url="/settings/lifecycle", status_code=303)
