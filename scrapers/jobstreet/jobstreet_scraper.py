def extract_job_card_info(card):
    """Extract job info from listing page card"""
    try:
        article = card.locator("xpath=ancestor::article").first
        
        title = article.locator("a[data-automation='jobTitle']").text_content().strip()
        
        company = "Not specified"
        try:
            company = article.locator("a[data-automation='jobCompany']").text_content().strip()
        except:
            pass
        
        locations = article.locator("a[data-automation='jobLocation']").all()
        lokasi = ", ".join([loc.text_content().strip() for loc in locations])
        
        job_type_full = article.locator("p").text_content().strip()
        job_type = job_type_full.replace("Ini adalah lowongan kerja ", "").strip()
        
        salary = "Not specified"
        try:
            salary = article.locator("span:has-text('Rp')").first.text_content().strip()
        except:
            pass
        
        description = article.locator("span[data-automation='jobShortDescription']").nth(0).text_content().strip()
        
        job_href = card.get_attribute("href")
        job_id = job_href.split("/job/")[1].split("?")[0] if job_href else "unknown"
        
        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": lokasi,
            "job_type": job_type,
            "salary": salary,
            "description": description,
            "job_url": f"https://id.jobstreet.com{job_href}" if job_href else ""
        }
        
    except Exception as e:
        print(f"Error extracting card info: {e}")
        return None
    
def scrape_jobstreet(lokasi, search_term=""):
    """Scrape JobStreet listings"""
    jobs = []
    
    try: 
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.set_default_timeout(30000)
            
            search_url = f"https://id.jobstreet.com/id/jobs?keyword={search_term}&location={lokasi}"
            page.goto(search_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            
            job_cards = page.locator("a[data-automation='job-list-item-link-overlay']").all()
            
            print(f"  Found {len(job_cards)} job cards")
            
            for card in job_cards[:10]:
                try:
                    basic_info = extract_job_card_info(card)
                    if basic_info:
                        print(f"    [{len(jobs) + 1}/10] {basic_info['title']}")
                        jobs.append(basic_info)
                except Exception as e:
                    print(f"    [SKIP] Error: {str(e)[:40]}...")
                    
            browser.close()
    
    except Exception as e:
        print(f"Error scraping: {e}")
        return []
            
    return jobs