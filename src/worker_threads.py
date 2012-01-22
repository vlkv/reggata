# -*- coding: utf-8 -*-
'''
Created on 21.01.2012

@author: vlkv
'''
from PyQt4 import QtCore
import os
import traceback
import shutil

class ExportItemsThread(QtCore.QThread):
    def __init__(self, parent, repo, item_ids, destination_path):
        super(ExportItemsThread, self).__init__(parent)
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
                item = uow.get_item(id)
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
                self.emit(QtCore.SIGNAL("progress"), int(100.0*float(i)/len(self.item_ids)))
                        
        except Exception as ex:
            self.emit(QtCore.SIGNAL("exception"), str(ex.__class__) + " " + str(ex))
            print(traceback.format_exc())
            
        finally:
            self.emit(QtCore.SIGNAL("finished"))
            uow.close()
            
            
    