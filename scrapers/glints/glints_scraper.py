from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time

# Mappings untuk filter values
EXPERIENCE_MAPPING = {
    "Tidak berpengalaman": "NO_EXPERIENCE",
    "Fresh graduate": "FRESH_GRAD",
    "Kurang dari setahun": "LESS_THAN_A_YEAR",
    "1-3 tahun": "ONE_TO_THREE_YEARS",
    "3-5 tahun": "THREE_TO_FIVE_YEARS",
    "5-10 tahun": "FIVE_TO_TEN_YEARS",
    "Lebih dari 10 tahun": "MORE_THAN_TEN_YEARS"
}

JOB_TYPE_MAPPING = {
    "Penuh waktu": "FULL_TIME",
    "Kontrak": "CONTRACT",
    "Magang": "INTERNSHIP",
    "Paruh waktu": "PART_TIME",
    "Freelance": "PROJECT_BASED"
}

def apply_filters(page, location, experience_level, job_type):
    """
    Apply filters on Glints job search page
    
    Args:
        page: Playwright page object
        location: str (city name, e.g., "Jakarta")
        experience_level: str (e.g., "Fresh graduate")
        job_type: str (e.g., "Penuh waktu")
    """
    
    try:
        # Close login popup if it appears
        try:
            page.click("button[aria-label='Close']")
            page.wait_for_timeout(500)
        except:
            pass
        
        # Click job type filter checkbox
        job_type_code = JOB_TYPE_MAPPING.get(job_type)
        page.locator(f"label[for='jobTypes{job_type_code}']").click(force=True)
        page.wait_for_timeout(500)
        
        # Click experience level filter checkbox
        experience_code = EXPERIENCE_MAPPING.get(experience_level)
        page.locator(f"label[for='yearsOfExperienceFilter{experience_code}']").click(force=True)
        page.wait_for_timeout(500)
        
        # Fill location search input
        page.locator("input[placeholder='Semua Kota/Provinsi']").fill(location)
        page.wait_for_timeout(500)
        
        # Press Enter to search
        page.locator("input[placeholder='Semua Kota/Provinsi']").press("Enter")
        page.wait_for_timeout(1000)
        
        # Wait for job cards to load
        page.wait_for_selector("div[role='article']", timeout=5000)
        
    except Exception as e:
        print(f"Error applying filters: {e}")
        raise

def scrape_glints(location, experience_level, job_type):
    """
    Scrape Glints job listings for given location, experience, and job type
    
    Args:
        location: str (e.g., "Jakarta")
        experience_level: str (e.g., "Fresh graduate")
        job_type: str (e.g., "Penuh waktu")
    
    Returns:
        list of job dictionaries
    """
    
    jobs = []
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.set_default_timeout(30000)
            
            # Navigate to Glints
            page.goto("https://glints.com/id/jobs", wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            
            # Apply filters
            apply_filters(page, location, experience_level, job_type)
            
            # TODO: Scroll & extract jobs
            # This section will be implemented in next step:
            # 1. Scroll down to load more job cards
            # 2. Extract job data from each card
            # 3. Parse: title, company, location, salary, job type, experience, education, skills
            # 4. Append to jobs list
            
            # Close browser
            browser.close()
    
    except Exception as e:
        print(f"Error scraping {location} - {experience_level} - {job_type}: {e}")
        return []
    
    return jobs

def main():
    """Main function to run scraping for all location/experience/job type combinations"""
    
    locations = ["Jakarta", "Bekasi", "Tangerang", "Yogyakarta", "Surabaya"]
    experience_levels = ["Fresh graduate", "1-3 tahun", "3-5 tahun"]
    job_types = ["Penuh waktu", "Kontrak", "Magang"]
    
    all_jobs = []
    total_combinations = len(locations) * len(experience_levels) * len(job_types)
    current = 0
    
    print(f"Starting Glints scraping for {total_combinations} combinations...")
    print(f"Locations: {', '.join(locations)}")
    print(f"Experience levels: {', '.join(experience_levels)}")
    print(f"Job types: {', '.join(job_types)}")
    print("-" * 60)
    
    for location in locations:
        for exp in experience_levels:
            for job_type in job_types:
                current += 1
                print(f"[{current}/{total_combinations}] Scraping: {location} - {exp} - {job_type}")
                
                try:
                    jobs = scrape_glints(location, exp, job_type)
                    all_jobs.extend(jobs)
                    print(f"  ✓ Found {len(jobs)} jobs")
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                
                # Small delay between requests to be respectful to server
                time.sleep(1)
    
    # Save to JSON
    filename = f"glints_jobs_{datetime.now().strftime('%Y%m%d')}.json"
    output_path = f"../output/{filename}"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        print("-" * 60)
        print(f"✓ Total jobs scraped: {len(all_jobs)}")
        print(f"✓ Saved to: {output_path}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

if __name__ == "__main__":
    main()