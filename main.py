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

    try:
        child_divs = driver.find_elements(By.XPATH, '//*[@id="bingRewards"]/div/div[7]/div')
        child_divs = driver.find_elements(By.XPATH, '//*[@id="bingRewards"]/div/div[8]/div')
    except Exception as e:
        child_divs = []
        print("[!] Could not find the child divs container. Skipping link collection.")
    print(f"[INFO] Found {len(child_divs)} child divs in the container.")
            
    # Collect links from specific divs
    special_links = []
    for div in child_divs:
        div_class = div.get_attribute('class')
        div_id = div.get_attribute('id')
        if div_class == "promo_cont slim" or (div_class == "promo_cont " and div_id == "exclusive_promo_cont"):
            a_tags = div.find_elements(By.TAG_NAME, 'a')
            for a in a_tags:
                href = a.get_attribute('href')
                if href:
                    special_links.append(href)
    print(f"[INFO] Found {len(special_links)} special links.")
    # Find the container with the links inside the iframe
    try:
        links_container = WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.XPATH, '//*[@id="bingRewards"]/div/div[5]/div/a/div/div[2]/div[3]')
        )
        links_container = WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.XPATH, '//*[@id="bingRewards"]/div/div[6]/div/a/div/div[2]/div[3]')
        )
    except Exception as e:
        links_container = None
        print("[!] Could not find the links container.")
    links=[]
    if links_container is not None:
        # Find all links within the container
        reward_links = links_container.find_elements(By.TAG_NAME, 'a')
        links.extend([link.get_attribute('href') for link in reward_links]) # Get all links
    links.extend(special_links)
    # Switch back to the default content
    driver.switch_to.default_content()
    for i in range(len(links)):
        try:
            driver.get(links[i])
            print(f"[OK] Opened link {i+1} by navigating to URL.")
            time.sleep(random.uniform(1, 3)) # Stay on the page for a bit
        except Exception as e:
            print(f"[!] Could not navigate to link {i+1}: {e}")
            print(f"[!] Skipping link {i+1}.")
            continue # Skip to the next iteration if navigation fails
        finally:
            time.sleep(random.uniform(3, 5))

    # After opening all links, check points again
    driver.get("https://www.bing.com/")
    time.sleep(2) # Wait for page to load

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