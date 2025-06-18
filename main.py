from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import time, os, random

NUM_SEARCHES = 30
QUERIES = [
    "news", "weather", "AI", "Python programming", "football", "movies 2025",
    "Microsoft Edge", "tech news", "meme", "how to cook pasta", "Elon Musk",
    "machine learning", "stock market", "cat videos", "dog facts", "fitness tips",
    "travel hacks", "Java vs Python", "moon landing", "latest games", "RTX 5090",
    "NASA news", "coding interview tips", "best mobile phones", "climate change",
    "mystery movies", "GTA 6 release", "OpenAI", "productivity hacks", "linux distros"
]

"""!!!!!!!!!!!!!!!! Change these acccording to your system !!!!!!!!!!!!!!!!"""
timeout = 5 # seconds to wait for page load
your_username = "yatharth"  # Replace with your actual username of the system

if os.name == 'nt': # Windows
    user_data_dir = f"C:/Users/{your_username}/AppData/Local/Microsoft/Edge/User Data/Default" # Replace with your actual profile path
elif os.name == 'posix': # Linux
    user_data_dir = f"/home/{your_username}/.config/microsoft-edge/Default"  # Replace with your actual profile path
else:
    raise Exception("Unsupported OS. Please update the user_data_dir path accordingly.") 

# Specify Edge exec/binary location
if os.name == 'nt': # Windows
    exec_path= r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" # Replace with your actual profile path
else: # Linux
    exec_path = "/usr/bin/microsoft-edge-stable" # Replace with your actual profile path


def setup_driver():
        """Set up and configure the WebDriver"""
        edge_options = Options()
        
        # Add common options to avoid detection
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        edge_options.add_argument("--disable-extensions")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option("useAutomationExtension", False)
        edge_options.add_experimental_option("detach", True)
        
        # Set user agent
        edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) edge/119.0.0.0 Safari/537.36")
        
        # Use user data directory for session persistence
        edge_options.add_argument(f"--user-data-dir={user_data_dir}")

        # Use user Edge exec/binary location
        edge_options.binary_location = exec_path
        
        # Initialize the driver
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        driver.set_window_size(1280, 800)
        
        # Set page load timeout
        driver.set_page_load_timeout(timeout)
        
        # Disable webdriver detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

# if already logged in to whatsapp then no need to login again this way
driver = setup_driver()

# Open first tab and perform an initial search
driver.get("https://bing.com/")
time.sleep(3)

# Function to perform a single search in a tab
def search_in_tab(query, tab_index):
    driver.switch_to.window(driver.window_handles[tab_index])
    try:
        search_box = WebDriverWait(driver, timeout).until(
            lambda d: d.find_element(By.NAME, "q")
        )
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
    except Exception as e:
        print(f"[!] Error in tab {tab_index}: {e}")

# Open new tabs and perform search
for i in range(1, NUM_SEARCHES):
    query = random.choice(QUERIES)
    driver.execute_script("window.open('https://bing.com');")
    time.sleep(0.7)  # slight delay between tab openings
    search_in_tab(query, i)

# Final sleep to let all tabs finish
time.sleep(10)

print("[✓] All searches completed. You can now close the browser.")