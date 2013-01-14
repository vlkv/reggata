'''
Created on 23.07.2012
@author: vlkv
'''
from sqlalchemy.orm import contains_eager, joinedload_all
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import ResourceClosedError
import shutil
import datetime
import os.path
import reggata.errors as err
import reggata.helpers as hlp
import reggata.consts as consts
import reggata.data.db_schema as db
from reggata.user_config import UserConfig
from reggata.data import operations


class AbstractCommand:
    def _execute(self, unitOfWork):
        raise NotImplementedError("Override this function in a subclass")


class GetExpungedItemCommand(AbstractCommand):
    '''
        Returns expunged (detached) object of Item class from database with given id.
    '''
    def __init__(self, itemId):
        self.__itemId = itemId

    def _execute(self, uow):
        self._session = uow.session
        item = self._session.query(db.Item)\
            .options(joinedload_all('data_ref'))\
            .options(joinedload_all('item_tags.tag'))\
            .options(joinedload_all('item_fields.field'))\
            .get(self.__itemId)

        if item is None:
            raise err.NotFoundError()

        self._session.expunge(item)
        return item

class DeleteHangingTagsCommand(AbstractCommand):
    '''
        Deletes from database all hanging Tag objects. A hanging Tag is a Tag that
    is not referenced by Items.
        Returns number of deleted tags.
    '''
    def _execute(self, uow):
        self._session = uow.session
        sql = '''select tags.id, tags.name, tags.synonym_code
        from tags left join items_tags on tags.id = items_tags.tag_id
        where items_tags.item_id is NULL
        '''
        hangingTags = self._session.query(db.Tag).from_statement(sql).all()
        count = len(hangingTags)
        for tag in hangingTags:
            self._session.delete(tag)
        if count > 0:
            self._session.commit()
        return count

class DeleteHangingFieldsCommand(AbstractCommand):
    '''
        Deletes from database all hanging Field objects. A hanging Field is a Field that
    is not referenced by Items.
        Returns number of deleted fields.
    '''
    def _execute(self, uow):
        self._session = uow.session
        sql = '''select fields.id, fields.name
        from fields left join items_fields on fields.id = items_fields.field_id
        where items_fields.item_id is NULL
        '''
        hangingFields = self._session.query(db.Field).from_statement(sql).all()
        count = len(hangingFields)
        for field in hangingFields:
            self._session.delete(field)
        if count > 0:
            self._session.commit()
        return count


class SaveThumbnailCommand(AbstractCommand):

    def __init__(self, data_ref_id, thumbnail):
        self.__dataRefId = data_ref_id
        self.__thumbnail = thumbnail

    def _execute(self, uow):
        self._session = uow.session

        data_ref = self._session.query(db.DataRef).get(self.__dataRefId)
        self._session.refresh(data_ref) #TODO: Research if we can remove this refresh

        self.__thumbnail.data_ref_id = data_ref.id
        data_ref.thumbnails.append(self.__thumbnail)

        self._session.add(self.__thumbnail)
        self._session.commit()

        self._session.refresh(self.__thumbnail)
        self._session.expunge(self.__thumbnail)
        self._session.expunge(data_ref)


class GetUntaggedItems(AbstractCommand):
    '''
        Gets from database all alive elements without tags.
    '''
    def __init__(self, limit=0, page=1, order_by=""):
        self.__limit = limit
        self.__page = page
        self.__orderBy = order_by

    def _execute(self, uow):
        self._session = uow.session
        return self.__getUntaggedItems(self.__limit, self.__page, self.__orderBy)

    def __getUntaggedItems(self, limit, page, order_by):
        order_by_1 = ""
        order_by_2 = ""
        for col, direction in order_by:
            if order_by_1:
                order_by_1 += ", "
            if order_by_2:
                order_by_2 += ", "
            order_by_2 += col + " " + direction + " "
            if col == "title":
                order_by_1 += col + " " + direction + " "
        if order_by_1:
            order_by_1 = " ORDER BY " + order_by_1
        if order_by_2:
            order_by_2 = " ORDER BY " + order_by_2

        thumbnail_default_size = UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE)

        if page < 1:
            raise ValueError("Page number cannot be negative or zero.")

        if limit < 0:
            raise ValueError("Limit cannot be negative number.")

        limit_offset = ""
        if limit > 0:
            offset = (page-1)*limit
            limit_offset += "LIMIT {0} OFFSET {1}".format(limit, offset)

        sql = '''
        select sub.*, ''' + \
        db.Item_Tag._sql_from() + ", " + \
        db.Tag._sql_from() + ", " + \
        db.Item_Field._sql_from() + ", " + \
        db.Field._sql_from() + \
        '''
        from (select i.*, ''' + \
            db.DataRef._sql_from() + ", " + \
            db.Thumbnail._sql_from() + \
            '''
            from items i
            left join items_tags it on i.id = it.item_id
            left join data_refs on i.data_ref_id = data_refs.id
            left join thumbnails on data_refs.id = thumbnails.data_ref_id and thumbnails.size = ''' + \
                str(thumbnail_default_size) + '''
            where
                it.item_id is null
                AND i.alive
            ''' + order_by_1 + " " + limit_offset + '''
        ) as sub
        left join items_tags on sub.id = items_tags.item_id
        left join tags on tags.id = items_tags.tag_id
        left join items_fields on sub.id = items_fields.item_id
        left join fields on fields.id = items_fields.field_id
        ''' + order_by_2

        items = []
        try:
            items = self._session.query(db.Item)\
            .options(contains_eager("data_ref"), \
                     contains_eager("data_ref.thumbnails"), \
                     contains_eager("item_tags"), \
                     contains_eager("item_tags.tag"), \
                     contains_eager("item_fields"),\
                     contains_eager("item_fields.field"))\
            .from_statement(sql).all()
            for item in items:
                self._session.expunge(item)

        except ResourceClosedError:
            pass

        return items




class QueryItemsByParseTree(AbstractCommand):
    '''
        Searches for items, according to given syntax parse tree (of query language).
    '''
    def __init__(self, query_tree, limit=0, page=1, order_by=[]):
        self.__queryTree = query_tree
        self.__limit = limit
        self.__page = page
        self.__orderBy = order_by

    def _execute(self, uow):
        self._session = uow.session
        return self.__queryItemsByParseTree(self.__queryTree, self.__limit, self.__page,
                                            self.__orderBy)

    def __queryItemsByParseTree(self, query_tree, limit, page, order_by):
        order_by_1 = ""
        order_by_2 = ""
        for col, direction in order_by:
            if order_by_1:
                order_by_1 += ", "
            if order_by_2:
                order_by_2 += ", "
            order_by_2 += col + " " + direction + " "
            if col == "title":
                order_by_1 += col + " " + direction + " "
        if order_by_1:
            order_by_1 = " ORDER BY " + order_by_1
        if order_by_2:
            order_by_2 = " ORDER BY " + order_by_2


        sub_sql = query_tree.interpret()

        if page < 1:
            raise ValueError("Page number cannot be negative or zero.")

        if limit < 0:
            raise ValueError("Limit cannot be negative number.")

        limit_offset = ""
        if limit > 0:
            offset = (page-1)*limit
            limit_offset += "LIMIT {0} OFFSET {1}".format(limit, offset)

        sql = '''
        select sub.*,
        ''' + db.Item_Tag._sql_from() + ''',
        ''' + db.Tag._sql_from() + ''',
        ''' + db.Thumbnail._sql_from() + ''',
        ''' + db.Item_Field._sql_from() + ''',
        ''' + db.Field._sql_from() + '''
        from (''' + sub_sql + " " + order_by_1 + " " + limit_offset +  ''') as sub
        left join items_tags on sub.id = items_tags.item_id
        left join tags on tags.id = items_tags.tag_id
        left join items_fields on sub.id = items_fields.item_id
        left join fields on fields.id = items_fields.field_id
        left join thumbnails on thumbnails.data_ref_id = sub.data_refs_id and
                  thumbnails.size = ''' + str(UserConfig().get("thumbnail_size",
                                                               consts.THUMBNAIL_DEFAULT_SIZE)) + '''
        where sub.alive
        ''' + order_by_2

        items = []
        try:
            items = self._session.query(db.Item)\
            .options(contains_eager("data_ref"), \
                     contains_eager("data_ref.thumbnails"), \
                     contains_eager("item_tags"), \
                     contains_eager("item_tags.tag"), \
                     contains_eager("item_fields"),\
                     contains_eager("item_fields.field"))\
            .from_statement(sql).all()

            for item in items:
                self._session.expunge(item)

        except ResourceClosedError:
            pass

        return items


class FileInfo(object):

    UNTRACKED = "UNTRACKED"
    STORED = "STORED"

    FILE = "FILE"
    DIR = "DIRECTORY"
    OTHER = "OTHER"

    def __init__(self, path, objType=None, status=None):
        assert not hlp.is_none_or_empty(path)
        assert objType is not None or status is not None

        #remove trailing slashes in the path
        while path.endswith(os.sep):
            path = path[0:-1]

        self.path = path
        self.status = status
        self.type = objType
        self.tags = []
        self.fields = []
        self.itemIds = []

    @property
    def fileBaseName(self):
        return os.path.basename(self.path)

    def __str__(self):
        return self.fileBaseName()

    def isDir(self):
        return self.type == FileInfo.DIR


class GetFileInfoCommand(AbstractCommand):
    def __init__(self, relPath):
        self.__relPath = relPath

    def _execute(self, uow):
        self._session = uow.session
        return self.__getFileInfo(self.__relPath)

    def __getFileInfo(self, path):
        try:
            data_ref = self._session.query(db.DataRef)\
                .filter(db.DataRef.url_raw==hlp.to_db_format(path))\
                .options(joinedload_all("items"))\
                .options(joinedload_all("items.item_tags.tag"))\
                .options(joinedload_all("items.item_fields.field"))\
                .one()
            self._session.expunge(data_ref)
            finfo = FileInfo(data_ref.url, objType=FileInfo.FILE, status=FileInfo.STORED)

            for item in data_ref.items:
                finfo.itemIds.append(item.id)
                for item_tag in item.item_tags:
                    finfo.tags.append(item_tag.tag.name)
                for item_field in item.item_fields:
                    finfo.fields.append((item_field.field.name, item_field.field_value))
            return finfo

        except NoResultFound:
            return FileInfo(self.__relPath, status=FileInfo.UNTRACKED)





class LoginUserCommand(AbstractCommand):
    '''
        Logins a user to a repository database.
        password --- is a SHA1 hexdigest() hash. When login or password incorrect
    command raises LoginError.
    '''
    def __init__(self, login, password):
        self.__login = login
        self.__password = password

    def _execute(self, uow):
        self._session = uow.session
        return self.__loginUser(self.__login, self.__password)

    def __loginUser(self, login, password):
        if hlp.is_none_or_empty(login):
            raise err.LoginError("User login cannot be empty.")
        user = self._session.query(db.User).get(login)
        if user is None:
            raise err.LoginError("User {} doesn't exist.".format(login))
        if user.password != password:
            raise err.LoginError("Password incorrect.")

        self._session.expunge(user)
        return user


class ChangeUserPasswordCommand(AbstractCommand):
    def __init__(self, userLogin, newPasswordHash):
        self.__userLogin = userLogin
        self.__newPasswordHash = newPasswordHash

    def _execute(self, uow):
        user = uow.session.query(db.User).get(self.__userLogin)
        if user is None:
            raise err.LoginError("User {} doesn't exist.".format(self.__userLogin))

        user.password = self.__newPasswordHash
        uow.session.commit()


class SaveNewUserCommand(AbstractCommand):
    def __init__(self, user):
        self.__user = user

    def _execute(self, uow):
        self._session = uow.session
        self.__saveNewUser(self.__user)

    def __saveNewUser(self, user):
        #TODO: have to do some basic check of user object validity
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        self._session.expunge(user)


class GetNamesOfAllTagsAndFields(AbstractCommand):
    def _execute(self, uow):
        self._session = uow.session
        return self.__getNamesOfAllTagsAndFields()

    def __getNamesOfAllTagsAndFields(self):
        sql = '''
        select distinct name from tags
        UNION
        select distinct name from fields
        ORDER BY name
        '''
        try:
            return self._session.query("name").from_statement(sql).all()
        except ResourceClosedError:
            return []


class GetRelatedTagsCommand(AbstractCommand):
    '''
        Returns a list of related tags for a list of given (selected) tags tag_names.
    When tag_names is empty, all tags are returned.

        Limit affects only if tag_names is empty. In other cases limit is ignored.
    If limit == 0 it means there is no limit.
    '''
    #TODO This command should return list of tags, related to arbitrary list of selected items.
    def __init__(self, tag_names=[], user_logins=[], limit=0):
        self.__tag_names = tag_names
        self.__user_logins = user_logins
        self.__limit = limit

    def _execute(self, uow):
        self._session = uow.session
        return self.__getRelatedTags(self.__tag_names, self.__user_logins, self.__limit)

    def __getRelatedTags(self, tag_names, user_logins, limit):
        #TODO user_logins is not used yet..
        if len(tag_names) == 0:
            #TODO The more items in the repository, the slower this query is performed.
            #I think, I should store in database some statistics information, such as number of items
            #tagged with each tag. With this information, the query can be rewritten and became much faster.
            if limit > 0:
                sql = '''
                select name, c
                from
                (select t.name as name, count(*) as c
                   from items i, tags t
                   join items_tags it on it.tag_id = t.id and it.item_id = i.id and i.alive
                where
                    1
                group by t.name
                ORDER BY c DESC LIMIT ''' + str(limit) + ''') as sub
                ORDER BY name
                '''
            else:
                sql = '''
                --get_related_tags() query
                select t.name as name, count(*) as c
                   from items i, tags t
                   join items_tags it on it.tag_id = t.id and it.item_id = i.id and i.alive
                where
                    1
                group by t.name
                ORDER BY t.name
                '''
            # ResourceClosedError could be raised when there are no related tags
            # for given list of tags.
            try:
                return self._session.query("name", "c").from_statement(sql).all()
            except ResourceClosedError:
                return []

        else:
            # First we get a list of item ids
            sql = '''--get_related_tags(): getting list of id for all selected tags
            select * from tags t
            where t.name in (''' + hlp.to_commalist(tag_names, lambda x: "'" + x + "'") + ''')
            order by t.id'''
            try:
                tags = self._session.query(db.Tag).from_statement(sql).all()
            except ResourceClosedError:
                tags = []
            tag_ids = []
            for tag in tags:
                tag_ids.append(tag.id)

            if len(tag_ids) == 0:
                #TODO Maybe raise an exception?
                return []

            sub_from = ""
            for i in range(len(tag_ids)):
                if i == 0:
                    sub_from = sub_from + " items_tags it{} ".format(i+1)
                else:
                    sub_from = sub_from + \
                    (" join items_tags it{1} on it{1}.item_id=it{0}.item_id " + \
                    " AND it{1}.tag_id > it{0}.tag_id ").format(i, i+1)

            sub_where = ""
            for i in range(len(tag_ids)):
                if i == 0:
                    sub_where = sub_where + \
                    " it{0}.tag_id = {1} ".format(i+1, tag_ids[i])
                else:
                    sub_where = sub_where + \
                    " AND it{0}.tag_id = {1} ".format(i+1, tag_ids[i])

            where = ""
            for i in range(len(tag_ids)):
                where = where + \
                " AND t.id <> {0} ".format(tag_ids[i])

            sql = '''--get_related_tags() query
            select t.name as name, count(*) as c
                from tags t
                join items_tags it on it.tag_id = t.id
                join items i on i.id = it.item_id
            where
                it.item_id IN (
                    select it1.item_id
                        from ''' + sub_from + '''
                    where ''' + sub_where + '''
                ) ''' + where + '''
                AND i.alive
                -- It is important that these ids followed in the order of raising
            group by t.name
            ORDER BY t.name'''
            try:
                return self._session.query("name", "c").from_statement(sql).all()
            except ResourceClosedError:
                return []



class DeleteItemCommand(AbstractCommand):

    def __init__(self, item_id, user_login, delete_physical_file=True):
        self.__itemId = item_id
        self.__userLogin = user_login
        self.__deletePhysicalFile = delete_physical_file

    def _execute(self, uow):
        self._session = uow.session
        self._repoBasePath = uow._repo_base_path
        return self.__deleteItem(self.__itemId, self.__userLogin, self.__deletePhysicalFile)

    def __deleteItem(self, item_id, user_login, delete_physical_file=True):
        # We should not delete Item objects from database, because
        # we do not want hanging references in HistoryRec table.
        # So we just mark Items as deleted.

        # DataRef objects are deleted from database, if there are no references to it from other alive Items.

        # TODO: Make admin users to be able to delete any files, owned by anybody.

        item = self._session.query(db.Item).get(item_id)
        if item.user_login != user_login:
            raise err.AccessError("Cannot delete item id={0} because it is owned by another user {1}."
                              .format(item_id, item.user_login))

        if item.has_tags_except_of(user_login):
            raise err.AccessError("Cannot delete item id={0} because another user tagged it."
                              .format(item_id))

        if item.has_fields_except_of(user_login):
            raise err.AccessError("Cannot delete item id={0} because another user attached a field to it."
                              .format(item_id))

        data_ref = item.data_ref

        item.data_ref = None
        item.data_ref_id = None
        item.alive = False
        self._session.flush()
        #All bounded ItemTag and ItemField objects stays in database with the Item

        #If data_ref is not referenced by other Items, we delete it

        delete_data_ref = data_ref is not None

        #We should not delete DataRef if it is owned by another user
        if delete_data_ref and data_ref.user_login != user_login:
            delete_data_ref = False

        if delete_data_ref:
            another_item = self._session.query(db.Item).filter(db.Item.data_ref==data_ref).first()
            if another_item:
                delete_data_ref = False

        if delete_data_ref:
            is_file = (data_ref.type == db.DataRef.FILE)
            abs_path = os.path.join(self._repoBasePath, data_ref.url)

            self._session.delete(data_ref)
            self._session.flush()

            if is_file and delete_physical_file and os.path.exists(abs_path):
                os.remove(abs_path)

        self._session.commit()


class SaveNewItemCommand(AbstractCommand):
    '''
        Command saves in database given item.
    Returns id of created item, or raises an exception if something wrong.
    When this function returns, item object is expunged from the current Session.
        item.user_login - specifies owner of this item (and all tags/fields linked with it).
        srcAbsPath - absolute path to a file which will be referenced by this item.
        dstRelPath - relative (to repository root) path where to put the file.
    File is always copyied from srcAbsPath to <repo_base_path>/dstRelPath, except when
    srcAbsPath is the same as <repo_base_path>/dstRelPath.

    Use cases:
            0) Both srcAbsPath and dstRelPath are None, so User wants to create an Item
        without DataRef object.
            1) User wants to add an external file into the repo. File is copied to the
        repo.
            2) There is an untracked file inside the repo tree. User wants to add such file
        into the repo to make it a stored file. File is not copied, because it is alredy in
        the repo tree.
            3) User wants to add a copy of a stored file from the repo into the same repo
        but to the another location. Original file is copyied. The copy of the original file
        will be attached to the new Item object.
            4) ERROR: User wants to attach to a stored file another new Item object.
        This is FORBIDDEN! Because existing item may be not integral with the file.
        TODO: We can allow this operation only if integrity check returns OK. May be implemented
        in the future.

        NOTE: Use cases 1,2,3 require creation of a new DataRef object.
        If given item has not null item.data_ref object, it is ignored anyway.
    '''
    def __init__(self, item, srcAbsPath=None, dstRelPath=None):
        self.__item = item
        self.__srcAbsPath = srcAbsPath
        self.__dstRelPath = dstRelPath

    def _execute(self, uow):
        self._session = uow.session
        self._repoBasePath = uow._repo_base_path
        return self.__saveNewItem(self.__item, self.__srcAbsPath, self.__dstRelPath)

    def __saveNewItem(self, item, srcAbsPath=None, dstRelPath=None):
        #We do not need any info, that can be in item.data_ref object at this point.
        #But if it is not None, it may break the creation of tags/fields.
        #Don't worry, item.data_ref will be assigned a new DataRef instance later (if required).
        item.data_ref = None

        isDataRefRequired = not hlp.is_none_or_empty(srcAbsPath)
        if isDataRefRequired:
            assert(dstRelPath is not None)
            #NOTE: If dstRelPath is an empty string it means the root of repository

            srcAbsPath = os.path.normpath(srcAbsPath)
            if not os.path.isabs(srcAbsPath):
                raise ValueError("srcAbsPath must be an absolute path.")

            if not os.path.exists(srcAbsPath):
                raise ValueError("srcAbsPath must point to an existing file.")

            if os.path.isabs(dstRelPath):
                raise ValueError("dstRelPath must be a relative to repository root path.")

            dstRelPath = hlp.removeTrailingOsSeps(dstRelPath)
            dstRelPath = os.path.normpath(dstRelPath)
            dstAbsPath = os.path.abspath(os.path.join(self._repoBasePath, dstRelPath))
            dstAbsPath = os.path.normpath(dstAbsPath)
            if srcAbsPath != dstAbsPath and os.path.exists(dstAbsPath):
                raise ValueError("{} should not point to an existing file.".format(dstAbsPath))

            dataRef = self._session.query(db.DataRef).filter(
                db.DataRef.url_raw==hlp.to_db_format(dstRelPath)).first()
            if dataRef is not None:
                raise err.DataRefAlreadyExistsError("DataRef instance with url='{}' "
                                                   "is already in database. ".format(dstRelPath))

        user_login = item.user_login
        if hlp.is_none_or_empty(user_login):
            raise err.AccessError("Argument user_login shouldn't be null or empty.")

        user = self._session.query(db.User).get(user_login)
        if user is None:
            raise err.AccessError("User with login {} doesn't exist.".format(user_login))


        #Remove from item those tags, which have corresponding Tag objects in database
        item_tags_copy = item.item_tags[:] #Making list copy
        existing_item_tags = []
        for item_tag in item_tags_copy:
            item_tag.user_login = user_login
            tag = item_tag.tag
            t = self._session.query(db.Tag).filter(db.Tag.name==tag.name).first()
            if t is not None:
                item_tag.tag = t
                existing_item_tags.append(item_tag)
                item.item_tags.remove(item_tag)

        #Remove from item those fields, which have corresponding Field objects in database
        item_fields_copy = item.item_fields[:] #Making list copy
        existing_item_fields = []
        for item_field in item_fields_copy:
            item_field.user_login = user_login
            field = item_field.field
            f = self._session.query(db.Field).filter(db.Field.name==field.name).first()
            if f is not None:
                item_field.field = f
                existing_item_fields.append(item_field)
                item.item_fields.remove(item_field)

        #Saving item with just absolutely new tags and fields
        self._session.add(item)
        self._session.flush()

        #Adding to the item existent tags
        for it in existing_item_tags:
            item.item_tags.append(it)
        #Adding to the item existent fields
        for if_ in existing_item_fields:
            item.item_fields.append(if_)
        #Saving item with existent tags and fields
        self._session.flush()


        if isDataRefRequired:
            item.data_ref = db.DataRef(objType=db.DataRef.FILE, url=dstRelPath)
            item.data_ref.user_login = user_login
            item.data_ref.size = os.path.getsize(srcAbsPath)
            item.data_ref.hash = hlp.computeFileHash(srcAbsPath)
            item.data_ref.date_hashed = datetime.datetime.today()
            self._session.add(item.data_ref)
            self._session.flush()

            item.data_ref_id = item.data_ref.id
            self._session.flush()
        else:
            item.data_ref = None

        #Now it's time to COPY physical file to the repository
        if isDataRefRequired and srcAbsPath != dstAbsPath:
            try:
                #Making dirs
                head, _tail = os.path.split(dstAbsPath)
                os.makedirs(head)
            except:
                pass
            shutil.copy(srcAbsPath, dstAbsPath)
            #TODO should not use shutil.copy() function, because I cannot specify block size!
            #On very large files (about 15Gb) shutil.copy() function takes really A LOT OF TIME.
            #Because of small block size, I think.

        self._session.commit()
        item_id = item.id
        self._session.expunge(item)
        return item_id




class UpdateExistingItemCommand(AbstractCommand):
    '''
        item - is a detached object, representing a new state for stored item with id == item.id.
        user_login - is a login of user, who is doing the modifications of the item.
        Returns detached updated item or raises an exception, if something goes wrong.

        If item.data_ref.url is changed --- that means that user wants this item
    to reference to another file.
        If item.data_ref.dstRelPath is not None --- that means that user wants
    to move (and maybe rename) original referenced file withing the repository.

    TODO: Maybe we should use item.data_ref.srcAbsPathForFileOperation instead of item.data_ref.url... ?
    TODO: We should deny any user to change tags/fields/files of items, owned by another user.
    '''
    #TODO: Use srcAbsPath=None, dstRelPath=None arguments in this command
    def __init__(self, item, userLogin):
        self.__item = item
        self.__userLogin = userLogin

    def _execute(self, uow):
        self._session = uow.session
        self._repoBasePath = uow._repo_base_path
        self.__updateExistingItem(self.__item, self.__userLogin)

    def __updateExistingItem(self, item, user_login):
        persistentItem = self._session.query(db.Item).get(item.id)

        #We must gather some information before any changes have been made
        srcAbsPathForFileOperation = None
        if persistentItem.data_ref is not None:
            srcAbsPathForFileOperation = os.path.join(self._repoBasePath, persistentItem.data_ref.url)
        elif item.data_ref is not None:
            srcAbsPathForFileOperation = item.data_ref.url

        self.__updatePlainDataMembers(item, persistentItem)
        self.__updateTags(item, persistentItem, user_login)
        self.__updateFields(item, persistentItem, user_login)
        fileOperation = self.__updateDataRefObject(item, persistentItem, user_login)

        self._session.refresh(persistentItem)

        self.__updateFilesystem(persistentItem, fileOperation, srcAbsPathForFileOperation)

        self._session.commit()

        self._session.refresh(persistentItem)
        self._session.expunge(persistentItem)
        return persistentItem

    def __updatePlainDataMembers(self, item, persistentItem):
        #Here we update simple data members of the item
        persistentItem.title = item.title
        persistentItem.user_login = item.user_login
        self._session.flush()

    def __updateTags(self, item, persistentItem, userLogin):
        oldTagNames = set(map(lambda itag: itag.tag.name, [itag for itag in item.item_tags]))
        newTagNames = set(map(lambda itag: itag.tag.name, [itag for itag in persistentItem.item_tags]))
        
        tagNamesToRemove = newTagNames - oldTagNames
        operations.ItemOperations.removeTags(self._session, persistentItem, tagNamesToRemove)

        tagNamesToAdd = oldTagNames - newTagNames
        operations.ItemOperations.addTags(self._session, persistentItem, tagNamesToAdd, userLogin)


    def __updateFields(self, item, persistentItem, user_login):
        # Removing fields
        for ifield in persistentItem.item_fields:
            i = hlp.index_of(item.item_fields, lambda o: True if o.field.name==ifield.field.name else False)
            if i is None:
                self._session.delete(ifield)
        self._session.flush()

        # Adding fields
        for ifield in item.item_fields:
            i = hlp.index_of(persistentItem.item_fields, \
                         lambda o: True if o.field.name==ifield.field.name else False)
            if i is None:
                field = self._session.query(db.Field).filter(db.Field.name==ifield.field.name).first()
                if field is None:
                    field = db.Field(ifield.field.name)
                    self._session.add(field)
                    self._session.flush()
                item_field = db.Item_Field(field, ifield.field_value, user_login)
                self._session.add(item_field)
                item_field.item = persistentItem
                persistentItem.item_fields.append(item_field)
            elif ifield.field_value != persistentItem.item_fields[i].field_value:
                # Item already has such a field, we should just change it's value
                self._session.add(persistentItem.item_fields[i])
                persistentItem.item_fields[i].field_value = ifield.field_value
        self._session.flush()

    def __updateDataRefObject(self, item, persistentItem, user_login):
        # Processing DataRef object
        srcAbsPath = None
        dstAbsPath = None
        need_file_operation = None

        shouldRemoveDataRef = item.data_ref is None
        if shouldRemoveDataRef:
            # User removed the DataRef object from item (or it was None before..)
            #TODO Maybe remove DataRef if there are no items that reference to it?
            persistentItem.data_ref = None
            persistentItem.data_ref_id = None

            self._session.flush()
            return need_file_operation

        shouldAttachAnotherDataRef = persistentItem.data_ref is None \
            or persistentItem.data_ref.url != item.data_ref.url
        if shouldAttachAnotherDataRef:
            # The item is attached to DataRef object at the first time or
            # it changes his DataRef object to another DataRef object
            url = item.data_ref.url
            if item.data_ref.type == db.DataRef.FILE:
                assert os.path.isabs(url), "item.data_ref.url should be an absolute path"
                url = os.path.relpath(url, self._repoBasePath)

            existing_data_ref = self._session.query(db.DataRef).filter(db.DataRef.url_raw==hlp.to_db_format(url)).first()
            if existing_data_ref is not None:
                persistentItem.data_ref = existing_data_ref
            else:
                #We should create new DataRef object in this case
                self._prepare_data_ref(item.data_ref, user_login)
                self._session.add(item.data_ref)
                self._session.flush()
                persistentItem.data_ref = item.data_ref
                if item.data_ref.type == db.DataRef.FILE:
                    need_file_operation = "copy"

            self._session.flush()
            return need_file_operation

        shouldMoveReferencedFile = item.data_ref.type == db.DataRef.FILE \
            and not hlp.is_none_or_empty(item.data_ref.dstRelPath) \
            and os.path.normpath(persistentItem.data_ref.url) != os.path.normpath(item.data_ref.dstRelPath)
        if shouldMoveReferencedFile:
            # A file referenced by the item is going to be moved to some another location
            # within the repository. item.data_ref.dstRelPath is the new relative
            # path to this file. File will be copied.

            srcAbsPath = os.path.join(self._repoBasePath, persistentItem.data_ref.url)
            dstAbsPath = os.path.join(self._repoBasePath, item.data_ref.dstRelPath)
            if not os.path.exists(srcAbsPath):
                raise Exception("File {0} not found!".format(srcAbsPath))

            if os.path.exists(dstAbsPath) and os.path.abspath(srcAbsPath) != os.path.abspath(dstAbsPath):
                raise Exception("Pathname {0} already exists. File {1} would not be moved."
                                .format(dstAbsPath, srcAbsPath))

            if os.path.abspath(srcAbsPath) == os.path.abspath(dstAbsPath):
                raise Exception("Destination path {0} should be different from item's DataRef.url {1}"
                                .format(dstAbsPath, srcAbsPath))

            persistentItem.data_ref.url = item.data_ref.dstRelPath
            need_file_operation = "move"
            self._session.flush()
            return need_file_operation

    def __updateFilesystem(self, persistentItem, fileOperation, srcAbsPathForFileOperation):
        # Performs operations with the file in OS filesystem

        assert fileOperation in [None, "copy", "move"]
        if hlp.is_none_or_empty(fileOperation):
            return

        assert persistentItem.data_ref is not None, \
        "Item must have a DataRef object to be able to do some filesystem operations."

        assert srcAbsPathForFileOperation is not None, \
        "Path to target file is not given. We couldn't do any filesystem operations without it."

        assert persistentItem.data_ref.type == db.DataRef.FILE, \
        "Filesystem operations can be done only when type is DataRef.FILE"

        dstAbsPath = os.path.join(self._repoBasePath, persistentItem.data_ref.url)
        if srcAbsPathForFileOperation == dstAbsPath:
            return # There is nothing to do in this case

        dstAbsPathDir, dstFilename = os.path.split(dstAbsPath)
        if not os.path.exists(dstAbsPathDir):
            os.makedirs(dstAbsPathDir)

        if fileOperation == "copy":
            shutil.copy(srcAbsPathForFileOperation, dstAbsPath)
        elif fileOperation == "move":
            shutil.move(srcAbsPathForFileOperation, dstAbsPathDir)
            oldName = os.path.join(dstAbsPathDir, os.path.basename(srcAbsPathForFileOperation))
            newName = os.path.join(dstAbsPathDir, dstFilename)
            os.rename(oldName, newName)


    def _prepare_data_ref(self, data_ref, user_login):

        def _prepare_data_ref_url(dr):
            dr.url = os.path.normpath(dr.url)

            # Remove trailing slash (if it presents)
            if dr.url.endswith(os.sep):
                dr.url = dr.url[0:len(dr.url)-1]

            # Check if the file is already withing repo tree
            if hlp.is_internal(dr.url, os.path.abspath(self._repoBasePath)):
                dr.url = os.path.relpath(dr.url, self._repoBasePath)
            else:
                if not hlp.is_none_or_empty(dr.dstRelPath) and dr.dstRelPath != ".":
                    dr.url = dr.dstRelPath
                    #TODO insert check to be sure that dr.dstRelPath inside a repository!!!
                else:
                    # When dstRelPath is empty or ".", then copy file to repo root dir
                    dr.url = os.path.basename(dr.url)

        data_ref.user_login = user_login

        data_ref.size = os.path.getsize(data_ref.url)

        data_ref.hash = hlp.computeFileHash(data_ref.url)
        data_ref.date_hashed = datetime.datetime.today()

        _prepare_data_ref_url(data_ref)


class CheckItemIntegrityCommand(AbstractCommand):
    def __init__(self, item, repoBasePath):
        super(CheckItemIntegrityCommand, self).__init__()
        self.__item = item
        self.__repoBasePath = repoBasePath

    def _execute(self, uow):
        errorSet = set()

        if self.__item.data_ref is not None and self.__item.data_ref.type == db.DataRef.FILE:
            self.__checkFileDataRef(uow.session, errorSet)

        return errorSet

    def __checkFileDataRef(self, session, errorSet):
        fileAbsPath = os.path.join(self.__repoBasePath, self.__item.data_ref.url)
        if not os.path.exists(fileAbsPath):
            errorSet.add(db.Item.ERROR_FILE_NOT_FOUND)
        else:
            size = os.path.getsize(fileAbsPath)
            if self.__item.data_ref.size != size:
                errorSet.add(db.Item.ERROR_FILE_HASH_MISMATCH)
                return
                # If sizes are different, then there is no need to compute hash:
                # hashes will be different too

            fileHash = hlp.computeFileHash(fileAbsPath)
            if self.__item.data_ref.hash != fileHash:
                errorSet.add(db.Item.ERROR_FILE_HASH_MISMATCH)
