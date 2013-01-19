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
            raise ValueError("srcAbsPath='{}' must be an absolute path.".format(srcAbsPath))

        if not os.path.exists(srcAbsPath):
            raise ValueError("srcAbsPath='{}' must point to an existing file.".format(srcAbsPath))

        if os.path.isabs(dstRelPath):
            raise ValueError("dstRelPath='{}' must be a relative to repository root path, but it is absolute."
                             .format(dstRelPath))

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
    def addStoredFile(session, item, repoBasePath, dataRef):
        fileAbsPath = os.path.join(repoBasePath, dataRef.url)
        if not os.path.exists(fileAbsPath):
            raise ValueError("dataRef object points a file that doesn't exist.")

        item.data_ref = dataRef
        item.data_ref_id = dataRef.id
        session.flush()





    @staticmethod
    def removeFile(session, item):
        '''
            This operation unlinks file from given item. If this file is not referenced by
        other alive items, it is deleted from filesystem also.
        '''
        assert item.data_ref is not None, "The Item instance doen't have any DataRef objects"
        dataRef = item.data_ref
        item.data_ref = None
        item.data_ref_id = None
        session.flush()

        anotherItem = session.query(db.Item).filter(db.Item.data_ref==dataRef).first()
        if anotherItem is None:
            session.delete(dataRef)
            session.flush()

        # TODO: I don't know if we should delete physical file also here...


    @staticmethod
    def moveFile(session, item, repoBasePath, newDstRelPath):
        assert item.data_ref is not None

        srcAbsPath = os.path.join(repoBasePath, item.data_ref.url)
        if not os.path.exists(srcAbsPath):
            raise ValueError("File '{}' is not found on the filesystem.".format(srcAbsPath))

        newDstAbsPath = os.path.join(repoBasePath, newDstRelPath)
        if os.path.exists(newDstAbsPath):
            raise ValueError("Cannot move file '{}' to '{}' because destination file already exists."
                             .format(srcAbsPath, newDstAbsPath))

        item.data_ref.url = newDstRelPath

        dstAbsPathDir = os.path.dirname(newDstAbsPath)
        if not os.path.exists(dstAbsPathDir):
            os.makedirs(dstAbsPathDir)

        shutil.move(srcAbsPath, dstAbsPathDir)
        oldName = os.path.join(dstAbsPathDir, os.path.basename(srcAbsPath))
        os.rename(oldName, newDstAbsPath)

        session.flush()


    @staticmethod
    def renameFile(session, item, newFileName):
        # TODO: call moveFile...
        pass


    @staticmethod
    def addThumbnail(session, item):
        pass

    @staticmethod
    def clearThumbnails(session, item):
        pass





