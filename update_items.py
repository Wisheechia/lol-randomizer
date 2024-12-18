import requests

# Riot Data Dragon URL for items
BASE_URL = "https://ddragon.leagueoflegends.com/cdn/12.23.1/data/en_US/item.json"

# Function to fetch items data from Riot's Data Dragon API
def update_items(save_to_mongo):
    try:
        # Fetch items data from Riot API Data Dragon
        url = BASE_URL
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for invalid responses
        
        # Extract the data (just the items dictionary)
        data = response.json()['data']
        
        # Prepare the simplified item data with only the image, name, and check for final items
        final_items = []  # Only final items will be stored here
        boots = []  # Boots are separated, but we store only final items in the final_items list
        
        for item_id, item in data.items():
            item_data = {
                "item_id": item_id,
                "name": item.get("name", "Unknown Name"),
                "image": item.get("image", {}).get("full", "No image available"),
                "tags": item.get("tags", []),
            }
            
            # Check if the item ID is greater than 3000 and it doesn't "into" anything
            if int(item_id) > 3000 and not item.get("into") and item.get("maps").get("11"):
                final_items.append(item_data)  # Add to final items list
            
            # Check if the item is a "Boots" item (Optional: separate for any other purpose)
            if "Boots" in item_data["name"]:
                boots.append(item_data)  # Separate boots items, but they're not stored unless final
            
        # Save only final items to MongoDB
        result = save_to_mongo(final_items, "items")  # Save only final items
        return result

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Error fetching data from Riot API: {str(e)}"}
