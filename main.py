from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time, os, random
import getpass
  
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

if os.name == "nt": # Windows
    driver_path="msedgedriver.exe"
else: # Linux
    driver_path="/bin/msedgedriver"




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
            if os.name == "nt": # Windows
                service = Service(executable_path=driver_path)
            else: # Linux
                service = Service(executable_path=driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)
        driver.set_window_size(1280, 800)
        
        # Set page load timeout
        driver.set_page_load_timeout(timeout)
        
        # Disable webdriver detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

def find_searches(driver):
    # Find the container with the links inside the iframe
    searches = []
    container_links_check = driver.find_element(By.XPATH, '//*[@class="search_earn_card"]/div')
    if container_links_check.get_attribute('aria-label') == "Offer not Completed":
        links_container = driver.find_element(By.XPATH, '//*[@class="search_earn_card"]/div/a/div/div[2]/div[3]')
        # Find all links within the container
        reward_links = links_container.find_elements(By.TAG_NAME, 'a')
        searches.extend([link.get_attribute('href') for link in reward_links])
        print(f"[INFO] Found {len(reward_links)} links.")
    else:
        print("[!] No more points to gain from searches today.")
    return searches

def find_offers(driver):
    offers = []
    all_offers = driver.find_elements(By.XPATH, '//*[@class="flyout_control_halfUnit"]/div')
            
    for div in all_offers:
        aria_label = div.get_attribute('aria-label')
        div_id = div.get_attribute('id')
        if div_id == "exclusive_promo_cont":
            # check if this offer is completed or not
            check_alt = div.find_element(By.TAG_NAME, 'img').get_attribute('alt')
            if check_alt == "Locked Image":
                a_tags = div.find_element(By.TAG_NAME, 'a')
                offers.append(a_tags.get_attribute('href'))
        elif aria_label is not None and "Offer not Completed" in aria_label:
            a_tags = div.find_element(By.TAG_NAME, 'a')
            offers.append(a_tags.get_attribute('href'))
    print(f"[INFO] Found {len(offers)} offers.")
    return offers

def open_links(driver, links):
    for i in range(len(links)):
        try:
            driver.get(links[i])
            print(f"[OK] Opened link {i+1} by navigating to URL.")
            time.sleep(random.uniform(3, 5)) # Stay on the page for a bit
        except Exception as e:
            print(f"[!] Could not navigate to link {i+1}: {e}")
            print(f"[!] Skipping link {i+1}.")
            continue # Skip to the next iteration if navigation fails
    
def start_loop(driver):
    # Open bing.com
    driver.get("https://www.bing.com/")
    time.sleep(3) # Wait for page to load

    points_before = WebDriverWait(driver, timeout).until(
        lambda d: d.find_element(By.XPATH, '//*[@id="rh_rwm"]/div/span[1]')
    ).text
    print(f"[INFO] Points before: {points_before}")

    # Open sidebar
    sidebar_button = WebDriverWait(driver, timeout).until(
        lambda d: d.find_element(By.XPATH, '//*[@id="rh_rwm"]/div/div')
    )
    sidebar_button.click()
    time.sleep(2) # Wait for sidebar to open and content to load

    # Switch to the iframe
    iframe_element = WebDriverWait(driver, timeout).until(
        lambda d: d.find_element(By.XPATH, '//*[@id="rewid-f"]/iframe')
    )
    driver.switch_to.frame(iframe_element)

    links = []
    links.extend(find_searches(driver))
    links.extend(find_offers(driver))

    # Switch back to the default content
    driver.switch_to.default_content()

    # open_links(driver, links)

    # After opening all links, check points again
    driver.get("https://www.bing.com/")
    time.sleep(3) # Wait for page to load

    points_after = driver.find_element(By.XPATH, '//*[@id="rh_rwm"]/div/span[1]').text
    print(f"[INFO] Points after: {points_after}")

    return int(points_after) - int(points_before)

gained=0
driver = setup_driver()
time.sleep(2) # Wait for the driver to initialize
gained = start_loop(driver)

print("[OK] Task completed.")
print(f"\n[INFO] Points gained: {gained}")

choice = input("Press Enter to close the browser or type 'open' to keep it open: ")
if choice.lower() == 'open':
    print("[INFO] Browser will remain open.")
else:
    print("[INFO] Closed the browser.")
    driver.quit() # Close the browser