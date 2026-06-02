from datetime import datetime, date


def mask_id_card(id_card: str) -> str:
    """脱敏身份证号: 前3后4保留，中间替换为星号"""
    if not id_card or len(id_card) < 8:
        return id_card or ""
    return id_card[:3] + "*" * (len(id_card) - 7) + id_card[-4:]


def mask_phone(phone: str) -> str:
    """脱敏手机号: 前3后4保留"""
    if not phone or len(phone) < 7:
        return phone or ""
    return phone[:3] + "*" * (len(phone) - 7) + phone[-4:]


def date_to_str(d: date | datetime | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")
    return d.isoformat()


def datetime_to_str(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")
