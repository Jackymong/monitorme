from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pymongo import MongoClient
import psycopg2
import subprocess
from fastapi.staticfiles import StaticFiles


app = FastAPI()

# Mount the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017")
mongo_db = mongo_client["your_mongo_database"]

# PostgreSQL connection
pg_conn = None


def connect_postgres():
    """Reconnect to PostgreSQL if the connection is closed."""
    global pg_conn
    if pg_conn is None or pg_conn.closed:
        pg_conn = psycopg2.connect(
            dbname="monitorme",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )


# Jinja2 templates setup
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def check_status(request: Request):
    mongo_status = "Running"
    postgres_status = "Running"

    try:
        # Check MongoDB connection
        mongo_client.admin.command("ping")
    except Exception as e:
        mongo_status = f"Unhealthy: {e}"

    try:
        # Check PostgreSQL connection
        connect_postgres()  # Ensure PostgreSQL is connected
        cursor = pg_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception as e:
        postgres_status = f"Unhealthy: {e}"

    return templates.TemplateResponse(
        "status.html",
        {
            "request": request,
            "mongo_status": mongo_status,
            "postgres_status": postgres_status,
        },
    )


@app.post("/control/{service}/{action}")
async def control_service(service: str, action: str):
    # Define service names for MongoDB and PostgreSQL
    services = {
        "mongo": "mongod",  # MongoDB service name
        "postgres": "postgresql"  # PostgreSQL service name
    }

    # Check if the service name is valid
    if service not in services:
        return JSONResponse(status_code=400, content={"error": "Invalid service"})

    # Construct the system command
    service_name = services[service]
    command = f"sudo systemctl {action} {service_name}"

    try:
        # Execute the command
        subprocess.run(command, shell=True, check=True)

        # Reconnect to PostgreSQL if necessary
        if service == "postgres" and action in ["start", "restart"]:
            connect_postgres()

        return {"status": "success", "message": f"{action.capitalize()}ed {service} successfully"}
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
