import json
from nepse_scraper import  Nepse_scraper

# Create object from Nepse_scraper class
request_obj = Nepse_scraper()

try:
    # Get all securities data
    securities_data = request_obj.is_trading_day()
    
    # Print the data for verification
    print(securities_data)
    
    # # Write to JSON file
    with open('qsecurities.json', 'w', encoding='utf-8') as f:
        json.dump(securities_data, f, indent=4, ensure_ascii=False)
    print("Data successfully written to qsecurities.json")
    
except Exception as e:
    print(f"Error fetching or saving data: {e}")

# import asyncio
# from nepse_scraper import  scraper as Nepse_scraper  # Assuming your class is in nepse_scraper.py

# scraper = Nepse_scraper()
# result = asyncio.run(scraper.is_trading_day())
# print(result)