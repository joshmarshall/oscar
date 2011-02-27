import tornado.web
import tornado.ioloop
import controllers
from tornado.options import define, options
import logging
import sys
import os

define("port", 8888, type=int, help="the port the server runs on")
define("login_url", "/login", help="the login url")
define("view_path", os.path.join(os.path.dirname(__file__), "views"))
define("static_path", os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../static")
))

def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application(
        controllers.ROUTES,
        login_url=options.login_url,
        template_path=options.view_path,
        static_path=options.static_path
    )
    application.listen(tornado.options.options.port)
    logging.info("Starting server on port %d", tornado.options.options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
