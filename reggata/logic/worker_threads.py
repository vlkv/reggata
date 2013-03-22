# -*- coding: utf-8 -*-
'''
Created on 21.01.2012
@author: vlkv
'''
from tarfile import TarFile
import tarfile
from _pyio import open
import logging
import os
import traceback
import datetime
from PyQt4 import QtCore, QtGui
import reggata.data.commands as cmds
from reggata.data.db_schema import Thumbnail
from reggata.data.integrity_fixer import IntegrityFixerFactory
import reggata.errors as errors
import reggata.consts as consts
from reggata.helpers import is_none_or_empty
from reggata import memento
import shutil
from reggata.user_config import UserConfig

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class AbstractWorkerThread(QtCore.QThread):
    def __init__(self, parent):
        super(AbstractWorkerThread, self).__init__(parent)
        self._exceptionDescription = ""

    def isExceptionRaised(self):
        return not is_none_or_empty(self._exceptionDescription)

    def exceptionDescription(self):
        return self._exceptionDescription

    def run(self):
        try:
            self.doWork()
        except Exception as ex:
            self._exceptionDescription = str(ex) + os.linesep + \
                "Stack trace:" + os.linesep + \
                traceback.format_exc()
            logger.error(self._exceptionDescription)
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
        finally:
            self.emit(QtCore.SIGNAL("finished"))

    def doWork(self):
        raise NotImplementedError("This function should be implemented in child classes.")


class ImportItemsThread(AbstractWorkerThread):
    def __init__(self, parent, repo, importFromFilename, userLogin):
        super(ImportItemsThread, self).__init__(parent)
        self.repo = repo
        self.srcFile = importFromFilename
        self.userLogin = userLogin

    def doWork(self):
        srcArchive = TarFile.open(self.srcFile, "r", format=tarfile.PAX_FORMAT)
        try:
            filenames = self.__getListOfMetadataFiles(srcArchive)
            for i in range(len(filenames)):
                filename = filenames[i]

                #Restore item from json state
                itemStateBytes = srcArchive.extractfile(filename).read()
                itemState = str(itemStateBytes, encoding="utf-8")
                item = memento.Decoder().decode(itemState)

                #Imported item will be owned by that user, who is performing the import
                item.user_login = self.userLogin

                #Move physical file to repository
                dstAbsPath = None
                if item.data_ref is not None:
                    dstAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
                    if os.path.exists(dstAbsPath):
                        #Skip this item. Count and remember this error
                        continue
                    srcArchive.extract(item.data_ref.url_raw, path=self.repo.base_path)

                uow = self.repo.createUnitOfWork()
                try:
                    itemSrcAbsPath = dstAbsPath
                    itemDstRelPath = os.path.relpath(dstAbsPath, self.repo.base_path) \
                        if dstAbsPath is not None else None
                    cmd = cmds.SaveNewItemCommand(item, itemSrcAbsPath, itemDstRelPath)
                    uow.executeCommand(cmd)
                except Exception:
                    if dstAbsPath is not None:
                        os.remove(dstAbsPath)
                    #count and remember error details to show it later in GUI
                finally:
                    uow.close()

                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(filenames)))
        finally:
            srcArchive.close()


    def __getListOfMetadataFiles(self, srcArchive):
        result = []
        tarInfos = srcArchive.getmembers()
        for tarInfo in tarInfos:
            #TODO use regexp here, for more precise check
            filename = tarInfo.name
            if not filename.startswith(".reggata"):
                continue
            result.append(filename)
        return result



class ExportItemsThread(AbstractWorkerThread):
    def __init__(self, parent, repo, itemIds, destinationFile):
        super(ExportItemsThread, self).__init__(parent)
        self.repo = repo
        self.itemIds = list(itemIds)
        self.dstFile = destinationFile
        self.exportedCount = 0
        self.skippedCount = 0

    def doWork(self):
        self.exportedCount = 0
        self.skippedCount = 0
        dstArchive = tarfile.open(self.dstFile, "w", format=tarfile.PAX_FORMAT)
        try:
            for i in range(len(self.itemIds)):
                item = self.__getItemById(self.itemIds[i])

                if not self.__isItemIntegrityOk(item):
                    logger.info("Skipping item id={}, title='{}' "
                                " during export operation: items's integrity check has failed."
                                .format(item.id, item.title))
                    self.skippedCount += 1
                    continue

                self.__putItemStateToArchive(item, dstArchive)
                self.__putItemFileToArchive(item, dstArchive)
                self.exportedCount += 1

                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(self.itemIds)))
        finally:
            dstArchive.close()


    def __isItemIntegrityOk(self, item):
        result = False;
        uow = self.repo.createUnitOfWork()
        try:
            error_set = uow.executeCommand(cmds.CheckItemIntegrityCommand(item, self.repo.base_path))
            result = (len(error_set) == 0)
        finally:
            uow.close()
        return result


    def __putItemFileToArchive(self, item, archive):
        if item.data_ref is None:
            return
        itemFileAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        archive.add(itemFileAbsPath, arcname=item.data_ref.url)


    def __putItemStateToArchive(self, item, archive):
        encoder = memento.Encoder()
        itemState = encoder.encode(item)
        itemStateFilename = "id=" + str(item.id) + "_title=" + item.title

        tmpFileName = os.path.join(consts.DEFAULT_TMP_DIR, "item_state.json")
        with open(tmpFileName, "w") as f:
            f.write(itemState)
        archive.add(tmpFileName, arcname=os.path.join(".reggata/items", itemStateFilename))

# TODO: Avoid creation of temporary file on filesystem..
#        fileObj = io.StringIO(itemState)
#        tarInfo = tarfile.TarInfo(name=os.path.join(".reggata/items", itemStateFilename))
#        tarInfo.size = len(fileObj.getvalue())
#        archive.addfile(tarinfo=tarInfo, fileobj=fileObj)


    def __getItemById(self, itemId):
        item = None
        uow = self.repo.createUnitOfWork()
        try:
            item = uow.executeCommand(cmds.GetExpungedItemCommand(itemId))
        finally:
            uow.close()
        assert item is not None
        return item



class ExportItemsFilesThread(AbstractWorkerThread):
    def __init__(self, parent, repo, item_ids, destination_path):
        super(ExportItemsFilesThread, self).__init__(parent)
        self.repo = repo
        self.item_ids = item_ids
        self.dst_path = destination_path
        self.filesExportedCount = 0
        self.filesSkippedCount = 0

    def doWork(self):
        self.filesExportedCount = 0
        self.filesSkippedCount = 0
        uow = self.repo.createUnitOfWork()
        try:
            i = 0
            for itemId in self.item_ids:
                item = uow.executeCommand(cmds.GetExpungedItemCommand(itemId))
                if not item.hasDataRef():
                    continue

                src_file_path = os.path.join(self.repo.base_path, item.data_ref.url)
                if not os.path.exists(src_file_path):
                    logger.info("Skipping file='{}' during export files operation: file not found."
                                .format(src_file_path))
                    self.filesSkippedCount += 1
                    continue

                unique_path = dst_file_path = os.path.join(self.dst_path, os.path.basename(src_file_path))
                filename_suffix = 1
                #Generate unique file name. I don't want different files with same name to overwrite each other
                while os.path.exists(unique_path):
                    name, ext = os.path.splitext(dst_file_path)
                    unique_path = name + str(filename_suffix) + ext
                    filename_suffix += 1

                shutil.copy(src_file_path, unique_path)
                self.filesExportedCount += 1

                i += 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(self.item_ids)))
        finally:
            uow.close()


class ItemIntegrityFixerThread(AbstractWorkerThread):

    def __init__(self, parent, repo, items, lock, strategy, user_login):
        super(ItemIntegrityFixerThread, self).__init__(parent)
        self.repo = repo
        self.items = items

        self.lock = lock

        self.interrupt = False

        # This is a dict with key - error code and a value - error fixing strategy
        self.strategy = strategy

        self.user_login = user_login


    def doWork(self):
        uow = self.repo.createUnitOfWork()

        fixers = dict()
        for error_code, strategy in self.strategy.items():
            fixers[error_code] = IntegrityFixerFactory.createFixer(
                                    error_code, strategy, uow, self.repo.base_path, self.lock)
        try:
            for i in range(len(self.items)):
                item = self.items[i]

                logger.debug("fixing item " + str(item.id))

                if item.error is None:
                    try:
                        self.lock.lockForWrite()
                        item.error = uow.executeCommand(
                            cmds.CheckItemIntegrityCommand(item, self.repo.base_path))
                    finally:
                        self.lock.unlock()

                for error_code in list(item.error):
                    fixer = fixers.get(error_code)
                    if fixer is not None:
                        fixed = fixer.fix_error(item, self.user_login)

                        uow.session.commit()

                        if fixed:
                            try:
                                self.lock.lockForWrite()
                                item.error.remove(error_code)
                            finally:
                                self.lock.unlock()

                percents = int(100.0*float(i) / len(self.items))
                self.emit(QtCore.SIGNAL("progress"), percents, item.table_row)
        finally:
            uow.close()



class ItemIntegrityCheckerThread(AbstractWorkerThread):

    def __init__(self, parent, repo, items, lock):
        super(ItemIntegrityCheckerThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.lock = lock
        self.interrupt = False
        self.timeoutMicroSec = 500000

    def doWork(self):
        error_count = 0
        uow = self.repo.createUnitOfWork()
        try:
            startTime = datetime.datetime.now()
            startIndex = 0
            for i in range(len(self.items)):
                item = self.items[i]
                error_set = uow.executeCommand(cmds.CheckItemIntegrityCommand(item, self.repo._base_path))

                try:
                    self.lock.lockForWrite()
                    item.error = error_set
                finally:
                    self.lock.unlock()

                if len(error_set) > 0:
                    error_count += 1

                currTime = datetime.datetime.now()
                isLastIteration = (i == len(self.items) - 1)
                if (currTime - startTime).microseconds > self.timeoutMicroSec or isLastIteration:
                    try:
                        self.lock.lockForRead()
                        topRow = self.items[startIndex].table_row
                    finally:
                        self.lock.unlock()
                    bottomRow = item.table_row
                    percents = int(100.0*float(i) / len(self.items))
                    self.emit(QtCore.SIGNAL("progress"), percents, topRow, bottomRow)
                    self.msleep(1)
                    startTime = currTime
                    startIndex = i
        finally:
            uow.close()


# TODO: ThumbnailBuilderThread should be refactored... code should be more readable
class ThumbnailBuilderThread(AbstractWorkerThread):
    '''
        This thread is started every time after any query execution in Intems Table Tool.
    '''
    def __init__(self, parent, repo, items, lock, rebuild=False):
        super(ThumbnailBuilderThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.lock = lock
        self.interrupt = False
        self.rebuild = rebuild

    def doWork(self):
        uow = self.repo.createUnitOfWork()
        try:
            thumbnail_size = int(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE))

            for i in range(len(self.items)):
                item = self.items[i]

                if self.interrupt:
                    logger.info("ThumbnailBuilderThread interrupted!")
                    break

                if not item.data_ref or not item.data_ref.is_image():
                    continue


                if self.rebuild == False and len(item.data_ref.thumbnails) > 0:
                    continue
                elif self.rebuild:
                    #Delete ALL existing thumbnails linked with current item.data_ref from database
                    uow.session.query(Thumbnail).filter(Thumbnail.data_ref_id==item.data_ref.id)\
                        .delete(synchronize_session=False)
                    uow.session.flush()

                    #Clear item.data_ref.thumbnails collection
                    try:
                        self.lock.lockForWrite()
                        item.data_ref.thumbnails[:] = []
                    finally:
                        self.lock.unlock()

                try:

                    #Read image from file
                    pixmap = QtGui.QImage(os.path.join(self.repo.base_path, item.data_ref.url))
                    if pixmap.isNull():
                        continue

                    #Scale image to thumbnail size
                    if (pixmap.height() > pixmap.width()):
                        pixmap = pixmap.scaledToHeight(thumbnail_size)
                    else:
                        pixmap = pixmap.scaledToWidth(thumbnail_size)
                    buffer = QtCore.QBuffer()
                    buffer.open(QtCore.QIODevice.WriteOnly)
                    pixmap.save(buffer, "JPG")

                    th = Thumbnail()
                    th.data = buffer.buffer().data()
                    th.size = thumbnail_size

                    uow.executeCommand(cmds.SaveThumbnailCommand(item.data_ref.id, th))

                    #Update items collection
                    try:
                        self.lock.lockForWrite()
                        item.data_ref.thumbnails.append(th)
                    finally:
                        self.lock.unlock()

                    self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)), item.table_row if hasattr(item, 'table_row') else i)

                except:
                    if self.rebuild:
                        #Stop thumbnails rebuilding
                        raise
                    else:
                        #Continue generating thumbnails in this case
                        logger.error(traceback.format_exc())
        finally:
            uow.close()



class DeleteGroupOfItemsThread(AbstractWorkerThread):
    def __init__(self, parent, repo, item_ids, user_login):
        super(DeleteGroupOfItemsThread, self).__init__(parent)
        self.repo = repo
        self.item_ids = item_ids
        self.user_login = user_login
        self.errors = 0
        self.detailed_message = None

    def doWork(self):
        self.errors = 0
        self.detailed_message = ""
        uow = self.repo.createUnitOfWork()
        try:
            i = 0
            for itemId in self.item_ids:
                try:
                    cmd = cmds.DeleteItemCommand(itemId, self.user_login)
                    uow.executeCommand(cmd)
                except errors.AccessError as ex:
                    # User self.user_login has no permissions to delete this item
                    self.errors += 1
                    self.detailed_message += str(ex) + os.linesep

                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.item_ids)))

            uow.executeCommand(cmds.DeleteHangingTagsCommand())
            uow.executeCommand(cmds.DeleteHangingFieldsCommand())
        finally:
            uow.close()



class CreateGroupOfItemsThread(AbstractWorkerThread):
    def __init__(self, parent, repo, items):
        super(CreateGroupOfItemsThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.skippedCount = 0
        self.createdCount = 0
        self.lastSavedItemIds = []

    def doWork(self):
        self.skippedCount = 0
        self.createdCount = 0
        uow = self.repo.createUnitOfWork()
        try:
            i = 0
            for item in self.items:
                try:
                    #Every item is saved in a separate transaction
                    srcAbsPath = None
                    dstRelPath = None
                    if item.data_ref:
                        srcAbsPath = item.data_ref.srcAbsPath
                        dstRelPath = item.data_ref.dstRelPath
                    savedItemId = uow.executeCommand(cmds.SaveNewItemCommand(item, srcAbsPath, dstRelPath))
                    self.lastSavedItemIds.append(savedItemId)
                    self.createdCount += 1

                except (ValueError, errors.DataRefAlreadyExistsError):
                    self.skippedCount += 1

                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)))
        finally:
            uow.close()


class UpdateGroupOfItemsThread(AbstractWorkerThread):

    def __init__(self, parent, repo, items):
        super(UpdateGroupOfItemsThread, self).__init__(parent)
        self.repo = repo
        self.items = items

    def doWork(self):
        uow = self.repo.createUnitOfWork()
        try:
            i = 0
            for item in self.items:
                srcAbsPath = os.path.join(self.repo.base_path, item.data_ref.url) \
                    if item.data_ref is not None \
                    else None
                dstRelPath = item.data_ref.dstRelPath if item.data_ref \
                    is not None \
                    else None
                cmd = cmds.UpdateExistingItemCommand(item, srcAbsPath, dstRelPath, item.user_login)
                uow.executeCommand(cmd)
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)))
        finally:
            uow.close()


class MoveFilesThread(AbstractWorkerThread):
    def __init__(self, parent, repo, srcDstFileAbsPaths, selFilesAndDirs):
        super(MoveFilesThread, self).__init__(parent)
        self._repo = repo
        self._srcDstFileAbsPaths = srcDstFileAbsPaths
        self._selFilesAndDirs = selFilesAndDirs
        self.errors = 0
        self.detailed_message = None

    def __removeIfEmpty(self, dirAbsPath):
        filesDirs = os.listdir(dirAbsPath)
        if len(filesDirs) == 0:
            os.rmdir(dirAbsPath)
        else:
            for fileOrDir in filesDirs:
                if os.path.isdir(fileOrDir):
                    self.__removeIfEmpty(self, fileOrDir)
            

    def doWork(self):
        self.errors = 0
        self.detailed_message = ""
        uow = self._repo.createUnitOfWork()
        try:
            i = 0
            for (srcFile, dstFile) in self._srcDstFileAbsPaths:
                try:
                    cmd = cmds.MoveFileCommand(srcFile, dstFile)
                    uow.executeCommand(cmd)
                except Exception as ex:
                    self.errors += 1
                    self.detailed_message += str(ex) + os.linesep

                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self._srcDstFileAbsPaths)))
            
            # Now we should delete empty dirs (if there are any)
            for selFile in self._selFilesAndDirs:
                if os.path.isdir(selFile):
                    self.__removeIfEmpty(selFile)
        finally:
            uow.close()



class BackgrThread(AbstractWorkerThread):

    def __init__(self, parent, function, *args):
        super(BackgrThread, self).__init__(parent)
        self._args = args
        self._function = function
        self.result = None

    def doWork(self):
        self.result = self._function(*self._args)
