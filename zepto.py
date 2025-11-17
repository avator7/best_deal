# zepto.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException


MAX_RETRIES = 1


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


    driver = create_driver(headless=True)
    wait = WebDriverWait(driver, 25)


    # ------------------------------------------------------------------
    # 🔥 UNIVERSAL "TRY AGAIN" POPUP HANDLER
    # ------------------------------------------------------------------
    def click_try_again(max_clicks=5):
        """Gently handles Zepto 'Try Again' popups anywhere."""
        for _ in range(max_clicks):
            try:
                btn = driver.find_elements(By.XPATH, "//button[contains(., 'Try Again')]")
                if btn:
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn[0])
                    btn[0].click()
                    print("⚠️ Clicked 'Try Again'")
                    time.sleep(2)
                else:
                    return False
            except:
                pass
        return True


    # ------------------------------------------------------------------
    # SAFE PAGE LOAD
    # ------------------------------------------------------------------
    def safe_get(url, retries=3):
        for attempt in range(1, retries + 1):
            try:
                driver.get(url)
                time.sleep(3)
                click_try_again()

                if "zepto" in driver.title.lower():
                    print(f"🌐 Zepto opened (attempt {attempt})")
                    return True
            except:
                pass

            print(f"⚠️ Retry opening Zepto {attempt}/{retries}")
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
                print(f"⚠️ Retry {i+1}/{retries} for {desc}: {e}")
                click_try_again()
                time.sleep(1)

        print(f"❌ Failed to click {desc}")
        return False


    # ------------------------------------------------------------------
    # LOCATION SETUP
    # ------------------------------------------------------------------
    def set_location():
        for attempt in range(1, MAX_RETRIES + 1):

            try:
                click_try_again()

                # Step 1: Open location selector
                click_element("button[aria-label='Select Location']", "Select Location", js=True)

                # Step 2: Type location
                input_box = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[placeholder='Search a new address']")
                    )
                )
                input_box.click()
                input_box.clear()
                for ch in location:
                    input_box.send_keys(ch)
                    time.sleep(0.04)
                print(f"📍 Typed location: {location}")

                time.sleep(2)
                click_try_again()

                # Step 3: Select suggestion
                suggestions = wait.until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div[data-testid='address-search-item']")
                    )
                )

                # choose best match OR fallback to first
                s = next((x for x in suggestions if location.lower() in x.text.lower()), suggestions[0])

                driver.execute_script("arguments[0].click();", s)
                print(f"🎯 Selected: {s.text}")

                time.sleep(2)

                # Step 4: Confirm location
                click_element("button[data-testid='location-confirm-btn']", "Confirm Location", js=True)

                print("🏁 Location set successfully")
                return True

            except Exception as e:
                print(f"⚠️ Location setup error attempt {attempt}: {e}")
                driver.refresh()
                time.sleep(3)

        print("❌ Could not set location")
        return False


    # ------------------------------------------------------------------
    # OPEN SEARCH MODAL
    # ------------------------------------------------------------------
    def open_search_modal():
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                click_try_again()

                btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-testid='search-bar-icon']"))
                )
                driver.execute_script("arguments[0].click();", btn)

                wait.until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, "input[placeholder*='Search for over']")
                    )
                )
                print("🔍 Search modal opened")
                return True

            except Exception as e:
                print(f"⚠️ Search modal retry {attempt}: {e}")
                driver.refresh()
                time.sleep(3)

        print("❌ Cannot open search modal")
        return False


    # ------------------------------------------------------------------
    # PERFORM SEARCH
    # ------------------------------------------------------------------
    def search_product(q):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                click_try_again()

                box = wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "input[placeholder*='Search for over']")
                    )
                )
                driver.execute_script("arguments[0].focus();", box)

                box.clear()
                for ch in q:
                    box.send_keys(ch)
                    time.sleep(0.05)
                box.send_keys(Keys.ENTER)

                print(f"🔎 Searching '{q}'")
                return True

            except Exception as e:
                print(f"⚠️ Search retry {attempt}: {e}")
                time.sleep(3)

        print("❌ Search failed")
        return False


    # ------------------------------------------------------------------
    # WAIT FOR PRODUCTS
    # ------------------------------------------------------------------
    def wait_for_products():
        for attempt in range(1, 12):
            click_try_again()
            time.sleep(2)

            # Zepto uses 2 different selectors depending on category
            cards = driver.find_elements(By.CSS_SELECTOR, "div[data-marketplace='super_saver'] a")
            if cards:
                print(f"🟢 Loaded {len(cards)} Zepto products")
                return cards

            print(f"⚠️ Retry loading products {attempt}/12")
            driver.refresh()

        print("❌ Could not load product grid")
        return []


    # ------------------------------------------------------------------
    # EXTRACT PRODUCT DATA
    # ------------------------------------------------------------------
    def extract_products(cards):
        results = []

        for c in cards:
            try: name = c.find_element(By.CSS_SELECTOR, "[data-slot-id='ProductName']").text
            except: name = ""

            try: price = c.find_element(By.CSS_SELECTOR, "span.cptQT7").text
            except: price = ""

            try: mrp = c.find_element(By.CSS_SELECTOR, "span.cx3iWL").text
            except: mrp = ""

            try: discount = c.find_element(By.CSS_SELECTOR, ".cYCsFo").text
            except: discount = ""

            try: weight = c.find_element(By.CSS_SELECTOR, "[data-slot-id='PackSize']").text
            except: weight = ""

            try: eta = c.find_element(By.CSS_SELECTOR, "[data-slot-id='EtaInformation']").text
            except: eta = ""

            try: image = c.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
            except: image = ""

            results.append({
                "name": name,
                "price": price,
                "mrp": mrp,
                "discount": discount,
                "weight": weight,
                "delivery_time": eta,
                "image_url": image
            })

        return results


    # ----------------- MAIN LOGIC -------------------

    if not safe_get("https://www.zepto.com/"):
        driver.quit()
        return []

    if not set_location():
        driver.quit()
        return []

    if not open_search_modal():
        driver.quit()
        return []

    if not search_product(search_query):
        driver.quit()
        return []

    cards = wait_for_products()
    data = extract_products(cards)

    driver.quit()
    return data
