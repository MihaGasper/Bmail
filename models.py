import hashlib
import hmac
import uuid
from google.appengine.ext import ndb


class User(ndb.Model):
    name = ndb.StringProperty()
    surname = ndb.StringProperty()
    email = ndb.StringProperty()
    code_password = ndb.StringProperty()

    @classmethod
    def create(cls, name, surname, email, original_password):
        user = cls(name=name, surname=surname, email=email, code_password=cls.coding_password(original_password=original_password))
        user.put()
        return user

    @classmethod
    def coding_password(cls, original_password):
        salt = uuid.uuid4().hex
        code = hmac.new(str(salt), str(original_password), hashlib.sha512).hexdigest()
        return "%s:%s" % (code, salt)

    @classmethod
    def check_password(cls, original_password, user):
        code, salt = user.code_password.split(":")
        check = hmac.new(str(salt), str(original_password), hashlib.sha512).hexdigest()

        if check == code:
            return True
        else:
            return False

class Message(ndb.Model):

    sender = ndb.StringProperty()
    receiver = ndb.StringProperty()
    name1 = ndb.StringProperty()
    body = ndb.TextProperty()
    created = ndb.DateProperty(auto_now_add=True)

    @classmethod
    def createmessage(cls, name1, body, sender, receiver):
        message = cls(name1=name1, body=body, sender=sender, receiver=receiver)
        message.put()
