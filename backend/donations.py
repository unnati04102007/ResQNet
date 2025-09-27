from datetime import datetime
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

try:
    from .db import get_db_session
    from .donation_models import Donation, DonationStatus
except ImportError:
    from db import get_db_session
    from donation_models import Donation, DonationStatus


donations_bp = Blueprint("donations", __name__)


def _parse_amount(value: Any) -> float:
    try:
        return round(float(value), 2)
    except Exception:
        raise ValueError("amount must be a number")


@donations_bp.route("/donate", methods=["POST"])
def donate():
    payload = request.get_json(silent=True) or {}

    amount = _parse_amount(payload.get("amount"))
    currency = (payload.get("currency") or "USD").upper()
    donor_name = (payload.get("donor_name") or None)
    donor_email = (payload.get("donor_email") or None)
    purpose = (payload.get("purpose") or None)
    provider = (payload.get("provider") or None)
    payment_method = (payload.get("payment_method") or None)
    payment_reference = (payload.get("payment_reference") or None)
    extra = payload.get("extra_data") or {}

    if not amount or amount <= 0:
        return jsonify({"error": "amount must be > 0"}), 400

    # TODO: Integrate with Stripe/Razorpay/PayPal to create/confirm payments
    # For now, we accept an already created payment_reference and mark succeeded; otherwise pending
    status = DonationStatus.SUCCEEDED if payment_reference else DonationStatus.PENDING

    # Persist donation
    for session in get_db_session():
        donation = Donation(
            donor_name=donor_name,
            donor_email=donor_email,
            amount=amount,
            currency=currency,
            purpose=purpose,
            payment_provider=provider,
            payment_method=payment_method,
            payment_reference=payment_reference,
            status=status,
            extra_data=extra,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(donation)
        session.flush()
        donation_id = int(donation.id)

    return jsonify({
        "id": donation_id,
        "status": status,
        "payment_reference": payment_reference,
    }), 201


@donations_bp.route("/get-donations", methods=["GET"])
def get_donations():
    limit = request.args.get("limit", default=50, type=int)
    status_filter = request.args.get("status")
    provider_filter = request.args.get("provider")

    limit = max(1, min(200, limit))

    for session in get_db_session():
        query = session.query(Donation)
        if status_filter:
            query = query.filter(Donation.status == status_filter)
        if provider_filter:
            query = query.filter(Donation.payment_provider == provider_filter)

        items = (
            query.order_by(Donation.created_at.desc())
            .limit(limit)
            .all()
        )

        data: List[Dict[str, Any]] = []
        for d in items:
            data.append({
                "id": int(d.id),
                "donor_name": d.donor_name,
                "donor_email": d.donor_email,
                "amount": float(d.amount),
                "currency": d.currency,
                "purpose": d.purpose,
                "payment_provider": d.payment_provider,
                "payment_method": d.payment_method,
                "payment_reference": d.payment_reference,
                "status": d.status,
                "extra_data": d.extra_data or {},
                "created_at": d.created_at.isoformat() + "Z",
            })

    return jsonify({"donations": data, "count": len(data)}), 200
