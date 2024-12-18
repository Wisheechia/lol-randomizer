import requests

BASE_URL = "https://ddragon.leagueoflegends.com/cdn/12.23.1/data/en_US/"

# Function to fetch all champions
def get_champions():
    url = f"{BASE_URL}champion.json"
    response = requests.get(url)
    if response.status_code == 200:
        champions_data = response.json()
        return champions_data['data']
    else:
        print(f"Error fetching champions: {e}")
        return None

# Function to fetch detailed data about a specific champion
def get_champion_details(name):
    url = f"{BASE_URL}champion/{name}.json"
    response = requests.get(url)
    if response.status_code == 200:
        champions_data = response.json()
        return champions_data['data']
    else:
        print(f"Error fetching details for champion {name}: {e}")
        return None

# Function to assign key bindings based on the spell's index (0 -> Q, 1 -> W, 2 -> E, 3 -> R)
def assign_key_binding(spell_index):
    key_bindings = ['Q', 'W', 'E', 'R']
    if spell_index < len(key_bindings):
        return key_bindings[spell_index]
    return "Unknown"  # Default if no binding exists (though should not occur with 4 spells)

def parse_champion_data(champ_key, champion_info):
    try:
        sprite = champion_info[champ_key].get("image").get("full", "Unknown image")
        spells = champion_info[champ_key].get("spells")
        parsed_spells = [
            {
                "spell_name": spell.get("name", "Unknown Name"),
                "image_name": spell.get("image", {}).get("full", "Unknown Image"),
                "key_binding": assign_key_binding(i)  # Assign key binding based on index
            }
            for i, spell in enumerate(spells)
        ]

        return {
            "champion": champ_key,
            "sprite": sprite,
            "spells": parsed_spells
        }
    except KeyError as e:
        print(f"Error parsing data for champion {champ_key}: {e}")
        return None

def update_champions(save_to_mongo):
    try:
        champions = get_champions()
        if not champions:
            return {"message": "Failed to fetch champions data."}, 500

        champions_data = []
        for champ_key, champ in champions.items():
            champion_info = get_champion_details(champ_key)
            if not champion_info:
                print(f"Skipping champion {champ_key} due to missing data.")
                continue

            # Parse and structure the data
            parsed_data = parse_champion_data(champ_key, champion_info)
            if parsed_data:
                champions_data.append(parsed_data)

        # Save the data to MongoDB
        save_result = save_to_mongo(champions_data, "champions")
        if save_result.get("status") == "success":
            return {"message": "Champions updated successfully!"}
        else:
            return {"message": save_result.get("message")}, 500

    except Exception as e:
        print(f"Unexpected error during champion update: {e}")
        return {"message": "An error occurred while updating champions."}, 500
