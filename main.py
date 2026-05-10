import os
import sys
import traceback

# 実行場所によらず crm/ を作業ディレクトリにする
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from database import engine, SessionLocal
from models import Base, Rank, EmailTemplate, LifecycleStage
from routers import dashboard, customers, history, settings
from routers import auth

app = FastAPI(title="顧客管理システム")

# グローバル例外ハンドラー（デバッグ用）
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    return JSONResponse(status_code=500, content={
        "error": str(exc),
        "type": type(exc).__name__,
        "path": str(request.url),
        "traceback": tb,
    })

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(history.router)
app.include_router(settings.router)


# 認証ミドルウェア: /login と /static と /_debug 以外は要ログイン
# ※ @app.middleware("http") は add_middleware より先に定義する必要がある
#   （Starlette は後から追加したものが外側＝先に実行されるため、
#     SessionMiddleware を最後に add_middleware することで外側に配置し
#     auth_middleware より先にセッションを初期化する）
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/login") or path.startswith("/static") or path.startswith("/_debug"):
        return await call_next(request)
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=302)
    return await call_next(request)


# セッションミドルウェア（署名付きCookie）
# ※ auth_middleware の後に add_middleware することで外側（先に実行）になり
#   session が初期化された状態で auth_middleware が動く
SECRET_KEY = os.environ.get("SESSION_SECRET", "local-dev-secret-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


# デバッグ用エンドポイント（問題解決後に削除）
@app.get("/_debug")
async def debug_info():
    import glob
    db_url = os.environ.get("DATABASE_URL", "NOT SET")
    # ファイル一覧確認
    all_files = glob.glob("**/*", recursive=True)
    template_files = [f for f in all_files if "template" in f.lower()]
    return JSONResponse({
        "db_url_set": bool(os.environ.get("DATABASE_URL")),
        "db_url_prefix": db_url[:40] + "..." if len(db_url) > 40 else db_url,
        "vercel": os.environ.get("VERCEL", "not set"),
        "cwd": os.getcwd(),
        "init_error": _init_error,
        "login_template_exists": os.path.exists("templates/auth/login.html"),
        "templates_dir_exists": os.path.exists("templates"),
        "template_files": template_files[:20],
    })


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # ランク初期データ
        if db.query(Rank).count() == 0:
            initial_ranks = [
                Rank(label="A", name="今すぐ客", description="購入意欲が非常に高い。即座のアプローチが必要。", contact_frequency="毎日〜週3回", priority=1, color="danger"),
                Rank(label="B", name="近々客", description="近い将来の購入を検討中。定期的な接触が有効。", contact_frequency="週1〜2回", priority=2, color="warning"),
                Rank(label="C", name="将来客", description="将来的な購入意欲はあるが、まだ時間がかかる見込み。", contact_frequency="月2〜4回", priority=3, color="primary"),
                Rank(label="D", name="長期・情報収集", description="購入意欲は低く、情報収集段階。無理なアプローチは逆効果。", contact_frequency="月1回程度", priority=4, color="secondary"),
            ]
            db.add_all(initial_ranks)
            db.commit()
            db.refresh(initial_ranks[0])

            initial_templates = [
                EmailTemplate(rank_id=initial_ranks[0].id, name="Aランク_初回ご提案",
                    subject="【ご案内】お客様への特別なご提案",
                    body="いつもお世話になっております。\n\nこの度、お客様に特別なご提案がございます。\nぜひお電話またはご来店いただき、詳細をご確認ください。\n\nご不明な点がございましたら、お気軽にご連絡ください。\n\nどうぞよろしくお願いいたします。"),
                EmailTemplate(rank_id=initial_ranks[1].id, name="Bランク_最新情報",
                    subject="【ご案内】最新情報のお知らせ",
                    body="いつもお世話になっております。\n\n最新の情報をお届けいたします。\nご興味があればぜひご連絡ください。\n\nどうぞよろしくお願いいたします。"),
                EmailTemplate(rank_id=initial_ranks[2].id, name="Cランク_定期連絡",
                    subject="【定期ご連絡】近況のご報告",
                    body="いつもお世話になっております。\n\n定期的にご連絡させていただいております。\n何かお役に立てることがあれば、お気軽にご相談ください。\n\nどうぞよろしくお願いいたします。"),
                EmailTemplate(rank_id=initial_ranks[3].id, name="Dランク_月次ニュース",
                    subject="【月次ニュースレター】今月の情報まとめ",
                    body="いつもお世話になっております。\n\n今月の情報をまとめてお届けいたします。\nご参考になれば幸いです。\n\nどうぞよろしくお願いいたします。"),
            ]
            db.add_all(initial_templates)
            db.commit()

        # ライフサイクルステージ初期データ
        if db.query(LifecycleStage).count() == 0:
            stages = [
                LifecycleStage(name="追客中", priority=1),
                LifecycleStage(name="未対応", priority=2),
                LifecycleStage(name="他決",   priority=3),
                LifecycleStage(name="中止",   priority=4),
            ]
            db.add_all(stages)
            db.commit()

    finally:
        db.close()


# DB 初期化（失敗してもアプリは起動させる）
_init_error = None
try:
    init_db()
except Exception as e:
    _init_error = traceback.format_exc()
    print(f"[CRM] DB init error: {_init_error}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
