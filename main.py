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
import random

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
            return False

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
        self.redirect_to("signin")


class KdosemHandler(BaseHandler):

    def get(self):
        user = User.query().get()
        params = {"user": user}
        self.render_template("kdosem.html", params)

class UraHandler(BaseHandler):

    def get(self):
        user = User.query().get()
        url = "https://script.googleusercontent.com/macros/echo?user_content_key=fG8dZvZ_Q4j4Dax5lS3YNDHBbNkRoqqFZe9cdu0HqJOkgcUXGKnCzBV8Js4T3uCs6rqXQRkXcZo7vCSIotZHBs-FDYLjcOhxm5_BxDlH2jW0nuo2oDemN9CCS2h10ox_1xSncGQajx_ryfhECjZEnJ9GRkcRevgjTvo8Dc32iw_BLJPcPfRdVKhJT5HNzQuXEeN3QFwl2n0M6ZmO-h7C6bwVq0tbM60-YSRgvERRRx-Tfxfwq6gY2Rp2qpLh6fRh&lib=MwxUjRcLr2qLlnVOLh12wSNkqcO1Ikdrk"
        result = urlfetch.fetch(url)
        podatki = json.loads(result.content)
        params = {"podatki": podatki,"user": user}
        self.render_template("ura.html", params)

class LokacijaHandler(BaseHandler):

    def get(self):

        user = User.query().get()
        url = "http://www.telize.com/geoip"
        result = urlfetch.fetch(url)
        podatki2 = json.loads(result.content)
        params = {"podatki2": podatki2,"user": user}
        self.render_template("lokacija.html", params)

class PocutjeHandler(BaseHandler):

    def get(self):
        pocutje = ["super", "dobro", "slabo"]
        trenutno = random.choice(pocutje)
        params = {"trenutno": trenutno}
        self.render_template("kakosem.html", params)

app = webapp2.WSGIApplication([
    webapp2.Route('/', MainHandler, name="main"),
    webapp2.Route('/registration', CreateAccountHandler, name="registration"),
    webapp2.Route('/signin', SigninHandler, name="signin"),
    webapp2.Route('/kdosem', KdosemHandler),
    webapp2.Route('/signout', SignoutHandler),
    webapp2.Route('/ura', UraHandler),
    webapp2.Route('/lokacija', LokacijaHandler),
    webapp2.Route('/kakosem', PocutjeHandler),

], debug=True)
