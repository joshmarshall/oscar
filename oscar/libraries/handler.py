import tornado.web
import time
from tornado.options import define, options
from oscar.libraries.database import Database

define("user_cookie", "cookie", help="the name of the user cookie")

class Handler(tornado.web.RequestHandler):
    # Master database instance
    db = Database.instance()
    
    def get_current_user(self):
        """ Retrieve user from cookie """
        value = self.get_cookie(options.user_cookie)
        if not value:
            return None
        cookie = self.db.cookies.find_one({'_id': value})
        if not cookie:
            return None
        if cookie['expires'] < time.time():
            self.db.cookies.remove({"_id": cookie['_id']})
            self.clear_cookie(options.user_cookie)
            return None
        user = self.db.users.find_one({"_id": cookie["user_id"]})
        return user
        
    def error(self, code, message = ""):
        raise tornado.web.HTTPError(code)
    
    def render(self, *args, **kwargs):
        kwargs.setdefault('body_class', 'normal')
        kwargs.setdefault("show_nav", True)
        return tornado.web.RequestHandler.render(self, *args, **kwargs)
    
class AdminHandler(Handler):
    
    def get_current_user(self):
        """ Verify the user is admin """
        user = Handler.get_current_user(self)
        if user and not user['admin']:
            return None
        return user
