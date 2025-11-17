import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ---------- CONFIG ----------
URL = "https://www.flipkart.com/flipkart-minutes-store?marketplace=HYPERLOCAL"
LOCATION = "Bengaluru"
SEARCH_QUERY = "onion"

# ---------- SETUP ----------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-notifications")
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

# ---------- STEP 1: OPEN PAGE ----------
driver.get(URL)
print("🌐 Opened Flipkart Minutes...")
time.sleep(4)

# ---------- STEP 2: WAIT FOR SIDE MODAL ----------
try:
    modal = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "main.Ff3t7M"))
    )
    print("✅ Location modal detected")
except Exception as e:
    print("❌ Modal not detected:", e)
    driver.quit()
    exit()

# ---------- STEP 3: CLICK “ENTER LOCATION MANUALLY” ----------
try:
    manual_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'Enter location manually')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", manual_btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", manual_btn)
    print("✅ Clicked 'Enter location manually'")
except Exception as e:
    print("❌ Failed to click manual location:", e)
    driver.quit()
    exit()

# ---------- STEP 4: TYPE LOCATION ----------
try:
    search_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input#search"))
    )
    search_input.clear()
    search_input.send_keys(LOCATION)
    print(f"⌨️ Typed location: {LOCATION}")
    time.sleep(2)

    # Wait for suggestions list to appear
    suggestions = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul li"))
    )
    if suggestions:
        driver.execute_script("arguments[0].scrollIntoView(true);", suggestions[0])
        suggestions[0].click()
        print("✅ Selected first location suggestion")
    else:
        print("⚠️ No suggestions found, retrying...")
except Exception as e:
    print("❌ Failed to enter/select location:", e)
    driver.quit()
    exit()

# ---------- STEP 5: CLICK CONFIRM ----------
try:
    confirm_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Confirm']"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", confirm_btn)
    time.sleep(0.5)
    confirm_btn.click()
    print("✅ Confirmed location")
    time.sleep(5)
except Exception as e:
    print("❌ Failed to confirm location:", e)
    driver.quit()
    exit()

# ---------- STEP 6: SEARCH FOR PRODUCT ----------
try:
    search_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input.Pke_EE[placeholder*='Search in Flipkart Minutes']"))
    )
    search_input.click()
    search_input.send_keys(SEARCH_QUERY)
    time.sleep(0.5)
    search_input.send_keys(Keys.ENTER)
    print(f"🔍 Searching for: {SEARCH_QUERY}")
except Exception as e:
    print("❌ Failed to perform search:", e)
    driver.quit()
    exit()

# ---------- STEP 7: WAIT & EXTRACT PRODUCTS ----------
time.sleep(5)
products = []
try:
    product_cards = driver.find_elements(By.CSS_SELECTOR, "div.VPqDeq div[style*='padding: 16px']")[:12]
    print(f"🛒 Found {len(product_cards)} product cards")

    for card in product_cards:
        try:
            name = card.find_element(By.XPATH, ".//a").text
        except:
            name = ""
        try:
            price = card.find_element(By.XPATH, ".//div[contains(text(),'₹')]").text
        except:
            price = ""
        try:
            img = card.find_element(By.TAG_NAME, "img").get_attribute("src")
        except:
            img = ""
        try:
            discount = card.find_element(By.XPATH, ".//*[contains(text(),'%') or contains(text(),'Off')]").text
        except:
            discount = ""
        products.append({
            "name": name.strip(),
            "price": price.strip(),
            "discount": discount.strip(),
            "image_url": img
        })
except Exception as e:
    print("⚠️ Product extraction failed:", e)

# ---------- STEP 8: SHOW RESULTS ----------
print(f"\n✅ Extracted {len(products)} products\n")
for i, p in enumerate(products[:10], 1):
    print(f"{i}. {p['name']} - {p['price']} | {p['discount']}")
    print(f"   🖼️ {p['image_url']}\n")

if products:
    pd.DataFrame(products).to_csv(f"flipkart_minutes_{SEARCH_QUERY}.csv", index=False)
    print(f"💾 Saved as flipkart_minutes_{SEARCH_QUERY}.csv")

driver.quit()
print("🎯 Done.")
