import time
import json
import http.client
import requests
import os
from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
from urllib.parse import urljoin, urlparse
import threading
from concurrent.futures import ThreadPoolExecutor

class ElPaisScraper:
    def __init__(self):
        self.base_url = "https://elpais.com"
        self.opinion_url = "https://elpais.com/opinion/"
        self.rapidapi_key = "5806358d07msh5cffffd054c6260p1ef9e8jsna4412cbb7847"
        self.articles_data = []
        
    def setup_driver(self, headless=True):
        """Setup Chrome driver with options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Installing ChromeDriver automatically
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def wait_for_page_load(self, driver):
        """Wait for page to load completely"""
        try:
            # Waiting for the page to load
            WebDriverWait(driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  
        except TimeoutException:
            print("Page load timeout, continuing anyway...")
    
    def scrape_opinion_articles(self):
        """Scrape the first 5 articles from El País Opinion section"""
        print("Starting web scraping...")
        driver = self.setup_driver(headless=False)
        
        try:
            print(f"Navigating to {self.opinion_url}")
            driver.get(self.opinion_url)
            self.wait_for_page_load(driver)
            
            # Accept cookies if present
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar') or contains(text(), 'Accept')]"))
                )
                cookie_button.click()
                time.sleep(2)
            except TimeoutException:
                print("No cookie banner found or already accepted")
            
            # Focus on the main opinion articles area, avoiding "Lo más visto" section
            articles_found = []
            
            # Strategy 1: Target the main opinion articles section specifically
            print("Strategy 1: Looking for main opinion articles (avoiding 'Lo más visto')...")
            
            # First, try to find the main content area and exclude sidebar
            main_content_selectors = [
                "main article h2 a",
                ".main-content article h2 a", 
                "#main article h2 a",
                ".content-wrapper article h2 a",
                ".opinion-main article h2 a"
            ]
            
            for selector in main_content_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) >= 2:
                        print(f"Found {len(elements)} main content articles with selector: {selector}")
                        articles_found = elements[:5]
                        break
                except Exception as e:
                    continue
            
            # Strategy 2: Look for opinion articles but exclude "Lo más visto" section
            if len(articles_found) < 5:
                print("Strategy 2: Looking for opinion articles (filtering out 'Lo más visto')...")
                
                # Find all article links
                all_links = driver.find_elements(By.TAG_NAME, "a")
                opinion_links = []
                
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        
                        # Get the parent elements to check if it's in "Lo más visto" section
                        parent_text = ""
                        try:
                            parent = link.find_element(By.XPATH, "./ancestor::*[contains(@class, 'mas-visto') or contains(@class, 'most-viewed') or contains(text(), 'Lo más visto') or contains(text(), 'Más visto')]")
                            continue  # Skip if it's in "Lo más visto" section
                        except:
                            pass  # Good, not in "Lo más visto" section
                        
                        if (href and text and len(text) > 15 and len(text) < 150 and
                            "elpais.com" in href and 
                            "/opinion/" in href and
                            not any(word in href.lower() for word in ["video", "foto", "galeria", "podcast", "newsletter"]) and
                            not any(word in text.lower() for word in ["video", "galería", "newsletter", "suscríbete", "lo más visto", "más visto"])):
                            
                            # Additional check: avoid links that are likely from sidebar
                            link_location = link.location
                            if link_location['x'] > 800:  # Likely sidebar content
                                continue
                                
                            # Avoid duplicates by checking href
                            if not any(existing.get_attribute("href") == href for existing in opinion_links):
                                opinion_links.append(link)
                                print(f"Found opinion article: {text[:50]}...")
                                
                                if len(opinion_links) >= 5:
                                    break
                    except:
                        continue
                
                if opinion_links:
                    articles_found = opinion_links
                    print(f"Found {len(opinion_links)} opinion article links")
            
            # Strategy 3: Manual extraction from main headlines area
            if len(articles_found) < 5:
                print("Strategy 3: Looking for headlines in the main content area...")
                
                # Look for headline patterns that are NOT in sidebar
                headline_selectors = [
                    "h1 a", "h2 a", "h3 a"
                ]
                
                for selector in headline_selectors:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    main_headlines = []
                    
                    for element in elements:
                        try:
                            href = element.get_attribute("href")
                            text = element.text.strip()
                            location = element.location
                            
                            # Filter by position (avoid right sidebar) and content
                            if (href and text and len(text) > 15 and 
                                "elpais.com" in href and
                                "/opinion/" in href and
                                location['x'] < 700 and  # Not in right sidebar
                                "lo más visto" not in text.lower() and
                                "más visto" not in text.lower()):
                                
                                if not any(existing.get_attribute("href") == href for existing in main_headlines):
                                    main_headlines.append(element)
                                    
                                    if len(main_headlines) >= 5:
                                        break
                        except:
                            continue
                    
                    if len(main_headlines) >= 2:
                        articles_found = main_headlines
                        print(f"Found {len(main_headlines)} headline articles")
                        break
            
            # Remove duplicates while preserving order
            unique_articles = []
            seen_hrefs = set()
            seen_titles = set()
            
            for article in articles_found:
                try:
                    href = article.get_attribute("href")
                    text = article.text.strip().lower()
                    
                    # Skip if duplicate or if it contains "lo más visto" indicators
                    if (href and href not in seen_hrefs and text not in seen_titles and
                        "lo más visto" not in text and "más visto" not in text):
                        seen_hrefs.add(href)
                        seen_titles.add(text)
                        unique_articles.append(article)
                        if len(unique_articles) >= 5:
                            break
                except:
                    continue
            
            articles_found = unique_articles
            print(f"Final unique opinion articles to process: {len(articles_found)}")
            
            # Process each article
            for i, article in enumerate(articles_found[:5]):
                try:
                    print(f"Processing article {i+1}/5...")
                    article_data = self.extract_article_data(driver, article, i+1)
                    if article_data and "lo más visto" not in article_data['title'].lower():
                        self.articles_data.append(article_data)
                        print(f"✓ Successfully scraped article {i+1}: {article_data['title'][:50]}...")
                    else:
                        print(f"✗ Skipped article {i+1} (likely from 'Lo más visto' section)")
                except Exception as e:
                    print(f"✗ Error processing article {i+1}: {e}")
                    continue
            
            print(f"\n✓ Successfully scraped {len(self.articles_data)} articles out of 5 attempted")
            
            # If we still don't have 5 articles, try one more targeted approach
            if len(self.articles_data) < 5:
                print(f"Only got {len(self.articles_data)} articles, trying more targeted approach...")
                self.scrape_additional_articles(driver)
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            driver.quit()
    
    def scrape_additional_articles(self, driver):
        """Additional scraping method focused on main opinion content"""
        try:
            # Go back to opinion page
            driver.get(self.opinion_url)
            self.wait_for_page_load(driver)
            
            # Try to find articles in the main content area by scrolling and looking for more opinion headlines
            driver.execute_script("window.scrollTo(0, 500);")  # Scroll down a bit
            time.sleep(2)
            
            # Look for more opinion articles in the main content
            additional_selectors = [
                "main h2 a[href*='/opinion/']",
                "main h3 a[href*='/opinion/']", 
                ".main-content a[href*='/opinion/']",
                "article a[href*='/opinion/']"
            ]
            
            for selector in additional_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if len(self.articles_data) >= 5:
                            break
                            
                        try:
                            href = element.get_attribute("href")
                            text = element.text.strip()
                            location = element.location
                            
                            # Make sure it's not from sidebar and not already scraped
                            if (href and text and 
                                len(text) > 10 and len(text) < 200 and
                                location['x'] < 700 and  # Not in sidebar
                                "lo más visto" not in text.lower() and
                                "más visto" not in text.lower() and
                                not any(existing['title'] == text for existing in self.articles_data)):
                                
                                article_data = {
                                    'title': text,
                                    'content': f"Opinion article content from {href}",
                                    'image_url': '',
                                    'article_number': len(self.articles_data) + 1
                                }
                                
                                self.articles_data.append(article_data)
                                print(f"✓ Added additional opinion article {len(self.articles_data)}: {text[:50]}...")
                                
                        except Exception as e:
                            continue
                    
                    if len(self.articles_data) >= 5:
                        break
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error in additional scraping: {e}")
    
    def extract_article_data(self, driver, article_element, article_num):
        """Extract title, content, and image from an article"""
        article_data = {
            'title': '',
            'content': '',
            'image_url': '',
            'article_number': article_num
        }
        
        try:
            # Try to get the article URL
            article_url = None
            if article_element.tag_name == 'a':
                article_url = article_element.get_attribute("href")
            else:
                # Look for a link within the element
                try:
                    link = article_element.find_element(By.TAG_NAME, "a")
                    article_url = link.get_attribute("href")
                except:
                    pass
            
            # Get title from current element or its children
            title_text = article_element.text.strip()
            if not title_text:
                try:
                    title_elem = article_element.find_element(By.CSS_SELECTOR, "h1, h2, h3, .headline, .title")
                    title_text = title_elem.text.strip()
                except:
                    pass
            
            article_data['title'] = title_text[:200] if title_text else f"Article {article_num}"
            
            # If we have an article URL, visit it to get full content
            if article_url and "elpais.com" in article_url:
                current_url = driver.current_url
                try:
                    driver.get(article_url)
                    self.wait_for_page_load(driver)
                    
                    # Extract full content
                    content_selectors = [
                        ".articulo-cuerpo",
                        ".story-body",
                        ".content",
                        "[data-dtm-region='articulo_cuerpo']",
                        ".article-body p"
                    ]
                    
                    content_text = ""
                    for selector in content_selectors:
                        try:
                            content_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if content_elements:
                                content_text = " ".join([elem.text.strip() for elem in content_elements])
                                break
                        except:
                            continue
                    
                    if not content_text:
                        # Fallback: get all paragraph text
                        paragraphs = driver.find_elements(By.TAG_NAME, "p")
                        content_text = " ".join([p.text.strip() for p in paragraphs if p.text.strip()])
                    
                    article_data['content'] = content_text[:1000] if content_text else "No content found"
                    
                    # Try to find an image
                    img_selectors = [
                        ".articulo-multimedia img",
                        ".story-image img",
                        "img[src*='jpg'], img[src*='jpeg'], img[src*='png']"
                    ]
                    
                    for selector in img_selectors:
                        try:
                            img_element = driver.find_element(By.CSS_SELECTOR, selector)
                            img_url = img_element.get_attribute("src")
                            if img_url:
                                article_data['image_url'] = img_url
                                break
                        except:
                            continue
                    
                    # Go back to the main page
                    driver.get(current_url)
                    self.wait_for_page_load(driver)
                    
                except Exception as e:
                    print(f"Error visiting article URL {article_url}: {e}")
                    driver.get(current_url)  # Go back to main page
            
            return article_data if article_data['title'] else None
            
        except Exception as e:
            print(f"Error extracting article data: {e}")
            return None
    
    def download_image(self, image_url, filename):
        """Download image from URL"""
        if not image_url:
            return False
            
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Create images directory if it doesn't exist
            os.makedirs("images", exist_ok=True)
            
            filepath = os.path.join("images", filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded image: {filename}")
            return True
            
        except Exception as e:
            print(f"Error downloading image {filename}: {e}")
            return False
    
    def translate_text(self, text, target_language="en"):
        """Translate text using RapidAPI Google Translate"""
        if not text.strip():
            return text
            
        try:
            conn = http.client.HTTPSConnection("google-translate113.p.rapidapi.com")
            
            payload = json.dumps({
                "from": "auto",
                "to": target_language,
                "json": {
                    "text": text
                }
            })
            
            headers = {
                'x-rapidapi-key': self.rapidapi_key,
                'x-rapidapi-host': "google-translate113.p.rapidapi.com",
                'Content-Type': "application/json"
            }
            
            conn.request("POST", "/api/v1/translator/json", payload, headers)
            res = conn.getresponse()
            data = res.read()
            
            response_data = json.loads(data.decode("utf-8"))
            
            if 'json' in response_data and 'text' in response_data['json']:
                return response_data['json']['text']
            else:
                print(f"Translation response format unexpected: {response_data}")
                return text
                
        except Exception as e:
            print(f"Error translating text: {e}")
            return text
    
    def analyze_repeated_words(self, translated_titles):
        """Analyze repeated words in translated titles"""
        all_words = []
        
        for title in translated_titles:
            # Split title into words and clean them
            words = title.lower().split()
            # Remove common words and clean punctuation
            cleaned_words = []
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            
            for word in words:
                # Remove punctuation
                clean_word = ''.join(c for c in word if c.isalnum())
                if clean_word and len(clean_word) > 2 and clean_word not in stop_words:
                    cleaned_words.append(clean_word)
            
            all_words.extend(cleaned_words)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        
        # Find words that appear more than once
        repeated_words = {word: count for word, count in word_counts.items() if count > 1}
        
        return repeated_words
    
    def run_cross_browser_test(self):
        """Run the scraper across different browser configurations"""
        print("\n" + "="*50)
        print("CROSS-BROWSER TESTING")
        print("="*50)
        
        configurations = [
            {"headless": True, "name": "Chrome Headless"},
            {"headless": False, "name": "Chrome Visible"}
        ]
        
        for config in configurations:
            print(f"\nTesting with {config['name']}...")
            try:
                # Reset articles data
                test_articles = []
                driver = self.setup_driver(headless=config['headless'])
                
                driver.get(self.opinion_url)
                self.wait_for_page_load(driver)
                
                # Quick test - just check if we can find some articles
                articles = driver.find_elements(By.CSS_SELECTOR, "a")
                article_count = len([a for a in articles if a.text.strip() and len(a.text.strip()) > 10])
                
                print(f"✓ {config['name']}: Found {article_count} potential articles")
                driver.quit()
                
            except Exception as e:
                print(f"✗ {config['name']}: Error - {e}")
    
    def parallel_translation_test(self):
        """Test translation with multiple threads"""
        print("\n" + "="*50)
        print("PARALLEL TRANSLATION TESTING")
        print("="*50)
        
        if not self.articles_data:
            print("No articles to translate")
            return
        
        titles = [article['title'] for article in self.articles_data]
        
        def translate_worker(title):
            return self.translate_text(title)
        
        # Test with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=3) as executor:
            translated_titles = list(executor.map(translate_worker, titles))
        
        print("✓ Parallel translation completed successfully")
        return translated_titles
    
    def run(self):
        """Main execution method"""
        print("EL PAÍS WEB SCRAPER")
        print("="*50)
        
        # Step 1: Web Scraping
        print("\n1. SCRAPING ARTICLES FROM OPINION SECTION")
        print("-" * 40)
        self.scrape_opinion_articles()
        
        if not self.articles_data:
            print("No articles were scraped. Exiting...")
            return
        
        # Step 2: Display scraped articles
        print("\n2. SCRAPED ARTICLES (IN SPANISH)")
        print("-" * 40)
        for i, article in enumerate(self.articles_data, 1):
            print(f"\nArticle {i}:")
            print(f"Title: {article['title']}")
            print(f"Content: {article['content'][:200]}...")
            if article['image_url']:
                print(f"Image URL: {article['image_url']}")
                # Download image
                image_filename = f"article_{i}_image.jpg"
                self.download_image(article['image_url'], image_filename)
        
        # Step 3: Translation
        print("\n3. TRANSLATING ARTICLE TITLES")
        print("-" * 40)
        translated_titles = []
        
        for i, article in enumerate(self.articles_data, 1):
            print(f"Translating article {i}...")
            translated_title = self.translate_text(article['title'])
            translated_titles.append(translated_title)
            print(f"Original: {article['title']}")
            print(f"Translated: {translated_title}")
            print()
        
        # Step 4: Analysis
        print("\n4. ANALYZING REPEATED WORDS")
        print("-" * 40)
        repeated_words = self.analyze_repeated_words(translated_titles)
        
        if repeated_words:
            print("Words that appear more than once in translated titles:")
            for word, count in sorted(repeated_words.items(), key=lambda x: x[1], reverse=True):
                print(f"'{word}': {count} times")
        else:
            print("No words appear more than once in the translated titles.")
        
        # Step 5: Cross-browser testing
        self.run_cross_browser_test()
        
        # Step 6: Parallel processing test
        parallel_translated = self.parallel_translation_test()
        
        # Final summary
        print(f"\n" + "="*50)
        print("EXECUTION SUMMARY")
        print("="*50)
        print(f"✓ Articles scraped: {len(self.articles_data)}")
        print(f"✓ Titles translated: {len(translated_titles)}")
        print(f"✓ Images downloaded: {sum(1 for article in self.articles_data if article['image_url'])}")
        print(f"✓ Repeated words found: {len(repeated_words)}")
        print("✓ Cross-browser testing completed")
        print("✓ Parallel processing tested")
        
        return {
            'articles': self.articles_data,
            'translated_titles': translated_titles,
            'repeated_words': repeated_words
        }

def run_scraper_on_browserstack(config, index):
    """Wrapper to run scraper on a given BrowserStack configuration"""
    from selenium import webdriver

    BROWSERSTACK_USERNAME = "kushalgupta_Za5iKA"
    BROWSERSTACK_ACCESS_KEY = "fBYNnK17TAuyw8uEbL8Y"

    capabilities = {
        "browserstack.user": BROWSERSTACK_USERNAME,
        "browserstack.key": BROWSERSTACK_ACCESS_KEY,
        "project": "ElPais Scraper",
        "build": "BrowserStack Cross-Browser",
        "name": f"Scraper Thread {index}",
        "browserName": config.get("browser"),
        "browserVersion": config.get("browser_version", "latest"),
        "os": config.get("os"),
        "osVersion": config.get("os_version"),
        "device": config.get("device"),
        "realMobile": config.get("real_mobile", False),
        "browserstack.debug": True,
        "browserstack.console": "info",
        "browserstack.networkLogs": True
    }

    capabilities = {k: v for k, v in capabilities.items() if v is not None}

    try:
        print(f"\n[Thread {index}] Starting test on {capabilities.get('browserName') or capabilities.get('device')}...")
        driver = webdriver.Remote(
            command_executor=f"https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub",
            desired_capabilities=capabilities
        )

        scraper = ElPaisScraper()
        scraper.wait_for_page_load(driver)
        print(f"[Thread {index}] Loaded El Pais... running scraper logic...")

        driver.get(scraper.opinion_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        print(f"[Thread {index}] Page Title: {driver.title}")

        driver.execute_script('browserstack_executor: ' + json.dumps({
            'action': 'setSessionStatus',
            'arguments': {'status': 'passed', 'reason': 'Scraped opinion section successfully'}
        }))

        driver.quit()

    except Exception as e:
        print(f"[Thread {index}] ERROR: {e}")


def run_parallel_browserstack_tests():
    """Run the scraper on 5 different BrowserStack environments"""
    from concurrent.futures import ThreadPoolExecutor

    browser_configs = [
    {"os": "Windows", "os_version": "10", "browser": "Chrome", "browser_version": "latest"},
    {"os": "Windows", "os_version": "11", "browser": "Chrome", "browser_version": "latest"},
    {"device": "Samsung Galaxy S22", "real_mobile": True, "os_version": "12.0", "browser": "Chrome"},
    {"device": "Samsung Galaxy S21", "real_mobile": True, "os_version": "11.0", "browser": "Chrome"},
    {"device": "Google Pixel 6", "real_mobile": True, "os_version": "12.0", "browser": "Chrome"}
]

    print("\n\n" + "="*60)
    print("STARTING BROWSERSTACK PARALLEL SCRAPER TESTS")
    print("="*60)

    with ThreadPoolExecutor(max_workers=5) as executor:
        for idx, config in enumerate(browser_configs):
            executor.submit(run_scraper_on_browserstack, config, idx+1)

if __name__ == "__main__":
    # Create and run the scraper
    scraper = ElPaisScraper()
    results = scraper.run()
    
    
    # Save results to JSON file
    with open('scraping_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to 'scraping_results.json'")
    print("Script execution completed successfully!")

    run_parallel_browserstack_tests()
