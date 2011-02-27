from oscar.controllers import dashboard
from oscar.controllers import admin

ROUTES = [
    ("/", dashboard.IndexHandler),
    ("/new", dashboard.NewUserHandler),
    ("/predictions", dashboard.PredictionLoginHandler),
    ("/predictions/([a-zA-Z0-9\-_]+)", dashboard.PredictionHandler),
    ("/admin", admin.AdminIndexHandler),
    ("/admin/logout", admin.LogoutHandler),
    ("/admin/login", admin.LoginHandler),
    ("/admin/categories/([a-zA-Z0-9\-_]+)", admin.AdminCategoryHandler),
    ("/admin/users/delete/([a-zA-Z0-9\-_]+)", admin.AdminUserDeleteHandler),
    ("/admin/users/([a-zA-Z0-9\-_]+)", admin.AdminUserHandler),
    ("/admin/predictions/([a-zA-Z0-9\-_]+)/delete", admin.AdminPredictionDeleteHandler),
]
