# File: backend/app/main.py
import os
import logging
from datetime import datetime
import pytz

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from sqlalchemy import select
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .routers.admin_telegram import router as admin_telegram_router

# Nạp .env SỚM
try:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=(Path(__file__).resolve().parent.parent / ".env"))
except Exception:
    pass

from .core.config import settings
from .core.database import engine, Base, get_db, SessionLocal
from .utils.logging_config import setup_logging
from . import models
from .services.form_sync_service import sync_google_form_registrations # Import Form Sync Service
from .modules.guest.service import long_term_guest_service

# Routers
from .core.auth import router as auth_router, get_password_hash
from .routers.users import router as users_router
from .routers.guests import router as guests_router
from .routers.suppliers import router as suppliers_router
from .routers.reports import router as reports_router
from .routers.gemini import router as gemini_router
from .routers.long_term_guests import router as long_term_guests_router
from .routers.vehicle_log import router as vehicle_log_router
from .routers.guests_confirm import router as guests_confirm_router
from .routers.assets import router as assets_router
from .routers.admin import router as admin_router
from .routers.print_tracking import router as print_tracking_router
from .routers.security_events import router as security_events_router
from .routers.security_events import router as security_events_router
from .routers.purchasing import router as purchasing_router
from .routers.notifications import router as notifications_router

app = FastAPI(
    title="Ứng dụng an ninh nội bộ - Local Security App",
    version="2.7.0"
)

# Cài đặt logging
setup_logging()
logging.info("Application startup...")

# CORS Middleware
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.223.176:5173",
    "http://192.168.223.176:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Tạo CSDL (nếu chưa có) và thư mục
try:
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception as e:
    logging.error(f"Error initializing database or directories: {e}")

# Include Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(guests_router)
app.include_router(suppliers_router)
app.include_router(reports_router)
app.include_router(gemini_router)
app.include_router(long_term_guests_router)
app.include_router(vehicle_log_router)
app.include_router(guests_confirm_router)
app.include_router(admin_telegram_router)
app.include_router(assets_router)
app.include_router(admin_router)
app.include_router(print_tracking_router)
app.include_router(security_events_router)
app.include_router(purchasing_router)
app.include_router(notifications_router)

# Mount static files
app.mount(f"/{os.path.basename(settings.UPLOAD_DIR)}", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

# Khởi tạo admin user và Job background
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == settings.ADMIN_USERNAME).first()
        if not admin_user:
            admin_password_hash = get_password_hash(settings.ADMIN_PASSWORD)
            db_admin = models.User(
                username=settings.ADMIN_USERNAME,
                password_hash=admin_password_hash,
                full_name="Administrator", 
                role="admin"
            )
            db.add(db_admin)
            db.commit()
            logging.info(f"Admin user '{settings.ADMIN_USERNAME}' created.")
    except Exception as e:
        logging.error(f"Error creating admin user: {e}")
    finally:
        db.close()

    # Job cho Khách dài hạn: sử dụng Service
    def create_daily_guest_entries():
        logging.info("[long_term] Job started: Creating daily guest entries...")
        db = SessionLocal()
        try:
            count = long_term_guest_service.process_daily_entries(db, settings.TZ)
            if count > 0:
                logging.info(f"[long_term] Job finished: Created {count} new daily guest(s).")
            else:
                logging.info("[long_term] Job finished: No new guests needed.")
        except Exception as e:
             logging.error(f"[long_term] Job failed: {e}", exc_info=True)
        finally:
             db.close()

    # Job cho No-Show Guest (23:55 daily)
    def process_no_show_guests_job():
        logging.info("[no_show] Job started: Processing no-show guests...")
        db = SessionLocal()
        try:
            from app.modules.guest.service import guest_service
            count = guest_service.process_no_show_guests(db)
            if count > 0:
                logging.info(f"[no_show] Job finished: Marked {count} guest(s) as no-show.")
            else:
                logging.info("[no_show] Job finished: No no-show guests found.")
        except Exception as e:
             logging.error(f"[no_show] Job failed: {e}", exc_info=True)
        finally:
             db.close()

    # Chạy ngay khi startup
    try:
        create_daily_guest_entries()
        logging.info("[long_term] Startup run completed.")
        
        # Chạy check no-show ngay khi start phòng trường hợp đêm qua server tắt
        process_no_show_guests_job()
        logging.info("[no_show] Startup run completed.")
    except Exception as e:
        logging.error(f"[startup] Startup run failed: {e}", exc_info=True)

    # Bắt đầu scheduler
    try:
        sched = BackgroundScheduler(timezone=settings.TZ)
        sched.add_job(
            create_daily_guest_entries,
            trigger=IntervalTrigger(minutes=30),
            id="create_daily_guests_job",
            name="Create daily guest entries from long-term registrations",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=30,
        )
        # Job đồng bộ Google Form (30 giây/lần)
        sched.add_job(
            sync_google_form_registrations,
            trigger=IntervalTrigger(seconds=30),
            id="sync_google_form_job",
            name="Sync guest registrations from Google Form",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=10,
        )
        # Job No-Show Guests (23:55)
        sched.add_job(
            process_no_show_guests_job,
            trigger='cron',
            hour=0,
            minute=0,
            id="process_no_show_guests_job",
            name="Process no-show guests daily",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=60,
        )
        sched.start()
        app.state.scheduler = sched
        logging.info(f"[scheduler] Scheduler started (TZ={settings.TZ}).")
    except Exception as e:
        logging.error(f"[scheduler] Could not start the scheduler: {e}", exc_info=True)


@app.on_event("shutdown")
def on_shutdown():
    try:
        sched = getattr(app.state, "scheduler", None)
        if sched:
            sched.shutdown()
            logging.info("[long_term] Scheduler shut down.")
    except Exception as e:
        logging.error(f"Error shutting down scheduler: {e}", exc_info=True)


@app.get("/")
def read_root():
    return {"message": "Welcome to Local Security API", "version": app.version}