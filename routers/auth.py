import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "error": None,
    })


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
):
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        request.session["user"] = username
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "error": "IDまたはパスワードが正しくありません",
    })


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
