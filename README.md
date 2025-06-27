# El País Opinion Scraper

A robust web scraper for extracting opinion articles from El País newspaper's website. This scraper includes advanced features like cross-browser testing, parallel processing, automatic translation, and BrowserStack integration for testing across multiple environments.

## Features

- **Smart Article Extraction**: Scrapes the first 5 opinion articles from El País while intelligently filtering out sidebar content and "Lo más visto" (Most Viewed) sections
- **Content Analysis**: Extracts full article content, titles, and associated images
- **Automatic Translation**: Translates Spanish article titles to English using Google Translate API
- **Word Frequency Analysis**: Analyzes repeated words in translated titles
- **Image Download**: Automatically downloads article images to local storage
- **Cross-Browser Testing**: Tests scraper functionality across different browser configurations
- **Parallel Processing**: Supports concurrent translation and processing tasks
- **BrowserStack Integration**: Runs tests across multiple real devices and browsers in the cloud

## Prerequisites

- Python 3.7+
- Chrome browser installed
- BrowserStack account (for cloud testing)
- RapidAPI account with Google Translate access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/browserstack-scraper.git
cd browserstack-scraper
```

2. Install required dependencies:
```bash
pip install selenium webdriver-manager requests
```

3. Set up your API credentials:
   - Replace `rapidapi_key` in the code with your RapidAPI key
   - Update BrowserStack credentials (`BROWSERSTACK_USERNAME` and `BROWSERSTACK_ACCESS_KEY`)

## Configuration

### Required API Keys

1. **RapidAPI Key**: For Google Translate functionality
   - Sign up at [RapidAPI](https://rapidapi.com/)
   - Subscribe to Google Translate API
   - Replace the key in the `ElPaisScraper` class

2. **BrowserStack Credentials**: For cloud testing
   - Sign up at [BrowserStack](https://www.browserstack.com/)
   - Get your username and access key
   - Update the credentials in the `run_scraper_on_browserstack` function

## Usage

### Basic Scraping

Run the main scraper:
```bash
python "BrowserStack Scraper.py"
```

This will:
1. Scrape 5 opinion articles from El País
2. Extract titles, content, and images
3. Translate titles to English
4. Analyze word frequency
5. Save results to `scraping_results.json`

### BrowserStack Testing

The script includes parallel testing across 5 different browser/device configurations:
- Windows 10 & 11 with Chrome
- Samsung Galaxy S22, S21, and Google Pixel 6

## Project Structure

```
├── BrowserStack Scraper.py    # Main scraper script
├── scraping_results.json      # Output file with scraped data
├── images/                    # Downloaded article images
│   ├── article_1_image.jpg
│   ├── article_2_image.jpg
│   └── ...
└── README.md                  # This file
```

## Output

The scraper generates:

1. **Console Output**: Real-time progress and status updates
2. **JSON File**: Complete scraped data including:
   - Original Spanish titles and content
   - Translated English titles
   - Image URLs and download status
   - Word frequency analysis
3. **Image Files**: Downloaded article images in the `images/` directory

### Sample Output Structure

```json
{
  "articles": [
    {
      "title": "Original Spanish Title",
      "content": "Article content...",
      "image_url": "https://...",
      "article_number": 1
    }
  ],
  "translated_titles": ["Translated English Title"],
  "repeated_words": {
    "politics": 3,
    "spain": 2
  }
}
```

## Advanced Features

### Cross-Browser Testing
Tests the scraper across different browser configurations to ensure compatibility.

### Parallel Processing
Uses ThreadPoolExecutor for concurrent translation tasks, improving performance for large datasets.

### Smart Content Filtering
Implements multiple strategies to avoid scraping sidebar content, advertisements, or "Most Viewed" sections.

### Error Handling
Comprehensive error handling for network issues, element not found exceptions, and API failures.

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**: The script automatically downloads ChromeDriver, but ensure Chrome browser is installed
2. **Timeout Errors**: Increase wait times in `wait_for_page_load()` if you have a slow internet connection
3. **Translation Failures**: Check your RapidAPI key and subscription status
4. **BrowserStack Errors**: Verify your credentials and account limits

### Debug Mode

Set `headless=False` in the `scrape_opinion_articles()` method to see the browser in action:
```python
driver = self.setup_driver(headless=False)
```

## Rate Limiting

The scraper includes built-in delays to be respectful to the target website:
- 2-second delays between page loads
- Timeout handling for various operations
- Respectful scraping practices

## Legal Disclaimer

This scraper is for educational and research purposes only. Always:
- Respect the website's robots.txt file
- Follow the website's terms of service
- Don't overload servers with excessive requests
- Use scraped data responsibly and ethically

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- El País for providing quality journalism
- Selenium WebDriver for browser automation
- BrowserStack for cross-browser testing capabilities
- RapidAPI for translation services
