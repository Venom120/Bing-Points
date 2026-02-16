from cProfile import label
import os
import json
import time
import random
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
from typing import Literal

import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
# Import the specific exception
from selenium.common.exceptions import SessionNotCreatedException, StaleElementReferenceException

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
	"do_offers": False,
	"do_leetcode": False
}

# --- Logging Setup ---
def setup_logging():
	"""Sets up file-based logging using UTF-8 for file and a stdout wrapper that replaces unencodable chars."""
	import sys, io
	root_logger = logging.getLogger()
	root_logger.setLevel(logging.INFO)

	# File handler uses UTF-8
	fh = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
	fh.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	fh.setFormatter(formatter)

	# Wrap stdout so any characters that cannot be encoded on the console are replaced
	try:
		stdout_wrapper = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
		sh = logging.StreamHandler(stdout_wrapper)
		sh.setLevel(logging.INFO)
		sh.setFormatter(formatter)
	except Exception:
		# Fallback to default stream handler if wrapping fails
		sh = logging.StreamHandler()
		sh.setLevel(logging.INFO)
		sh.setFormatter(formatter)

	# Clear existing handlers to avoid duplicates in repeated imports/runs
	if root_logger.handlers:
		for h in list(root_logger.handlers):
			root_logger.removeHandler(h)

	root_logger.addHandler(fh)
	root_logger.addHandler(sh)
	root_logger.info("Logging initialized.")

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
			"do_leetcode": tk.BooleanVar(value=self.config.get("do_leetcode")),
			"status": tk.StringVar(value="Ready. Fill settings and click Run.")
		}
		
		self.driver: webdriver.Edge | None = None # Explicitly type hint
		self.cancel_event = threading.Event()  # Event to signal cancellation from UI
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

	def mixed_text(self, parent_frame, multiple_text: list[tuple[str, str]]):
		"""Create a row of labels with mixed colors. Returns list of labels."""
		labels: list[ttk.Label] = []
		for color, text in multiple_text:
			label = ttk.Label(parent_frame, text=text, foreground=color)
			label.pack(side="left", anchor="w")
			labels.append(label)
		return labels

	def update_mixed_text(self, parent_frame, labels: list[ttk.Label], multiple_text: list[tuple[str, str]]):
		"""Update mixed-color labels; recreate if counts differ."""
		if len(labels) != len(multiple_text):
			for label in labels:
				label.destroy()
			labels.clear()
			for color, text in multiple_text:
				label = ttk.Label(parent_frame, text=text, foreground=color)
				label.pack(side="left", anchor="w")
				labels.append(label)
			return labels
		for label, (color, text) in zip(labels, multiple_text):
			label.config(text=text, foreground=color)
		return labels
		

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
		self.create_path_entry(path_frame, "Driver Path:", "driver_path", self.select_driver_path, 1)
		self.create_path_entry(path_frame, "Binary Path:", "binary_path", self.select_binary_path, 2)

		# --- Bot Settings ---
		settings_frame = ttk.LabelFrame(main_frame, text="Bot Settings", padding="10")
		settings_frame.grid(row=1, column=0, sticky="ew", pady=5) # Use grid for settings_frame
		# Options
		options_frame = ttk.Frame(settings_frame)
		options_frame.pack(fill="x", expand=True) # Allow options_frame to expand

		ttk.Checkbutton(options_frame, text="Run Headless (in background)", variable=self.vars["headless"]).pack(side="left", padx=5) # Headless option
		ttk.Checkbutton(options_frame, text="Perform Searches", variable=self.vars["do_searches"], command=self.update_widget_states).pack(side="left", padx=5) # Search option
		ttk.Checkbutton(options_frame, text="Collect Offers", variable=self.vars["do_offers"]).pack(side="left", padx=5) # Collect Offers option
		ttk.Checkbutton(options_frame, text="Leetcode Bot", variable=self.vars["do_leetcode"], command=self.update_widget_states).pack(side="left", padx=5) # Leetcode Bot option

		# Numeric settings
		numeric_frame = ttk.Frame(settings_frame)
		numeric_frame.pack(fill="x", pady=5, expand=True) # Allow numeric_frame to expand

		self.search_count_label = ttk.Label(numeric_frame, text="Number of Searches:")
		self.search_count_label.pack(side="left", padx=5)
		self.search_count_spinbox = ttk.Spinbox(numeric_frame, from_=1, to=25, width=5, textvariable=self.vars["num_searches"])
		self.search_count_spinbox.pack(side="left", padx=5)

		ttk.Label(numeric_frame, text="Page Timeout (sec):").pack(side="left", padx=5)
		ttk.Spinbox(numeric_frame, from_=5, to=60, width=5, textvariable=self.vars["timeout"]).pack(side="left", padx=5)

		# --- Info Note ---
		info_labels = ttk.Frame(main_frame)
		info_labels.grid(row=2, column=0, sticky="ew", pady=5)
		info_labels.columnconfigure(0, weight=1)

		microsoft_line = ttk.Frame(info_labels)
		microsoft_line.grid(row=0, column=0, sticky="ew", pady=(5, 0))
		self.microsoft_info_labels = self.mixed_text(
			microsoft_line,
			[
				("red", "Important: "),
				("black", "Ensure you are logged into your "),
				("#4d8cf4", "Microsoft "),
				("black", "account in the Edge profile you select.")
			]
		)
		for label in self.microsoft_info_labels:
			label.config(font=("TkDefaultFont", 9, "italic"), wraplength=650)

		self.leetcode_info_line = ttk.Frame(info_labels)
		self.leetcode_info_line.grid(row=1, column=0, sticky="ew", pady=(5, 0))
		self.leetcode_info_labels = self.mixed_text(
			self.leetcode_info_line,
			[
				("red", "Important: "),
				("black", "Ensure you are logged into your "),
				("#dc6128", "Leetcode "),
				("black", "account in the Edge profile you select.")
			]
		)
		for label in self.leetcode_info_labels:
			label.config(font=("TkDefaultFont", 9, "italic"), wraplength=650)

		# --- Controls ---
		control_frame = ttk.Frame(main_frame)
		control_frame.grid(row=3, column=0, sticky="ew", pady=5) # Use grid for control_frame
		control_frame.columnconfigure(0, weight=1) # Allow space between buttons to expand
		# Ensure we have columns for spacing and buttons
		control_frame.grid_columnconfigure(1, weight=0)
		control_frame.grid_columnconfigure(2, weight=0)
		
		# Save button (left of the action buttons)
		self.save_button = ttk.Button(control_frame, text="Save Settings", command=self.save_config)
		self.save_button.grid(row=0, column=1, sticky="e", padx=5)

		# Run button (right-most by design)
		self.run_button = ttk.Button(control_frame, text="Run Bot", command=self.start_bot_thread)
		self.run_button.grid(row=0, column=2, sticky="e", padx=5)
		
		# Cancel button shown only while a run is active (start hidden)
		self.cancel_button = ttk.Button(control_frame, text="Cancel", command=self.cancel_bot)
		self.cancel_button.grid(row=0, column=2, sticky="e", padx=5)
		self.cancel_button.grid_remove()  # hidden until a run starts

		# --- Status Bar ---
		status_bar = ttk.Frame(self, relief="sunken", padding=(5, 2))
		status_bar.pack(side="bottom", fill="x")
		ttk.Label(status_bar, textvariable=self.vars["status"]).pack(side="left", fill="x", expand=True) # Allow status label to expand

	def update_widget_states(self):
		"""Enables/disables widgets based on current settings"""
		if self.vars["do_searches"].get():
			self.search_count_label.config(state="normal")
			self.search_count_spinbox.config(state="normal")
		else:
			self.search_count_label.config(state="disabled")
			self.search_count_spinbox.config(state="disabled")

		if self.vars["do_leetcode"].get():
			self.update_mixed_text(
				self.leetcode_info_line,
				self.leetcode_info_labels,
				[
					("red", "Important: "),
					("black", "Ensure you are logged into your "),
					("#dc6128", "Leetcode "),
					("black", "account in the Edge profile you select.")
				]
			)
		else:
			self.update_mixed_text(self.leetcode_info_line, self.leetcode_info_labels, [])

	def create_path_entry(self, parent, label_text, var_key, browse_command, row):
		"""Helper to create a label, entry, and browse button row."""
		ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=5)
		entry = ttk.Entry(parent, textvariable=self.vars[var_key]) # Removed fixed width
		entry.grid(row=row, column=1, sticky="ew", padx=5)
		ttk.Button(parent, text="Browse", command=browse_command).grid(row=row, column=2, sticky="e", padx=5)
		parent.columnconfigure(1, weight=1) # Ensure the entry column expands

	def get_default_user_data_dir(self):
		"""Gets the default Edge user data directory for the OS."""
		if os.name == 'nt': # Windows
			appdata = os.getenv('APPDATA')
			if appdata:
				return os.path.abspath(os.path.join(appdata, "..", "Local", "Microsoft", "Edge", "User Data"))
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
	def log_status(self, message, lvl: Literal["info", "warn", "debug", "error"]="info"):
		"""Updates status bar and logs to file."""
		self.vars["status"].set(message)
		if lvl == "warn":
			logging.warning(message)
		elif lvl == "debug":
			logging.debug(message)
		elif lvl == "error":
			logging.error(message)
		else:
			logging.info(message)

	def show_error(self, title, message):
		"""Logs error and shows a Tkinter error messagebox."""
		logging.error(message)
		# Ensure messagebox runs on the main UI thread
		self.after(0, lambda: messagebox.showerror(title, message, icon='error'))

	def show_info(self, title, message):
		"""Logs info and shows a Tkinter info messagebox."""
		logging.info(message)
		self.after(0, lambda: messagebox.showinfo(title, message))

	def prompt_close_driver(self):
		"""Ask the user whether to close the active driver."""
		if not self.driver:
			return
		def _ask():
			try:
				should_close = messagebox.askyesno(
					"Close Browser?",
					"Leetcode completed successfully. Close the browser now?"
				)
				if should_close and self.driver:
					self.driver.quit()
					self.driver = None
					self.log_status("Browser closed after Leetcode completion.")
			except Exception as e:
				logging.debug(f"Error while prompting to close driver: {e}")
		self.after(0, _ask)

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
		# Hide cancel button (if shown) and restore run button
		try:
			self.cancel_button.grid_remove()
		except Exception:
			pass
		# Re-show the run button in the right-most column and enable buttons
		try:
			self.run_button.grid()
		except Exception:
			pass
		self.run_button.config(state="normal")
		self.save_button.config(state="normal")
		self.log_status("Bot run finished. Ready for next run.")

	# --- Bot Logic Threading ---
	def start_bot_thread(self):
		"""Starts the main bot logic in a separate thread to keep UI responsive."""
		# Prepare UI
		# Hide run button and show cancel button in its place
		try:
			self.run_button.grid_remove()
		except Exception:
			pass
		try:
			self.cancel_button.grid()  # show cancel button in the same column (right-most)
		except Exception:
			pass

		self.save_button.config(state="disabled")
		self.log_status("Starting bot...")
		
		# Reset cancel event and create a copy of config for the thread
		self.cancel_event.clear()
		self.thread_config = {key: var.get() for key, var in self.vars.items() if key != "status"}
		
		bot_thread = threading.Thread(target=self.run_bot_logic, daemon=True)
		bot_thread.start()

	def cancel_bot(self):
		"""Signal the worker thread to stop and attempt to quit the browser."""
		self.cancel_event.set()
		self.log_status("Cancellation requested. Attempting to stop...")
		# Try to close the browser immediately from the main thread to accelerate shutdown
		try:
			if self.driver:
				self.driver.quit()
		except Exception as e:
			logging.debug(f"Error while quitting driver on cancel: {e}")

	def run_bot_logic(self):
		"""The main Selenium automation logic. Runs in a thread."""
		try:
			# --- 1. Setup Driver ---
			self.log_status("[1/5] Setting up Edge driver...")
			self.driver = self.setup_driver()
			if not self.driver:
				# setup_driver() will have already shown a specific error
				# and logged it. We just need to stop this thread, which
				# will trigger the 'finally' block for cleanup.
				self.log_status("Driver setup failed. Halting bot run.")
				return # Simply exit the function

			# If cancellation requested right after setup, stop early
			if self.cancel_event.is_set():
				self.log_status("Run cancelled before navigation.")
				return

			# --- 2. Get Initial Points ---
			if self.thread_config["do_searches"] or self.thread_config["do_offers"]:
				self.log_status("[2/4] Retrieving initial points...")
				points_before = self.get_current_points()
				self.log_status(f"Points before: {points_before}")
				
				initial_tab = self.driver.current_window_handle

				# --- 3. Perform Searches ---
				if self.thread_config["do_searches"]:
					self.log_status("[3/4] Performing trending searches...")
					self.perform_trending_searches(initial_tab)
					self.driver.switch_to.window(initial_tab)
					self.driver.get("https://www.bing.com/") # Refresh
					time.sleep(3)
				else:
					self.log_status("[3/4] Skipping searches.")

				# --- 4. Collect Offers ---
				if self.thread_config["do_offers"]:
					self.log_status("[4/4] Collecting special offers...")
					self.collect_special_offers(initial_tab)
					self.driver.switch_to.window(initial_tab)
					self.driver.get("https://www.bing.com/") # Refresh
					time.sleep(3)
				else:
					self.log_status("[4/4] Skipping offers. Feature coming soon.")

				# --- 5. Get Final Points ---
				self.log_status("Retrieving final points...")
				points_after = self.get_current_points()
				self.log_status(f"Points after: {points_after}")

				# Handle case where points couldn't be read
				if points_before == 0 and points_after == 0:
					self.log_status("Could not read points before or after. Check UI manually.")
					self.show_info("Bing Bot Finished", "Bot run complete.\n\nCould not read point values. Please check Bing manually.")
				else:
					total_gained = points_after - points_before
					self.log_status(f"Total points gained: {total_gained}")
					self.show_info("Bing Bot Finished", f"Bot run complete.\n\nPoints Gained: {total_gained}\nPoints Before: {points_before}\nPoints After: {points_after}")

			# --- 6. Leetcode Bot ---
			if self.thread_config["do_leetcode"]:
				self.log_status("Preparing Leetcode bot...")
				if self.thread_config["headless"]:
					self.log_status("Leetcode requires non-headless mode. Restarting driver...")
					try:
						if self.driver:
							self.driver.quit()
					except Exception as e_close:
						logging.debug(f"Error while closing driver before Leetcode: {e_close}")

					self.driver = None
					self.thread_config["headless"] = False
					self.driver = self.setup_driver()
					if not self.driver:
						self.log_status("Driver restart failed. Skipping Leetcode bot.")
						return
				else:
					self.log_status("Non-headless mode already enabled. Continuing with current driver.")

				self.log_status("Running Leetcode bot...")
				self.run_leetcode_bot()
				self.log_status("Leetcode bot finished.")
				
		except Exception as e:
			self.show_error("Bing Bot Error", f"An error occurred during bot operation:\n{e}")
		finally:
			# --- 7. Cleanup ---
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
			# Keep browser open for non-headless runs, except during Leetcode where users may opt to close it.
			edge_options.add_experimental_option(
				"detach",
				not cfg["headless"] and not cfg.get("do_leetcode", False)
			)
			
			edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) edge/119.0.0.0 Safari/537.36")
			
			# Use user-selected profile path
			if not cfg["profile_path"] or not os.path.exists(cfg["profile_path"]):
				error_msg = f"Profile path is invalid or not set:\n{cfg['profile_path']}"
				self.show_error("Profile Error", error_msg)
				raise Exception(error_msg) # This will be caught by the outer catch
			edge_options.add_argument(f"--user-data-dir={cfg['profile_path']}") 

			# Use user-selected binary location (if provided)
			if cfg["binary_path"] and os.path.exists(cfg["binary_path"]):
				edge_options.binary_location = cfg["binary_path"]
			elif cfg["binary_path"] and not os.path.exists(cfg["binary_path"]):
				# If path is given but invalid, it's an error
				error_msg = f"Binary path is set but invalid (file not found):\n{cfg['binary_path']}"
				self.show_error("Binary Path Error", error_msg)
				raise Exception(error_msg)
			
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
					self.log_status("User-defined driver path is also invalid. Prompting user.")
					self.after(0, self._prompt_for_driver_path) # Schedule prompt on main thread
					return None # Stop the current bot run
				
				self.log_status(f"Using saved driver path: {user_driver_path}")
				service = Service(executable_path=user_driver_path)

			if not service:
				self.log_status("Could not initialize driver service.")
				return None
				
			driver = webdriver.Edge(service=service, options=edge_options)
			driver.set_window_size(1280, 800)
			driver.set_page_load_timeout(cfg["timeout"])
			driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
			
			return driver
		
		except SessionNotCreatedException as e:
			error_str = str(e).lower()
			if "cannot find msedge binary" in error_str:
				error_msg = ("Microsoft Edge binary not found.\n\n"
							"Please ensure Microsoft Edge is installed correctly, "
							f"or manually provide the path to {'msedge.exe' if os.name=='nt' else 'msedge'} in the 'Binary Path' setting.")
				self.show_error("Edge Binary Not Found", error_msg)
			else:
				self.show_error("Driver Session Error", f"Failed to create driver session:\n{e.msg}")
			return None
			
		except Exception as e:
			self.show_error("Driver Setup Failed", f"Failed to initialize WebDriver: {e}")
			return None

	def get_current_points(self):
		"""Retrieves the current point balance from the Bing page."""
		if not self.driver:
			self.log_status("Driver not available. Cannot get points.", "warn")
			return 0

		try:
			self.driver.get("https://www.bing.com/rewards/panelflyout")
			points_element = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
				EC.presence_of_element_located((By.XPATH, '//*[@id="bingRewards"]/div/div[1]/div[1]/div/div[1]/span'))
			)
			points_str = points_element.text.replace(',', '')
			return int(points_str)
		except Exception as e:
			self.log_status(f"Could not retrieve points. Defaulting to 0. {e}", "warn")
			# Try one more time with a broader selector
			try:
				points_element = self.driver.find_element(By.ID, "id_rc")
				points_str = points_element.text.replace(',', '')
				return int(points_str)
			except Exception as e2:
				self.log_status(f"Second attempt to get points failed: {e2}. Defaulting to 0.", "warn")
				return 0
		finally:
			self.driver.switch_to.default_content()


	def get_trending_searches(self):
		"""Extracts trending search titles from Google Trends."""
		if not self.driver:
			self.log_status("Driver not available. Cannot get trends.", "warn")
			return [] # Return empty list

		self.log_status("Getting trending searches from Google...")
		try:
			# honor cancellation
			if self.cancel_event.is_set():
				self.log_status("Cancellation requested. Aborting trend fetch.")
				return []
			self.driver.get("https://trends.google.com/trending")
			timeout = self.thread_config["timeout"]
			
			WebDriverWait(self.driver, timeout).until(
				EC.presence_of_element_located((By.XPATH, '//*[@id="trend-table"]/div[1]/table/tbody[2]/tr[1]'))
			)
			tbody_element =self.driver.find_element(By.XPATH, '//*[@id="trend-table"]/div[1]/table/tbody[2]')
			tr_elements = tbody_element.find_elements(By.TAG_NAME, 'tr')
			
			self.log_status(f"Found {len(tr_elements)} potential trend elements.")
			
			trending_searches = []
			for i, tr in enumerate(tr_elements):
				if i >= self.thread_config["num_searches"]:
					break
				# Check for cancellation inside the loop
				if self.cancel_event.is_set():
					self.log_status("Cancellation requested. Stopping trend extraction.")
					break
				try:
					# Try multiple ways to extract text
					term = None
					try:
						search_title_element = tr.find_element(By.XPATH, './td[2]/div[1]')
						term = search_title_element.text.strip()

					except Exception:
						term = tr.text.strip()
					
					if term and len(term) > 0 and len(term) < 100:
						trending_searches.append(term)
						self.log_status(f"Extracted trend: {term}")
				except Exception as e_row:
					self.log_status(f"Could not extract a search title: {e_row}", "warn")
			
			if trending_searches:
				return trending_searches

		except Exception as e:
			self.log_status(f"Error extracting trending searches: {e}", "warn")
		
		# Fallback list
		self.log_status("Using fallback search list.", "warn")
		return [
			"news", "weather", "sports", "technology", "entertainment",
			"health", "science", "finance", "travel", "food",
			"music", "movies", "books", "fashion", "gaming",
			"shopping", "education", "business", "fitness", "politics"
		][:self.thread_config["num_searches"]] # Ensure list is correct length

	def perform_trending_searches(self, initial_tab):
		"""Performs Bing searches based on trending topics."""
		if not self.driver:
			self.log_status("Driver not available. Skipping searches.", "warn")
			return

		trending_searches = self.get_trending_searches()
		total_searches = len(trending_searches)
		self.log_status(f"Retrieved {total_searches} trending searches.")

		for i, search_term in enumerate(trending_searches):
			# allow user to cancel between searches
			if self.cancel_event.is_set():
				self.log_status("Cancellation requested. Aborting remaining searches.")
				break
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
				self.log_status(f"Error during search for '{search_term}': {e}", "warn")
			
			finally:
				# Close current tab and switch back
				if len(self.driver.window_handles) > 1:
					self.driver.close()
				self.driver.switch_to.window(initial_tab)
				time.sleep(0.5)

	def find_offer(self):
		"""Finds clickable offer elements in the offers flyout."""
		if not self.driver:
			self.log_status("Driver not available. Cannot find offers.", "warn")
			return []

		self.driver.get("https://www.bing.com/rewards/panelflyout")
		try:
			WebDriverWait(self.driver, self.thread_config["timeout"]).until(
				EC.presence_of_element_located((By.XPATH, '//*[@id="bingRewards"]/div/div[@class="flyout_control_halfUnit"]'))
			)
			offers_parent_div = self.driver.find_elements(By.XPATH, '//*[@id="bingRewards"]/div/div[@class="flyout_control_halfUnit"]')
			all_offers = offers_parent_div[-1].find_elements(By.XPATH, './div')
			
			for div in all_offers:
				try:
					aria_label = str(div.get_attribute("aria-label"))
					div_id = str(div.get_attribute('id'))
					class_name = str(div.get_attribute('class'))

					if div_id == "exclusive_promo_cont":
						check_locked = div.find_element(By.TAG_NAME, 'img')
						if check_locked.get_attribute('alt') == "Locked Image" or check_locked.get_attribute('class') == "locked_img":
							continue # Skip locked exclusive promo

					if aria_label.lower() == "Turn referrals into Rewards - Offer not Completed":
						continue # Skip referral offer

					elif "slim" not in class_name and "Offer not Completed" in aria_label:
						a_tag = div.find_element(By.TAG_NAME, 'a')
						return (a_tag, aria_label.split("-")[0].strip())

				except Exception as e_offer:
					self.log_status(f"Error parsing one offer: {e_offer}", "warn")
			
			self.log_status(f"Found 0 offers.")
		except Exception as e_find:
			self.show_error("Offer Error", f"Could not find offers container: {e_find}")
		return None

	def collect_special_offers(self, initial_tab):
		"""Clicks through all available special offers."""
		if not self.driver:
			self.log_status("Driver not available. Skipping offers.", "warn")
			return

		self.log_status("Checking for special offers...")
		try:
			offer = self.find_offer()
			while offer:
				offer_element, offer_label = offer
				self.log_status(f"Attempting to click offer: {offer_label}")
				try:
					offer_element.click()
					time.sleep(2)
				except Exception as e_click:
					self.log_status(f"Failed to click offer '{offer_label}': {e_click}", "warn")
				offer = self.find_offer() # Look for next offer after clicking

		except Exception as e:
			self.log_status(f"Error during offer collection -> {e}", "warn")

		finally:
			# Close current tab and switch back
			if len(self.driver.window_handles) > 1:
				self.driver.close()
			self.driver.switch_to.window(initial_tab)
			time.sleep(0.5)
			
		self.log_status("Finished processing offers.")

	def check_leetcode_login_status(self): # check leetcode login status by looking for the `navbar_user_avatar` id anywhere on the headers
		"""Checks if the user is logged into Leetcode by looking for the avatar element."""
		if not self.driver:
			self.log_status("Driver not available. Cannot check login status.", "warn")
			return False

		try:
			locators = [
				(By.ID, "navbar_user_avatar"),
				(By.CSS_SELECTOR, "img[alt*='avatar' i]"),
				(By.CSS_SELECTOR, "[data-cy='navbar-avatar']"),
				(By.XPATH, "//img[contains(@alt, 'Avatar') or contains(@alt, 'avatar')]")
			]
			avatar = self.wait_for_any(locators, self.thread_config["timeout"], "login avatar")
			return avatar is not None
		except Exception:
			return False

	def log_browser_state(self, context):
		"""Logs current URL and title for diagnostics."""
		if not self.driver:
			return
		try:
			self.log_status(f"{context} | url={self.driver.current_url} | title={self.driver.title}")
		except Exception as e:
			logging.debug(f"Could not read browser state: {e}")

	def wait_for_any(self, locators, timeout, label, clickable=False):
		"""Waits for the first matching locator and returns the element."""
		if not self.driver:
			return None
		last_exc = None
		for by, value in locators:
			try:
				if clickable:
					return WebDriverWait(self.driver, timeout).until(
						EC.element_to_be_clickable((by, value))
					)
				return WebDriverWait(self.driver, timeout).until(
					EC.presence_of_element_located((by, value))
				)
			except Exception as e:
				last_exc = e
				continue
		self.log_status(f"Leetcode step failed: {label}. Last error: {last_exc}", "warn")
		self.log_browser_state(f"Leetcode failure: {label}")
		return None
	
	def select_python_in_editor(self):
		"""Selects Python3 as the language in the Leetcode editor."""
		if not self.driver:
			self.log_status("Driver not available. Cannot select editor language.", "warn")
			return
		try:
			locators = [
				(By.XPATH, '//*[@id="editor"]/div[1]/div[1]/div[1]/button'),
				(By.CSS_SELECTOR, "button[aria-controls='radix-:r21:']")
			]
			language_dropdown = self.wait_for_any(locators, self.thread_config["timeout"], "editor language dropdown", clickable=True)
			if not language_dropdown:
				self.log_status("Editor language dropdown not found.", "warn")
				return False
			
			current_label = language_dropdown.find_element(By.XPATH, "./..").text.strip().lower()
			if current_label == "python3" or current_label == "python 3":
				self.log_status("Editor already set to Python3.")
				return True
			
			language_dropdown.click()
			time.sleep(1) # wait for dropdown to open
			

			python_locators = [
				(By.XPATH, "/html/body/div[7]/div/div/div[1]"),
				(By.XPATH, "//*[@id='radix-:r21:']/div/div[1]")
			]
			python_option = self.wait_for_any(python_locators, self.thread_config["timeout"], "python3 language select", clickable=True)
			if python_option:
				self.log_status("Selecting Python3 in editor language dropdown...")
				python_option.click()
				time.sleep(1) # wait for editor to switch
				self.log_status("Switched editor language to Python3.")
				return True
			else:
				self.log_status("Python3 option not found in editor language dropdown.", "warn")
				return False
		except Exception as e:
			self.log_status(f"Error switching editor language: {e}", "warn")
			return False

	def get_solution_from_solutions(self):
		"""Attempts to extract a Python3 solution from the user solutions."""
		if not self.driver:
			self.log_status("Driver not available. Cannot get solutions.", "warn")
			return None

		self.log_status("Attempting to retrieve Python3 solution from solutions...")
		try:
			if self.cancel_event.is_set():
				return None
			# Navigate to the solutions tab
			solutions_tab = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
				EC.element_to_be_clickable((By.XPATH, '//*[@id="description_tabbar_outer"]/div[1]/div/div[5]'))
			)
			solutions_tab.click()
			
			# wait for filters to load
			initial_filter_tab = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
				EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "My Solution")]')) # a span which contains text "My Solution"
			)

			# Find Python3 filter and click it
			python_filter = None
			filters = initial_filter_tab.find_elements(By.XPATH, '../div[1]/span') # filter options
			for f in filters:
				if f.text.strip().lower() == "python3":
					python_filter = f
					break
			if python_filter:
				python_filter.click()
				self.log_status("Applied Python3 filter to solutions.")
				time.sleep(1)
			else:
				self.log_status("Python3 filter not found in solutions. Continuing without filter.", "warn")

			# Wait for solution list container to appear
			flyout_container = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
				EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div/div[4]/div/div/div[6]'))
			) # wait for solution flyout to load

			WebDriverWait(self.driver, self.thread_config["timeout"]).until(
				EC.presence_of_element_located((By.XPATH, "(.//*[contains(@class,'group/ads')])")) # Wait for ad element to load which ensures that most solutions are loaded
			)
			solution_posts = flyout_container.find_elements(By.XPATH, './div/div/div[3]/div[3]/div[1]/div') # get all solution posts
			self.log_status(f"Found {len(solution_posts)} solution posts.")
			post_count = len(solution_posts)
			for idx in range(1, post_count): # skip the first one since it's usually pinned
				try:
					fresh_posts = flyout_container.find_elements(By.XPATH, './div/div/div[3]/div[3]/div[1]/div')
					if idx >= len(fresh_posts):
						break
					post = fresh_posts[idx]
					post_title = post.find_element(By.XPATH, './div[1]/div/div[2]/div[2]/div/a')
					post_title.click()
					self.log_status("Opened a solution post.")
					solution_flyout = WebDriverWait(flyout_container, self.thread_config["timeout"]).until(
						EC.presence_of_element_located((By.XPATH, './div[2]'))
					) # wait for solution to load
					if not solution_flyout:
						self.log_status("Solution content did not load properly, trying next post if available.", "warn")
						continue
					self.log_status("Solution content loaded, looking for code blocks...")
					# Find for code blocks in the solution content by class if not found continue to next post
					time.sleep(1.5) # wait for content to fully render
					block_divs = solution_flyout.find_element(By.XPATH, './div/div/div/div[2]/div/div[1]/div[2]/div/div/div/div').find_elements(By.XPATH, './div') # get the actual code block element which is the second div inside the container
					if not block_divs:
						self.log_status("No code blocks found in this solution post, trying next post if available.", "warn")
						all_solutions_flyout = WebDriverWait(solution_flyout, self.thread_config["timeout"]).until(
							EC.presence_of_element_located((By.XPATH, './div/div/div/div[1]/div[1]'))
						) # wait for the flyout which contains all solutions to load
						all_solutions_flyout.click() # click it to open the sidebar which contains the list of all solutions which usually triggers the content to load properly and show the code blocks, then try finding the code block again
						time.sleep(1) # wait for content to load after clicking
						continue
					try:
						python_code_block = block_divs[0].find_elements(By.CLASS_NAME, 'language-python')
						if not python_code_block:
							self.log_status("No Python code block found in this solution post, trying next post if available.", "warn")
							all_solutions_flyout = WebDriverWait(solution_flyout, self.thread_config["timeout"]).until(
								EC.presence_of_element_located((By.XPATH, './div/div/div/div[1]/div[1]'))
							) # wait for the flyout which contains all solutions to load
							all_solutions_flyout.click() # click it to open the sidebar which contains the list of all solutions which usually triggers the content to load properly and show the code blocks, then try finding the code block again
							time.sleep(1) # wait for content to load after clicking
							continue
						solution_text = python_code_block[0].text.strip()
					except Exception as e_code:
						self.log_status(f"Error extracting code block text: {e_code}", "warn")
						solution_text = None
					if solution_text:
						self.log_status(f"Successfully extracted a Python3 solution from user solutions: {solution_text[:120]}\n.\n.\n.\n{solution_text[-120:]}") # Log the first 120 and last 120 chars of the solution for verification
					else:
						solution_text = self.driver.execute_script("""
							return document.querySelector("code.language-python").innerText;
						""")
					return solution_text

				except StaleElementReferenceException as e_post:
					self.log_status(f"Solution post stale, retrying... -> {e_post}", "warn")
					time.sleep(0.5)
					continue
				except Exception as e_post:
					self.log_status(f"Solution post skipped!! -> {e_post}", "warn")
					try:
						all_solutions_flyout = WebDriverWait(solution_flyout, self.thread_config["timeout"]).until(
							EC.presence_of_element_located((By.XPATH, './div/div/div/div[1]/div[1]'))
						) # wait for the flyout which contains all solutions to load
						all_solutions_flyout.click() # click it to open the sidebar which contains the list of all solutions which usually triggers the content to load properly and show the code blocks, then try finding the code block again
						time.sleep(1) # wait for content to load after clicking
					except Exception:
						pass
					continue
				finally:
					time.sleep(0.75) # small delay before trying the next post if available
			return None

		except Exception as e_solution:
			self.log_status(f"Error accessing solutions: {e_solution}", "warn")
			return None
		
	def paste_solution_into_editor(self, solution):
		# paste the solution into the editor using the string we extracted from the solution post.
		if not self.driver:
			self.log_status("Driver not available. Cannot paste solution.", "warn")
			return False
		try:
			editor_locators = [
				(By.XPATH, '//*[@id="editor"]/div[2]/div[1]/div/div/div[1]/div[2]/div[1]/div[5]'),
				(By.CSS_SELECTOR, ".monaco-editor"),
				(By.XPATH, '//*[@id="editor"]/div[2]//div[@role="textbox"]'),
				(By.CSS_SELECTOR, "#editor [contenteditable='true']"),
			]
			editor_flyout = self.wait_for_any(editor_locators, self.thread_config["timeout"], "editor textbox")
			if not editor_flyout:
				return False
			self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", editor_flyout)
			self.driver.execute_script("arguments[0].click();", editor_flyout)
			time.sleep(0.5)

			# Prefer JS injection for Monaco editor to avoid non-interactable errors.
			injected = self.driver.execute_script(
				"""
				const code = arguments[0];
				try {
					if (window.monaco && monaco.editor && monaco.editor.getModels().length) {
						monaco.editor.getModels()[0].setValue(code);
						return true;
					}
					const editor = document.querySelector('.monaco-editor');
					const textarea = editor ? editor.querySelector('textarea') : null;
					if (textarea) {
						textarea.focus();
						textarea.value = code;
						textarea.dispatchEvent(new Event('input', { bubbles: true }));
						return true;
					}
				} catch (e) {}
				return false;
				""",
				solution
			)
			if injected:
				self.log_status("Injected solution into Monaco editor via JS.")
			else:
				editor_flyout.send_keys(Keys.CONTROL, 'a')
				time.sleep(0.5)
				editor_flyout.send_keys(solution)
				self.log_status("Typed solution into editor.")
			time.sleep(1)
			return True

		except Exception as e_editor:
			self.log_status(f"Error pasting solution into editor: {e_editor}", "warn")
			self.show_info("Leetcode Bot", "Could not paste solution into editor. Bot logic to solve the problem will be added in a future update.")
			return False

	def confirm_submission_result(self):
		"""Checks the result of the submission and logs it."""
		# Checks for "testcases passed" text in the flyout
		if not self.driver:
			self.log_status("Driver not available. Cannot confirm submission result.", "warn")
			return

		self.log_status("Checking submission result...")
		results_container = WebDriverWait(self.driver, self.thread_config["timeout"]).until(
			EC.presence_of_element_located((By.XPATH, '//*[@data-e2e-locator="submission-result"]'))
		)
		if results_container:
			self.log_status("Successfully submitted solution. Confirming submission result...")
			try:
				testcase_passed_check = WebDriverWait(results_container, self.thread_config["timeout"]).until(
					EC.presence_of_element_located((By.XPATH, './../div/span'))
				)
				if not testcase_passed_check:
					self.log_status("Could not find submission result. It may still be processing.", "warn")
					return False
				self.log_status(f"Submission result: {testcase_passed_check.text.strip()}")
			except Exception as e_result:
				self.log_status(f"Could not retrieve submission result: {e_result}", "warn")
				return False
		else:
			self.log_status("Wrong answer submitted!!!", "warn")
			self.show_info("Leetcode Bot", "Submitted wrong solution. Please submit correct solution manually on Leetcode.")
			return False
		return True

	def run_leetcode_bot(self):
		"""Leetcode daily question solver"""
		if not self.driver:
			self.log_status("Driver not available. Cannot run Leetcode bot.", "warn")
			return
		self.driver.get("https://leetcode.com/problemset/")
		nav_locators = [
			(By.CSS_SELECTOR, "nav"),
			(By.XPATH, "//nav//a[contains(., 'Daily')]"),
			(By.XPATH, "//*[@id='leetcode-navbar']")
		]
		self.wait_for_any(nav_locators, self.thread_config["timeout"], "leetcode navbar")

		# check login status first before trying to navigate to the page
		self.log_status("Checking Leetcode login status...")
		if not self.check_leetcode_login_status():
			self.log_status("Not logged into Leetcode. Please log in and try again.", "warn")
			self.show_info("Leetcode Login Required", "Please log into Leetcode in your Edge browser and run the bot again.")
			return

		self.log_status("Logged into Leetcode. Navigating to daily question...")
		try:
			if self.cancel_event.is_set():
				return
			# "Daily Challenge" link in the navbar
			daily_locators = [
				(By.XPATH, "//*[@id='__next']/div[2]/div/div/div[3]/nav/div[3]/div[2]/div[3]/button/a"),
				(By.CSS_SELECTOR, "a[href*='daily-question']")
			]
			daily_link_button = self.wait_for_any(daily_locators, self.thread_config["timeout"], "daily link", clickable=True)
			if not daily_link_button:
				return
			try:
				href = daily_link_button.get_attribute("href")
				if href:
					self.log_status(f"Navigating to: {href}")
					self.driver.get(href)
				else:
					self.log_status("Could not click daily link. Please click it manually.", "warn")
					time.sleep(5) # wait for manual navigation
			except Exception:
				daily_link_button.find_element(By.XPATH, "./..").click() # try clicking the parent element if the link itself is not clickable
				time.sleep(3)
				self.driver.switch_to.window(self.driver.window_handles[-1])
				self.log_status(f"Navigating to: {self.driver.current_url}")
			finally:
				editor_locators = [
					(By.ID, "editor"),
					(By.XPATH, "//*[@id='editor']//button"),
					(By.CSS_SELECTOR, "div[class*='editor']")
				]
				if not self.wait_for_any(editor_locators, self.thread_config["timeout"], "editor load"):
					return
				self.log_status("Daily question page loaded.")


			# switch the editor to python3 (if not already) by clicking the language dropdown and selecting python3
			if not self.select_python_in_editor():
				self.log_status("Failed to select Python3 in editor.", "warn")
				return

			# Get solution from the user posted solutions (if any) and try to extract a python3 solution. This is a bit hacky but leetcode doesn't make it easy to get the official solution content without subscribing, but many users post their own solutions in the solution section which we can scrape.
			solution: str|None = self.get_solution_from_solutions()
			if not solution:
				self.log_status("No Python3 solution found. Cannot proceed with solving the problem.", "warn")
				self.show_info("Leetcode Bot", "Could not find a Python3 solution in the user solutions. Bot logic to solve the problem will be added in a future update.")
				return

			# copy the solution to clipboard and paste it into the editor
			try:
				pyperclip.copy(solution)
				self.log_status("Copied solution to clipboard.")
			except Exception as e_clipboard:
				self.log_status(f"Error copying solution to clipboard: {e_clipboard}", "warn")
				self.show_info("Leetcode Bot", "Could not copy solution to clipboard. Bot logic to solve the problem will be added in a future update.")
				return

			if not self.paste_solution_into_editor(solution):
				self.log_status("Failed to paste solution into editor.", "warn")
				return

			# clicking the submit button
			try:
				submit_locators = [
					(By.XPATH, '//*[@id="ide-top-btns"]//button'),
					(By.XPATH, '//*[@data-e2e-locator="console-submit-button"]')
				]
				submit_button = self.wait_for_any(submit_locators, self.thread_config["timeout"], "submit button", clickable=True)
				if not submit_button:
					return
				submit_button.click()
				time.sleep(3)
			except Exception as e_submit:
				self.log_status(f"Error clicking submit button: {e_submit}", "warn")
				self.show_info("Leetcode Bot", "Could not click submit button. Bot logic to solve the problem will be added in a future update.")
				return
			try:
				if not self.confirm_submission_result():
					self.log_status("Could not confirm submission result. Please check Leetcode manually.", "warn")
					self.show_info("Leetcode Bot", "Submitted solution but could not confirm result. Please check Leetcode manually.")
				else:
					self.log_status("Submission result confirmed successfully.")
					self.prompt_close_driver()
			except Exception as e_confirm:
				self.log_status(f"Error confirming submission result: {e_confirm}", "warn")
				self.show_info("Leetcode Bot", "Submitted solution but an error occurred while confirming result. Please check Leetcode manually.")

		except Exception as e:
			self.log_status(f"Error during Leetcode bot operation: {e}", "warn")
			self.show_error("Leetcode Bot Error", f"An error occurred while running the Leetcode bot:\n{e}")
		

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
