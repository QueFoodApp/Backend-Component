from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import psycopg2
import os
import logging
from .auth import verify_token  # Ensure this is the correct path
import base64

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the router
router = APIRouter()

# OAuth2 dependency for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependency to get the current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    manager_id = payload.get("manager_id")
    if manager_id is None:
        raise HTTPException(status_code=401, detail="Invalid user")
    return manager_id

# Endpoint for uploading photos
@router.post("/restaurant/upload-photo")
async def upload_photo(
    restaurant_id: int = Form(...),  # Restaurant ID
    description: str = Form(None),  # Optional description
    file: UploadFile = File(...),   # File upload
    manager_id: int = Depends(get_current_user)  # Validate manager
):
    try:
        # Log input details
        logger.debug(f"Manager ID: {manager_id}, Restaurant ID: {restaurant_id}, File: {file.filename}")

        # Read file content
        file_content = await file.read()

        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host="34.123.21.31",
            database="quefoodhall",
            user="developuser",
            password="]&l381[czY:F@sV*",
            port=5432,
        )

        cursor = connection.cursor()

        # Insert photo details into the database
        cursor.execute(
            """
            INSERT INTO restaurant_photos (restaurant_id, description, photo_data, file_name, content_type)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (restaurant_id, description, file_content, file.filename, file.content_type)
        )

        connection.commit()

        # Log success and close the connection
        logger.info(f"Photo uploaded successfully for Restaurant ID {restaurant_id}")
        cursor.close()
        connection.close()

        return {"message": "Photo uploaded successfully!"}
    except Exception as e:
        # Log the error and return an HTTPException
        logger.error(f"Error uploading photo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload photo: {str(e)}")


# GET endpoint to retrieve a photo's metadata
@router.get("/restaurant/photo/{photo_id}")
async def get_photo(photo_id: int, manager_id: int = Depends(get_current_user)):
    try:
        # Connect to the database
        connection = psycopg2.connect(
            host="34.123.21.31",
            database="quefoodhall",
            user="developuser",
            password="]&l381[czY:F@sV*",
            port=5432,
        )
        cursor = connection.cursor()

        # Fetch the photo record
        cursor.execute(
            """
            SELECT photo_id, restaurant_id, description, file_name, content_type, photo_data
            FROM restaurant_photos
            WHERE photo_id = %s
            """,
            (photo_id,)
        )
        record = cursor.fetchone()

        # Handle the case where the record is not found
        if not record:
            raise HTTPException(status_code=404, detail="Photo not found")

        # Define column names
        column_names = ["photo_id", "restaurant_id", "description", "file_name", "content_type", "photo_data"]

        # Convert to a dictionary
        result = dict(zip(column_names, record))

        # Encode photo_data to base64
        if result["photo_data"]:
            result["photo_data"] = base64.b64encode(result["photo_data"]).decode("utf-8")

        cursor.close()
        connection.close()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch photo: {str(e)}")

@router.delete("/restaurant/photo/{photo_id}")
async def delete_photo(
    photo_id: int, 
    manager_id: int = Depends(get_current_user)  # Validate manager
):
    """
    DELETE endpoint for removing a photo record by photo_id.
    """
    try:
        # Log the request
        logger.debug(f"Manager ID: {manager_id}, Photo ID to delete: {photo_id}")

        # Connect to the PostgreSQL database
        connection = psycopg2.connect(
            host="34.123.21.31",
            database="quefoodhall",
            user="developuser",
            password="]&l381[czY:F@sV*",
            port=5432,
        )
        cursor = connection.cursor()

        # Attempt to delete the photo
        cursor.execute(
            """
            DELETE FROM restaurant_photos
            WHERE photo_id = %s
            """,
            (photo_id,)
        )

        # Check if any row was affected (i.e., if the photo existed)
        if cursor.rowcount == 0:
            logger.warning(f"No photo found with ID {photo_id}.")
            raise HTTPException(
                status_code=404, 
                detail=f"Photo with ID {photo_id} not found."
            )

        # Commit the deletion
        connection.commit()

        # Log success and close the connection
        logger.info(f"Photo with ID {photo_id} deleted successfully.")
        cursor.close()
        connection.close()

        return {"message": f"Photo with ID {photo_id} has been deleted successfully."}
    except HTTPException as http_exc:
        # Re-raise known HTTPExceptions
        raise http_exc
    except Exception as e:
        # Log any other errors and return a generic 500
        logger.error(f"Error deleting photo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")