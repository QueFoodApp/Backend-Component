from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import test, dbop, photos



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


# routers/test -> /api/test
app.include_router(test.router, prefix="/api")
# routers/test -> /api/dbop
app.include_router(dbop.router, prefix="/api")

app.include_router(photos.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "this is the base app file"}
