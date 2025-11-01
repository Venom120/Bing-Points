# Bing Points Bot - Automated Microsoft Rewards Points Collection (GUI Application)

This project provides a graphical user interface (GUI) application to automate the collection of Microsoft Rewards points. It uses Selenium to control a Microsoft Edge browser instance, performing searches to accumulate points efficiently.

**Key Features:**
* **User-Friendly GUI:** Configure settings and run the bot easily through a Tkinter-based interface.
* **Automated Bing Searches:** Performs a configurable number of searches using trending topics to earn daily search points.
* **Profile Management:** Uses your existing Microsoft Edge user profile, ensuring you stay logged in and points are credited correctly.
* **Headless Mode:** Option to run the browser in the background without a visible window.
* **Cross-Platform:** Designed to work on both Linux and Windows operating systems.
* **Smart Driver Management:** Automatically attempts to download the correct Edge WebDriver, with a fallback for manual path selection.

---

## ⚠️ Disclaimer & Limitations

* **Disclaimer:** This application automates actions that are likely against the Microsoft Terms of Service. Using this bot may lead to the suspension of your Microsoft Rewards account. **Use this software entirely at your own risk.** The creators and contributors are not responsible for any-lost points or banned accounts.
* **Limitations:** The bot relies on scraping the Bing website. Microsoft can (and does) change its website layout frequently. A change to the website's code can break the bot's ability to find the search bar or read your point balance. If this happens, please [open an issue](https://github.com/Venom120/Bing-Points/issues).

---

## Installation

### Arch Linux (AUR)

For Arch Linux and its derivatives (like Manjaro), you can install the `bing_points-git` package from the Arch User Repository (AUR). This package builds the latest development version directly from this Git repository.

**Prerequisites:**
* An AUR helper (e.g., `yay`, `paru`). If you don't have one, you can install `yay` with:
    ```bash
    sudo pacman -Sy --needed git base-devel
    git clone https://aur.archlinux.org/yay.git
    cd yay
    makepkg -si
    ```

**Installation using an AUR helper:**
```bash
yay -S bing_points-git
```

This command will:

  * Download the package build files from the AUR.
  * Resolve and install required dependencies (`python-selenium`, `python-webdriver-manager`) from the official repositories.
  * Install the application files to `/usr/share/bing_points/`.
  * Create a desktop entry, allowing you to launch the bot from your application menu.

### Manual Linux Installation

1.  **Prerequisites:**

      * Ensure you have `git`, `make`, `python3`, and `python3-venv` installed.
      * On Debian/Ubuntu-based systems:
        ```bash
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv git make
        ```
      * On Arch/Manjaro-based systems:
        ```bash
        sudo pacman -Sy python python-pip git make
        ```

2.  **Clone the Repository and Install:**

    ```bash
    git clone https://github.com/Venom120/Bing-Points.git
    cd Bing-Points
    sudo make install
    ```

    The `make install` command will:

      * Copy the application files to `/usr/share/bing_points/`.
      * Create a Python virtual environment inside `/usr/share/bing_points/`.
      * Install all necessary Python dependencies (Selenium, etc.) into that venv.
      * Create a desktop entry for easy launching from your application menu.

### Windows

1.  **Install Python:**

      * Download and install Python 3 from [python.org](https://www.python.org/downloads/).
      * **Important:** During installation, make sure to check the box that says "Add Python to PATH".

2.  **Download the Project:**

      * Download the project ZIP file from the GitHub repository and extract it, or clone the repository using Git:
        ```bash
        git clone https://github.com/Venom120/Bing-Points.git
        cd Bing-Points
        ```

3.  **Run the Bot:**

      * Double-click the `bing_points.bat` file.
      * The batch script will automatically:
          * Create a Python virtual environment (`.venv`) in the project folder (if it doesn't exist).
          * Install all required Python dependencies (`selenium`, `webdriver-manager`) into the virtual environment.
          * Launch the `main.py` GUI application.

-----

## Usage

### Linux

  * **From Application Menu:** After installation, search for "Bing Points Bot" in your application launcher and click to run.
  * **From Terminal (if manually installed):**
    ```bash
    /usr/share/bing_points/bing_points.sh
    ```

### Windows

  * **From File Explorer:** Navigate to the project directory and double-click `bing_points.bat`.

**Using the GUI:**

Once the application launches:

1.  **Path Settings:**

      * **Profile Path:** This is crucial. Click "Browse" and select your Microsoft Edge user data directory. This is typically found at:
          * **Windows:** `%LOCALAPPDATA%\Microsoft\Edge\User Data`
          * **Linux:** `~/.config/microsoft-edge/`
          * *Note: Select the main `User Data` or `microsoft-edge` folder, or a specific profile folder like `Default` or `Profile 1`.*
          * **You must be logged into your Microsoft account in the Edge profile you select.**
      * **Driver Path (Optional):** The bot will attempt to automatically download the correct `msedgedriver`. If it fails, you will be prompted to manually select the driver.
      * **Binary Path (Optional):** If your Microsoft Edge executable is not in a standard location, you can specify its path here.

2.  **Bot Settings:**

      * **Run Headless (in background):** If checked, the Edge browser will run without a visible window.
      * **Perform Searches:** If checked, the bot will perform trending searches to earn points.
      * **Collect Offers:** This feature is currently disabled and will be available in a future update.

3.  **Controls:**

      * **Save Settings:** Saves your current configuration to `config.json`.
      * **Run Bot:** Starts the automation process. The status bar at the bottom will show progress.

-----

## Contributing

Contributions are welcome\! If you'd like to help improve the bot, please feel free to:

  * [Open an issue](https://github.com/Venom120/Bing-Points/issues) to report a bug or suggest a new feature.
  * Fork the repository and submit a pull request with your changes.

When contributing, please try to:

  * Write clear and descriptive commit messages.
  * Ensure your code works on both Linux and Windows.
  * Address any potential breakages (e.g., if you are updating selectors, explain why the new ones are more robust).
