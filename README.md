# Bing Points - An automation for bing points collection

## Installation

### Arch Linux (AUR)

You can install the latest development version directly from the AUR using an AUR helper like [`yay`](https://github.com/Jguer/yay):

```bash
yay -S bing_points-git
```

This will automatically install all required dependencies and set up the desktop entry.

### Manual Installation

1.  **Install Dependencies (Linux):**
    ###### Manjaro/Arch
    ```bash
    sudo pacman -Sy python python-selenium python-webdriver-manager
    ```
    if the above doesn't work then use this
    ```bash
    yay -S python-selenium python-webdriver-manager
    ```
    ###### Ubuntu
    ```bash
    sudo apt update
    sudo apt install -y python3 python3-pip
    pip install selenium webdriver-manager
    ```

2.  **(Optional) Manual Makefile Install:**
**For distros other than Manjaro/Arch**
    ```bash
    git clone https://github.com/Venom120/Bing-Points.git
    cd Bing-Points
    sudo make install
    ```

### Windows

*   Install Python from [python.org](https://www.python.org/downloads/). Make sure to add Python to your PATH during installation.
*   Dependencies are installed automatically when running `bing_points.bat` for the first time.

## Usage
### Linux

*   Run the program from your application menu as **Bing Points Bot** (desktop entry is installed).
*   Or run directly:
    ```bash
    python /usr/share/bing_points/main.py
    ```
    After starting the script, you will be prompted in the console to choose whether to collect points from trending searches and/or special offers. Enter 'yes' or 'no' (case-insensitive, 'y' or 'n' also accepted) for each option.

### Windows

*   To run the program, double-click `bing_points.bat`:
    - The batch script will automatically install the required Python dependencies (`selenium` and `webdriver-manager`) if they are not already installed.
    - It will then run `main.py` for you.
    - After starting the script, you will be prompted in the console to choose whether to collect points from trending searches and/or special offers. Enter 'yes' or 'no' (case-insensitive, 'y' or 'n' also accepted) for each option.
*   **From anywhere (Global Access):**
    1.  Right-click on `bing_points.bat` and select "Create shortcut".
    2.  Move the shortcut to a convenient location, such as your Desktop or a folder in your PATH.
    3.  Double-click the shortcut

## Edge Driver Installation

For Windows users, the program will automatically prompt you to select the `msedgedriver.exe` file the first time you run it. This path will then be saved locally in a `config.json` file, so you won't need to select it again.

If you encounter issues or are a Linux user, you may still need to manually download the Microsoft Edge WebDriver from the official [Microsoft website](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver) and place the executable in:
*   `/bin/msedgedriver` (Linux)
*   A directory in your PATH (Windows, if not using the automated prompt)

## Contributing

Feel free to contribute to this project by submitting pull requests or opening issues.
