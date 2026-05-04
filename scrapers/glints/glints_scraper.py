from playwright.sync_api import sync_playwright
import json
from datetime import datetime
import time
import os

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

def apply_filters(page, location, experience_level, job_type, search_term=""):
    """
    Apply filters on Glints job search page
    
    Args:
        page: Playwright page object
        location: str (city name, e.g., "Jakarta")
        experience_level: str (e.g., "Fresh graduate")
        job_type: str (e.g., "Penuh waktu")
        search_term: str (e.g., "Data Engineer")
    """
    
    try:
        # Close login popup if it appears
        try:
            page.click("button[aria-label='Close']")
            page.wait_for_timeout(500)
        except:
            pass
        
        # Fill search term if provided
        if search_term:
            page.get_by_role("textbox", name="Cari Nama Pekerjaan, Skill, dan Perusahaan").fill(search_term)
            page.wait_for_timeout(500)
            page.get_by_role("textbox", name="Cari Nama Pekerjaan, Skill, dan Perusahaan").press("Enter")
            page.wait_for_timeout(1000)
        
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

def extract_job_card_info(card):
    """
    Extract basic job info from job card on listing page
    
    Args:
        card: Locator object of job card
    
    Returns:
        dict with basic job info
    """
    
    try:
        # Extract job title
        title = card.locator("h2 a").text_content().strip()
        
        # Extract company name
        company = card.locator("a[role='link'][aria-label*='company name']").text_content().strip()
        
        # Extract location
        location_elem = card.locator("div.CardJobLocation__LocationWrapper-sc-v7ofa9-0")
        location = location_elem.text_content().strip()
        
        # Extract salary
        try:
            salary = card.locator("span.CompactOpportunityCardsc__SalaryWrapper-sc-dkg8my-32.jTefKS").text_content().strip()
        except:
            salary = "Not specified"
        
        # Get job URL from link
        job_href = card.locator("h2 a").get_attribute("href")
        job_id = job_href.split("/")[-1].split("?")[0] if job_href else "unknown"
        
        # Get posted time
        try:
            posted_time = card.locator("p.CompactOpportunityCardsc__UpdatedAtMessage-sc-dkg8my-27").text_content().strip()
        except:
            posted_time = "Unknown"
        
        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "salary": salary,
            "posted_date": posted_time,
            "job_url": f"https://glints.com{job_href}" if job_href else ""
        }
    
    except Exception as e:
        print(f"Error extracting card info: {e}")
        return None

def extract_details_from_url(page, job_url):
    """
    Navigate to job detail URL and extract detailed info
    
    Args:
        page: Playwright page object
        job_url: str (full job URL)
    
    Returns:
        dict with detailed job info
    """
    
    try:
        # Navigate to detail URL
        page.goto(job_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        
        detail_info = {}
        
        # Extract job type & work policy (3rd element)
        try:
            info_elements = page.locator("div.TopFoldExperimentsc__JobOverViewInfo-sc-b8dbys-9").all()
            if len(info_elements) >= 3:
                job_type_text = info_elements[2].text_content().strip()
                parts = job_type_text.split(" · ")
                detail_info["job_type"] = parts[0] if len(parts) > 0 else "Unknown"
                detail_info["work_policy"] = parts[1] if len(parts) > 1 else "Unknown"
            else:
                detail_info["job_type"] = "Unknown"
                detail_info["work_policy"] = "Unknown"
        except:
            detail_info["job_type"] = "Unknown"
            detail_info["work_policy"] = "Unknown"
        
        # Extract experience required (5th element)
        try:
            info_elements = page.locator("div.TopFoldExperimentsc__JobOverViewInfo-sc-b8dbys-9").all()
            if len(info_elements) >= 5:
                experience_text = info_elements[4].text_content().strip()
                detail_info["experience_required"] = experience_text.replace(" pengalaman", "").strip()
            else:
                detail_info["experience_required"] = "Tidak Dicantumkan"
        except:
            detail_info["experience_required"] = "Unknown"
        
        # Extract description
        try:
            description = page.locator("div.Opportunitysc__JobDescriptionContainer-sc-gb4ubh-5").inner_text()
            detail_info["description"] = description.strip()
        except:
            detail_info["description"] = ""
        
        return detail_info
    
    except Exception as e:
        print(f"Error extracting from detail URL: {e}")
        return {}

def scrape_glints(location, experience_level, job_type, search_term=""):
    """
    Scrape Glints job listings with detail extraction from URLs
    
    Args:
        location: str (e.g., "Jakarta")
        experience_level: str (e.g., "Fresh graduate")
        job_type: str (e.g., "Penuh waktu")
        search_term: str (e.g., "Data Engineer")
    
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
            apply_filters(page, location, experience_level, job_type, search_term=search_term)
            
            # Get job cards
            page.wait_for_timeout(2000)
            job_cards = page.locator("div[role='article']").all()
            
            print(f"  Found {len(job_cards)} job cards")
            print(f"  Extracting first 10...")
            
            # Extract basic info & details from first 10 cards
            for idx, card in enumerate(job_cards[:5]):
                try:
                    basic_info = extract_job_card_info(card)
                    if basic_info:
                        print(f"    [{len(jobs) + 1}/10] {basic_info['title']}")
                        
                        # Extract detail info from URL
                        detail_info = extract_details_from_url(page, basic_info['job_url'])
                        
                        # Merge basic + detail
                        job_data = {**basic_info, **detail_info}
                        jobs.append(job_data)
                        
                except Exception as e:
                    print(f"    [SKIP] Error: {str(e)[:40]}...")
            
            # Close browser
            browser.close()
    
    except Exception as e:
        print(f"Error scraping {location} - {experience_level} - {job_type}: {e}")
        return []
    
    return jobs

def main():
    """Main function to run scraping for all location/experience/job type combinations"""
    
    # FULL CONFIGURATION - All locations, experience levels, job types
    locations = ["Jakarta"]
    experience_levels = ["Fresh graduate"]
    job_types = ["Penuh waktu", "Magang"]
    
    all_jobs = []
    total_combinations = len(locations) * len(experience_levels) * len(job_types)
    current = 0
    
    print(f"Starting Glints scraping - FULL VERSION WITH DETAILS")
    print(f"Locations: {', '.join(locations)}")
    print(f"Experience levels: {', '.join(experience_levels)}")
    print(f"Job types: {', '.join(job_types)}")
    print(f"Search term: 'Data Engineer'")
    print(f"Total combinations: {total_combinations}")
    print(f"Jobs per combination: 10")
    print(f"Total expected jobs: {total_combinations * 10}")
    print("-" * 80)
    
    for location in locations:
        for exp in experience_levels:
            for job_type in job_types:
                current += 1
                print(f"\n[{current}/{total_combinations}] Scraping: {location} - {exp} - {job_type}")
                
                try:
                    jobs = scrape_glints(location, exp, job_type, search_term="Data Engineer")
                    all_jobs.extend(jobs)
                    print(f"[OK] Found {len(jobs)} jobs")
                except Exception as e:
                    print(f"[ERROR] Error: {e}")
                
                time.sleep(2)
    
    # Save to JSON
    output_dir = r"C:\Users\kinet\OneDrive\Documents\PROJECT-ALMAAA\career-intelligence-pipeline\scrapers\output"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"glints_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path = os.path.join(output_dir, filename)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        print("\n" + "-" * 80)
        print(f"[OK] Total jobs scraped: {len(all_jobs)}")
        print(f"[OK] Saved to: {output_path}")
    except Exception as e:
        print(f"[ERROR] Error saving JSON: {e}")

if __name__ == "__main__":
    main()