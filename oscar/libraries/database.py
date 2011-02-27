import pymongo
from tornado.options import define, options

define("database", "oscars")

VALID_COLLECTIONS = [
    "users", "admins", "nominees", "categories",
    "predictions", "rankings", "cookies"
]

class Database(object):
    """ Instancing the connection """
    
    _instance = None
    _connection = None
    
    @classmethod
    def instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
        
    def connect(self):
        if not self._connection:
            conn = pymongo.Connection()
            self._connection = conn
        return self._connection
        
    def disconnect(self):
        if self._connection:
            self._connection.disconnect()
    
    def __getattr__(self, name):
        if name not in VALID_COLLECTIONS:
            raise AttributeError("Collection %s is not valid." % name)
        coll = self.connect()[options.database][name]
        return coll
        
    def __del__(self):
        self.disconnect()
