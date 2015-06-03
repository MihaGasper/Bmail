#!/usr/bin/env python
import os
import jinja2
import webapp2
from models import User
import hashlib
import hmac
import datetime
from secret import secret
import time
from models import Message
from google.appengine.api import urlfetch
import json

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)


class BaseHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        cookie_value = self.request.cookies.get("uid")

        if cookie_value:
            params["login"] = self.checkcookie(cookie_vrednost=cookie_value)
        else:
            params["login"] = False

        template = jinja_env.get_template(view_filename)
        self.response.out.write(template.render(params))

    def createcookie(self, user):
        user_id = user.key.id()
        expires = datetime.datetime.utcnow() + datetime.timedelta(days=10)
        expires_ts = int(time.mktime(expires.timetuple()))
        code = hmac.new(str(user_id), str(secret) + str(expires_ts), hashlib.sha1).hexdigest()
        vrednost = "{0}:{1}:{2}".format(user_id, code, expires_ts)
        self.response.set_cookie(key="uid", value=vrednost, expires=expires)

    def checkcookie(self, cookie_vrednost):
        if cookie_vrednost == "empty":
            self.redirect_to("signin")
            return

        else:
            user_id, code, expires_ts = cookie_vrednost.split(":")
            if datetime.datetime.utcfromtimestamp(float(expires_ts)) > datetime.datetime.now():
                check = hmac.new(str(user_id), str(secret) + str(expires_ts), hashlib.sha1).hexdigest()

                if code == check:
                    return True
                else:
                    self.redirect_to("signin")
                    return

            else:
                return False

    def render_template(self, view_filename, params=None):
        if not params:
            params = {}

        cookie_value = self.request.cookies.get("uid")

        if cookie_value:
            params["login"] = self.checkcookie(cookie_vrednost=cookie_value)
        else:
            params["login"] = False

        template = jinja_env.get_template(view_filename)
        self.response.out.write(template.render(params))


class MainHandler(BaseHandler):

    def get(self):
        self.render_template("hello.html")

class CreateAccountHandler(BaseHandler):

    def get(self):
        self.render_template("registration.html")

    def post(self):
        name = self.request.get("name")
        surname = self.request.get("surname")
        email = self.request.get("email")
        password = self.request.get("password")
        check_password = self.request.get("check_password")


        if password == check_password:
            user = User.query(User.email == email).get()
            if user:
                return self.write("Uporabnik s tem emailom ze obstaja")
            else:
                user1 = User.create(name=name, surname=surname, email=email, original_password=password)
                self.createcookie(user=user1)
                return self.redirect_to("main")
        else:
            self.write("Ponovljeno geslo je napacno")
            params={"name":name, "surname":surname, "email":email}
            return self.render_template("registration.html", params=params)

class SigninHandler(BaseHandler):

    def get(self):
        self.render_template("signin.html")

    def post(self):
        email = self.request.get("email")
        password = self.request.get("password")

        user = User.query(User.email == email).get()

        if User.check_password(original_password=password, user=user):
            self.createcookie(user=user)
            self.redirect_to("main")
            return
        else:
            return self.write("Napacno geslo ali email")

class SignoutHandler(BaseHandler):

    def get(self):
        self.request.cookies.get("uid")
        expires = datetime.datetime.utcnow()
        self.response.set_cookie(key="uid", value="empty", expires=expires)

class PoslanoHandler(BaseHandler):

    def get(self):
        cookie_value = self.request.cookies.get("uid")
        if self.checkcookie(cookie_vrednost=cookie_value):
            user_id, code, expires_ts = cookie_value.split(":")
            user = User.get_by_id(int(user_id))
            list = Message.query(Message.sender==user.email).fetch()
            params = {"list": list, "user":user}
            self.render_template("poslano.html", params=params)

class PosameznoposlanosporociloHandler(BaseHandler):

    def get(self, message_id):
            message = Message.get_by_id(int(message_id))
            params = {"message": message}
            self.render_template("poslanosporocilo.html", params=params)

class PosameznoprejetosporociloHandler(BaseHandler):

    def get(self, message_id):
            message = Message.get_by_id(int(message_id))
            params = {"message": message}
            self.render_template("prejetosporocilo.html", params=params)

class PrejetoHandler(BaseHandler):

    def get(self):
        cookie_value = self.request.cookies.get("uid")
        if self.checkcookie(cookie_vrednost=cookie_value):
            user_id, code, expires_ts = cookie_value.split(":")
            user = User.get_by_id(int(user_id))
            list = Message.query(Message.receiver==user.email).fetch()
            params = {"list": list, "user": user}
        self.render_template("prejeto.html", params=params)

class NovosporociloHandler(BaseHandler):

    def get(self):
        self.render_template("novosporocilo.html")

class RezultatHandler(BaseHandler):

    def post(self):
        cookie_value = self.request.cookies.get("uid")
        if self.checkcookie(cookie_vrednost=cookie_value):
            user_id, code, expires_ts = cookie_value.split(":")
            sender = User.get_by_id(int(user_id))
            receiver = self.request.get("receiver")
            name1 = self.request.get("name1")
            body = self.request.get("body")

        Message.createmessage(name1=name1, body=body, sender=sender.email, receiver=receiver)

        self.render_template("novosporocilo.html")
        self.write("Sporocilo poslano")

class WeatherHandler(BaseHandler):

    def get(self):
        url = "http://api.openweathermap.org/data/2.5/weather?q=Kamnik,si&units=metric"
        result = urlfetch.fetch(url)
        podatki = json.loads(result.content)
        params = {"podatki": podatki}
        self.render_template("vreme.html", params)


app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name="main"),
    webapp2.Route('/registration', CreateAccountHandler, name="registration"),
    webapp2.Route('/signin', SigninHandler, name="signin"),
    webapp2.Route('/rezultat', RezultatHandler),
    webapp2.Route('/signout', SignoutHandler),
    webapp2.Route('/poslano', PoslanoHandler),
    webapp2.Route('/poslano/<message_id:\d+>', PosameznoposlanosporociloHandler),
    webapp2.Route('/prejeto/<message_id:\d+>', PosameznoprejetosporociloHandler),
    webapp2.Route('/prejeto', PrejetoHandler),
    webapp2.Route('/novosporocilo', NovosporociloHandler, name="novosporocilo"),
    webapp2.Route('/vreme', WeatherHandler),

], debug=True)
