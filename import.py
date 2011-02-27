import json
import pymongo
import string
import hashlib
import re
from oscar.libraries.database import Database

def main():
    
    db = Database.instance()

    data = json.loads(open('oscars.json', 'r').read())

    db.categories.remove()
    db.nominees.remove()
    db.users.remove()

    for category in data:
        
        title = string.capwords(category['title'].lower())
        short = re.sub("[^a-zA-Z0-9\s_]", "", category['short'])
        short = re.sub("\s", "_", short)
        
        cat_data = {
            'title': title,
            'short': short,
            'winner': None,
            'locked': False,
        }
            
        nominee_ids = []
        
        cat_id = db.categories.save(cat_data, safe=True)
        for nominee in category['nominees']:
            nominee['category_id'] = cat_id
            nominee_id = db.nominees.save(nominee, safe=True)
            nominee_ids.append(nominee_id)
            
        cat_data['_id'] = cat_id
        cat_data['nominee_ids'] = nominee_ids
        db.categories.save(cat_data, safe=True)
        
    admin = {
        "username": "admin",
        "name": "Admin",
        "admin": True,
        "password": hashlib.md5("password").hexdigest()
    }
    db.users.save(admin, safe=True)
    
        
if __name__ == "__main__":
    main()
