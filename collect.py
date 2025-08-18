from typing import List
import requests
import json
import time

def fetch_all_tickers(api_key: str, delay: float = 2.5) -> List[str]:
    base_url = "https://api.polygon.io/v3/reference/tickers"
    params = {
        "market": "stocks",
        "active": "true",
        "order": "asc",
        "limit": "1000",
        "sort": "ticker",
        "apiKey": api_key
    }
    
    all_tickers = []
    current_url = base_url
    request_count = 0
    
    print("Starting to fetch tickers...")
    
    while current_url:
        try:
            response = requests.get(current_url, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            # Extract tickers from results
            if "results" in data and data["results"]:
                batch_tickers = [result["ticker"] for result in data["results"]]
                all_tickers.extend(batch_tickers)
                
                request_count += 1
                print(f"Request {request_count}: Fetched {len(batch_tickers)} tickers "
                      f"(Total: {len(all_tickers)})")
                
                # Get next URL for pagination
                current_url = data.get("next_url")
                print(current_url)
                
                # Add delay to respect rate limits
                if current_url and delay > 0:
                    time.sleep(delay)
            else:
                print("No results found in response")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            break
        except KeyError as e:
            print(f"Unexpected response structure: {e}")
            break
    
    print(f"\nCompleted! Total tickers collected: {len(all_tickers)}")
    return all_tickers

def load_existing_tickers(filename: str = "tickers.json") -> List[str]:
    """
    Load existing tickers from tickers.json file
    
    Args:
        filename: Tickers JSON filename
    
    Returns:
        List of ticker symbols from existing file
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Handle different possible formats
        if isinstance(data, list):
            # Direct array of tickers
            existing_tickers = [str(ticker) for ticker in data if ticker]
        elif isinstance(data, dict):
            # Dictionary format - extract values or tickers
            existing_tickers = []
            for key, value in data.items():
                if isinstance(value, str):
                    existing_tickers.append(value)
                elif isinstance(value, dict) and 'ticker' in value:
                    existing_tickers.append(value['ticker'])
        else:
            print(f"Unexpected format in {filename}")
            return []
        
        print(f"Loaded {len(existing_tickers)} existing tickers from {filename}")
        return existing_tickers
        
    except FileNotFoundError:
        print(f"Existing tickers file {filename} not found, starting fresh...")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing existing tickers JSON: {e}")
        return []
    except Exception as e:
        print(f"Error loading existing tickers: {e}")
        return []

def load_sec_tickers(filename: str = "sec_tickers.json") -> List[str]:
    """
    Load tickers from SEC tickers JSON file
    
    Args:
        filename: SEC tickers JSON filename
    
    Returns:
        List of ticker symbols from SEC file
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Extract tickers from the SEC format
        sec_tickers = []
        for key, value in data.items():
            if isinstance(value, dict) and 'ticker' in value:
                sec_tickers.append(value['ticker'])
        
        print(f"Loaded {len(sec_tickers)} tickers from {filename}")
        return sec_tickers
        
    except FileNotFoundError:
        print(f"SEC tickers file {filename} not found, skipping...")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing SEC tickers JSON: {e}")
        return []
    except Exception as e:
        print(f"Error loading SEC tickers: {e}")
        return []

def save_tickers_to_file(tickers: List[str], filename: str = "tickers.json") -> None:
    """
    Save tickers list to JSON file
    
    Args:
        tickers: List of ticker symbols
        filename: Output filename
    """
    try:
        with open(filename, 'w') as f:
            json.dump(tickers, f, indent=2)
        print(f"Tickers saved to {filename}")
    except IOError as e:
        print(f"Error saving to file: {e}")

def main():
    # Your API key
    API_KEY = "CpZj6msyprLmcgjcsDABdog6B1OBdHtj"
    
    # Load existing tickers first
    existing_tickers = load_existing_tickers("tickers.json")
    
    # Fetch all tickers from Polygon API
    polygon_tickers = fetch_all_tickers(API_KEY, delay=0.1)
    
    # Load SEC tickers
    sec_tickers = load_sec_tickers("sec_tickers.json")
    
    # Combine all tickers and remove duplicates while preserving order
    all_tickers = existing_tickers + polygon_tickers + sec_tickers
    unique_tickers = list(dict.fromkeys(all_tickers))  # Preserves order, removes duplicates
    
    if unique_tickers:
        # Save to JSON file
        save_tickers_to_file(unique_tickers, "tickers.json")
        
        # Print some statistics
        print(f"\nStatistics:")
        print(f"Existing tickers: {len(existing_tickers)}")
        print(f"Polygon API tickers: {len(polygon_tickers)}")
        print(f"SEC tickers: {len(sec_tickers)}")
        print(f"Total before dedup: {len(all_tickers)}")
        print(f"Total unique tickers: {len(unique_tickers)}")
        print(f"Duplicates removed: {len(all_tickers) - len(unique_tickers)}")
        
    else:
        print("No tickers were collected")

if __name__ == "__main__":
    main()
