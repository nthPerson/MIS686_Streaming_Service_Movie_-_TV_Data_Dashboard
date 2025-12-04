"""SQLAlchemy declarative models for the dashboard."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class StreamingService(Base):
    __tablename__ = "streaming_service"

    streaming_service_id = Column(Integer, primary_key=True)
    service_name = Column(String(100), nullable=False, unique=True)

    availabilities = relationship("StreamingAvailability", back_populates="service")


class Title(Base):
    __tablename__ = "title"

    title_id = Column(BigInteger, primary_key=True)
    global_title_name = Column(String(255), nullable=False)
    original_title = Column(String(255))
    description = Column(Text)
    release_year = Column(Integer, nullable=False)
    content_type = Column(String(10), nullable=False)
    age_rating_code = Column(String(20))
    runtime_minutes = Column(SmallInteger)
    num_seasons = Column(SmallInteger)

    availabilities = relationship("StreamingAvailability", back_populates="title")


class StreamingAvailability(Base):
    __tablename__ = "streaming_availability"

    availability_id = Column(BigInteger, primary_key=True)
    streaming_service_id = Column(Integer, ForeignKey("streaming_service.streaming_service_id"), nullable=False)
    title_id = Column(BigInteger, ForeignKey("title.title_id"), nullable=False)
    platform_show_id = Column(String(50), nullable=False)
    date_added = Column(Date)
    duration_raw = Column(String(50))
    is_exclusive = Column(Boolean, default=False)
    availability_status = Column(String(10), nullable=False, default="ACTIVE")

    service = relationship("StreamingService", back_populates="availabilities")
    title = relationship("Title", back_populates="availabilities")


class Genre(Base):
    __tablename__ = "genre"

    genre_id = Column(Integer, primary_key=True)
    genre_name = Column(String(100), nullable=False, unique=True)


class TitleGenre(Base):
    __tablename__ = "title_genre"

    title_id = Column(BigInteger, ForeignKey("title.title_id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genre.genre_id"), primary_key=True)


class Country(Base):
    __tablename__ = "country"

    country_id = Column(Integer, primary_key=True)
    country_name = Column(String(100), nullable=False, unique=True)


class TitleCountry(Base):
    __tablename__ = "title_country"

    title_id = Column(BigInteger, ForeignKey("title.title_id"), primary_key=True)
    country_id = Column(Integer, ForeignKey("country.country_id"), primary_key=True)


class AppRole(Base):
    __tablename__ = "app_role"

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(50), nullable=False, unique=True)

    users = relationship("AppUser", back_populates="role")


class AppUser(Base):
    __tablename__ = "app_user"

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("app_role.role_id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = Column(DateTime)

    role = relationship("AppRole", back_populates="users")


class AppUserAudit(Base):
    __tablename__ = "app_user_audit"

    audit_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    action = Column(String(10), nullable=False)
    old_role_id = Column(Integer)
    new_role_id = Column(Integer)
    changed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    changed_by = Column(String(100), nullable=False)
