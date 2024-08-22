from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
from bs4 import BeautifulSoup
import json
from datetime import datetime

def current_timestamp():
    # Get current time and format it
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

chrome_driver_path = 'C:/Users/RobEnright/chromedriver.exe'
# Set up Chrome options (optional)
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
chrome_options.add_argument("--start-maximized")
# Set up ChromeDriver
service = Service(ChromeDriverManager().install())

def current_timestamp():
    # Get current time and format it
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def pull_indeed_search_urls(job, location):

    job_split = job.strip().split(' ')
    job_formatted = "+".join(job_split)

    # Open a website
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(f"https://ca.indeed.com/jobs?q={job_formatted}&l={location}&from=searchOnHP")

    # Locate the element using the provided XPath
    first_tile = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "mosaic-provider-jobcards")))

    # Find all <a> tags which contain hyperlinks
    links = first_tile.find_elements(By.TAG_NAME, 'a')#for elem in elems:

    # Extract the href attribute from each link
    hyperlinks = [link.get_attribute("href") for link in links if link.get_attribute("href") is not None]

    job_urls = []

    # Print or process the hrefs
    for hlink in hyperlinks:
        if 'clk?jk' in hlink:
            job_urls.append(hlink)

    driver.quit()

    return hyperlinks, job_urls

def pull_indeed_listing_details(url):

    # Pull URL
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    page_html = driver.page_source

    # Parse page_source code for the HTML
    soup = BeautifulSoup(page_html, 'html.parser')

    # Extract job title
    try:
        job_title = soup.find('h1', class_='jobsearch-JobInfoHeader-title').text.strip()
    except:
        job_title = "Not Listed"
    # Extract Company Details
    try:
        company = soup.find('div', class_='css-hon9z8 eu4oa1w0')
        try:
            company_name = company.text
        except:
            company_name = "Not Listed"
        try:
            company_link = company.find('a', href=True).get('href')
        except:
            company_link = "Not Listed"
    except:
        company, company_link, company_link  = "Not Listed", "Not Listed", "Not Listed"

    # Extract Job Details
    try:
        job_details = soup.find('div', class_='js-match-insights-provider-kyg8or eu4oa1w0')
        # Extract Pay Details
        try:
            pay_section = job_details.find('div', {'aria-label': 'Pay'})
            pay = pay_section.find('div', {'data-testid': True}).text if pay_section else "Pay not found"
        except:
            pay = "Not Listed"
        # Extract Job type information
        try:
            job_type_section = job_details.find('div', {'aria-label': 'Job type'})
            job_type = [li.text for li in job_type_section.find_all('li', {'data-testid': True})] if job_type_section else "Job type not found"
        except:
            job_type = "Not Listed"
    except:
        pay, job_type = "Not Listed"
    # Extract job location  
    try:
        location_section = soup.find(id="jobLocationSectionWrapper")
        job_location = location_section.find(id="jobLocationText").text.strip() if location_section else "Job type not found"
    except:
        job_location = "Not Listed"
    # Extract job description
    job_description = soup.find('div', class_='jobsearch-JobComponent-description css-16y4thd eu4oa1w0').text.strip()

    job_dict = {
        'Listing URL':url, 
        'Title':job_title,
        'Company':company_name,
        'Company Link':company_link,
        'Pay Details':pay,
        'Job Type':job_type,
        'Location':job_location,
        'Description':job_description,
        'Scrape Date':current_timestamp()
    }

    driver.quit()

    return job_dict
