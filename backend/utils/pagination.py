"""
NyumbaLink — Pagination & Sorting Utilities
────────────────────────────────────────────
Provides a consistent paginate() helper that:
  • Parses page / per_page / sort_by / sort_dir from request args
  • Applies column whitelisting to prevent SQL injection via sort
  • Returns a uniform PaginatedResult envelope
  • Serialises to a JSON-safe dict for API responses
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

from flask import request, url_for
from sqlalchemy.orm import Query


# ── Constants ─────────────────────────────────────────────────────────

DEFAULT_PAGE     = 1
DEFAULT_PER_PAGE = 12
MAX_PER_PAGE     = 50

SORT_ASC  = 'asc'
SORT_DESC = 'desc'


# ── Data class ────────────────────────────────────────────────────────

@dataclass
class PaginatedResult:
    items:       List[Any]
    total:       int
    page:        int
    per_page:    int
    sort_by:     Optional[str]
    sort_dir:    str

    @property
    def pages(self) -> int:
        return math.ceil(self.total / self.per_page) if self.per_page else 1

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    def to_dict(
        self,
        serializer: Callable[[Any], Dict] = None,
        endpoint:   str = None,
        **url_kwargs,
    ) -> Dict:
        """
        Return a JSON-serialisable dict.

        Args:
            serializer: callable applied to each item (e.g. lambda p: p.to_dict())
            endpoint:   Flask endpoint name used to build prev/next URLs
        """
        items = [serializer(i) for i in self.items] if serializer else self.items

        meta: Dict = {
            'total':    self.total,
            'page':     self.page,
            'per_page': self.per_page,
            'pages':    self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'sort_by':  self.sort_by,
            'sort_dir': self.sort_dir,
        }

        if endpoint:
            def _url(p: int) -> str:
                return url_for(endpoint, page=p, per_page=self.per_page, **url_kwargs)

            meta['prev_url'] = _url(self.page - 1) if self.has_prev else None
            meta['next_url'] = _url(self.page + 1) if self.has_next else None

        return {'data': items, 'pagination': meta}


# ── Core helper ───────────────────────────────────────────────────────

def paginate(
    query:           Query,
    model:           Type,
    allowed_sort:    Optional[List[str]] = None,
    default_sort:    str = 'created_at',
    default_dir:     str = SORT_DESC,
    serializer:      Callable[[Any], Dict] = None,
    endpoint:        str = None,
    **url_kwargs,
) -> PaginatedResult:
    """
    Parse request args, apply sorting + pagination to a SQLAlchemy Query,
    and return a PaginatedResult.

    Usage in a route:
        result = paginate(
            Property.query.filter_by(status='active'),
            model=Property,
            allowed_sort=['price', 'created_at', 'views_count'],
            serializer=lambda p: p.to_dict(),
        )
        return jsonify(result.to_dict()), 200

    Accepted query params:
        page        int >= 1            (default 1)
        per_page    int 1–50            (default 12)
        sort_by     column name         (validated against allowed_sort)
        sort_dir    asc | desc          (default desc)
    """

    # ── Parse ─────────────────────────────────
    try:
        page = max(1, int(request.args.get('page', DEFAULT_PAGE)))
    except (TypeError, ValueError):
        page = DEFAULT_PAGE

    try:
        per_page = min(MAX_PER_PAGE, max(1, int(request.args.get('per_page', DEFAULT_PER_PAGE))))
    except (TypeError, ValueError):
        per_page = DEFAULT_PER_PAGE

    sort_by  = request.args.get('sort_by', default_sort)
    sort_dir = request.args.get('sort_dir', default_dir).lower()

    if sort_dir not in (SORT_ASC, SORT_DESC):
        sort_dir = default_dir

    # ── Whitelist sort column ─────────────────
    safe_sort = allowed_sort or [default_sort]
    if sort_by not in safe_sort:
        sort_by = default_sort

    column = getattr(model, sort_by, None)
    if column is not None:
        query = query.order_by(column.desc() if sort_dir == SORT_DESC else column.asc())

    # ── Execute ───────────────────────────────
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return PaginatedResult(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


# ── Convenience wrapper ───────────────────────────────────────────────

def paginated_response(
    query:        Query,
    model:        Type,
    allowed_sort: Optional[List[str]] = None,
    default_sort: str = 'created_at',
    default_dir:  str = SORT_DESC,
    serializer:   Callable[[Any], Dict] = None,
    endpoint:     str = None,
    **url_kwargs,
) -> Dict:
    """One-liner that returns a ready-to-jsonify dict."""
    result = paginate(
        query=query,
        model=model,
        allowed_sort=allowed_sort,
        default_sort=default_sort,
        default_dir=default_dir,
        serializer=serializer,
        endpoint=endpoint,
        **url_kwargs,
    )
    return result.to_dict(serializer=serializer, endpoint=endpoint, **url_kwargs)
