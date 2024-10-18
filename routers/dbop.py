from fastapi import APIRouter

router = APIRouter()

@router.get("/dbop")
def read_dbop():
    return {"message": "This is the db operation route"}