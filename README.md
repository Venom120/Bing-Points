# Bing Points - A Python Program

## Important Notes

*   **Do not remove this Git repository folder.**

## Installation

1.  **Install Dependencies (Linux):**
    ###### Manjaro(arch)
    ```bash
    sudo pacman -Sy python python-pip make
    sudo make install
    ```
    ###### Ubuntu
    ```bash
    sudo apt update  # Or your distribution's equivalent
    sudo apt install -y python3 python3-pip make
    sudo make install
    ```

2.  **Install Dependencies (Windows):**
    *   Install Python from [python.org](https://www.python.org/downloads/). Make sure to add Python to your PATH during installation.
    *   Dependencies are installed automatically when running `bing_points.bat` for the first time.

## Usage

1.  **Linux:**
    *   Run the program using:
        ```bash
        ./bing_points.sh
        ```
        or
        ```bash
        python3 main.py
        ```
2.  **Windows:**
    *   **First Time Setup:** Double-click `bing_points.bat` to create the virtual environment and install dependencies.
    *   **Running the Program:**
        *   **From the project directory:** Double-click `bing_points.bat`.
        *   **From anywhere (Global Access):**
            1.  Right-click on `bing_points.bat` and select "Create shortcut".
            2.  Move the shortcut to a convenient location, such as your Desktop or a folder in your PATH.
            3.  Double-click the shortcut to run the program.

## Edge Driver Installation (Manual)

If you see the following error during execution:
```
[!] Error installing Edge driver"
[!] Rolling back to using user defined Edge driver path.
```

You will need to manually download the Microsoft Edge WebDriver from the official [Microsoft website](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/?form=MA13LH) and place the executable in:
*   `/bin/msedgedriver` (Linux)
*   A directory in your PATH (Windows)

## System Compatibility

This program is primarily designed for Manjaro Linux. However, it should work on other Linux systems and Windows as well. If you encounter issues, please modify the variables under the following section in `main.py` to match your system's configuration:

```python
"""!!!!!!!!!!!!!!!! Change these acccording to your system !!!!!!!!!!!!!!!!"""
# Example variables to change
# driver_path = "/usr/bin/msedgedriver"
# ... other variables
```

## Contributing

Feel free to contribute to this project by submitting pull requests or opening issues.