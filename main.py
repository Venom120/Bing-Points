import os
import json
import time
import random
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# --- Constants ---
CONFIG_FILE = "config.json"
LOG_FILE = "bing_points.log"

# --- Default Configuration ---
DEFAULT_CONFIG = {
    "profile_path": "",
    "driver_path": "",
    "binary_path": "",
    "headless": True,
    "num_searches": 10,
    "timeout": 10,
    "do_searches": True,
    "do_offers": False
}

# --- Logging Setup ---
def setup_logging():
    """Sets up file-based logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'),
            logging.StreamHandler() # Also print to console/terminal
        ]
    )
    logging.info("Logging initialized.")

# --- Main Application Class ---
class BingPointsApp(tk.Tk):
    """
    Main Tkinter application window for the Bing Points Bot.
    Handles configuration, UI, and launching the bot logic.
    """
    def __init__(self):
        super().__init__()
        self.title("Bing Points Bot")
        self.geometry("700x450")
        self.minsize(700, 450)
        
        # Prevent resizing
        self.resizable(True, True)

        self.config = self.load_config()
        self.vars = {
            "profile_path": tk.StringVar(value=self.config.get("profile_path")),
            "driver_path": tk.StringVar(value=self.config.get("driver_path")),
            "binary_path": tk.StringVar(value=self.config.get("binary_path")),
            "headless": tk.BooleanVar(value=self.config.get("headless")),
            "num_searches": tk.IntVar(value=self.config.get("num_searches")),
            "timeout": tk.IntVar(value=self.config.get("timeout")),
            "do_searches": tk.BooleanVar(value=self.config.get("do_searches")),
            "do_offers": tk.BooleanVar(value=self.config.get("do_offers")),
            "status": tk.StringVar(value="Ready. Fill settings and click Run.")
        }
        
        self.driver: webdriver.Edge | None = None # Explicitly type hint
        self.create_widgets()

    def load_config(self):
        """Loads configuration from JSON, merging with defaults."""
        logging.info(f"Loading config from {CONFIG_FILE}")
        if not os.path.exists(CONFIG_FILE):
            logging.warning("Config file not found. Creating with defaults.")
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                saved_config = json.load(f)
            # Merge defaults with saved config to ensure all keys exist
            config = DEFAULT_CONFIG.copy()
            config.update(saved_config)
            return config
        except json.JSONDecodeError:
            logging.error("Failed to decode config.json. Using defaults.")
            return DEFAULT_CONFIG

    def save_config(self):
        """Saves current settings from UI to config.json."""
        logging.info("Saving configuration...")
        current_config = {key: var.get() for key, var in self.vars.items() if key != "status"}
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(current_config, f, indent=4)
            self.vars["status"].set("Configuration saved.")
            logging.info("Configuration saved successfully.")
        except Exception as e:
            self.show_error("Save Error", f"Failed to save config: {e}")

    def create_widgets(self):
        """Creates and lays out all UI elements."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=1) # Allow main_frame's column to expand
        main_frame.rowconfigure(0, weight=0) # Path Settings row
        main_frame.rowconfigure(1, weight=1) # Bot Settings row (can expand vertically)
        main_frame.rowconfigure(2, weight=0) # Info Note row
        main_frame.rowconfigure(3, weight=0) # Controls row

        # --- Path Settings ---
        path_frame = ttk.LabelFrame(main_frame, text="Path Settings", padding="10")
        path_frame.grid(row=0, column=0, sticky="ew", pady=5) # Use grid for path_frame
        path_frame.columnconfigure(1, weight=1) # Allow the entry column to expand

        self.create_path_entry(path_frame, "Profile Path:", "profile_path", self.select_profile_path, 0)
        self.create_path_entry(path_frame, "Driver Path (Optional):", "driver_path", self.select_driver_path, 1)
        self.create_path_entry(path_frame, "Binary Path (Optional):", "binary_path", self.select_binary_path, 2)

        # --- Bot Settings ---
        settings_frame = ttk.LabelFrame(main_frame, text="Bot Settings", padding="10")
        settings_frame.grid(row=1, column=0, sticky="ew", pady=5) # Use grid for settings_frame
        # Options
        options_frame = ttk.Frame(settings_frame)
        options_frame.pack(fill="x", expand=True) # Allow options_frame to expand
        ttk.Checkbutton(options_frame, text="Run Headless (in background)", variable=self.vars["headless"]).pack(side="left", padx=5)
        ttk.Checkbutton(options_frame, text="Perform Searches", variable=self.vars["do_searches"]).pack(side="left", padx=5)
        ttk.Checkbutton(options_frame, text="Collect Offers", variable=self.vars["do_offers"]).pack(side="left", padx=5)
        
        # Numeric settings
        numeric_frame = ttk.Frame(settings_frame)
        numeric_frame.pack(fill="x", pady=5, expand=True) # Allow numeric_frame to expand
        ttk.Label(numeric_frame, text="Number of Searches:").pack(side="left", padx=5)
        ttk.Spinbox(numeric_frame, from_=1, to=20, width=5, textvariable=self.vars["num_searches"]).pack(side="left", padx=5)
        ttk.Label(numeric_frame, text="Page Timeout (sec):").pack(side="left", padx=5)
        ttk.Spinbox(numeric_frame, from_=5, to=60, width=5, textvariable=self.vars["timeout"]).pack(side="left", padx=5)

        # --- Info Note ---
        info_label = ttk.Label(main_frame,
                               text="Important: Ensure you are logged into your Microsoft account in the Edge profile you select.",
                               font=("TkDefaultFont", 9, "italic")) # Removed wraplength
        info_label.grid(row=2, column=0, sticky="ew", pady=(5, 10)) # Use grid for info_label

        # --- Controls ---
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, sticky="ew", pady=5) # Use grid for control_frame
        control_frame.columnconfigure(0, weight=1) # Allow space between buttons to expand
        
        self.run_button = ttk.Button(control_frame, text="Run Bot", command=self.start_bot_thread)
        self.run_button.pack(side="right", padx=5)
        
        self.save_button = ttk.Button(control_frame, text="Save Settings", command=self.save_config)
        self.save_button.pack(side="right", padx=5)

        # --- Status Bar ---
        status_bar = ttk.Frame(self, relief="sunken", padding=(5, 2))
        status_bar.pack(side="bottom", fill="x")
        ttk.Label(status_bar, textvariable=self.vars["status"]).pack(side="left", fill="x", expand=True) # Allow status label to expand

    def create_path_entry(self, parent, label_text, var_key, browse_command, row):
        """Helper to create a label, entry, and browse button row."""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        entry = ttk.Entry(parent, textvariable=self.vars[var_key]) # Removed fixed width
        entry.grid(row=row, column=1, sticky="ew", padx=5)
        ttk.Button(parent, text="Browse", command=browse_command).grid(row=row, column=2, sticky="e", padx=5)
        parent.columnconfigure(1, weight=1) # Ensure the entry column expands
        ttk.Button(parent, text="Browse", command=browse_command).grid(row=row, column=2, sticky="e", padx=5)
        parent.columnconfigure(1, weight=1)

    def get_default_user_data_dir(self):
        """Gets the default Edge user data directory for the OS."""
        if os.name == 'nt': # Windows
            appdata = os.getenv('APPDATA')
            if appdata:
                return os.path.abspath(os.path.join(appdata, "..", "Local", "Microsoft", "Edge", "User Data", "Default"))
        else: # Linux
            return os.path.expanduser("~/.config/microsoft-edge/Default")
        return None

    def select_profile_path(self):
        """Opens file dialog to select the Edge Profile folder."""
        default_dir = self.get_default_user_data_dir()
        path = filedialog.askdirectory(
            title="Select Edge User Data Folder (e.g., 'User Data' or a specific profile 'Profile 1')",
            initialdir=default_dir
        )
        if path:
            self.vars["profile_path"].set(path)
            logging.info(f"User selected profile path: {path}")

    def select_driver_path(self):
        """Opens file dialog to select the msedgedriver executable."""
        file_type = [("Edge Driver", "msedgedriver.exe")] if os.name == "nt" else [("Edge Driver", "msedgedriver")]
        path = filedialog.askopenfilename(
            title="Select msedgedriver",
            filetypes=file_type
        )
        if path:
            self.vars["driver_path"].set(path)
            logging.info(f"User selected driver path: {path}")

    def select_binary_path(self):
        """Opens file dialog to select the msedge executable."""
        file_type = [("Edge Executable", "msedge.exe")] if os.name == "nt" else [("Edge Executable", "microsoft-edge-stable")]
        path = filedialog.askopenfilename(
            title="Select Edge Executable (msedge.exe or microsoft-edge-stable)",
            filetypes=file_type
        )
        if path:
            self.vars["binary_path"].set(path)
            logging.info(f"User selected binary path: {path}")

    # --- UI Status & Error Helpers ---
    def log_status(self, message):
        """Updates status bar and logs to file."""
        self.vars["status"].set(message)
        logging.info(message)

    def show_error(self, title, message):
        """Logs error and shows a Tkinter error messagebox."""
        logging.error(message)
        # Ensure messagebox runs on the main UI thread
        self.after(0, lambda: messagebox.showerror(title, message))

    def show_info(self, title, message):
        """Logs info and shows a Tkinter info messagebox."""
        logging.info(message)
        self.after(0, lambda: messagebox.showinfo(title, message))

    def _prompt_for_driver_path(self):
        """
        Shows an error and opens the file dialog to select the driver path.
        This method MUST be called on the main UI thread (e.g., via self.after).
        """
        self.show_error("Driver Error", "webdriver-manager failed and no valid driver path is set. Please select 'msedgedriver' manually.")
        self.select_driver_path() # Open file dialog
        # Re-enable buttons so user can save the new path and try again
        self.run_button.config(state="normal")
        self.save_button.config(state="normal")
        self.log_status("Ready. Please save settings and try again.")

    def _finalize_run(self):
        """
        Thread-safe method to re-enable UI elements after a bot run.
        This is called from the finally block of the worker thread.
        """
        # Re-enable buttons if they are disabled
        self.run_button.config(state="normal")
        self.save_button.config(state="normal")
        self.log_status("Bot run finished. Ready for next run.")

    # --- Bot Logic Threading ---
    def start_bot_thread(self):
        """Starts the main bot logic in a separate thread to keep UI responsive."""
        self.run_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.log_status("Starting bot...")
        
        # Create a copy of config for the thread
        self.thread_config = {key: var.get() for key, var in self.vars.items() if key != "status"}
        
        bot_thread = threading.Thread(target=self.run_bot_logic, daemon=True)
        bot_thread.start()

    def run_bot_logic(self):
        """The main Selenium automation logic. Runs in a thread."""
        try:
            # --- 1. Setup Driver ---
            self.log_status("[1/5] Setting up Edge driver...")
            self.driver = self.setup_driver()
            if not self.driver:
                # setup_driver() will have already shown an error or prompted user
                raise Exception("Failed to initialize WebDriver. Check logs and settings.")
            
            self.log_status("[2/5] Navigating to Bing.com...")
            self.driver.get("https://www.bing.com/")
            time.sleep(3) # Wait for page to load

            # --- 2. Get Initial Points ---
            self.log_status("[3/5] Retrieving initial points...")
            points_before = self.get_current_points()
            self.log_status(f"Points before: {points_before}")
            
            initial_tab = self.driver.current_window_handle

            # --- 3. Perform Searches ---
            if self.thread_config["do_searches"]:
                self.log_status("[4/5] Performing trending searches...")
                self.perform_trending_searches(initial_tab)
                self.driver.switch_to.window(initial_tab)
                self.driver.get("https://www.bing.com/") # Refresh
                time.sleep(3)
            else:
                self.log_status("[4/5] Skipping searches.")

            # --- 4. Collect Offers ---
            if self.thread_config["do_offers"]:
                self.log_status("[5/5] Collecting special offers...")
                self.collect_special_offers(initial_tab)
                self.driver.switch_to.window(initial_tab)
                self.driver.get("https://www.bing.com/") # Refresh
                time.sleep(3)
            else:
                self.log_status("[5/5] Skipping offers.")

            # --- 5. Get Final Points ---
            self.log_status("Retrieving final points...")
            points_after = self.get_current_points()
            self.log_status(f"Points after: {points_after}")

            total_gained = points_after - points_before
            self.log_status(f"Total points gained: {total_gained}")
            self.show_info("Bot Finished", f"Bot run complete.\n\nPoints Gained: {total_gained}\nPoints Before: {points_before}\nPoints After: {points_after}")

        except Exception as e:
            self.show_error("Bot Error", f"An error occurred during bot operation:\n{e}")
        finally:
            # --- 6. Cleanup ---
            if self.driver:
                if self.thread_config["headless"]:
                    self.log_status("Headless mode: Quitting driver.")
                    self.driver.quit()
                else:
                    self.log_status("Browser left open. Close UI to quit driver (if not detached).")
            
            self.driver = None
            
            # Schedule the UI update on the main thread to avoid race conditions.
            self.after(0, self._finalize_run)

    def on_closing(self):
        """Handle window close event."""
        if self.driver:
            logging.info("UI closing, quitting active driver.")
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(f"Error while quitting driver on close: {e}")
        self.destroy()

    # --- Selenium Core Functions ---
    def setup_driver(self):
        """Sets up and configures the WebDriver based on UI settings."""
        try:
            cfg = self.thread_config
            edge_options = Options()
            
            if cfg["headless"]:
                edge_options.add_argument("--headless=new")
            
            # Anti-detection options
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_argument("--disable-extensions")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option("useAutomationExtension", False)
            edge_options.add_experimental_option("detach", not cfg["headless"]) # Keep open if not headless
            
            edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) edge/119.0.0.0 Safari/537.36")
            
            # Use user-selected profile path
            if not cfg["profile_path"] or not os.path.exists(cfg["profile_path"]):
                self.show_error("Profile Error", f"Profile path is invalid or not set:\n{cfg['profile_path']}")
                return None
            edge_options.add_argument(f"--user-data-dir={cfg['profile_path']}") 

            # Use user-selected binary location (if provided)
            if cfg["binary_path"] and os.path.exists(cfg["binary_path"]):
                edge_options.binary_location = cfg["binary_path"]
            
            # Initialize the driver service
            service = None
            try:
                self.log_status("Attempting driver install via webdriver-manager...")
                service = Service(EdgeChromiumDriverManager().install())
                self.log_status("webdriver-manager successful.")
            
            # Catch ALL exceptions from webdriver-manager
            except Exception as e_manager: 
                self.log_status(f"webdriver-manager failed: {e_manager}. Trying saved path.")
                
                user_driver_path = cfg.get("driver_path")
                if not user_driver_path or not os.path.exists(user_driver_path):
                    # webdriver-manager failed AND user path is bad.
                    self.log_status("User-defined driver path is also invalid. Prompting user.")
                    self.after(0, self._prompt_for_driver_path) # Schedule prompt on main thread
                    return None # Stop the current bot run
                
                # webdriver-manager failed, BUT user path is valid.
                self.log_status(f"Using saved driver path: {user_driver_path}")
                service = Service(executable_path=user_driver_path)

            if not service:
                # This will be hit if the prompt was scheduled
                self.log_status("Could not initialize driver service.")
                return None
                
            driver = webdriver.Edge(service=service, options=edge_options)
            driver.set_window_size(1280, 800)
            driver.set_page_load_timeout(cfg["timeout"])
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        # This outer try/except catches errors in setting options, paths, etc.
        except Exception as e:
            self.show_error("Driver Setup Failed", f"A critical error occurred during driver setup:\n{e}")
            return None

    def get_current_points(self):
        """Retrieves the current point balance from the Bing page."""
        if not self.driver:
            self.log_status("[WARN] Driver not available. Cannot get points.")
            return 0

        try:
            points_element = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="rh_rwm"]/div/span[1]'))
            )
            points_str = points_element.text.replace(',', '')
            return int(points_str)
        except Exception as e:
            self.log_status(f"[WARN] Could not retrieve points: {e}. Defaulting to 0.")
            return 0

    def get_trending_searches(self):
        """Extracts trending search titles from Google Trends."""
        if not self.driver:
            self.log_status("[WARN] Driver not available. Cannot get trends.")
            return [] # Return empty list

        self.log_status("Getting trending searches from Google...")
        try:
            self.driver.get("https://trends.google.com/trending?geo=IN")
            timeout = self.thread_config["timeout"]
            
            tbody_element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="trend-table"]/div[1]/table/tbody[2]'))
            )
            tr_elements = tbody_element.find_elements(By.TAG_NAME, 'tr')
            
            trending_searches = []
            for i, tr in enumerate(tr_elements):
                if i >= self.thread_config["num_searches"]:
                    break
                try:
                    search_title_element = tr.find_element(By.XPATH, './td[2]/div[1]')
                    term = search_title_element.text
                    trending_searches.append(term)
                    self.log_status(f"Extracted trend: {term}")
                except Exception as e_row:
                    self.log_status(f"[WARN] Could not extract a search title: {e_row}")
            
            if trending_searches:
                return trending_searches

        except Exception as e:
            self.log_status(f"[WARN] Error extracting trending searches: {e}")
        
        # Fallback list
        self.log_status("[WARN] Using fallback search list.")
        return [
            "news", "weather", "sports", "technology", "entertainment",
            "health", "science", "finance", "travel", "food",
            "music", "movies", "books", "fashion", "gaming"
        ][:self.thread_config["num_searches"]] # Ensure list is correct length

    def perform_trending_searches(self, initial_tab):
        """Performs Bing searches based on trending topics."""
        if not self.driver:
            self.log_status("[WARN] Driver not available. Skipping searches.")
            return

        trending_searches = self.get_trending_searches()
        total_searches = len(trending_searches)
        self.log_status(f"Retrieved {total_searches} trending searches.")

        for i, search_term in enumerate(trending_searches):
            self.log_status(f"Performing search {i+1}/{total_searches}: {search_term}")
            
            try:
                original_handles = self.driver.window_handles
                self.driver.execute_script("window.open('https://www.bing.com/', '_blank');")
                time.sleep(1.25)
                
                new_tab_handle = [h for h in self.driver.window_handles if h not in original_handles][0]
                self.driver.switch_to.window(new_tab_handle)
                time.sleep(random.uniform(1, 3))

                search_box = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
                    EC.presence_of_element_located((By.NAME, "q"))
                )
                search_box.send_keys(search_term)
                search_box.send_keys(Keys.RETURN)
                self.log_status(f"Searched for '{search_term}'.")
                time.sleep(random.uniform(3, 5))

            except Exception as e:
                self.log_status(f"[WARN] Error during search for '{search_term}': {e}")
            
            finally:
                # Close current tab and switch back
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(initial_tab)
                time.sleep(0.5)

    def find_offers(self):
        """Finds clickable offer elements in the rewards iframe."""
        if not self.driver:
            self.log_status("[WARN] Driver not available. Cannot find offers.")
            return []

        offers = []
        try:
            all_offers_div = self.driver.find_elements(By.XPATH, '//*[@class="flyout_control_halfUnit"]')[-1]
            all_offers = all_offers_div.find_elements(By.XPATH, './div')
            
            for div in all_offers:
                try:
                    aria_label = div.get_attribute("aria-label")
                    div_id = div.get_attribute('id')
                    
                    if div_id == "exclusive_promo_cont":
                        check_alt = div.find_element(By.TAG_NAME, 'img').get_attribute('alt')
                        if check_alt == "Locked Image":
                            a_tag = div.find_element(By.TAG_NAME, 'a')
                            offers.append((a_tag, str(aria_label).split("-")[0].strip()))
                    elif aria_label is not None and "Offer not Completed" in aria_label:
                        a_tag = div.find_element(By.TAG_NAME, 'a')
                        offers.append((a_tag, aria_label.split("-")[0].strip()))
                except Exception as e_offer:
                    self.log_status(f"[WARN] Error parsing one offer: {e_offer}")
            
            self.log_status(f"Found {len(offers)} offers.")
        except Exception as e_find:
            self.show_error("Offer Error", f"Could not find offers container: {e_find}")
        return offers

    def collect_special_offers(self, initial_tab):
        """Clicks through all available special offers."""
        if not self.driver:
            self.log_status("[WARN] Driver not available. Skipping offers.")
            return

        self.log_status("Checking for special offers...")
        try:
            # Open sidebar
            sidebar_button = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="rh_rwm"]/div/div'))
            )
            sidebar_button.click()
            time.sleep(2)

            # Switch to iframe
            iframe_element = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="rewid-f"]/iframe'))
            )
            self.driver.switch_to.frame(iframe_element)
            
            offers = self.find_offers()
            new_tab_handles = []

            for i, (offer_element, offer_name) in enumerate(offers):
                self.log_status(f"Clicking offer {i+1}/{len(offers)}: {offer_name}")
                try:
                    original_handles = self.driver.window_handles
                    offer_element.click()
                    time.sleep(2)
                    
                    new_handles = [h for h in self.driver.window_handles if h not in original_handles]
                    if new_handles:
                        new_tab_handles.append(new_handles[0])
                        self.log_status(f"Opened new tab for offer {i+1}.")
                    else:
                        self.log_status(f"[WARN] No new tab found for offer {i+1}.")
                except Exception as e_click:
                    self.log_status(f"[WARN] Error clicking offer {i+1} ({offer_name}): {e_click}")
            
            # Switch back from iframe
            self.driver.switch_to.default_content()
            time.sleep(1.25)
            
            # Process new tabs
            for i, handle in enumerate(new_tab_handles):
                try:
                    self.driver.switch_to.window(handle)
                    self.log_status(f"Switched to tab for offer {i+1}.")
                    time.sleep(random.uniform(3, 5))
                    self.driver.close()
                    self.log_status(f"Closed tab for offer {i+1}.")
                except Exception as e_tab:
                    self.log_status(f"[WARN] Error processing tab for offer {i+1}: {e_tab}")
                finally:
                    self.driver.switch_to.window(initial_tab) # Ensure we're back

        except Exception as e_sidebar:
            self.show_error("Offer Error", f"Could not process special offers: {e_sidebar}")
        finally:
            # Always ensure we switch back to default content and initial tab
            try:
                self.driver.switch_to.default_content()
            except: pass
            try:
                self.driver.switch_to.window(initial_tab)
            except: pass
        
        self.log_status("Finished processing offers.")

# --- Main Execution ---
if __name__ == "__main__":
    setup_logging()
    try:
        app = BingPointsApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing) # Handle window close
        app.mainloop()
    except Exception as e:
        logging.critical(f"A critical error occurred: {e}", exc_info=True)
        messagebox.showerror("Fatal Error", f"A fatal error occurred and the app must close:\n{e}")