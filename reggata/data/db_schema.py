'''
Copyright 2010 Vitaly Volkov
Created on 11.10.2010

Database schema of Reggata repository entities.
'''
import sqlalchemy as sqa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, orm
import datetime
import os
import hashlib
import reggata.memento as memento
import reggata.helpers as helpers
from reggata.helpers import is_none_or_empty



class JsonUnsupportedVersionError(Exception):
    def __init__(self, msg=None, cause=None):
        super(JsonUnsupportedVersionError, self).__init__(msg)
        self.cause = cause



Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    USER = 'USER'
    ADMIN = 'ADMIN'

    login = sqa.Column(sqa.String, primary_key=True)
    password = sqa.Column(sqa.String)
    group = sqa.Column(sqa.Enum(USER, ADMIN), nullable=False, default=USER)
    date_created = sqa.Column(sqa.DateTime)

    def __init__(self, login=None, password=None, group=USER):
        self.login = login
        self.password = password
        self.group = group
        self.date_created = datetime.datetime.today()

    def checkValid(self):
        if helpers.is_none_or_empty(self.login):
            raise ValueError("Attribute User.login shouldn't be empty.")
        return True

# TODO: this class is deprecated and is not used in the code now. Will be removed maybe in the future
class HistoryRec(Base):
    '''
        This is a record of Item instance creation/modification/deletion.
    '''
    __tablename__ = "history_recs"

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    MERGE = "MERGE"

    id = sqa.Column(sqa.Integer, primary_key=True)
    parent1_id = sqa.Column(sqa.Integer, ForeignKey("history_recs.id"))
    parent2_id = sqa.Column(sqa.Integer, ForeignKey("history_recs.id"))
    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"))
    item_hash = sqa.Column(sqa.String)
    data_ref_hash = sqa.Column(sqa.String)
    data_ref_url_raw = sqa.Column(sqa.String, name="data_ref_url")
    operation = sqa.Column(sqa.Enum(CREATE, UPDATE, DELETE, MERGE))
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))

    def __init__(self, item_id=None, item_hash=None, data_ref_hash=None, \
                 data_ref_url=None, operation=None, user_login=None, \
                 parent1_id=None, parent2_id=None):
        self.item_id = item_id
        self.item_hash = item_hash
        self.data_ref_hash = data_ref_hash
        self.data_ref_url = data_ref_url
        self.operation = operation
        self.user_login = user_login
        self.parent1_id = parent1_id
        self.parent2_id = parent2_id

    def _get_data_ref_url(self):
        if not is_none_or_empty(self.data_ref_hash):
            return helpers.from_db_format(self.data_ref_url_raw)
        else:
            return self.data_ref_url_raw

    def _set_data_ref_url(self, value):
        if not is_none_or_empty(self.data_ref_hash):
            self.data_ref_url_raw = helpers.to_db_format(value)
        else:
            self.data_ref_url_raw = value

    data_ref_url = property(_get_data_ref_url, _set_data_ref_url, 'Свойство data_ref_url.')


    def __eq__(self, obj):
        if self.item_id != obj.item_id:
            return False
        if self.item_hash != obj.item_hash:
            return False
        if self.data_ref_hash != obj.data_ref_hash:
            return False
        if self.data_ref_url != obj.data_ref_url:
            return False
        if self.user_login != obj.user_login:
            return False

        return True

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __str__(self):
        s = "item_id={}, item_hash={}, data_ref_hash={}, data_ref_url={}, operation={}, "
        "user_login={}, parent1_id={}, parent2_id={}" \
            .format(self.item_id, self.item_hash, self.data_ref_hash, self.data_ref_url,
                    self.operation, self.user_login, self.parent1_id, self.parent2_id)
        return s

class Item(Base, memento.Serializable):
    '''
        The Item is an element of repository. Usually it is liked with a file (see DataRef class),
    not nescesary.
    '''
    __tablename__ = "items"

    ERROR_FILE_NOT_FOUND = 1
    ERROR_FILE_HASH_MISMATCH = 2


    id = sqa.Column(sqa.Integer, primary_key=True)

    title = sqa.Column(sqa.String, nullable=False)

    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))

    date_created = sqa.Column(sqa.DateTime)

    data_ref_id = sqa.Column(sqa.Integer, ForeignKey("data_refs.id"))

    # When Item is deleted, it is just set to be alive==False
    alive = sqa.Column(sqa.Boolean, default=True)

    user = relationship(User, cascade="merge, expunge, refresh-expire")

    data_ref = relationship("DataRef", cascade="merge, expunge, refresh-expire")

    item_tags = relationship("Item_Tag", cascade="all, delete-orphan")

    item_fields = relationship("Item_Field", cascade="all, delete-orphan")

    def __init__(self, user_login=None, title=None, date_created=None, alive=True):
        self.alive = alive
        self.user_login = user_login
        self.title = title
        if date_created is not None:
            self.date_created = date_created
        else:
            self.date_created = datetime.datetime.today()

        self.error = None


    @orm.reconstructor
    def __init_on_load__(self):
        self.error = None #When error is None, it means that there was no integrity check yet

    def __listOfTagsAndTheirOwners(self):
        return list((self.item_tags[i].tag.name,
                     self.item_tags[i].user_login)
                    for i in range(len(self.item_tags)) )

    def __listOfFieldValsAndTheirOwners(self):
        return list((self.item_fields[i].field.name,
                     self.item_fields[i].field_value,
                     self.item_fields[i].user_login)
                    for i in range(len(self.item_fields)) )

    CURRENT_JSON_VERSION = 1

    def toJson(self):
        return {"__class__": self.__class__.__name__,
                "__module__": "reggata.data.db_schema",
                "__version__": Item.CURRENT_JSON_VERSION,
                "title": self.title,
                "user_login": self.user_login,
                "date_created": self.date_created,
                "tags": self.__listOfTagsAndTheirOwners(),
                "fields": self.__listOfFieldValsAndTheirOwners(),
                "data_ref": self.data_ref,
                }

    @staticmethod
    def fromJson(objState):
        version = objState["__version__"]
        if version is None:
            return Item.fromJsonVersion0(objState)
        elif version == DataRef.CURRENT_JSON_VERSION:
            return Item.fromJsonVersionCurrent(objState)
        else:
            raise JsonUnsupportedVersionError()

    @staticmethod
    def fromJsonVersion0(objState):
        module = objState["__module__"]
        objState["__module__"] = "reggata." + module
        return Item.fromJsonVersionCurrent(objState)

    @staticmethod
    def fromJsonVersionCurrent(objState):
        item = Item()
        item.title = objState["title"]
        item.user_login = objState["user_login"]
        item.date_created = objState["date_created"]

        for (tag_name, tag_owner) in objState["tags"]:
            tag = Tag(tag_name)
            item.item_tags.append(Item_Tag(tag, tag_owner))

        for (field_name, field_val, field_owner) in objState["fields"]:
            field = Field(field_name)
            item.item_fields.append(Item_Field(field, field_val, field_owner))

        item.data_ref = objState["data_ref"]

        return item



    def hash(self):
        '''
            Calculates and returns a hash of the Item instance state.
        '''
        text = ""

        if not is_none_or_empty(self.title):
            text += self.title

        if not is_none_or_empty(self.user_login):
            text += self.user_login

        if self.date_created is not None:
            text += str(self.date_created)

        tag_names = []
        for item_tag in self.item_tags:
            tag_names.append(item_tag.tag.name)
        tag_names.sort()

        for tag_name in tag_names:
            text += tag_name

        field_vals = []
        for item_field in self.item_fields:
            field_vals.append(item_field.field.name + str(item_field.field_value))
        field_vals.sort()

        for field_val in field_vals:
            text += field_val

        return hashlib.sha1(text.encode("utf-8")).hexdigest()


    def getFieldValue(self, fieldName, userLogin=None):
        '''
            Returns value of field fieldName. If no such field exists in this item,
        returns None.
        '''
        for item_field in self.item_fields:
            if item_field.field.name == fieldName:
                if userLogin is None or item_field.user_login == userLogin:
                    return item_field.field_value
        return None

    def hasTagsExceptOf(self, userLogin):
        for item_tag in self.item_tags:
            if item_tag.user_login != userLogin:
                return True
        return False

    def hasFieldsExceptOf(self, userLogin):
        for item_field in self.item_fields:
            if item_field.user_login != userLogin:
                return True
        return False

    def addTag(self, name, userLogin):
        # TODO: Maybe raise exception if this item already has such (tag, user_login)?
        assert userLogin is not None
        tag = Tag(name)
        itemTag = Item_Tag(tag, userLogin)
        self.item_tags.append(itemTag)

    def setFieldValue(self, name, value, userLogin):
        '''
            Changes field value if it exists, or creates new field and sets a value to it.
        '''
        assert userLogin is not None

        itf = None
        for item_field in self.item_fields:
            if item_field.field.name == name and item_field.user_login == userLogin:
                itf = item_field
                break

        if itf is not None:
            itf.field_value = value
        else:
            field = Field(name)
            item_field = Item_Field(field, value, userLogin)
            self.item_fields.append(item_field)

    # TODO: this function should be moved to a separate formatter class
    def format_field_vals(self):
        s = ""
        for item_field in self.item_fields:
            s += item_field.field.name + ": " + item_field.field_value + os.linesep
        if s:
            s = s[0:-1]
        return s

    # TODO: this function should be moved to a separate formatter class
    def format_tags(self):
        '''
            Returns a string representation of all Items tags.
        '''
        s = ""
        for item_tag in self.item_tags:
            s += item_tag.tag.name + " "
        if s:
            s = s[0:-1]
        return s

    def removeTag(self, tagName):
        #TODO: Maybe should pass userLogin to this fun?
        i = 0
        while i < len(self.item_tags):
            item_tag = self.item_tags[i]
            if item_tag.tag.name == tagName:
                break
            i = i + 1

        if i < len(self.item_tags):
            self.item_tags.pop(i)
            return True
        else:
            return None

    def removeField(self, fieldName):
        #TODO: Maybe should pass userLogin to this fun?
        i = 0
        while i < len(self.item_fields):
            item_field = self.item_fields[i]
            if item_field.field.name == fieldName:
                break
            i = i + 1

        if i < len(self.item_fields):
            self.item_fields.pop(i)
            return True
        else:
            return None


    def hasTag(self, tagName):
        for item_tag in self.item_tags:
            if item_tag.tag.name == tagName:
                return True
        return False

    def hasField(self, fieldName, fieldValue=None):
        '''
            Returns True if this Item has a field with given name and a given value
        (only if field_value arg is not None).
        When field_value is None, only field names are checked for match.
        '''
        for item_field in self.item_fields:
            if item_field.field.name == fieldName:
                if fieldValue is None or item_field.field_value == str(fieldValue):
                    return True
        return False

    def checkValid(self):
        if self.title == "" or self.title is None:
            raise Exception("Attribute Item.title shouldn't be empty.")
        return True

    def hasDataRef(self):
        return self.data_ref is not None


class DataRef(Base, memento.Serializable):
    '''
        This is a reference of Item to a physical file on the filesystem.
    '''
    FILE = "FILE"
    URL = "URL" #TODO: URL type is deprecated. Do not use it anymore. User can always save an url for an item with a field
    #TODO Maybe add ZIP, and DIR types...

    __tablename__ = "data_refs"

    id = sqa.Column(sqa.Integer, primary_key=True)

    # When type is 'FILE' this is a relative path in UNIX format
    url_raw = sqa.Column(sqa.String, name="url", nullable=False, unique=True)

    type = sqa.Column(sqa.Enum(FILE, URL), nullable=False)

    # sha1 hash of file contents. For DataRef objects with type != FILE this field is NULL
    hash = sqa.Column(sqa.String)

    date_hashed = sqa.Column(sqa.DateTime)

    # Physical size of referenced file on the disk. For DataRef objects with type != FILE this field is NULL
    size = sqa.Column(sqa.Integer)

    # Creation date of this DataRef instance
    date_created = sqa.Column(sqa.DateTime)

    #deprecated because it's enough information in field Item.user_login
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"))

    user = relationship(User, cascade="save-update, merge, expunge, refresh-expire")

    thumbnails = relationship("Thumbnail", cascade="all, delete-orphan")

    items = relationship("Item", cascade="expunge, refresh-expire")


    def __init__(self, objType=None, url=None, date_created=None):
        self.type = objType
        self.url = url

        if date_created is not None:
            self.date_created = date_created
        else:
            self.date_created = datetime.datetime.today()

        # This two fields is used only in function "Add many items recursively"
        # srcAbsPathToRoot is a absolute path to the directory one level up from root
        # from where recursive scanning was started.
        self.srcAbsPathToRoot = None
        self.srcAbsPath = None

        # This is a relative path to file in repository (where you want to put it)
        # NOTE: This is not a path to directory!
        self.dstRelPath = None

    @orm.reconstructor
    def __init_on_load__(self):
        self.srcAbsPathToRoot = None
        self.srcAbsPath = None
        self.dstRelPath = None

    CURRENT_JSON_VERSION = 1

    def toJson(self):
        return {"__class__": self.__class__.__name__,
                "__module__": "reggata.data.db_schema",
                "__version__": DataRef.CURRENT_JSON_VERSION,
                "url": self.url_raw,
                "type": self.type,
                "hash": self.hash,
                "date_hashed": self.date_hashed,
                "size": self.size,
                "date_created": self.date_created,
                "user_login": self.user_login,
                }

    @staticmethod
    def fromJson(objState):
        version = objState["__version__"]
        if version is None:
            return DataRef.fromJsonVersion0(objState)
        elif version == DataRef.CURRENT_JSON_VERSION:
            return DataRef.fromJsonVersionCurrent(objState)
        else:
            raise JsonUnsupportedVersionError()

    @staticmethod
    def fromJsonVersion0(objState):
        module = objState["__module__"]
        objState["__module__"] = "reggata." + module
        return DataRef.fromJsonVersionCurrent(objState)

    @staticmethod
    def fromJsonVersionCurrent(objState):
        dr = DataRef(objType=objState["type"],
                     url=objState["url"],
                     date_created=objState["date_created"])
        dr.hash = objState["hash"]
        dr.date_hashed = objState["date_hashed"]
        dr.size = objState["size"]
        dr.user_login = objState["user_login"]
        return dr


    def _get_url(self):
        if self.type == DataRef.FILE and self.url_raw is not None:
            return helpers.from_db_format(self.url_raw)
        else:
            return self.url_raw

    def _set_url(self, value):
        if self.type == DataRef.FILE and value is not None:
            value = helpers.to_db_format(value)
        self.url_raw = value

    url = property(_get_url, _set_url)

    @staticmethod
    def _sql_from():
        return '''
            data_refs.id AS data_refs_id,
            data_refs.url AS data_refs_url,
            data_refs.type AS data_refs_type,
            data_refs.hash AS data_refs_hash,
            data_refs.date_hashed AS data_refs_date_hashed,
            data_refs.size AS data_refs_size,
            data_refs.date_created AS data_refs_date_created,
            data_refs.user_login AS data_refs_user_login '''




    def is_image(self):
        supported = set([".bmp", ".gif", ".jpg", ".jpeg", ".png", ".pbm", ".pgm",
                         ".ppm", ".xbm", ".xpm"])
        if self.type and self.type == "FILE" and not is_none_or_empty(self.url):
            _root, ext = os.path.splitext(self.url.lower())
            if ext in supported:
                return True

        return False




class Thumbnail(Base):

    __tablename__ = "thumbnails"

    data_ref_id = sqa.Column(sqa.Integer, ForeignKey("data_refs.id"), primary_key=True)

    # Size of thumbnail in pixels
    size = sqa.Column(sqa.Integer, primary_key=True)

    data = sqa.Column(sqa.LargeBinary)

    date_created = sqa.Column(sqa.DateTime)

    def __init__(self):
        self.data_ref_id = None
        self.size = None
        self.data = None
        self.date_created = datetime.datetime.today()

    @staticmethod
    def _sql_from():
        return '''
        thumbnails.data_ref_id AS thumbnails_data_ref_id,
        thumbnails.size AS thumbnails_size,
        thumbnails.data AS thumbnails_data,
        thumbnails.date_created AS thumbnails_date_created '''

class Tag(Base):
    '''
        Tag is a short string that can be attached to the Item.
    '''
    __tablename__ = "tags"

    id = sqa.Column(sqa.Integer, primary_key=True)
    name = sqa.Column(sqa.String, nullable=False, unique=True)
    synonym_code = sqa.Column(sqa.Integer)

    def __init__(self, name=None):
        self.id = None
        self.name = name
        self.synonym_code = None

    @staticmethod
    def _sql_from():
        return '''
        tags.id as tags_id,
        tags.name as tags_name,
        tags.synonym_code as tags_synonym_code '''


class Item_Tag(Base):
    __tablename__ = "items_tags"

    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"), primary_key=True)
    tag_id = sqa.Column(sqa.Integer, ForeignKey("tags.id"), primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"), primary_key=True)

    tag = relationship(Tag, cascade="save-update, merge, expunge, refresh-expire")


    def __init__(self, tag=None, user_login=None):
        self.tag = tag
        self.user_login = user_login
        if tag is not None:
            self.tag_id = tag.id

    @staticmethod
    def _sql_from():
        return '''
        items_tags.item_id as items_tags_item_id,
        items_tags.tag_id as items_tags_tag_id,
        items_tags.user_login as items_tags_user_login '''

class Field(Base):
    '''
        Key:Value pair, that can be attached to the Item.
    '''
    __tablename__ = "fields"

    id = sqa.Column(sqa.Integer, primary_key=True)
    name = sqa.Column(sqa.String, nullable=False, unique=True)
    synonym_code = sqa.Column(sqa.Integer)

    def __init__(self, name=None):
        self.id = None
        self.name = name
        self.synonym_code = None

    @staticmethod
    def _sql_from():
        return '''
        fields.id as fields_id,
        fields.name as fields_name,
        fields.synonym_code as fields_synonym_code '''


class Item_Field(Base):

    __tablename__ = "items_fields"

    item_id = sqa.Column(sqa.Integer, ForeignKey("items.id"), primary_key=True)
    field_id = sqa.Column(sqa.String, ForeignKey("fields.id"), primary_key=True)
    user_login = sqa.Column(sqa.String, ForeignKey("users.login"), primary_key=True)
    field_value = sqa.Column(sqa.String, nullable=False, default="")

    field = relationship(Field, cascade="save-update, merge, expunge, refresh-expire")


    def __init__(self, field=None, value=None, user_login=None):
        self.field = field
        if field is not None:
            self.field_id = field.id
        self.field_value = value
        self.user_login = user_login

    @staticmethod
    def _sql_from():
        return '''
        items_fields.item_id as items_fields_item_id,
        items_fields.field_id as items_fields_field_id,
        items_fields.user_login as items_fields_user_login,
        items_fields.field_value as items_fields_field_value '''

#TODO implement classes for such entities as GroupOfTags, GroupOfFields
