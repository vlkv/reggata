# -*- coding: utf-8 -*-
'''
Created on 21.01.2012

@author: vlkv
'''
from PyQt4 import QtCore, QtGui
import traceback
from integrity_fixer import IntegrityFixer
from repo_mgr import *
import sys
from db_schema import Thumbnail
from exceptions import *
from commands import *
import zipfile
import os



class ImportItemsThread(QtCore.QThread):
    def __init__(self, parent, repo, importFromFilename, userLogin):
        super(ImportItemsThread, self).__init__(parent)
        self.repo = repo
        self.srcFile = importFromFilename
        self.userLogin = userLogin

    def run(self):
        srcArchive = zipfile.ZipFile(self.srcFile, "r")
        try:
            filenames = self.__getListOfMetadataFiles(srcArchive)
            for i in range(len(filenames)):
                filename = filenames[i]
                
                #Restore item from json state
                itemState = str(srcArchive.read(filename), "utf-8")
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
                    srcArchive.extract(item.data_ref.url, self.repo.base_path)
                    
                uow = self.repo.create_unit_of_work()
                try:
                    itemSrcAbsPath = dstAbsPath
                    itemDstRelPath = os.path.relpath(dstAbsPath, self.repo.base_path) \
                        if dstAbsPath is not None else None
                    cmd = SaveNewItemCommand(item, itemSrcAbsPath, itemDstRelPath)
                    uow.executeCommand(cmd)
                except Exception as ex:
                    if dstAbsPath is not None:
                        os.remove(dstAbsPath)
                    #count and remember error details to show it later in GUI
                finally:
                    uow.close()

                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(filenames)))
                        
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
            
        finally:
            srcArchive.close()
            self.emit(QtCore.SIGNAL("finished"))

    def __getListOfMetadataFiles(self, srcArchive):
        result = []
        filenames = srcArchive.namelist()
        for filename in filenames:
            #TODO use regexp here, for more precise check
            if not filename.startswith(".reggata"):
                continue
            result.append(filename)
        return result

class ExportItemsThread(QtCore.QThread):
    def __init__(self, parent, repo, itemIds, destinationFile):
        super(ExportItemsThread, self).__init__(parent)
        self.repo = repo
        self.itemIds = list(itemIds)
        self.dstFile = destinationFile
        
    def run(self):
        dstArchive = zipfile.ZipFile(self.dstFile, "w")
        try:
            for i in range(len(self.itemIds)):
                item = self.__getItemById(self.itemIds[i])
                
                if not self.__isItemIntegrityOk(item):
                    #TODO report about this problem to log and to list of errors
                    # Number of errors should be displayed in status bar at the end
                    continue

                self.__putItemStateToArchive(item, dstArchive)
                self.__putItemFileToArchive(item, dstArchive)
                        
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(self.itemIds)))
                        
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
            
        finally:
            dstArchive.close()
            self.emit(QtCore.SIGNAL("finished"))
    
    def __isItemIntegrityOk(self, item):
        result = False;
        uow = self.repo.create_unit_of_work()
        try:
            error_set = uow._check_item_integrity(uow.session, item, self.repo.base_path) 
            result = (len(error_set) == 0)
        finally:
            uow.close()
        return result
    
    def __putItemFileToArchive(self, item, archive):
        if item.data_ref is None:
            return
        itemFileAbsPath = os.path.join(self.repo.base_path, item.data_ref.url)
        archive.write(itemFileAbsPath, item.data_ref.url)
            
    def __putItemStateToArchive(self, item, archive):
        encoder = memento.Encoder()
        itemState = encoder.encode(item)
        itemStateFilename = "id=" + str(item.id) + "_title=" + item.title
        archive.writestr(os.path.join(".reggata/items", itemStateFilename), itemState)
        
    def __getItemById(self, itemId):
        item = None
        uow = self.repo.create_unit_of_work()
        try:
            item = uow.executeCommand(GetExpungedItemCommand(itemId))
        finally:
            uow.close()
        assert item is not None
        return item



class ExportItemsFilesThread(QtCore.QThread):
    def __init__(self, parent, repo, item_ids, destination_path):
        super(ExportItemsFilesThread, self).__init__(parent)
        self.repo = repo
        self.item_ids = item_ids
        self.dst_path = destination_path
        
    def run(self):
        self.errors = 0
        self.detailed_message = ""
        uow = self.repo.create_unit_of_work()
        try:
            i = 0
            for id in self.item_ids:
                item = uow.executeCommand(GetExpungedItemCommand(id))
                if item.is_data_ref_null():
                    continue
                
                src_file_path = os.path.join(self.repo.base_path, item.data_ref.url)
                unique_path = dst_file_path = os.path.join(self.dst_path, os.path.basename(src_file_path))
                filename_suffix = 1
                #Generate unique file name. I don't want different files with same name to overwrite each other
                while os.path.exists(unique_path):
                    name, ext = os.path.splitext(dst_file_path)
                    unique_path = name + str(filename_suffix) + ext
                    filename_suffix += 1
                    
                shutil.copy(src_file_path, unique_path)
                
                i += 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(self.item_ids)))
                        
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
            
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            uow.close()
            
            
class ItemIntegrityFixerThread(QtCore.QThread):
    '''
    Поток, выполняющий исправление целостности выбранной группы элементов (обычно из 
    результатов поискового запроса). 
    
    Нужно сделать функцию, чтобы запускать данный поток для выделенной группы элементов. 
    Для всех элементов хранилища тоже надо бы (но это потом может быть сделаю). 
    '''
    def __init__(self, parent, repo, items, lock, strategy, user_login):
        super(ItemIntegrityFixerThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        
        #Замок, для того, чтобы поток смог изменять передаваемые ему объекты, содержащиеся в списке items
        self.lock = lock
        
        self.interrupt = False
        
        #Это словарь, в котором ключи - это коды ошибок, а значения - способ исправления данной ошибки
        self.strategy = strategy
        #Задавать стратегию исправления ошибок хотелось бы несложным образом:
        #strategy = {ERROR_FILE_NOT_FOUND: STRATEGY_1, ERROR_FILE_SIZE_MISMATCH: STRATEGY_2} и т.п.
        
        self.user_login = user_login
        
    
    def run(self):
        
        uow = self.repo.create_unit_of_work()
        
        fixers = dict()
        for error_code, strategy in self.strategy.items():
            fixers[error_code] = IntegrityFixer.create_fixer(error_code, strategy, uow, self.repo.base_path, self.lock)
        
        try:
            #Список self.items должен содержать только что извлеченные из БД элементы
            #(вместе с data_ref объектами).
            for i in range(len(self.items)):
                item = self.items[i]
                
                print("fixing item " + str(item.id))
                
                #Сначала смотрим, проверялся ли item на целостность данных?
                if item.error is None:
                    try:
                        self.lock.lockForWrite()
                        #Если нет, то проверяем                    
                        item.error = UnitOfWork._check_item_integrity(uow.session, item, self.repo.base_path)
                    finally:
                        self.lock.unlock()
                                
                #Смотрим, есть ли у item-а ошибки
                for error_code in list(item.error):
                    #Для каждой ошибки item-а нужно
                    #глянуть, есть ли стратегия исправления в поле self.strategy для данной ошибки?                
                    #если нет, то пропускаем, ничего не делаем
                    #если есть, то выполняем исправление ошибки
                    #сообщаем, что элемент нужно обновить
                    fixer = fixers.get(error_code)
                    if fixer is not None:
                        fixed = fixer.fix_error(item, self.user_login)
                                                
                        uow.session.commit()
                        
                        if fixed:
                            try:
                                self.lock.lockForWrite()
                                #Убираем ошибку из списка
                                
                                item.error.remove(error_code)
                            finally:
                                self.lock.unlock()
                            
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(self.items)), item.table_row)
                    
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), sys.exc_info())
        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"))


       
class ItemIntegrityCheckerThread(QtCore.QThread):
    '''
    Поток, выполняющий в фоне проверку целостности группы элементов (обычно 
    результатов поискового запроса). 
    
    Нужно сделать функцию, чтобы запускать данный поток для выделенной группы элементов. 
    Для всех элементов хранилища тоже надо бы (но это потом может быть сделаю). 
    '''
    def __init__(self, parent, repo, items, lock):
        super(ItemIntegrityCheckerThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.lock = lock
        self.interrupt = False
    
    def run(self):
        error_count = 0
        uow = self.repo.create_unit_of_work()
        try:
            #Список self.items должен содержать только что извлеченные из БД элементы
            #(вместе с data_ref объектами).
            for i in range(len(self.items)):
                item = self.items[i]
                
                error_set = UnitOfWork._check_item_integrity(uow.session, item, self.repo._base_path)
                
                try:
                    self.lock.lockForWrite()
                    
                    #Сохраняем результат
                    item.error = error_set
                    
                    if len(error_set) > 0:                        
                        error_count += 1  
                    
                    self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i) / len(self.items)), item.table_row)
                    
                finally:
                    self.lock.unlock()
                    
        except:
            print(traceback.format_exc())
        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"), error_count)


class ThumbnailBuilderThread(QtCore.QThread):
    '''
    Поток, выполняющий построение миниатюр изображений и сохранение их в БД.
    
    Данный поток автоматически запускается после выполнение любого запроса элементов 
    (т.к. в результате любого запроса могут оказаться изображения.
    '''
    def __init__(self, parent, repo, items, lock, rebuild=False):
        super(ThumbnailBuilderThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.lock = lock
        self.interrupt = False
        self.rebuild = rebuild

    def run(self):
        uow = self.repo.create_unit_of_work()
        try:
            thumbnail_size = int(UserConfig().get("thumbnail_size", consts.THUMBNAIL_DEFAULT_SIZE))
            
            for i in range(len(self.items)):
                item = self.items[i]
                
                if self.interrupt:
                    print("ThumbnailBuilderThread interrupted!")
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
                    
                    uow.executeCommand(SaveThumbnailCommand(item.data_ref.id, th))
                    
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
                        print(traceback.format_exc())                
                                    
        except:
            self.emit(QtCore.SIGNAL("exception"), sys.exc_info())
            
        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"))
                        

       
class DeleteGroupOfItemsThread(QtCore.QThread):
    def __init__(self, parent, repo, item_ids, user_login):
        super(DeleteGroupOfItemsThread, self).__init__(parent)
        self.repo = repo
        self.item_ids = item_ids
        self.user_login = user_login
        self.errors = 0
        self.detailed_message = None
        
    def run(self):
        self.errors = 0
        self.detailed_message = ""
        uow = self.repo.create_unit_of_work()
        try:
            i = 0
            for id in self.item_ids:
                try:
                    cmd = DeleteItemCommand(id, self.user_login)
                    uow.executeCommand(cmd)
                except AccessError as ex:
                    #У пользователя self.user_login нет прав удалять данный элемент
                    self.errors += 1
                    self.detailed_message += str(ex) + os.linesep
                    
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.item_ids)))
                        
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
            
        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"))
            
        
class CreateGroupIfItemsThread(QtCore.QThread):
    def __init__(self, parent, repo, items):
        super(CreateGroupIfItemsThread, self).__init__(parent)
        self.repo = repo
        self.items = items
        self.error_log = []
        self.created_objects_count = 0
    
    def run(self):        
        self.error_log = []
        self.created_objects_count = 0
        uow = self.repo.create_unit_of_work()
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
                    uow.executeCommand(SaveNewItemCommand(item, srcAbsPath, dstRelPath))
                    self.created_objects_count += 1
                    
                except (ValueError, DataRefAlreadyExistsError):
                    #Skip this item and remember it's data_ref.url)
                    if item.data_ref:
                        self.error_log.append(item.data_ref.url)
                        
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)))
    
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
            
        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"), len(self.error_log))
            
        

class UpdateGroupOfItemsThread(QtCore.QThread):
    
    def __init__(self, parent, repo, items):
        super(UpdateGroupOfItemsThread, self).__init__(parent)
        self.repo = repo
        self.items = items

    def run(self):
        uow = self.repo.create_unit_of_work()
        try:
            i = 0
            for item in self.items:
                cmd = UpdateExistingItemCommand(item, item.user_login)
                uow.executeCommand(cmd)
                i = i + 1
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.items)))
                
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
        
        finally:
            uow.close()
            self.emit(QtCore.SIGNAL("finished"))
            
        
    
class BackgrThread(QtCore.QThread):
        
    def __init__(self, parent, callable, *args):
        super(BackgrThread, self).__init__(parent)
        self.args = args
        self.callable = callable
    
    def run(self):
        try:
            self.callable(*self.args)
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), traceback.format_exc())
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            
