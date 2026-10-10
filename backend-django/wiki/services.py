"""Writes to Pages. Every change goes through here (API now, Agent in M3)."""

from django.db import IntegrityError, transaction

from wiki import okf
from wiki.models import Page, PageVersion


class PathTaken(Exception):  # noqa: N818
    pass


class StaleVersion(Exception):  # noqa: N818
    pass


def _str_or_none(value):
    return value if isinstance(value, str) else None


def _apply(page, content, frontmatter):
    """Content plus the frontmatter copies used by queries."""
    page.content = content
    page.title = frontmatter["title"]
    page.book = _str_or_none(frontmatter.get("book"))
    page.universe = _str_or_none(frontmatter.get("universe"))


def insert_page(owner, path, page_type, content):
    """New Page with its first Version (`created`, `human`)."""
    frontmatter = okf.validate(content, page_type)
    page = Page(owner=owner, path=path, type=page_type)
    _apply(page, content, frontmatter)
    try:
        with transaction.atomic():
            page.save()
            PageVersion.objects.create(page=page, content=content, kind="created", author="human")
    except IntegrityError as e:
        raise PathTaken(f"Page already exists: {path}") from e
    return page


def _check_ref(owner, path, page_type):
    if not Page.objects.filter(owner=owner, path=path, type=page_type).exists():
        raise okf.OKFError(f"No {page_type} page at {path}", field=page_type)


def create_page(owner, page_type, title, *, author=None, year=None, book=None, universe=None):
    """Empty Template Page; the server picks the Path."""
    if page_type in ("character", "place"):
        if not book:
            raise okf.OKFError("This field is required.", field="book")
        _check_ref(owner, book, "book")
        meta = {"title": title, "book": book}
    elif page_type == "book":
        if universe:
            _check_ref(owner, universe, "universe")
        meta = {"title": title, "author": author, "year": year, "universe": universe}
    else:
        meta = {"title": title}
    path = okf.page_path(page_type, title, book)
    return insert_page(owner, path, page_type, okf.render_template(page_type, meta))


def edit_page(page, content, base_version, *, kind="edit", author="human"):
    """New Version on top of `base_version`; StaleVersion if the Page moved on."""
    frontmatter = okf.validate(content, page.type)
    with transaction.atomic():
        locked = Page.objects.select_for_update().get(pk=page.pk)
        if locked.version != base_version:
            raise StaleVersion("Page has a newer version, reload it")
        _apply(locked, content, frontmatter)
        locked.save()
        PageVersion.objects.create(page=locked, content=content, kind=kind, author=author)
    return locked
