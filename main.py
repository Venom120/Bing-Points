from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time, os, random
import getpass
import re
import json
from tkinter import filedialog
import tkinter as tk

CONFIG_FILE = "config.json"
NUMBER_OF_SEARCHES=20

"""!!!!!!!!!!!!!!!! Change these acccording to your system !!!!!!!!!!!!!!!!"""
your_username = getpass.getuser()
timeout = 5 # seconds to wait for page load
profile_name = "Profile 2" # Change this to your Edge profile name if needed (can use 'Default' for the default profile)
 
if os.name == 'nt': # Windows
    appdata = os.path.dirname(os.getenv('APPDATA'))
    if appdata is None:
        raise EnvironmentError("APPDATA environment variable is not set. Please check your system configuration.")
    user_data_dir = os.path.join(appdata, "Local", "Microsoft", "Edge", "User Data", profile_name)  # Replace with your actual profile path
else: # Linux
    user_data_dir = f"/home/{your_username}/.config/microsoft-edge/Default"  # Replace with your actual profile path

# Specify Edge exec/binary location
if os.name == 'nt': # Windows
    exec_path= r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" # Replace with your actual executable path
else: # Linux
    exec_path = "/usr/bin/microsoft-edge-stable" # Replace with your actual executable path

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def get_edge_driver_path():
    config = load_config()
    driver_path = config.get("driver_path")

    if driver_path and os.path.exists(driver_path):
        print(f"[INFO] Using saved Edge driver path: {driver_path}")
        return driver_path
    else:
        root = tk.Tk()
        root.withdraw() # Hide the main window
        if os.name == "nt": # Windows
            print("[WARN] Edge driver path not found or invalid. Please select the msedgedriver.exe file.")
            file_path = filedialog.askopenfilename(
                title="Select msedgedriver.exe",
                filetypes=[("Edge Driver Executable", "msedgedriver.exe")]
            )
        else: # Linux
            print("[WARN] Edge driver path not found or invalid. Please select the msedgedriver file.")
            file_path = filedialog.askopenfilename(
                title="Select msedgedriver",
                filetypes=[("Edge Driver Bin", "msedgedriver")]
            )
        root.destroy() # Destroy the Tkinter root window
        if file_path:
            config["driver_path"] = file_path
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
                print(f"[INFO] Saved Edge driver path: {file_path}")
            return file_path
        else:
            print("[!] No Edge driver selected. Exiting.")
            exit()


def setup_driver():
    """Set up and configure the WebDriver"""
    edge_options = Options()
    
    # Add common options to avoid detection
    edge_options.add_argument("--no-sandbox") # Bypass OS security model  
    edge_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    edge_options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    edge_options.add_argument("--disable-blink-features=AutomationControlled") # Disable automation features
    edge_options.add_argument("--disable-extensions") # Disable extensions
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option("useAutomationExtension", False)
    edge_options.add_experimental_option("detach", True) # Keep the browser open after script execution

    # Set user agent
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) edge/119.0.0.0 Safari/537.36")
    
    # Use user data directory for session persistence
    edge_options.add_argument(f"--user-data-dir={user_data_dir}") 

    # Use user Edge exec/binary location
    edge_options.binary_location = exec_path
    
    # Initialize the driver
    try:
        service = Service(EdgeChromiumDriverManager().install())
    except Exception as e:
        print("[!] Error installing Edge driver")
        print("[!] Rolling back to using user defined Edge driver path.")
        service = Service(executable_path=get_edge_driver_path())
    driver = webdriver.Edge(service=service, options=edge_options)
    driver.set_window_size(1280, 800)
    
    # Set page load timeout
    driver.set_page_load_timeout(timeout)
    
    # Disable webdriver detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def get_trending_searches(driver):
    """Extracts 20(default) trending search titles from Google Trends."""
    driver.get("https://trends.google.com/trending?geo=IN")
    time.sleep(timeout)  # Wait for the page to load

    trending_searches = [] # Initialize here once
    try:
        # Updated XPath based on user's provided structure
        # Find the tbody with jsname="cC57zf" within the table with class "enOdEe-wZVHld-zg7Cn"
        tbody_element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, '//table[@class="enOdEe-wZVHld-zg7Cn"]/tbody[@jsname="cC57zf"]'))
        )
        # Find all tr elements within the tbody
        tr_elements = tbody_element.find_elements(By.TAG_NAME, 'tr')

        for i, tr in enumerate(tr_elements):
            if i >= NUMBER_OF_SEARCHES:  # Limit to 20(default) searches
                break
            try:
                # Get the second td element and then the div with class "mZ3RIc"
                search_title_element = tr.find_element(By.XPATH, './/td[2]/div[@class="mZ3RIc"]')
                trending_searches.append(search_title_element.text)
                print(f"[INFO] Extracted trend: {search_title_element.text}")
            except Exception as e:
                print(f"[!] Could not extract search title from a row: {e}")
                continue # Skip to the next row if extraction fails

    except Exception as e:
        print(f"[!] Error extracting trending searches: {e}")
        print("[!] Using a fallback list of common search terms.")
        # Fallback in case of extraction failure
        trending_searches = [
            "news", "weather", "sports", "technology", "entertainment",
            "health", "science", "finance", "travel", "food",
            "music", "movies", "books", "fashion", "gaming",
            "education", "business", "politics", "environment", "art",
            "history", "culture", "design", "fitness", "cars"
        ]
    return trending_searches


def find_offers(driver):
    offers = []
    all_offers_div = driver.find_elements(By.XPATH, '//*[@class="flyout_control_halfUnit"]')[-1]
    all_offers = all_offers_div.find_elements(By.XPATH, './div')            
    for div in all_offers:
        aria_label = div.get_attribute("aria-label")
        div_id = div.get_attribute('id')
        if div_id == "exclusive_promo_cont":
            # check if this offer is completed or not
            check_alt = div.find_element(By.TAG_NAME, 'img').get_attribute('alt')
            if check_alt == "Locked Image":
                a_tags = div.find_element(By.TAG_NAME, 'a')
                offers.append((a_tags, aria_label.split("-")[0].strip())) # Append tuple (element, offer_name)
        elif aria_label is not None and "Offer not Completed" in aria_label:
            a_tags = div.find_element(By.TAG_NAME, 'a')
            offers.append((a_tags, aria_label.split("-")[0].strip())) # Append tuple (element, offer_name)
    print(f"[INFO] Found {len(offers)} offers.")
    return offers

def perform_trending_searches(driver, initial_tab):
    trending_searches = get_trending_searches(driver)
    print(f"[INFO] Retrieved {len(trending_searches)} trending searches.")

    for i, search_term in enumerate(trending_searches):
        print(f"[INFO] Performing search {i+1}/{len(trending_searches)}: {search_term}")

        # Get current window handles before opening a new tab
        original_handles = driver.window_handles

        # Open a new tab and navigate to Bing
        driver.execute_script("window.open('https://www.bing.com/', '_blank');")
        time.sleep(2) # Give browser time to open the tab and for the handle to register

        # Get all handles after opening new tab
        all_handles_after_open = driver.window_handles

        # Find the handle that is not in the original set
        new_tab_handle = list(set(all_handles_after_open) - set(original_handles))[0]
        driver.switch_to.window(new_tab_handle)
        
        time.sleep(random.uniform(1, 3))
        
        try:
            search_box = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            print(f"[OK] Searched for '{search_term}'.")
            time.sleep(random.uniform(3, 5)) # Wait for search results to load
        except Exception as e:
            print(f"[!] Error performing search for '{search_term}': {e}")
            driver.close() # Close current problematic tab
            driver.switch_to.window(initial_tab) # Switch back to initial tab
            continue

        # Close the current (newly opened) tab after search. This is the "previous tab" where the search was just executed.
        driver.close()
        # Always switch back to the initial tab for the next iteration to maintain a consistent state.
        driver.switch_to.window(initial_tab)

def collect_special_offers(driver):
    print("[INFO] Checking for special offers...")
    # Open sidebar
    sidebar_button = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="rh_rwm"]/div/div'))
    )
    sidebar_button.click()
    time.sleep(2) # Wait for sidebar to open and content to load

    # Switch to the iframe
    iframe_element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="rewid-f"]/iframe'))
    )
    initial_tab = driver.current_window_handle # Store the initial tab handle
    driver.switch_to.frame(iframe_element)

    offers = find_offers(driver)

    if offers:
        print(f"[INFO] Found {len(offers)} special offers. Processing them...")
        new_tab_handles = []

        # Click all offers while still in the iframe
        for i, (offer_element, offer_name) in enumerate(offers):
            print(f"[INFO] Clicking offer {i+1}/{len(offers)}: {offer_name}")
            try:
                # Get current window handles before opening a new tab
                original_handles = driver.window_handles # Get handles before click
                offer_element.click()
                time.sleep(2) # Give browser time to open the tab and for the handle to register
                
                # Find the handle that is not in the original set
                all_handles_after_click = driver.window_handles
                new_handle = list(set(all_handles_after_click) - set(original_handles))
                if new_handle:
                    new_tab_handles.append(new_handle[0])
                    print(f"[OK] Opened new tab for offer {i+1}.")
                else:
                    print(f"[!] Could not open new tab for offer {i+1}. It might have opened in the current tab or failed.")
                
            except Exception as e:
                print(f"[!] Error clicking offer {i+1} ({offer_name}): {e}")
                print(f"[!] Skipping offer {i+1}.")
                continue # Skip to the next offer
        
        # Now, switch back to default content before processing new tabs
        driver.switch_to.default_content()
        time.sleep(1.25)
        print("[INFO] Switched back to default content.")
        
        # Process each new tab
        for i, handle in enumerate(new_tab_handles):
            try:
                driver.switch_to.window(handle)
                print(f"[OK] Switched to new tab for offer {i+1}.")
                time.sleep(random.uniform(3, 5)) # Stay on the page for a bit
                driver.close() # Close the new tab
                print(f"[OK] Closed tab for offer {i+1}.")
                
            except Exception as e:
                print(f"[!] Error processing new tab for offer {i+1}: {e}")
                print(f"[!] Attempting to switch back to initial tab.")
                try:
                    driver.switch_to.window(initial_tab)
                except Exception as e_switch:
                    print(f"[!] Critical: Could not switch back to initial tab: {e_switch}")
                continue
    else:
        print("[INFO] No special offers found.")
    time.sleep(random.uniform(2,3))

gained=0
driver = setup_driver()
time.sleep(2) # Wait for the driver to initialize

total_gained_points = 0
choice_yes = re.compile(r"^(yes|y)$", re.IGNORECASE)
choice_no = re.compile(r"^(no|n)$", re.IGNORECASE)
while True:
    choice_search = input("\nDo you want to collect points from trending searches? (yes/no): ").lower()
    if choice_yes.match(choice_search) or choice_no.match(choice_search):
        break
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")

count = int(input("\nHow many searches? (default=20): "))
if count:
    NUMBER_OF_SEARCHES=count
    print(f"[INFO] Will search {NUMBER_OF_SEARCHES} trends on bing!!")

while True:
    choice_offers = input("\nDo you want to collect points from special offers? (yes/no): ").lower()
    if choice_yes.match(choice_offers) or choice_no.match(choice_offers):
        break
    else:
        print("Invalid input. Please enter 'Y/N'.")

driver.get("https://www.bing.com/")
time.sleep(3) # Wait for page to load

points_before_str = "0"
try:
    points_element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="rh_rwm"]/div/span[1]'))
    )
    points_before_str = points_element.text
except Exception as e:
    print(f"[!] Could not retrieve initial points: {e}")
    print("[!] Setting points before to 0.")

points_before = int(points_before_str.replace(',', ''))
print(f"[INFO] Points before starting activities: {points_before}")

initial_tab = driver.current_window_handle # Store the initial tab handle

if choice_yes.match(choice_search):
    perform_trending_searches(driver, initial_tab)
    # Ensure we are back on the initial tab after searches
    driver.switch_to.window(initial_tab)
    driver.get("https://www.bing.com/") # Refresh to get updated points
    time.sleep(3)

if choice_yes.match(choice_offers):
    collect_special_offers(driver)
    # Ensure we are back on the initial tab after offers
    driver.switch_to.window(initial_tab)
    driver.get("https://www.bing.com/") # Refresh to get updated points
    time.sleep(3)

points_after_str = "0"
try:
    points_element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="rh_rwm"]/div/span[1]'))
    )
    points_after_str = points_element.text
except Exception as e:
    print(f"[!] Could not retrieve points after all activities: {e}")
    print("[!] Setting points after to 0.")

points_after = int(points_after_str.replace(',', ''))
print(f"[INFO] Points after all activities: {points_after}")

total_gained_points = points_after - points_before
print(f"\n[INFO] Total points gained: {total_gained_points}")

choice_close = input("Press Enter to close the browser or type 'open' to keep it open: ").lower()
if choice_close == 'open':
    print("[INFO] Browser will remain open.")
else:
    print("[INFO] Closed the browser.")
    driver.quit() # Close the browser