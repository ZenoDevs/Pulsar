from fastapi import APIRouter #type: ignore

router = APIRouter()

@router.post("/chat")
def chat_placeholder():
    # TODO: Implement chat functionality
    return {"detail": "Chat endpoint not implemented yet. Coming soon."}
