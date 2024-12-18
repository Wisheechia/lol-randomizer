from flask import Flask, jsonify, send_from_directory
from pymongo import MongoClient
from dotenv import load_dotenv
from update_champions import update_champions
from update_items import update_items
import random, os


# Configuration
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "lol-randomizer"
CHAMPIONS_COLLECTION = "champions"
ITEMS_COLLECTION = "items"

# MongoDB client setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Flask app setup
app = Flask(__name__)

# Function to save data to MongoDB
from pymongo.errors import PyMongoError

def save_to_mongo(data, collection_name):
    try:
        # Get the specified collection
        collection = db[collection_name]
        
        # Drop the collection to clear old data (optional)
        collection.drop()
        
        # Insert the new data
        if data:
            collection.insert_many(data)
        else:
            return {"status": "warning", "message": "No data to save."}

        # Return success message
        return {"status": "success", "message": f"Data saved to collection '{collection_name}' successfully."}
    
    except PyMongoError as e:
        # Log the error and return an error response
        return {"status": "error", "message": f"An error occurred while saving data: {str(e)}"}

    except Exception as e:
        # Catch any unexpected errors
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

@app.route('/random_champion', methods=['GET'])
def random_champion():
    try:
        collection = db[CHAMPIONS_COLLECTION]
        count = collection.count_documents({})
        if count == 0:
            return jsonify({"message": "No champions found in the database."}), 404

        random_index = random.randint(0, count - 1)
        random_champion = collection.find().skip(random_index).limit(1).next()
        random_champion.pop("_id", None)  # Remove the ObjectId as it’s not JSON serializable
        print(random_champion["champion"])
        # Get a random spell
        if 'spells' in random_champion and len(random_champion['spells']) > 0:
            filtered_spells = [spell for spell in random_champion['spells'] if spell.get('key_binding') != 'R']

            if len(filtered_spells) == 0:
                return jsonify({"message": "Champion has no spells to randomize (all spells have keybinding 'R')."}), 404

            random_spell = random.choice(filtered_spells)
        else:
            return jsonify({"message": "Champion has no spells."}), 404
        
        # Send back only the champion and one random spell
        return jsonify({
            "champion": random_champion["champion"],
            "sprite": random_champion["sprite"],
            "spell": random_spell
        })
    except Exception as e:
        return jsonify({"message": "Error fetching random champion", "error": str(e)}), 500

@app.route('/random_items', methods=['GET'])
def random_items():
    try:
        collection = db[ITEMS_COLLECTION]
        items = list(collection.find())
        # Ensure that we have at least one item with the "boots" tag
        boots_items = [item for item in items if 'Boots' in item.get('tags', [])]
        if len(boots_items) == 0:
            return jsonify({"message": "No items with the 'boots' tag found."}), 404
        
        # Select 6 random items, ensuring that at least one of them is a boots item
        random_items = random.sample(items, 5)  # Get 5 random items
        random_items.append(random.choice(boots_items))  # Ensure at least one boots item
        
        # Shuffle the list to randomize which item is the boots item
        random.shuffle(random_items)
        
        # Prepare the response
        result_items = [{
            "name": item.get("name"),
            "tags": item.get("tags"),
            "image": item.get("image"),
        } for item in random_items]
        
        return jsonify(result_items)
    
    except Exception as e:
        return jsonify({"message": "Error fetching random items", "error": str(e)}), 500


@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/update_champions', methods=['GET'])
def update_champions_endpoint():
    result = update_champions(save_to_mongo)  # Pass save_to_mongo as a dependency
    return jsonify(result)

@app.route('/update_items', methods=['GET'])
def update_items_endpoint():
    result = update_items(save_to_mongo)  # Pass save_to_mongo as a dependency
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=8000, debug=True)
