from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def read_test():
    return {"message": "This is the test route"}