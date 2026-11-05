from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from . import database
from .auth import require_admin
from .database import get_db
from .models import AuditEvent, Experience, Qualification, Resident, Skill
from .qualifications import get_all_qualifications
from .schemas import (
    AuditEventOut,
    ErrorOut,
    ResidentIn,
    ResidentOut,
)
from .villages import get_all_villages

router = APIRouter(dependencies=[Depends(require_admin)])

MAX_QUERY_LENGTH = 200


def _like_pattern(value: str) -> str:
    """Build a literal contains-pattern for SQL LIKE/ILIKE."""
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _qualification_terms(query: str) -> list[str]:
    """Match a qualification field to its known names, or fall back to a name."""
    names_by_field = get_all_qualifications().get("names", {})
    for field, names in names_by_field.items():
        if field.casefold() == query.casefold():
            return list(names) or [query]
    return [query]


def _resident_options():
    """Eager-load child rows to avoid N+1 queries on list and search."""
    return (
        selectinload(Resident.qualifications),
        selectinload(Resident.experiences),
        selectinload(Resident.skills),
    )


def _ensure_backup() -> None:
    """Take a pre-write backup, honouring the fail-closed configuration.

    Backups are best-effort by default for availability. Operators can set
    ``RESIDENTS_BACKUP_REQUIRED=true`` to abort a write when an enabled backup
    fails, rather than accepting an unprotected write.
    """
    if database.backup_database():
        return
    if database.BACKUP_ENABLED and database.BACKUP_REQUIRED:
        raise HTTPException(
            status_code=503,
            detail="Database backup failed; the write was aborted",
        )


def _audit_actor(request: Request) -> str:
    """Return the authenticated account name without storing credentials or PII."""
    return getattr(request.state, "admin_username", "unknown")


def _record_audit(
    db: Session,
    request: Request,
    action: str,
    resident_id: int,
    detail: Optional[str] = None,
) -> None:
    """Append a non-PII audit event in the same transaction as the write."""
    db.add(
        AuditEvent(
            action=action,
            resident_id=resident_id,
            actor=_audit_actor(request),
            request_id=getattr(request.state, "request_id", None),
            detail=detail,
        )
    )


def _resident_to_dict(r: Resident) -> dict:
    return {
        "id": r.id,
        "first_name": r.first_name,
        "last_name": r.last_name,
        "dob": str(r.dob),
        "gender": r.gender,
        "village": r.village,
        "cellphone_no": r.cellphone_no,
        "cellphone_no2": r.cellphone_no2,
        "email": r.email,
        "qualifications": [
            {"id": q.id, "institution": q.institution, "name": q.name,
             "type": q.type, "level": q.level, "year": q.year}
            for q in r.qualifications
        ],
        "experiences": [
            {"id": e.id, "company": e.company, "position": e.position, "years": e.years}
            for e in r.experiences
        ],
        "skills": [{"id": s.id, "name": s.name} for s in r.skills],
    }


# ── Authentication ────────────────────────────────────────────────────────────

@router.get("/auth/verify", tags=["auth"])
def verify_auth():
    """Confirm that the current administrator session is valid."""
    return {"authenticated": True}


# ── Reference data ─────────────────────────────────────────────────────────────

@router.get("/villages", response_model=list[str], tags=["reference"])
def list_villages():
    return get_all_villages()


@router.get("/qualifications", response_model=dict, tags=["reference"])
def list_qualifications():
    return get_all_qualifications()


# ── Residents CRUD ─────────────────────────────────────────────────────────────

@router.get("/residents", response_model=list[ResidentOut], tags=["residents"])
def list_residents(
    response: Response,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    name: Optional[str] = Query(None, max_length=MAX_QUERY_LENGTH),
    village: Optional[str] = Query(None, max_length=MAX_QUERY_LENGTH),
    qualification: Optional[str] = Query(None, max_length=MAX_QUERY_LENGTH),
    skill: Optional[str] = Query(None, max_length=MAX_QUERY_LENGTH),
    sort_by: Literal["id", "first_name", "last_name", "village", "dob"] = "id",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Session = Depends(get_db),
):
    query = db.query(Resident)
    if name and name.strip():
        pattern = _like_pattern(name.strip())
        query = query.filter(
            or_(
                Resident.first_name.ilike(pattern, escape="\\"),
                Resident.last_name.ilike(pattern, escape="\\"),
            )
        )
    if village and village.strip():
        query = query.filter(
            Resident.village.ilike(_like_pattern(village.strip()), escape="\\")
        )
    if qualification and qualification.strip():
        terms = _qualification_terms(qualification.strip())
        query = query.filter(
            Resident.qualifications.any(
                or_(
                    *[
                        Qualification.name.ilike(_like_pattern(term), escape="\\")
                        for term in terms
                    ]
                )
            )
        )
    if skill and skill.strip():
        query = query.filter(
            Resident.skills.any(
                Skill.name.ilike(_like_pattern(skill.strip()), escape="\\")
            )
        )

    total = query.count()
    sort_column = getattr(Resident, sort_by)
    ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    order_by = [ordering]
    if sort_by != "id":
        order_by.append(Resident.id.asc())
    residents = (
        query
        .options(*_resident_options())
        .order_by(*order_by)
        .offset(offset)
        .limit(limit)
        .all()
    )
    response.headers["X-Total-Count"] = str(total)
    return [_resident_to_dict(r) for r in residents]


@router.get(
    "/residents/{resident_id}",
    response_model=ResidentOut,
    responses={404: {"model": ErrorOut}},
    tags=["residents"],
)
def get_resident(resident_id: int, db: Session = Depends(get_db)):
    r = (
        db.query(Resident)
        .options(*_resident_options())
        .filter(Resident.id == resident_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Resident not found")
    return _resident_to_dict(r)


@router.post(
    "/residents",
    status_code=201,
    response_model=ResidentOut,
    responses={
        413: {"model": ErrorOut},
        422: {"model": ErrorOut},
        503: {"model": ErrorOut},
    },
    tags=["residents"],
)
def create_resident(
    payload: ResidentIn,
    request: Request,
    db: Session = Depends(get_db),
):
    _ensure_backup()
    try:
        resident = Resident(
            first_name=payload.first_name,
            last_name=payload.last_name,
            dob=payload.dob,
            gender=payload.gender,
            village=payload.village,
            cellphone_no=payload.cellphone_no,
            cellphone_no2=payload.cellphone_no2,
            email=payload.email,
            qualifications=[Qualification(**q.model_dump()) for q in payload.qualifications],
            experiences=[Experience(**e.model_dump()) for e in payload.experiences],
            skills=[Skill(**s.model_dump()) for s in payload.skills],
        )
        db.add(resident)
        db.flush()
        _record_audit(db, request, "create", resident.id)
        db.commit()
        db.refresh(resident)
        return _resident_to_dict(resident)
    except Exception:
        db.rollback()
        raise


@router.put(
    "/residents/{resident_id}",
    response_model=ResidentOut,
    responses={
        404: {"model": ErrorOut},
        409: {"model": ErrorOut},
        413: {"model": ErrorOut},
        422: {"model": ErrorOut},
        503: {"model": ErrorOut},
    },
    tags=["residents"],
)
def update_resident(
    resident_id: int,
    payload: ResidentIn,
    request: Request,
    db: Session = Depends(get_db),
):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    identity_fields = ("first_name", "last_name", "dob", "gender", "village")
    changed = [
        field for field in identity_fields
        if getattr(resident, field) != getattr(payload, field)
    ]
    if changed:
        raise HTTPException(
            status_code=409,
            detail=(
                "Identity fields cannot be changed through this endpoint: "
                + ", ".join(changed)
            ),
        )

    contact_fields = ("cellphone_no", "cellphone_no2", "email")
    changed_contact = [
        field for field in contact_fields
        if getattr(resident, field) != getattr(payload, field)
    ]

    _ensure_backup()
    try:
        db.query(Qualification).filter(Qualification.resident_id == resident_id).delete()
        db.query(Experience).filter(Experience.resident_id == resident_id).delete()
        db.query(Skill).filter(Skill.resident_id == resident_id).delete()

        for key, value in payload.model_dump(exclude={"qualifications", "experiences", "skills"}).items():
            setattr(resident, key, value)

        for q in payload.qualifications:
            db.add(Qualification(**q.model_dump(), resident_id=resident_id))
        for e in payload.experiences:
            db.add(Experience(**e.model_dump(), resident_id=resident_id))
        for s in payload.skills:
            db.add(Skill(**s.model_dump(), resident_id=resident_id))

        _record_audit(
            db,
            request,
            "update",
            resident_id,
            detail="contact_fields=" + (",".join(changed_contact) or "none"),
        )
        db.commit()
        db.refresh(resident)
        return _resident_to_dict(resident)
    except Exception:
        db.rollback()
        raise


@router.delete(
    "/residents/{resident_id}",
    status_code=204,
    responses={404: {"model": ErrorOut}, 503: {"model": ErrorOut}},
    tags=["residents"],
)
def delete_resident(
    resident_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    _ensure_backup()
    try:
        _record_audit(db, request, "delete", resident_id)
        db.delete(resident)
        db.commit()
    except Exception:
        db.rollback()
        raise


# ── Search ─────────────────────────────────────────────────────────────────────

@router.get("/search", response_model=list[ResidentOut], tags=["search"])
def search_residents(
    response: Response,
    query: str = Query("", max_length=MAX_QUERY_LENGTH),
    search_type: Literal["name", "village", "qualification", "skill"] = "name",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    term = query.strip()
    if not term:
        response.headers["X-Total-Count"] = "0"
        return []

    if search_type == "name":
        pattern = _like_pattern(term)
        base_query = db.query(Resident).filter(
            or_(
                Resident.first_name.ilike(pattern, escape="\\"),
                Resident.last_name.ilike(pattern, escape="\\"),
            )
        )
    elif search_type == "village":
        base_query = db.query(Resident).filter(
            Resident.village.ilike(_like_pattern(term), escape="\\")
        )
    elif search_type == "qualification":
        terms = _qualification_terms(term)
        base_query = (
            db.query(Resident)
            .join(Resident.qualifications)
            .filter(
                or_(
                    *[
                        Qualification.name.ilike(_like_pattern(name), escape="\\")
                        for name in terms
                    ]
                )
            )
        )
    else:  # skill
        base_query = (
            db.query(Resident)
            .join(Resident.skills)
            .filter(Skill.name.ilike(_like_pattern(term), escape="\\"))
        )

    total = base_query.distinct().count()
    results = (
        base_query.distinct()
        .options(*_resident_options())
        .order_by(Resident.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    response.headers["X-Total-Count"] = str(total)
    return [_resident_to_dict(r) for r in results]


# ── Audit trail ────────────────────────────────────────────────────────────────

@router.get("/audit", response_model=list[AuditEventOut], tags=["audit"])
def list_audit_events(
    response: Response,
    action: Optional[Literal["create", "update", "delete"]] = None,
    resident_id: Optional[int] = Query(None, ge=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return non-PII write events, newest first.

    The audit trail records the action, resident ID, actor class, request ID,
    and changed contact-field names. It never records field values, names,
    tokens, or client IP addresses.
    """
    query = db.query(AuditEvent)
    if action is not None:
        query = query.filter(AuditEvent.action == action)
    if resident_id is not None:
        query = query.filter(AuditEvent.resident_id == resident_id)

    total = query.count()
    events = (
        query.order_by(AuditEvent.id.desc()).offset(offset).limit(limit).all()
    )
    response.headers["X-Total-Count"] = str(total)
    return events
