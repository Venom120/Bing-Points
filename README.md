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

### Windows

*   To run the program, double-click `bing_points.bat`:
    - The batch script will automatically install the required Python dependencies (`selenium` and `webdriver-manager`) if they are not already installed.
    - It will then run `main.py` for you.
*   **From anywhere (Global Access):**
    1.  Right-click on `bing_points.bat` and select "Create shortcut".
    2.  Move the shortcut to a convenient location, such as your Desktop or a folder in your PATH.
    3.  Double-click the shortcut

## Edge Driver Installation (Manual)

If you see the following error during execution:
```
[!] Error installing Edge driver
[!] Rolling back to using user defined Edge driver path.
```

You will need to manually download the Microsoft Edge WebDriver from the official [Microsoft website](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver) and place the executable in:
*   `/bin/msedgedriver` (Linux)
*   A directory in your PATH (Windows)

## System Compatibility

This program is primarily designed for Manjaro Linux and Arch-based systems, but should work on other Linux distributions and Windows as well. If you encounter issues, please modify the variables under the following section in `main.py` to match your system's configuration:

```python
"""!!!!!!!!!!!!!!!! Change these acccording to your system !!!!!!!!!!!!!!!!"""
# Example variables to change
# driver_path = "/usr/bin/msedgedriver"
# ... other variables
```

## Contributing

Feel free to contribute to this project by submitting pull requests or opening issues.
