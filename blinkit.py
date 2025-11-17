# blinkit.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException


def get_products(location, search_query):
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


    MAX_RETRIES = 1

    # ----------------- SELENIUM SETUP -----------------
    # chrome_options = Options()
    # # chrome_options.add_argument("--headless=new")
    # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # chrome_options.add_argument("--disable-notifications")
    # chrome_options.add_argument("--disable-infobars")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")

    driver = create_driver(headless=True)
    wait = WebDriverWait(driver, 25)


    # ------------------------------------------------------------------
    # 🔥 UNIVERSAL TRY AGAIN HANDLER (Global for Blinkit)
    # ------------------------------------------------------------------
    def click_try_again(max_clicks=5):
        """Clicks 'Try Again' popups anywhere on Blinkit."""
        for _ in range(max_clicks):
            btns = driver.find_elements(By.XPATH, "//button[contains(., 'Try Again')]")
            if btns:
                driver.execute_script("arguments[0].scrollIntoView(true);", btns[0])
                btns[0].click()
                print("⚠️ Clicked 'Try Again' to recover Blinkit.")
                time.sleep(2)
            else:
                return False
        return True


    # ------------------------------------------------------------------
    # STEP 1: SAFE PAGE LOAD
    # ------------------------------------------------------------------
    def safe_get(url, retries=3):
        for attempt in range(1, retries + 1):
            try:
                driver.get(url)
                print(f"🌐 Blinkit open attempt {attempt}")
                time.sleep(3)

                click_try_again()

                if "blinkit" in driver.title.lower():
                    return True
            except:
                pass

            print("⚠️ Page load retry ...")
            time.sleep(2)

        return False


    # ------------------------------------------------------------------
    # SAFE CLICK
    # ------------------------------------------------------------------
    def click_element(selector, desc, by=By.CSS_SELECTOR, retries=3, js=True):
        for i in range(retries):
            try:
                el = wait.until(EC.element_to_be_clickable((by, selector)))
                if js:
                    driver.execute_script("arguments[0].click();", el)
                else:
                    el.click()
                print(f"✅ Clicked {desc}")
                return True
            except Exception as e:
                print(f"⚠️ Retry {i+1}/{retries} failed clicking {desc}: {e}")
                click_try_again()
                time.sleep(1)
        print(f"❌ Could not click {desc}")
        return False


    # ------------------------------------------------------------------
    # STEP 2: LOCATION SETUP
    # ------------------------------------------------------------------
    def set_location():
        for attempt in range(MAX_RETRIES):

            try:
                click_try_again()

                # open location box
                location_box = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='select-locality']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", location_box)
                location_box.click()
                time.sleep(1)

                # type location
                for ch in location:
                    location_box.send_keys(ch)
                    time.sleep(0.03)

                print(f"📍 Typed location: {location}")
                time.sleep(2)
                click_try_again()

                # select first suggestion
                suggestion = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR,
                        "div.LocationSearchList__LocationListContainer-sc-93rfr7-0 div"))
                )
                driver.execute_script("arguments[0].click();", suggestion)
                print("🎯 Selected first location suggestion")
                return True

            except Exception as e:
                print(f"⚠️ Location setup failed attempt {attempt+1}: {e}")
                driver.refresh()
                time.sleep(3)

        return False


    # ------------------------------------------------------------------
    # STEP 3: OPEN SEARCH BAR
    # ------------------------------------------------------------------
    def open_search_bar():
        for attempt in range(MAX_RETRIES):
            try:
                click_try_again()

                # homepage search button
                search_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.SearchBar__Button-sc-16lps2d-4"))
                )
                driver.execute_script("arguments[0].click();", search_btn)

                print("🔎 Search bar opened")
                return True
            except Exception as e:
                print(f"⚠️ Search open retry {attempt+1}: {e}")
                driver.refresh()
                time.sleep(3)
        return False


    # ------------------------------------------------------------------
    # STEP 4: PERFORM SEARCH
    # ------------------------------------------------------------------
    def perform_search(query):
        for attempt in range(MAX_RETRIES):
            try:
                click_try_again()

                search_input = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input.SearchBarContainer__Input-sc-hl8pft-3"))
                )
                driver.execute_script("arguments[0].focus();", search_input)
                search_input.clear()

                for ch in query:
                    search_input.send_keys(ch)
                    time.sleep(0.05)

                search_input.send_keys(Keys.ENTER)
                print(f"🔍 Searching '{query}' ...")
                return True

            except Exception as e:
                print(f"⚠️ Search retry {attempt+1}: {e}")
                time.sleep(3)

        return False


    # ------------------------------------------------------------------
    # STEP 5: WAIT FOR PRODUCT GRID
    # ------------------------------------------------------------------
    def wait_for_products():
        for attempt in range(1, 10):
            time.sleep(2)

            click_try_again()

            try:
                grid = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(@style,'grid-template-columns: repeat(12, 1fr)')]")
                    )
                )
                cards = grid.find_elements(By.XPATH, "./div")
                if cards:
                    print(f"🟢 Found {len(cards)} products")
                    return cards
            except:
                pass

            print(f"⚠️ Products not found retry {attempt}/10")
            driver.refresh()

        print("❌ Product loading failed")
        return []


    # ------------------------------------------------------------------
    # STEP 6: EXTRACT PRODUCTS
    # ------------------------------------------------------------------
    def extract_products(cards):
        products = []
        for c in cards:
            try: name = c.find_element(By.CSS_SELECTOR, "div.tw-font-semibold").text
            except: name = ""

            try: weight = c.find_element(By.XPATH,
                ".//div[contains(text(),'g') or contains(text(),'kg') or contains(text(),'ml')]").text
            except: weight = ""

            try: price = c.find_element(By.XPATH, ".//div[contains(text(),'₹')]").text
            except: price = ""

            try: mrp = c.find_element(By.XPATH, ".//div[contains(@class,'tw-line-through')]").text
            except: mrp = ""

            try: discount = c.find_element(By.XPATH, ".//div[contains(text(),'%OFF')]").text
            except: discount = ""

            try: eta = c.find_element(By.XPATH, ".//div[contains(text(),'mins')]").text
            except: eta = ""

            try: img = c.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
            except: img = ""

            products.append({
                "name": name,
                "weight": weight,
                "price": price,
                "mrp": mrp,
                "discount": discount,
                "delivery_time": eta,
                "image_url": img
            })
        return products


    # ------------------------ MAIN EXECUTION -----------------------------

    if not safe_get("https://blinkit.com/"):
        driver.quit()
        return []

    if not set_location():
        driver.quit()
        return []

    if not open_search_bar():
        driver.quit()
        return []

    if not perform_search(search_query):
        driver.quit()
        return []

    cards = wait_for_products()
    data = extract_products(cards)

    driver.quit()
    return data
