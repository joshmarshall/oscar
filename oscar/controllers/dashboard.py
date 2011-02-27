from oscar.libraries.handler import Handler
import hashlib
from pymongo.objectid import ObjectId

class IndexHandler(Handler):
    
    def get(self):
        
        categories = list(self.db.categories.find().sort('points', -1))
        users = list(self.db.users.find({"admin": False}))
        users_by_id = dict([(user['_id'], user) for user in users])
        predictions = self.db.predictions.find({"user_id":
            { "$in": [user['_id'] for user in users] }
        })
        
        scores = []
        
        users_used = []
        
        for prediction in predictions:
            
            score = 0
            for category in categories:
                winner = category.get('winner')
                predicted = prediction.get(category['short'], None)
                if winner and predicted and winner == predicted:
                    score += category['points']
                    
            inserted = False
            for i in range(0, len(scores)):
                if score > scores[i][1]:
                    scores.insert(i, (prediction['user_id'], score))
                    inserted = True
                    break
                    
            if not inserted:
                scores.append((prediction['user_id'], score))
            users_used.append(prediction['user_id'])
            
        for user in users:
            if user['_id'] not in users_used:
                scores.append((user['_id'], 0))
        
        print scores
        self.render(
            "rank.htm", 
            scores=scores,
            users_by_id=users_by_id
        );
        
class NewUserHandler(Handler):
    
    def get(self):
        self.render("new_user.htm", message=None)
        
    def post(self):
        username = self.get_argument("username")
        email = self.get_argument("email")
        password = self.get_argument("password")
        password = hashlib.md5(password).hexdigest()
        user = self.db.users.find_one({"username": username})
        if user:
            return self.render("new_user.htm", message="Username taken.")
        user = self.db.users.find_one({"email": email})
        if user:
            return self.render("new_user.htm", message="Email taken.")
        user = {
            "username": username,
            "password": password,
            "email": email,
            "admin": False,
        }
        self.db.users.save(user)
        return self.redirect("/prediction/%s" % user['_id'])
        
class PredictionHandler(Handler):
    
    def get(self, user_id):
        user = self.db.users.find_one({
            "_id": ObjectId(user_id),
            "admin": False
        })
        if not user:
            self.error(404)
        categories = self.db.categories.find().sort("points", -1)
        nominee_by_id = dict([
            (nominee['_id'], nominee)
            for nominee in 
            self.db.nominees.find()
        ])
        predictions = self.db.predictions.find_one({
            "user_id": ObjectId(user_id)
        })
        if not predictions:
            predictions = {}
            
        print predictions
            
        self.render(
            "predictions.htm",
            user=user,
            categories=categories,
            nominee_by_id=nominee_by_id,
            predictions=predictions
        )
        
    def post(self, user_id):
        user = self.db.users.find_one({
            "_id": ObjectId(user_id),
            "admin": False
        })
        if not user:
            self.error(404)
        categories = self.db.categories.find()
        predictions = self.db.predictions.find_one({
            "user_id": ObjectId(user_id)
        })
        if not predictions:
            predictions = {"user_id": ObjectId(user_id)}
        for category in categories:
            if category.get('locked'):
                continue
            prediction = self.get_argument(category['short'], None)
            if not prediction:
                continue
            prediction = ObjectId(prediction)
            predictions[category['short']] = prediction
            
        self.db.predictions.save(predictions)
        return self.redirect("/")
