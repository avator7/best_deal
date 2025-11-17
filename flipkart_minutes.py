# flipkart_minutes.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException


URL = "https://www.flipkart.com/flipkart-minutes-store?marketplace=HYPERLOCAL"

MAX_RETRIES = 1
WAIT_TIME = 25


def get_products(LOCATION, search_query):

    # ----------------- DRIVER SETUP ------------------
    def create_driver():
        options = Options()
        # options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--window-size=1920,1080")
        return webdriver.Chrome(options=options)

    driver = create_driver()
    wait = WebDriverWait(driver, WAIT_TIME)


    # ---------------- GLOBAL “TRY AGAIN” HANDLER ----------------
    def click_try_again():
        try:
            btns = driver.find_elements(By.XPATH, "//button[contains(.,'Try Again')]")
            if btns:
                driver.execute_script("arguments[0].click();", btns[0])
                print("⚠️ Handled 'Try Again'")
                time.sleep(2)
                return True
        except:
            pass
        return False


    # ---------------- SAFE ACTION WRAPPER ----------------
    def safe_attempt(action_name, func, retries=MAX_RETRIES, *args, **kwargs):
        for attempt in range(1, retries + 1):
            try:
                result = func(*args, **kwargs)
                if result:
                    print(f"✅ {action_name} (attempt {attempt})")
                    return result
            except Exception as e:
                print(f"⚠️ Failed {action_name} attempt {attempt}: {e}")
            time.sleep(2)
            click_try_again()
        print(f"❌ Giving up on {action_name}")
        return None


    # ---------------- OPEN PAGE ----------------
    def open_page():
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                driver.get(URL)
                print(f"🌐 Opening Flipkart Minutes (attempt {attempt})")
                time.sleep(4)

                if "Flipkart" in driver.title:
                    return True
            except WebDriverException:
                pass
            time.sleep(2)
        return False


    # ---------------- LOCATION MODAL ----------------
    def wait_for_location_modal():
        try:
            modal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main.Ff3t7M")))
            print("🟢 Location modal detected")
            return modal
        except:
            return None


    # ---------------- CLICK ENTER MANUAL LOCATION ----------------
    def click_enter_location_manually():
        try:
            btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Enter location manually')]"))
            )
            driver.execute_script("arguments[0].click();", btn)
            return True
        except:
            return False


    # ---------------- SET LOCATION ----------------
    def set_location():
        """Safely type location, wait for hydrated suggestions, pick best match, confirm."""
        try:
            # Step 1: Type in search box
            input_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#search"))
            )
            input_box.clear()

            # Type slowly like user
            for ch in LOCATION:
                input_box.send_keys(ch)
                time.sleep(0.04)

            print(f"📍 Typed location: {LOCATION}")
            time.sleep(1.5)

            # Step 2: Wait for suggestion container
            suggestions = wait.until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//ul/li[contains(@class,'_')]")
                )
            )

            print(f"🔎 Found {len(suggestions)} raw suggestions")

            # Step 3: Pick the best suggestion
            target = None
            location_lower = LOCATION.lower()

            for s in suggestions:
                try:
                    text = s.text.strip()
                    if text and location_lower in text.lower():
                        target = s
                        break
                except:
                    continue

            # If nothing matched, fallback to first hydrated suggestion
            if not target:
                print("⚠️ No exact match → selecting first loaded suggestion")
                target = suggestions[0]

            # Step 4: Scroll into view & JS click
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", target)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", target)

            print(f"🎯 Selected suggestion: {target.text.strip()}")

            # Step 5: Confirm location
            confirm_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @value='Confirm']")
                )
            )
            driver.execute_script("arguments[0].click();", confirm_btn)
            print("🏁 Location confirmed")
            time.sleep(2)
            return True

        except Exception as e:
            print("❌ set_location failed:", e)
            return False


    # ---------------- PERFORM SEARCH ----------------
    def perform_search():
        try:
            search_box = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input.Pke_EE[placeholder*='Search in Flipkart Minutes']")
                )
            )
            driver.execute_script("arguments[0].click();", search_box)
            search_box.clear()

            for ch in search_query:
                search_box.send_keys(ch)
                time.sleep(0.05)

            search_box.send_keys(Keys.ENTER)
            print(f"🔍 Searching '{search_query}'")

            time.sleep(5)
            return True
        except:
            return False


    # ---------------- SCROLL UNTIL FULL LOAD ----------------
    def scroll_all():
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        print("📜 Scrolling complete")


    # ---------------- EXTRACT PRODUCTS ----------------
    def extract_products():
        result = []
        cards = driver.find_elements(By.CSS_SELECTOR, "div.VPqDeq div[style*='padding: 16px']")

        print(f"🛒 Found {len(cards)} products")

        for card in cards:
            try: name = card.find_element(By.XPATH, ".//a").text
            except: name = ""

            try: price = card.find_element(By.XPATH, ".//div[contains(text(),'₹')]").text
            except: price = ""

            try: img = card.find_element(By.TAG_NAME, "img").get_attribute("src")
            except: img = ""

            try: discount = card.find_element(By.XPATH, ".//*[contains(text(),'%') or contains(text(),'Off')]").text
            except: discount = ""

            result.append({
                "name": name.strip(),
                "price": price.strip(),
                "discount": discount.strip(),
                "image_url": img
            })

        return result


    # ---------------- MAIN FLOW ----------------
    if not safe_attempt("Open Flipkart Minutes", open_page):
        driver.quit()
        return []

    safe_attempt("Wait for Location Modal", wait_for_location_modal)
    safe_attempt("Click 'Enter Location Manually'", click_enter_location_manually)
    safe_attempt("Set Location", set_location)

    if not safe_attempt("Search Product", perform_search):
        driver.quit()
        return []

    scroll_all()

    products = safe_attempt("Extract Products", extract_products)
    if not products:
        products = []

    driver.quit()
    return products
