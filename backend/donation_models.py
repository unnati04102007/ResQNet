from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from .db import Base

class DonationStatus:
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class Donation(Base):
    __tablename__ = "donations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    donor_name = Column(Text, nullable=True)
    donor_email = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    purpose = Column(Text, nullable=True)
    payment_provider = Column(Text, nullable=True)
    payment_method = Column(Text, nullable=True)
    payment_reference = Column(Text, nullable=True, unique=True)
    status = Column(String(16), nullable=False, default=DonationStatus.PENDING)
    extra_data = Column(JSONB, nullable=True)  # renamed from metadata ✅
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("amount > 0", name="donations_amount_positive"),
    )
