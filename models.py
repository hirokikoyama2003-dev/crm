from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Rank(Base):
    __tablename__ = "ranks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    contact_frequency: Mapped[str] = mapped_column(String(100), default="")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str] = mapped_column(String(20), default="secondary")

    customers: Mapped[List["Customer"]] = relationship("Customer", back_populates="rank")
    email_templates: Mapped[List["EmailTemplate"]] = relationship("EmailTemplate", back_populates="rank")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # ── 基本情報 ──────────────────────────────
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    best_contact_time: Mapped[str] = mapped_column(String(100), default="")  # 連絡の繋がりやすい時間帯

    # ── 住所 ──────────────────────────────────
    postal_code: Mapped[str] = mapped_column(String(10), default="")
    prefecture: Mapped[str] = mapped_column(String(20), default="")
    city: Mapped[str] = mapped_column(String(50), default="")
    address: Mapped[str] = mapped_column(String(200), default="")
    current_residence_type: Mapped[str] = mapped_column(String(50), default="")  # 居住物件種別

    # ── 流入・反響情報 ────────────────────────
    first_contact_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # 初回コンタクト日
    first_inflow_source: Mapped[str] = mapped_column(String(100), default="")        # 初回流入元
    first_response_type: Mapped[str] = mapped_column(String(100), default="")        # 初回反響種別
    referral_agency: Mapped[str] = mapped_column(String(100), default="")            # 紹介業者名
    inquiry_property_name: Mapped[str] = mapped_column(String(200), default="")      # お問い合わせ物件名
    inquiry_property_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # お問い合わせ物件価格（万円）

    # ── ライフサイクル・営業状況 ───────────────
    rank_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ranks.id"), nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(String(50), default="")             # ライフサイクルステージ
    status: Mapped[str] = mapped_column(String(20), default="prospect")              # prospect/existing/lost
    assigned_to: Mapped[str] = mapped_column(String(100), default="")
    last_email_reply_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # 最近メール返信日
    rental_renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)    # 賃貸契約更新時期
    sale_activity_status: Mapped[str] = mapped_column(String(100), default="")          # 売却活動状況
    next_contact_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ── 購入希望条件 ──────────────────────────
    purchase_purpose: Mapped[str] = mapped_column(String(100), default="")           # 購入目的
    purchase_motivation: Mapped[str] = mapped_column(String(200), default="")        # 購入動機
    planned_purchase_period: Mapped[str] = mapped_column(String(50), default="")     # 購入予定時期
    desired_property_type: Mapped[str] = mapped_column(String(100), default="")      # 購入希望物件種別
    desired_area: Mapped[str] = mapped_column(String(200), default="")               # 購入希望エリア
    desired_area_memo: Mapped[str] = mapped_column(Text, default="")                 # メモ（エリア）
    desired_rail_line: Mapped[str] = mapped_column(String(200), default="")          # 希望路線
    desired_rail_line_memo: Mapped[str] = mapped_column(Text, default="")            # メモ（希望路線）
    max_station_distance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 最寄り駅距離（分）
    budget_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)             # 予算最大（万円）
    desired_land_area_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 希望土地面積最大（㎡）
    desired_floor_area_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 希望延床面積最大（㎡）
    desired_floor_plan: Mapped[str] = mapped_column(String(50), default="")          # 購入希望間取り
    purchase_conditions_memo: Mapped[str] = mapped_column(Text, default="")          # 購入条件メモ

    # ── 家族・世帯情報 ────────────────────────
    num_adults: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)        # 大人の人数
    num_children: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)      # 子供の人数
    child_age_1: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    child_age_2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    child_age_3: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_cars: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)          # 車所有台数

    # ── 世帯主情報 ────────────────────────────
    household_company: Mapped[str] = mapped_column(String(100), default="")          # 会社名（世帯主）
    household_industry: Mapped[str] = mapped_column(String(100), default="")         # 業種（世帯主）
    household_income: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 年収（世帯主・万円）

    # ── 配偶者情報 ────────────────────────────
    spouse_company: Mapped[str] = mapped_column(String(100), default="")
    spouse_industry: Mapped[str] = mapped_column(String(100), default="")
    spouse_income: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)     # 年収（配偶者・万円）

    # ── その他メモ ────────────────────────────
    contract_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 成約金額（万円）
    memo: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    rank: Mapped[Optional["Rank"]] = relationship("Rank", back_populates="customers")
    contact_history: Mapped[List["ContactHistory"]] = relationship(
        "ContactHistory", back_populates="customer", cascade="all, delete-orphan",
        order_by="ContactHistory.contacted_at.desc()"
    )


class ContactHistory(Base):
    __tablename__ = "contact_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    contact_type: Mapped[str] = mapped_column(String(20), default="other")  # phone/email/meeting/visit/other
    content: Mapped[str] = mapped_column(Text, default="")
    contacted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), default="")

    customer: Mapped["Customer"] = relationship("Customer", back_populates="contact_history")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rank_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ranks.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), default="")   # テンプレート名
    subject: Mapped[str] = mapped_column(String(200), default="")
    body: Mapped[str] = mapped_column(Text, default="")

    rank: Mapped[Optional["Rank"]] = relationship("Rank", back_populates="email_templates")


class LifecycleStage(Base):
    __tablename__ = "lifecycle_stages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # 表示順
