import os
import requests
import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm
from termcolor import colored
import argparse
import sys
import time
import threading
from queue import Queue


_ua_ = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
_headers_ = {
    'User-Agent': _ua_
}
_cookies_ = {}
BASE_URL = "https://www.pbinfo.ro"
global_error_flag = False
PAGE_LOAD_DELAY = 5  
MAX_THREADS = 5  
download_queue = Queue()


class Logger:
    def __init__(self, log_file="script.log"):
        self.log_file = log_file
        self.lock = threading.Lock()

    def log(self, message):
        _timestamp_ = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        with self.lock:
            with open(self.log_file, "a") as log_file:
                log_file.write(_timestamp_ + " " + message + "\n")

    def debug(self, variable_name, value):
        self.log(f"DEBUG - {variable_name}: {value}")


logger = Logger()

def create_directory_structure(base_path, grade, subcategory_title, sub_subcategory_title):
    
    grade_map = {
        "9th": "clasa a 9 a",
        "10th": "clasa a 10 a",
        "11th": "clasa a 11 a"
    }
    grade_path = os.path.join(base_path, grade_map.get(grade, grade))

   
    subcategory_path = os.path.join(grade_path, subcategory_title, sub_subcategory_title)
    os.makedirs(subcategory_path, exist_ok=True)
    return subcategory_path

def fetch_subcategories(url):
    subcategories = []
    while url:
        try:
            print(f"Fetching subcategories from URL: {url}")
            response = requests.get(url, headers=_headers_)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            panels = soup.find_all('div', class_='panel panel-primary')
            if not panels:
                logger.log(f"No panels found on page: {url}")
                print(colored(f"No panels found on page: {url}", 'red'))
                return []

            for panel in panels:
               
                panel_heading = panel.find('div', class_='panel-heading')
                if panel_heading:
                    subcategory_title = panel_heading.text.strip().replace(' ', '_')
                else:
                    logger.log(f"No panel heading found in panel: {str(panel)}")
                    print(colored(f"No panel heading found in a panel", 'red'))
                    continue
                
                subcategory_links = panel.find_all('li', class_='list-group-item')
                for link in subcategory_links:
                    sub_subcategory_title = link.find('span', class_='big').text.strip().replace(' ', '_')
                    full_url = BASE_URL + link.find('a')['href']
                    subcategories.append((subcategory_title, sub_subcategory_title, full_url))

            logger.debug("Subcategories", subcategories)  

            next_page = soup.find('a', string='»')
            if next_page and 'href' in next_page.attrs:
                url = BASE_URL + next_page['href']
            else:
                url = None

        except requests.RequestException as e:
            logger.log(f"Request error while fetching subcategories: {str(e)}")
            print(colored(f"Request error while fetching subcategories: {str(e)}", 'red'))
            return []

    return subcategories

def fetch_problems(subcategory_url):
    problems = []
    page_start = 0
    page_size = 10
    
    while True:
        try:
            paginated_url = f"{subcategory_url}?start={page_start}"
            print(f"Fetching problems from URL: {paginated_url}")
            response = requests.get(paginated_url, headers=_headers_, cookies=_cookies_)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            problem_items = soup.find_all('a', class_='btn btn-primary')
            if not problem_items:
                print(f"No problems found on page: {paginated_url}")
                break

            logger.debug("Problem Items", [str(item) for item in problem_items]) 

            for item in problem_items:
                badge = item.find('span', class_='badge')
                logger.debug("Badge", badge) 
                if badge and '100' in badge.text.strip():
                    problem_id = item['href'].split('/')[2]
                    problem_url = BASE_URL + item['href']
                    problems.append({'id': problem_id, 'url': problem_url})

            page_start += page_size

        except requests.RequestException as e:
            logger.log(f"Request error while fetching problems: {str(e)}")
            print(colored(f"Request error while fetching problems: {str(e)}", 'red'))
            break

    return problems

def fetch_solution_page(problem_url):
    try:
        print(f"Fetching solution page for problem URL: {problem_url}")
        time.sleep(PAGE_LOAD_DELAY)  
        response = requests.get(problem_url, headers=_headers_, cookies=_cookies_)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        logger.debug(f"HTML Content of {problem_url}", soup.prettify()[:1000])  
        evaluation_table = soup.find('table', class_='table')
        if evaluation_table:
            evaluation_rows = evaluation_table.find_all('tr')
            logger.debug("Evaluation Rows", [str(row) for row in evaluation_rows]) 
        else:
            evaluation_rows = []

        valid_evaluations = []

        for row in evaluation_rows[1:]:
            cells = row.find_all('td')
            if len(cells) >= 5:
                score_cell = cells[-1] 
                score = score_cell.get_text(strip=True)
                date = cells[3].get_text(strip=True)
                
                if score == '100':
                    evaluation_link = cells[-1].find('a')
                    if evaluation_link:
                        evaluation_id = evaluation_link['href'].split('/')[-1] 
                        valid_evaluations.append((date, evaluation_id))

        logger.debug("Valid Evaluations", valid_evaluations) 

        valid_evaluations.sort(key=lambda x: x[0], reverse=True)

        if valid_evaluations:
            latest_evaluation_id = valid_evaluations[0][1]
            print(f"Most recent valid evaluation ID for problem URL {problem_url}: {latest_evaluation_id}")
            return latest_evaluation_id
        else:
            logger.log(f"No valid evaluations with 100 points found for problem URL: {problem_url}")
            print(colored(f"No valid evaluations with 100 points found for problem URL: {problem_url}", 'red'))
            return None

    except requests.RequestException as e:
        logger.log(f"Request error while fetching solution page: {str(e)}")
        print(colored(f"Request error while fetching solution page: {str(e)}", 'red'))
        return None
    except Exception as e:
        logger.log(f"Unexpected error while fetching solution page: {str(e)}")
        print(colored(f"Unexpected error while fetching solution page: {str(e)}", 'red'))
        return None

def download_solution(evaluation_id, problem_id, problem_path):
    global global_error_flag
    try:
        evaluation_url = f"https://www.pbinfo.ro/detalii-evaluare/{evaluation_id}"
        print(f"Fetching evaluation detail page from URL: {evaluation_url}")
        response = requests.get(evaluation_url, headers=_headers_, cookies=_cookies_)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        download_button = soup.find('a', class_='btn btn-default', href=True)
        if download_button:
            download_url = BASE_URL + download_button['href']
            file_name = download_button.text.strip().split()[-1].strip("<code>").strip("</code>")
        else:
            logger.log(f"No download button found on evaluation page: {evaluation_url}")
            print(colored(f"No download button found on evaluation page: {evaluation_url}", 'red'))
            global_error_flag = True
            return

        print(f"Downloading solution from URL: {download_url}")
        response = requests.get(download_url, headers=_headers_, cookies=_cookies_)
        response.raise_for_status()

        os.makedirs(problem_path, exist_ok=True)

        file_path = os.path.join(problem_path, file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)

        logger.log(f"Downloaded source code for problem {file_name} [SUCCESS]")
        print(colored(f"Downloaded source code for problem {file_name}", 'green'))

    except requests.RequestException as e:
        print(colored(f"Request error for problem {problem_id}: {str(e)}", 'red'))
        logger.log(f"Request error for problem {problem_id}: {str(e)}")
        global_error_flag = True
    except Exception as e:
        print(colored(f"Unexpected error for problem {problem_id}: {str(e)}", 'red'))
        logger.log(f"Unexpected error for problem {problem_id}: {str(e)}")
        global_error_flag = True

def download_problems_for_grade(grade, url, base_path):
    global global_error_flag
    print(colored(f"Downloading problems for {grade} grade", 'cyan'))
    
    grade_path = os.path.join(base_path, f"Grade_{grade}")
    os.makedirs(grade_path, exist_ok=True)
    
    subcategories = fetch_subcategories(url)

    if global_error_flag:
        print(colored("Error encountered, stopping download.", 'red'))
        return

    for subcategory_title, sub_subcategory_title, subcategory_url in tqdm(subcategories, desc=f"Fetching Subcategories ({grade})", unit="subcategory", colour='green'):
        if global_error_flag:
            print(colored("Error encountered, stopping download.", 'red'))
            return
        
        print(colored(f"Downloading problems from subcategory: {subcategory_title} in {grade} grade", 'cyan'))
        
        subcategory_path = create_directory_structure(base_path, grade, subcategory_title, sub_subcategory_title)
        
        problems = fetch_problems(subcategory_url)
        for problem in tqdm(problems, desc=f"Downloading Problems ({subcategory_title})", unit="problem", colour='green'):
            if global_error_flag:
                print(colored("Error encountered, stopping download.", 'red'))
                return

            print(colored(f"Attempting to download solution for problem #{problem['id']}", 'yellow'))
            evaluation_id = fetch_solution_page(problem['url'])
            if evaluation_id:
                download_solution(evaluation_id, problem['id'], subcategory_path)

    print(colored(f"Finished downloading problems for {grade} grade", 'cyan'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download solutions from pbinfo.ro")
    parser.add_argument("--base-path", required=True, help="Path to save the solutions")
    parser.add_argument("--cookie", required=True, help="Login cookie value")
    parser.add_argument("--grades", nargs='+', choices=["9th", "10th", "11th"], required=True, help="List of grades to download problems from")

    args = parser.parse_args()

    base_path = args.base_path
    _cookies_ = {
        'SSID': args.cookie
    }

    if not os.path.isdir(base_path):
        try:
            os.makedirs(base_path)
            print(colored(f"Directory {base_path} was created!", 'yellow'))
        except PermissionError as e:
            print(colored(f"Permission denied while creating directory {base_path}: {str(e)}", 'red'))
            sys.exit()

    logger.log("Application was started [SUCCESS]\n")

    grade_urls = {
        "9th": "https://www.pbinfo.ro/probleme-categorii/9",
        "10th": "https://www.pbinfo.ro/probleme-categorii/10",
        "11th": "https://www.pbinfo.ro/probleme-categorii/11"
    }

    for grade in args.grades:
        url = grade_urls.get(grade)
        if url:
            download_problems_for_grade(grade, url, base_path)
            if global_error_flag:
                print(colored("Error encountered, stopping further processing.", 'red'))
                sys.exit()

    print(colored(f"Finished downloading problems.", 'cyan'))
