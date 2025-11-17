from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
# import pandas as pd



# ---------- CONFIG ----------
LOCATION = "Bengaluru"
SEARCH_QUERY = "onion"

# ---------- SETUP ----------
driver = webdriver.Chrome()
driver.maximize_window()
driver.delete_all_cookies()
driver.get("https://www.bigbasket.com/")
wait = WebDriverWait(driver, 30)
print("🌐 BigBasket opened successfully")

# ---------- STEP 1: Click 'Select Location' ----------
try:
    print("📍 Waiting for 'Select Location' button...")
    location_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Select Location')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", location_btn)
    time.sleep(1)
    location_btn.click()
    print("✅ Clicked 'Select Location' button.")
except Exception as e:
    print("❌ Location button not found:", e)

# ---------- STEP 2: Type in Location ----------
try:
    print("⌛ Waiting for location search input...")
    location_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search for area or street name']"))
    )
    location_input.click()
    time.sleep(1)
    location_input.send_keys(LOCATION)
    print(f"✅ Typed location: {LOCATION}")

    # Wait for suggestion list
    suggestion = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "li.AddressDropdown___StyledMenuItem-sc-i4k67t-7"))
    )
    suggestion.click()
    print("✅ Selected first suggestion.")
except Exception as e:
    print("❌ Error selecting location:", e)

# ---------- STEP 3: Wait for homepage to reload ----------
time.sleep(3)

# ---------- STEP 4: Search Product ----------
try:
    print("🔎 Searching for product...")
    search_box = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search for Products']"))
    )
    search_box.click()
    search_box.send_keys(SEARCH_QUERY)
    search_box.send_keys(Keys.ENTER)
    print(f"✅ Searching for '{SEARCH_QUERY}'")
except Exception as e:
    print("❌ Search box not found:", e)

# ---------- STEP 5: Wait for product grid ----------
time.sleep(5)
try:
    product_cards = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.grid-cols-9 > li"))
    )
    print(f"🛒 Found {len(product_cards)} products for '{SEARCH_QUERY}'")
except Exception as e:
    print("❌ Product cards not found:", e)
    product_cards = []

# ---------- STEP 6: Extract Product Data ----------
products = []

for card in product_cards:
    try:
        name = card.find_element(By.CSS_SELECTOR, "h3.block").text
    except:
        name = ""
    try:
        brand = card.find_element(By.CSS_SELECTOR, "span.BrandName___StyledLabel2-sc-hssfrl-1").text
    except:
        brand = ""
    try:
        pack = card.find_element(By.CSS_SELECTOR, "span.Label-sc-15v1nk5-0.gJxZPQ.truncate").text
    except:
        pack = ""
    try:
        price = card.find_element(By.CSS_SELECTOR, "span.Pricing___StyledLabel-sc-pldi2d-1").text
    except:
        price = ""
    try:
        mrp = card.find_element(By.CSS_SELECTOR, "span.Pricing___StyledLabel2-sc-pldi2d-2").text
    except:
        mrp = ""
    try:
        discount = card.find_element(By.XPATH, ".//span[contains(text(),'% OFF')]").text
    except:
        discount = ""
    try:
        image = card.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
    except:
        image = ""
    try:
        url = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
    except:
        url = ""

    products.append({
        "name": name.strip(),
        "brand": brand.strip(),
        "pack": pack.strip(),
        "price": price.strip(),
        "mrp": mrp.strip(),
        "discount": discount.strip(),
        "image_url": image,
        "product_url": url
    })

# ---------- STEP 7: Preview Extracted Products ----------
print(f"\n✅ Total extracted: {len(products)} products\n")
for i, p in enumerate(products[:10], start=1):
    print(f"{i}. {p['brand']} {p['name']} ({p['pack']})")
    print(f"   💰 Price: {p['price']} | MRP: {p['mrp']} | Discount: {p['discount']}")
    print(f"   🖼️ {p['image_url']}")
    print(f"   🔗 {p['product_url']}\n")

# ---------- STEP 8: Save to CSV ----------
# if products:
#     pd.DataFrame(products).to_csv(f"bigbasket_{SEARCH_QUERY}_products.csv", index=False)
#     print(f"💾 Saved to bigbasket_{SEARCH_QUERY}_products.csv")

driver.quit()
print("🎯 Done.")
