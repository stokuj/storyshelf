from fastapi import APIRouter, Depends, HTTPException


from api.models.model import TextContentRequest
from api.services.book_service import analyse_text

router = APIRouter(prefix="/analyse", tags=["analyse"])


# @router.post("/{book_id}")
# def analyse_by_id(book_id: int, db: Session = Depends(get_db)):
#     content = get_book_content_by_id(db, book_id)
#     if content is None:
#         raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")
#
#     return {"book_id": book_id, "content": content}


@router.post("/")
def analyse_text_endpoint(payload: TextContentRequest):
    result = analyse_text(payload.content)
    return {"analysis": result}
