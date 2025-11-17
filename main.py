# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging, asyncio, requests
from concurrent.futures import ThreadPoolExecutor

# Import scrapers (all must have get_products(location, product))
from zepto import get_products as zepto_scrape
from blinkit import get_products as blinkit_scrape
from instamart import get_products as instamart_scrape
# from flipkart_minutes import get_products as flipkart_scrape

# ============================================================
# APP CONFIG
# ============================================================

app = FastAPI(
    title="🛒 BestDeal API",
    version="1.0.0",
    docs_url="/docverse",
    redoc_url="/docverse-advanced"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BestDealAPI")

executor = ThreadPoolExecutor(max_workers=4)



# ============================================================
# LOCATION UTILITIES
# ============================================================

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org?format=json", timeout=3).json().get("ip")
    except:
        return None


def get_location_from_multiple_apis(ip):
    """Try up to 3 different services and return best result."""

    if not ip:
        return "Unknown"

    headers = {"User-Agent": "Mozilla/5.0"}

    # 1️⃣ ipapi.co
    try:
        data = requests.get(f"https://ipapi.co/{ip}/json/", headers=headers, timeout=3).json()
        if data.get("city"):
            return f"{data['city']}, {data.get('region','')}, {data.get('country_name','')}"
    except: pass

    # 2️⃣ ipinfo.io
    try:
        data = requests.get(f"https://ipinfo.io/{ip}/json", headers=headers, timeout=3).json()
        if data.get("city"):
            return f"{data['city']}, {data.get('region','')}, {data.get('country','')}"
    except: pass

    # 3️⃣ ip-api.com
    try:
        data = requests.get(f"http://ip-api.com/json/{ip}", headers=headers, timeout=3).json()
        if data.get("status") == "success":
            return f"{data['city']}, {data['regionName']}, {data['country']}"
    except: pass

    return "Unknown"



# ============================================================
# MODELS
# ============================================================

class SearchInput(BaseModel):
    product: str
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None



# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def home():
    return {"status": "OK", "message": "BestDeal API running"}

@app.get("/get-location")
def detect_location(request: Request):
    ip = request.client.host

    if ip.startswith("127.") or "localhost" in ip:
        ip = get_public_ip()

    loc = get_location_from_multiple_apis(ip)
    return {"ip": ip, "location": loc}



# ============================================================
# PARALLEL SCRAPING ENDPOINT
# ============================================================

@app.post("/search")
async def search_all(body: SearchInput):
    product = body.product
    user_location = body.location

    # Auto-location if missing
    if not user_location:
        ip = get_public_ip()
        user_location = get_location_from_multiple_apis(ip)
        logger.info(f"📍 Auto-detected location: {user_location}")

    logger.info(f"🚀 Start scraping for '{product}' @ {user_location}")

    scrapers = {
        "Zepto": zepto_scrape,
        "Blinkit": blinkit_scrape,
        "Instamart": instamart_scrape,
        # "Flipkart": flipkart_scrape
    }

    results = {}
    errors = {}

    async def run_scraper(name, func):
        try:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(
                executor,
                lambda: func(user_location, product)
            )
            results[name] = data
        except Exception as e:
            logger.error(f"{name} FAILED: {e}")
            errors[name] = str(e)

    await asyncio.gather(*(run_scraper(name, func) for name, func in scrapers.items()))

    logger.info("🎉 Scraping complete")

    return {
        "query": product,
        "location_used": user_location,
        "results": results,
        "errors": errors
    }



# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
