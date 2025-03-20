from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import pandas as pd
import logging
import os
import psycopg2
from dotenv import load_dotenv
import hashlib 
from .auth import create_access_token, verify_token 
from utils.db_authenticate import get_db
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi import Query

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

router = APIRouter()

# Define a User model for registration
class User(BaseModel):
    username: str
    password: str
    restaurant_id: int 
    manager_id: int 

# Define a Login model for login requests
class Login(BaseModel):
    username: str
    password: str

class UpdateMenuAvailability(BaseModel):
    category: str  
    food_name: str 
    availability: str  
    
class UpdateMenuByCategory(BaseModel):
    category: str  
    availability: str  
    
class UpdateOrderStatus(BaseModel):
    order_number: str
    status: str

    

# OAuth2 dependency
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Get current user
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    manager_id = payload.get("manager_id")
    print(manager_id)
    if manager_id is None:
        raise HTTPException(status_code=401, detail="Invalid user")
    return manager_id

# Function to hash passwords using SHA-256
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest() 

# Registration endpoint
@router.post("/register")
async def register(user: User):
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        # Hash the password before storing it
        hashed_password = user.password

        # Insert new user securely
        cursor.execute(
            "INSERT INTO manager_account_table (manager_account_name, manager_account_password, restaurant_id, manager_id) VALUES (%s, %s, %s, %s)",
            (user.username, hashed_password, user.restaurant_id, user.manager_id) 
        )
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": "User registered successfully!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register user: {str(e)}")

# Login endpoint
@router.post("/login")
async def login(user: Login): 
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        # Validate user credentials
        cursor.execute(
            "SELECT manager_account_password, manager_id FROM manager_account_table WHERE manager_account_name = %s",
            (user.username,)
        )
        result = cursor.fetchone()

        if result and result[0] == user.password: 
            access_token = create_access_token(data={"sub": user.username, "manager_id": result[1]}) 
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Login failed: " + str(e))

# Additional routes (unchanged)
@router.get("/dbop")
def read_dbop():
    return {"message": "This is the db operation route"}

@router.get("/dbop/test")
async def test_route():
    logger.debug("This is a debug message")
    return {"message": "This is the dbop test route"}

@router.get("/dbop/get_selected_results")
async def get_selected_results(query: str, cursor=Depends(get_db)):
    try:
        
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
        logger.error("Validation Error: %s", ve)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as error:
        logger.error("Error executing query: %s", error)
        raise HTTPException(status_code=500, detail="Query execution failed.")
    
    
    
@router.get("/menus")
async def get_menus(manager_id: int = Depends(get_current_user)):
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        # Assume the table structure and logic is correct
        cursor.execute(
            """
            SELECT DISTINCT category
            FROM menu_table 
            WHERE restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s)
            """,
            (manager_id,)
        )

        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(records, columns=column_names)

        cursor.close()
        connection.close()

        return df.to_dict(orient="records")
    except Exception as error:
        logger.error("Error fetching menus: %s", error)
        raise HTTPException(status_code=500, detail="Failed to fetch menus.")
    
    
    
@router.get("/menus/food")
async def get_menus(
    manager_id: int = Depends(get_current_user), 
    category: str = Query(..., description="The category of food items to fetch")
):
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT food_name, food_price, availability
            FROM menu_table
            WHERE restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s
            ) AND category = %s
            """,
            (manager_id, category)
        )

        # Fetch and format results
        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(records, columns=column_names)
        
        cursor.close()
        connection.close()

        return df.to_dict(orient="records")  # Return as list of dictionaries
    except Exception as error:
        logger.error("Error fetching menus: %s", error)
        raise HTTPException(status_code=500, detail="Failed to fetch menus.")
    
    
@router.get("/order")
async def get_order(manager_id: int = Depends(get_current_user)):
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT 
                ot.*,
                json_agg(json_build_object(
                    'food_name', elem ->> 'food_name',
                    'unit_price', (elem ->> 'unit_price')::numeric
                )) AS fooditems
            FROM order_table ot
            LEFT JOIN LATERAL jsonb_array_elements(ot.fooditems) AS elem ON true
            WHERE ot.restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s
            )
            AND ot.status IN ('new', 'prepare')
            GROUP BY ot.order_number
            ORDER BY ot.order_number;
            """,
            (manager_id,)
        )

        # Fetch and format results
        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(records, columns=column_names)
        
        cursor.close()
        connection.close()

        return df.to_dict(orient="records") 
    except Exception as error:
        logger.error("Error fetching menus: %s", error)
        raise HTTPException(status_code=500, detail="Failed to fetch menus.")
    
    
@router.get("/history")
async def get_order(manager_id: int = Depends(get_current_user)):
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT 
                ot.*,
                json_agg(json_build_object(
                    'food_name', elem ->> 'food_name',
                    'unit_price', (elem ->> 'unit_price')::numeric
                )) AS fooditems
            FROM order_table ot
            LEFT JOIN LATERAL jsonb_array_elements(ot.fooditems) AS elem ON true
            WHERE ot.restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s
            )
            AND ot.status IN ('complete', 'cancelled')
            GROUP BY ot.order_number
            ORDER BY ot.order_number;
            """,
            (manager_id,)
        )

        # Fetch and format results
        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(records, columns=column_names)
        
        cursor.close()
        connection.close()

        return df.to_dict(orient="records")  # Return as list of dictionaries
    except Exception as error:
        logger.error("Error fetching menus: %s", error)
        raise HTTPException(status_code=500, detail="Failed to fetch menus.")
    
    
    
    

# PUT endpoint to update menu availability
@router.put("/menus/availability")
async def update_menu_availability(item: UpdateMenuAvailability, manager_id: int = Depends(get_current_user)):
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        # Combined SQL query to update availability based on category and check food name
        cursor.execute(
            """
            UPDATE menu_table
            SET availability = %s
            WHERE category = %s AND restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s
            )
            AND food_name = %s
            RETURNING food_name
            """,
            (item.availability, item.category, manager_id, item.food_name)  # Updated to include category and food_name
        )
        
        result = cursor.fetchone()

        if result is None:
            raise HTTPException(status_code=404, detail="No food items found for this category or you do not have permission to modify them.")

        actual_food_name = result[0]
        
        connection.commit()
        cursor.close()
        connection.close()

        return {
            "message": "Menu availability updated successfully!", 
            "food_name": actual_food_name, 
            "new_availability": item.availability
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update menu availability: {str(e)}")
    
@router.put("/menus/update-availability")  # Updated endpoint path
async def update_menu_by_category(item: UpdateMenuByCategory, manager_id: int = Depends(get_current_user)):
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        # SQL query to update availability for all items in the specified category
        cursor.execute(
            """
            UPDATE menu_table
            SET availability = %s
            WHERE category = %s AND restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s
            )
            RETURNING food_name
            """,
            (item.availability, item.category, manager_id)  # Use the new parameters
        )
        
        results = cursor.fetchall()  # Fetch all updated food names

        if not results:
            raise HTTPException(status_code=404, detail="No food items found for this category or you do not have permission to modify them.")
        
        food_names = [result[0] for result in results] 
        
        connection.commit()
        cursor.close()
        connection.close()

        return {
            "message": "Menu availability updated successfully!", 
            "updated_food_names": food_names,  # Return all modified food names
            "new_availability": item.availability
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update menu availability: {str(e)}")
    
@router.put("/order/update-status")
async def update_order_status(order: UpdateOrderStatus, manager_id: int = Depends(get_current_user)):
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        # SQL query to update order status based on order_number
        cursor.execute(
            """
            UPDATE public.order_table
            SET status = %s
            WHERE order_number = %s
            RETURNING order_number, status
            """,
            (order.status, order.order_number)
        )
        
        updated_order = cursor.fetchone()

        if updated_order is None:
            raise HTTPException(status_code=404, detail="Order not found or status could not be updated.")
        
        connection.commit()
        cursor.close()
        connection.close()

        return {
            "message": "Order status updated successfully!",
            "order_number": updated_order[0],
            "new_status": updated_order[1]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update order status: {str(e)}")
    
    
@router.get("/restaurant")
async def get_restaurant_by_manager(manager_id: int = Depends(get_current_user)):
    """
    Fetch restaurant details based on the manager ID.

    Args:
        manager_id (int): The manager ID obtained from the JWT token.

    Returns:
        dict: Restaurant details including restaurant_id, name, ratings, type, and pricing levels.
    """
    try:
        # Establish database connection
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()

        # Updated SQL query to fetch required restaurant details
        cursor.execute(
            """
            SELECT 
                restaurant_id, 
                restaurant_name, 
                ratings, 
                restaurant_type, 
                pricing_levels
            FROM public.restaurant_table
            WHERE restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s
            )
            """,
            (manager_id,)
        )

        # Fetch restaurant details
        record = cursor.fetchone()

        if not record:
            raise HTTPException(
                status_code=404, 
                detail="No restaurant found for the provided manager ID."
            )

        # Map the record to a dictionary
        column_names = [desc[0] for desc in cursor.description]
        restaurant_details = dict(zip(column_names, record))

        cursor.close()
        connection.close()

        return restaurant_details

    except Exception as error:
        logger.error("Error fetching restaurant details: %s", error)
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch restaurant details."
        )


@router.get("/foodnames")
async def get_food_names(manager_id: int = Depends(get_current_user)):
    try:
        connection = psycopg2.connect(
            host=os.getenv("HOST"),
            database=os.getenv("DATABASE"),
            user="developuser",
            password=os.getenv("PASSWORD"),
            port=os.getenv("PORT"),
        )
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT food_name
            FROM menu_table
            WHERE restaurant_id IN (
                SELECT restaurant_id 
                FROM manager_account_table 
                WHERE manager_id = %s
            )
            """,
            (manager_id,)
        )

        # Fetch all food names
        records = cursor.fetchall()
        food_names = [record[0] for record in records]

        cursor.close()
        connection.close()

        return {"food_names": food_names}
    except Exception as error:
        logger.error("Error fetching food names: %s", error)
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch food names."
        )