from oscar.libraries.handler import AdminHandler
from pymongo.objectid import ObjectId
from tornado.options import options
import tornado.web
import hashlib
import uuid
from time import time

class AdminIndexHandler(AdminHandler):
    
    @tornado.web.authenticated
    def get(self):
        nominees = list(self.db.nominees.find().sort("category_id", 1))
        categories = self.db.categories.find().sort("points", -1)
        users = self.db.users.find()
        predictions_by_user = dict([
            (predict['user_id'], predict)
            for predict in self.db.predictions.find()
        ])
        
        nominees_by_id = dict([
            (nominee['_id'], nominee)
            for nominee in nominees
        ])
        
        return self.render('admin/index.htm',
            nominees = nominees,
            nominees_by_id = nominees_by_id,
            categories = categories,
            users = users,
            predictions_by_user=predictions_by_user
        )

class AdminCategoryHandler(AdminHandler):
    
    @tornado.web.authenticated
    def get(self, category_id):
        category = self.db.categories.find_one(
            {"_id": ObjectId(category_id)}
        )
        if not category:
            self.error(404)
        nominees = self.db.nominees.find(
            {"_id": {"$in": category['nominee_ids'] }}
        )
        return self.render(
            "admin/category.htm", 
            category=category,
            nominees=nominees
        );
        
    @tornado.web.authenticated
    def post(self, category_id):
        points = self.get_argument("points")
        title = self.get_argument("title")
        short = self.get_argument("short")
        locked = self.get_argument('locked', None)
        winner = self.get_argument("winner", None)
        category = self.db.categories.find_one(
            {"_id": ObjectId(category_id)}
        )
        if not category:
            self.error(404)
            
        if not locked:
            locked = False
            
        if winner:
            winner = ObjectId(winner)
            locked = True
        else:
            winner = None
            
        update_spec = {"$set": {
            "points": int(points),
            "title": title,
            "short": short,
            "winner": winner,
            "locked": locked,
        }}
        
        self.db.categories.update(
            {"_id": ObjectId(category_id)}, 
            update_spec, 
            safe=True
        )
        return self.redirect("/admin")
        
class AdminUserHandler(AdminHandler):
    
    @tornado.web.authenticated
    def get(self, user_id):
        user = self.db.users.find_one({
            "_id": ObjectId(user_id),
            "admin": False
        })
        if not user:
            self.error(404)
        return self.render(
            "admin/user.htm", 
            user=user
        );
        
    @tornado.web.authenticated
    def post(self, user_id):
        username = self.get_argument("username")
        email = self.get_argument("email")
        password = self.get_argument("password", None)
        if password:
            password = hashlib.md5(password).hexdigest()
        user = self.db.users.find_one({
            "_id": ObjectId(user_id),
            "admin": False,
        })
        if not user:
            self.error(404)
            
        update_spec = {"$set": {
            "username": username,
            "email": email,
        }}
        if password:
            update_spec["$set"]["password"] = password
        
        self.db.users.update(
            {"_id": ObjectId(user_id)}, 
            update_spec, 
            safe=True
        )
        return self.redirect("/admin")
        
class AdminUserDeleteHandler(AdminHandler):
    
    @tornado.web.authenticated
    def get(self, user_id):
        user = self.db.users.find_one({
            "_id": ObjectId(user_id),
            'admin': False,
        })
        if not user:
            self.error(404)
        self.db.users.remove({"_id": ObjectId(user_id)})
        self.redirect("/admin")
        
class AdminPredictionDeleteHandler(AdminHandler):
    
    @tornado.web.authenticated
    def get(self, user_id):
        user = self.db.users.find_one({
            "_id": ObjectId(user_id),
            'admin': False
        })
        if not user:
            self.error(404)
        self.db.predictions.remove({"user_id": ObjectId(user_id)})
        self.redirect("/admin")
        
        
class LoginHandler(AdminHandler):
    
    def get(self):
        next = self.get_argument('next', '/admin')
        if self.get_current_user():
            return self.redirect(next)
        self.render('admin/login.htm', next=next)
        
    def post(self):
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        next = self.get_argument("next", "/admin")
        
        redirect = "/admin/login"
        if not username or not password:
            return self.redirect(redirect)
        
        md5pass = hashlib.md5(password).hexdigest()
        
        admin = self.db.users.find_one({
            "username": username,
            "password": md5pass,
            'admin': True
        })
        
        if not admin:
            return self.redirect(redirect)
        
        cookie = self.db.cookies.find_one({"user_id": admin['_id']})
        if cookie and cookie['expires']  < time():
            self.db.cookies.remove(cookie['_id'])
            cookie = None
            
        if not cookie:
            cookie = {
                "_id": uuid.uuid4().hex, 
                "user_id": admin['_id'],
                "expires": time()+3600 # one hour
            }
            self.db.cookies.save(cookie)
        
        self.set_cookie(options.user_cookie, cookie['_id'])
        return self.redirect(redirect)

class LogoutHandler(AdminHandler):
    """ Just clears cookies and redirects to login page """
    
    def get(self):
        cookie_value = self.get_cookie(options.user_cookie)
        self.db.cookies.remove({"_id": cookie_value})
        self.clear_cookie(options.user_cookie)
        return self.redirect("/admin/login")
