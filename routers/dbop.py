from fastapi import APIRouter, Depends, HTTPException
import pandas as pd
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from utils.db_authenticate import get_db


router = APIRouter()

@router.get("/dbop")
def read_dbop():
    return {"message": "This is the db operation route"}


@router.get("/dbop/test")
async def test_route():
    logger.debug("This is a debug message")
    return {"message": "This is the dbop test route"}


@router.get("/dbop/get_selected_results")
async def get_selected_results(query: str, cursor = Depends(get_db)):
    try:
        # Ensure the query is a SELECT statement
        if not query.strip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")

        # Execute the query
        cursor.execute(query)

        # Fetch results and convert to a DataFrame
        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(records, columns=column_names)

        return df.to_dict(orient="records")  # Converts DataFrame to JSON-compatible format

    except ValueError as ve:
        print("Validation Error:", ve)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as error:
        print("Error executing query:", error)
        raise HTTPException(status_code=500, detail="Query execution failed.")