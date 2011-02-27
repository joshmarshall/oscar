from oscar.libraries.handler import Handler
import hashlib
import math
import re
from pymongo.objectid import ObjectId

EMAIL_RE = re.compile("^[^@]+@[a-zA-Z0-9\._\-]+\.[a-zA-Z]+$")

class IndexHandler(Handler):
    
    def get(self):
        
        categories = list(self.db.categories.find().sort('points', -1))
        users = list(self.db.users.find({"admin": False}))
        users_by_id = dict([(user['_id'], user) for user in users])
        nominees = list(self.db.nominees.find())
        predictions = self.db.predictions.find({"user_id":
            { "$in": [user['_id'] for user in users] }
        })
        
        nominees_by_id = dict([
            (nominee['_id'], nominee) 
            for nominee in nominees
        ])
        
        scores = []
        
        users_used = []
        
        for prediction in predictions:
            
            score = 0
            correct = 0
            for category in categories:
                winner = category.get('winner')
                predicted = prediction.get(category['short'], None)
                if winner and predicted and winner == predicted:
                    score += category['points']
                    correct += 1
                    
            inserted = False
            for i in range(0, len(scores)):
                if score > scores[i][1]:
                    scores.insert(i, (prediction['user_id'], score, correct))
                    inserted = True
                    break
                    
            if not inserted:
                scores.append((prediction['user_id'], score, correct))
            users_used.append(prediction['user_id'])
            
        for user in users:
            if user['_id'] not in users_used:
                scores.append((user['_id'], 0, 0))
        
        points = {}
        # should be in descending order
        for category in categories:
            category_points = category.get('points', 0)
            points.setdefault(category_points, [])
            points[category_points].append(category)
        
        # sorting for columns
        keys = points.keys()
        keys.sort(reverse=True)
        columns = []
        
        i = 0
        for key in keys:
            point_cats = points[key]
            split_index = int(math.ceil(len(point_cats) / 2.0))
            left = point_cats[:split_index]
            right = point_cats[split_index:]
            if left:
                columns.insert(0, left)
            if right:
                columns.append(right)
        
        self.render(
            "rank.htm", 
            scores=scores,
            users_by_id=users_by_id,
            columns=columns,
            nominees_by_id=nominees_by_id,
            total=len(categories)
        )
        
class NewUserHandler(Handler):
    
    def get(self):
        self.show_form()
        
    def post(self):
        name = re.sub("[<>/\/]", "", self.get_argument("name", "")).strip()
        username = self.get_argument("username", "").strip()
        email = self.get_argument("email", "").strip()
        password = self.get_argument("password", "")
        
        message = None
        
        if not name or not username or not email or not password:
            return self.show_form("Missing field(s)")
        
        if len(password) < 6:
            return self.show_form("Password is not long enough")
        
        password = hashlib.md5(password).hexdigest()
        user = self.db.users.find_one({"username": username})
        
        if user:
            return self.show_form("Username already claimed")
        user = self.db.users.find_one({"email": email})
        if user:
            return self.show_form("Email already claimed")
            
        if not EMAIL_RE.match(email):
            return self.show_form("Email is not valid")
            
        if re.sub("[^a-z0-9_]", "", username) != username:
            return self.show_form(
                "Username can only be digits or lowercase characters."
            )
            
        user = {
            "name": name,
            "username": username,
            "password": password,
            "email": email,
            "admin": False,
        }
        self.db.users.save(user)
        return self.redirect("/predictions/%s" % user['_id'])
        
    def show_form(self, message=""):
        name = re.sub("[<>/]", "", self.get_argument("name", ""))
        username = self.get_argument("username", "")
        email = self.get_argument("email", "")
        return self.render(
            "new_user.htm", 
            username=username,
            name=name,
            email=email,
            message=message,
            show_nav=False,
            body_class=""
        )
        
class PredictionLoginHandler(Handler):
    """ 
    Doesn't actually 'login' as much as it gives access to
    the predictions.
    """
    
    def get(self):
        return self.show_form()
        
    def post(self):
        username = self.get_argument("username", None)
        password = self.get_argument("password", None)
        
        if not username or not password:
            return self.show_form("Required field missing")
        
        password = hashlib.md5(password).hexdigest()
        user = self.db.users.find_one({
            "username": username,
            "password": password,
            "admin": False
        })
        
        if not user:
            return self.show_form("Your username or password is incorrect.")
            
        return self.redirect("/predictions/%s" % user['_id'])
        
    def show_form(self, message=""):
        return self.render(
            "login.htm", 
            message=message,
            show_nav=False,
            body_class=""
        )
        
        
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

class RankingsHandler(Handler):
    
    def get(self):
        
        categories = list(self.db.categories.find().sort('points', -1))
        users = list(self.db.users.find({"admin": False}))
        users_by_id = dict([(user['_id'], user) for user in users])
        nominees = list(self.db.nominees.find())
        predictions = self.db.predictions.find({"user_id":
            { "$in": [user['_id'] for user in users] }
        })
        
        nominees_by_id = dict([
            (nominee['_id'], nominee) 
            for nominee in nominees
        ])
        
        scores = []
        
        users_used = []
        
        for prediction in predictions:
            
            score = 0
            correct = 0
            for category in categories:
                winner = category.get('winner')
                predicted = prediction.get(category['short'], None)
                if winner and predicted and winner == predicted:
                    score += category['points']
                    correct += 1
                    
            inserted = False
            for i in range(0, len(scores)):
                if score > scores[i][1]:
                    scores.insert(i, (prediction['user_id'], score, correct))
                    inserted = True
                    break
                    
            if not inserted:
                scores.append((prediction['user_id'], score, correct))
            users_used.append(prediction['user_id'])
            
        for user in users:
            if user['_id'] not in users_used:
                scores.append((user['_id'], 0, 0))
           
        self.render(
            "rankings.htm", 
            scores=scores,
            users_by_id=users_by_id,
            nominees_by_id=nominees_by_id,
            total=len(categories)
        )
