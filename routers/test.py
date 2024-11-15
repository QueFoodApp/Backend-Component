from fastapi import APIRouter

router = APIRouter()

def get_password_by_username(username: str):
    query = f"SELECT manager_account_password FROM {TABLE_NAME} WHERE manager_account_name = %s;"
    cursor = db.execute(query, (username,))
    result = cursor.fetchone()
    return result[0] if result else None

@router.get("/test")
def read_test():
    return {"message": "This is the test route"}
