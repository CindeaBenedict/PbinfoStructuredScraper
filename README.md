PBinfo Solution Downloader

Description

The PBinfo Solution Downloader is a Python script designed to automate the process of downloading programming problem solutions from the PBinfo website. The script allows users to specify the grade level (9th, 10th, or 11th) and downloads the problems that have received a perfect score (100 points). The downloaded solutions are organized into a structured directory format based on the grade, subcategory, and problem titles.
Features

    Automated Downloading: Fetches and downloads solutions that scored 100 points from the PBinfo website.
    Directory Structure: Organizes downloaded solutions into directories based on the grade level, subcategory, and problem titles.
    Multithreading Support: Utilizes multithreading to speed up the download process.
    Error Logging: Logs errors and other debug information to help with troubleshooting.
    Cookie-Based Authentication: Uses a provided session cookie to authenticate requests to PBinfo.

Requirements

    Python 3.x

    Required Python packages: requests, beautifulsoup4, tqdm, termcolor, argparse

You can install the required packages using the following command:

bash

pip install requests beautifulsoup4 tqdm termcolor argparse

Usage

To use the PBinfo Solution Downloader, you need to provide the following arguments:

    --base-path: The base directory where the downloaded solutions will be saved.
    --cookie: Your session cookie from PBinfo (required for authentication).
    --grades: List of grades to download problems for (choose from "9th", "10th", or "11th").

Example Command

bash

python pbinfo_downloader.py --base-path /path/to/save/solutions --cookie your_cookie_value --grades 9th 10th 11th

This command will download solutions for the 9th, 10th, and 11th grades and save them in the specified base path directory.
How It Works

    Cookie Authentication: The script uses the provided session cookie to authenticate with PBinfo. This is necessary to access the solution pages.

    Fetching Subcategories: For each grade, the script fetches the subcategories (e.g., "Loops", "Arrays") from the PBinfo website.

    Fetching Problems: For each subcategory, it fetches all problems and filters out those that have achieved a perfect score (100 points).

    Downloading Solutions: The script downloads the source code of the solutions with perfect scores and saves them in a structured directory format.

    Logging: Any errors or significant actions are logged to a log file (script.log) to help with debugging and tracking the process.

Directory Structure

The solutions will be organized in the following directory structure:

bash

/base-path/
??? Grade_9th/
    ??? Subcategory_Title/
        ??? Sub_Subcategory_Title/
            ??? Problem_Solution_File.cpp

This structure ensures that all downloaded solutions are neatly organized by grade and subcategory.
Error Handling

If any errors are encountered during the downloading process, they are logged, and the script attempts to continue processing other problems. If a critical error occurs, the script will stop and display an error message.
Notes

    Ensure you have a stable internet connection, as the script will be making numerous HTTP requests to the PBinfo website.
    The script includes a delay (PAGE_LOAD_DELAY) between requests to avoid overloading the server.
    Your session cookie (SSID) is required to access the solution pages. Make sure to keep it secure and do not share it publicly.

Troubleshooting

    Permission Denied: If you encounter a permission error when creating the base directory, ensure that you have the necessary write permissions.
    Request Errors: If the script fails to fetch pages or resources, it could be due to network issues or changes in the PBinfo website structure.
    Missing Solutions: If some problems don't have solutions downloaded, check the log file (script.log) for details on what went wrong.

License

This script is open-source and free to use. Modify it as needed for your personal use. Contributions and improvements are welcome!
Disclaimer

This script is intended for personal and educational use only. Please use it responsibly and in compliance with the PBinfo website's terms of service. The author is not responsible for any misuse or issues arising from the use of this script.
