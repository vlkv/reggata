'''
Created on 13.01.2013
@author: vlkv
'''
import reggata.data.db_schema as db
import reggata.helpers as hlp
import reggata.errors as err
import os
import datetime
import shutil

class ItemOperations:

    @staticmethod
    def addTags(session, item, tagNames, userLogin):
        for tagName in tagNames:
            tag = session.query(db.Tag).filter(db.Tag.name==tagName).first()
            if tag is None:
                # Such a tag is not in DB yet
                tag = db.Tag(tagName)
                session.add(tag)
                session.flush()
            # Link the tag with the item
            itemTag = db.Item_Tag(tag, userLogin)
            session.add(itemTag)
            itemTag.item = item
            item.item_tags.append(itemTag)
        session.flush()

    @staticmethod
    def removeTags(session, item, tagNames):
        for itag in item.item_tags:
            if itag.tag.name in tagNames:
                session.delete(itag)
        session.flush()


    @staticmethod
    def removeFields(session, item, fieldNames):
        for ifield in item.item_fields:
            if ifield.field.name in fieldNames:
                session.delete(ifield)
        session.flush()

    @staticmethod
    def addOrUpdateFields(session, item, nameValuePairs, userLogin):
        for (name, value) in nameValuePairs:
            ifield = next((ifield for ifield in item.item_fields if ifield.field.name == name), None)
            if ifield:
                ifield.field_value = value
                continue

            field = session.query(db.Field).filter(db.Field.name==name).first()
            if field is None:
                field = db.Field(name)
                session.add(field)
                session.flush()

            itemField = db.Item_Field(field, value, userLogin)
            session.add(itemField)
            itemField.item = item
            item.item_fields.append(itemField)

        session.flush()

    @staticmethod
    def addUntrackedFile(session, item, repoBasePath, srcAbsPath, dstRelPath, userLogin):
        assert not hlp.is_none_or_empty(srcAbsPath)
        assert dstRelPath is not None
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
        dstAbsPath = os.path.abspath(os.path.join(repoBasePath, dstRelPath))
        dstAbsPath = os.path.normpath(dstAbsPath)
        if srcAbsPath != dstAbsPath and os.path.exists(dstAbsPath):
            raise ValueError("{} should not point to an existing file.".format(dstAbsPath))

        dataRef = session.query(db.DataRef).filter(
            db.DataRef.url_raw==hlp.to_db_format(dstRelPath)).first()
        if dataRef is not None:
            raise err.DataRefAlreadyExistsError("DataRef instance with url='{}' "
                                               "is already in database. ".format(dstRelPath))

        item.data_ref = db.DataRef(objType=db.DataRef.FILE, url=dstRelPath)
        item.data_ref.user_login = userLogin
        item.data_ref.size = os.path.getsize(srcAbsPath)
        item.data_ref.hash = hlp.computeFileHash(srcAbsPath)
        item.data_ref.date_hashed = datetime.datetime.today()
        session.add(item.data_ref)
        item.data_ref_id = item.data_ref.id
        session.flush()

        #Now it's time to COPY physical file to the repository
        if srcAbsPath != dstAbsPath:
            try:
                head, _tail = os.path.split(dstAbsPath)
                os.makedirs(head)
            except:
                pass
            shutil.copy(srcAbsPath, dstAbsPath)
            #TODO should not use shutil.copy() function, because I cannot specify block size!
            #On very large files (about 15Gb) shutil.copy() function takes really A LOT OF TIME.
            #Because of small block size, I think.


    @staticmethod
    def addStoredFile(session, item, repoRootPath, srcRelPath, dstRelPath):
        pass

    @staticmethod
    def removeFile(session, item):
        '''
            This operation unlinks file from given item. If this file is not referenced by
        other alive items, it is deleted from filesystem also.
        '''
        pass

    @staticmethod
    def renameFile(session, item, newFileName):
        pass

    @staticmethod
    def moveFile(session, item, repoRootPath, newDstRelPath):
        pass

    @staticmethod
    def addThumbnail(session, item):
        pass

    @staticmethod
    def clearThumbnails(session, item):
        pass





