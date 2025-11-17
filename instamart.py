import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException


def get_products(LOCATION, SEARCH_QUERY):
    def create_driver(headless=True):
        options = Options()
        
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--force-device-scale-factor=1")
            options.add_argument("--disable-gpu")
            options.add_argument("--hide-scrollbars")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_argument("--blink-settings=imagesEnabled=true")

            # 🔥 Trick websites into thinking it's NOT headless
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-notifications")

            # 🔥 Fake user agent (desktop Chrome)
            options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            )

            # 🔥 Enable display rendering even in headless mode
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--use-gl=swiftshader")  # Fix hydration loading

            # Flipkart sometimes blocks headless, this bypasses:
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

        else:
            options.add_argument("--start-maximized")

        return webdriver.Chrome(options=options)


    MAX_RETRIES = 3

    # # ---------- SETUP ----------
    # chrome_options = Options()
    # # chrome_options.add_argument("--headless=new")
    # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # chrome_options.add_argument("--disable-notifications")
    # chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")

    driver = create_driver(headless=True)
    wait = WebDriverWait(driver, 25)

    # --------------------------------------------------------------------------
    # 🔥 UNIVERSAL TRY-AGAIN HANDLER → works on homepage, location popup, products
    # --------------------------------------------------------------------------
    def click_try_again(max_clicks=5):
        for _ in range(max_clicks):
            try_again_buttons = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='error-button'] button")
            if try_again_buttons:
                driver.execute_script("arguments[0].scrollIntoView(true);", try_again_buttons[0])
                try_again_buttons[0].click()
                print("⚠️ Clicked TRY AGAIN to recover Instamart")
                time.sleep(2)
            else:
                return False
        return True

    # ----------------------- STEP 1: SAFE PAGE LOAD ---------------------------
    def safe_get(url, retries=3):
        for attempt in range(1, retries + 1):
            try:
                driver.get(url)
                print(f"🌐 Loading Instamart (attempt {attempt})")
                time.sleep(3)

                click_try_again()   # <–– NEW FIX

                if "instamart" in driver.title.lower():
                    return True
            except:
                pass
            print("⚠️ Retrying page load...")
            time.sleep(2)
        return False

    # ----------------------- SAFE CLICK ---------------------------------------
    def click_element(selector, desc, by=By.CSS_SELECTOR, retries=3, js=True):
        for i in range(retries):
            try:
                elem = wait.until(EC.element_to_be_clickable((by, selector)))
                if js:
                    driver.execute_script("arguments[0].click();", elem)
                else:
                    elem.click()
                print(f"✅ Clicked {desc}")
                return True
            except Exception as e:
                print(f"⚠️ Retry {i+1}/{retries} failed clicking {desc}")
                click_try_again()
                time.sleep(1)
        print(f"❌ Could not click {desc}")
        return False

    # ---------------------- STEP 2: SET LOCATION ------------------------------
    def set_location():
        for attempt in range(MAX_RETRIES):
            try:
                click_try_again()

                click_element("div[data-testid='DEFAULT_ADDRESS_CONTAINER']", "Add your location")
                click_try_again()

                click_element("div[data-testid='search-location']", "Search address")
                click_try_again()

                location_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search for area']"))
                )

                location_input.clear()
                for ch in LOCATION:
                    location_input.send_keys(ch)
                    time.sleep(0.03)

                print(f"📍 Typed location: {LOCATION}")

                time.sleep(2)
                click_try_again()

                click_element("div._11n32", "First suggestion")

                click_try_again()

                click_element("//button[.//span[text()='Confirm Location']]",
                              "Confirm Location",
                              by=By.XPATH)

                print("🎉 Location set!")
                return True

            except Exception as e:
                print(f"⚠️ Location setup failed attempt {attempt+1}")
                driver.refresh()
                time.sleep(4)

        return False

    # -------------------- STEP 3: OPEN SEARCH BAR -----------------------------
    def open_search_bar():
        for attempt in range(MAX_RETRIES):
            try:
                click_try_again()
                click_element("div._1AaZg", "Homepage search box")

                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div._3y3yB")))
                return True
            except:
                print(f"⚠️ Search bar open failed {attempt+1}")
                driver.refresh()
                time.sleep(3)
        return False

    # -------------------- STEP 4: SEARCH PRODUCT -----------------------------
    def search_product(query):
        try:
            search_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input[data-testid='search-page-header-search-bar-input']")
            ))
            driver.execute_script("arguments[0].focus();", search_input)
            search_input.clear()

            for ch in query:
                search_input.send_keys(ch)
                time.sleep(0.04)

            search_input.send_keys(Keys.ENTER)
            print(f"🔍 Searching '{query}'")
            return True
        except Exception as e:
            print("❌ Failed to type search query for instamrt")
            return False

    # -------------------- STEP 5: WAIT FOR PRODUCT RESULTS --------------------
    def wait_for_products():
        for attempt in range(15):
            time.sleep(2)

            click_try_again()

            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='item-collection-card-full']")
            if cards:
                print(f"🟢 Products loaded on attempt {attempt+1}")
                return cards

            print(f"⚠️ Still loading products {attempt+1}/15")

        print("❌ Could not load products after retries.")
        return []

    # ------------------- STEP 6: EXTRACT PRODUCTS -----------------------------
    def extract_products(cards):
        products = []

        for card in cards:
            try: name = card.find_element(By.CSS_SELECTOR, "div.sc-gEvEer.bvSpbA").text
            except: name = ""

            try: desc = card.find_element(By.CSS_SELECTOR, "div.sc-gEvEer.diZRny").text
            except: desc = ""

            try: weight = card.find_element(By.CSS_SELECTOR, "div.sc-gEvEer.bCqPoH").text
            except: weight = ""

            try: price = card.find_element(By.CSS_SELECTOR, "div.sc-gEvEer.iQcBUp").text
            except: price = ""

            try: mrp = card.find_element(By.CSS_SELECTOR, "div.sc-gEvEer.fULQHN").text
            except: mrp = ""

            try: discount = card.find_element(By.CSS_SELECTOR, "div[data-testid='item-offer-label-discount-text']").text
            except: discount = ""

            try: eta = card.find_element(By.CSS_SELECTOR, "div._2zIRo div").text
            except: eta = ""

            try: image = card.find_element(By.CSS_SELECTOR, "img._16I1D").get_attribute("src")
            except: image = ""

            products.append({
                "name": name,
                "description": desc,
                "weight": weight,
                "price": price,
                "mrp": mrp,
                "discount": discount,
                "delivery_time": eta,
                "image_url": image
            })

        return products

    # ------------------------------ MAIN FLOW ---------------------------------

    if not safe_get("https://www.swiggy.com/instamart"):
        driver.quit()
        return []

    if not set_location():
        driver.quit()
        return []

    if not open_search_bar():
        driver.quit()
        return []

    if not search_product(SEARCH_QUERY):
        driver.quit()
        return []

    cards = wait_for_products()
    products = extract_products(cards)

    driver.quit()
    return products
