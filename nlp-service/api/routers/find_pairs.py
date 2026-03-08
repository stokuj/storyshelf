from fastapi import APIRouter, Depends, HTTPException


from api.models.model import NamesRequest, NamesWithContentRequest
from api.services.book_service import find_sentences_with_both_characters


router = APIRouter(prefix="/find-pairs", tags=["find-pairs"])


# @router.post("/{book_id}")
# def find_pairs_by_id(book_id: int,payload: NamesRequest,db: Session = Depends(get_db),):
#     content = get_book_content_by_id(db, book_id)
#     if content is None:
#         raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")
#
#     pairs = find_pair_sentences(content, payload.names)
#     return {"book_id": book_id, "pairs": pairs}


@router.post("/")
def find_sentences_with_both_characters(payload: NamesWithContentRequest):
    pairs = find_sentences_with_both_characters(payload.content, payload.names)
    return {"pairs": pairs}
