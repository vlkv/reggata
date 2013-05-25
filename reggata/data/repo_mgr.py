'''
Created on 30.09.2010
@author: vlkv
'''
import sqlalchemy as sqa
from sqlalchemy.orm import sessionmaker
import os.path
from reggata.errors import CannotOpenRepoError
import reggata.consts as consts
from reggata.user_config import UserConfig
from reggata.data.db_schema import Base, HistoryRec
from reggata.helpers import stringToBool

class RepoMgr(object):
    '''
        Represents one single repository. Manages it as a whole.
    '''

    def __init__(self, path_to_repo):
        '''
            Opens an existing repository at given path.
        '''
        try:
            self._base_path = path_to_repo
            if not os.path.exists(self.base_path + os.sep + consts.METADATA_DIR):
                raise Exception("Directory {} is not a repository base path."
                                .format(self.base_path))

            engine_echo = stringToBool(UserConfig().get("sqlalchemy.engine_echo"))

            self.__engine = sqa.create_engine(\
                "sqlite:///" + self.base_path + os.sep + consts.METADATA_DIR + os.sep + \
                consts.DB_FILE, echo=engine_echo)

            self.Session = sessionmaker(bind=self.__engine)
        except Exception as ex:
            raise CannotOpenRepoError(ex)

    def __del__(self):
        pass

    @property
    def base_path(self):
        '''
            Repository base path is the root directory of the repository.
        '''
        return self._base_path

    @base_path.setter
    def base_path(self, value):
        self._base_path = value

    @staticmethod
    def createNewRepo(base_path):
        '''
            Initializes a new repo at a given path. This consists of these steps:
            1) Checks that base_path exists
            2) Checks that <base_path>/.reggata directory does not exist yet
            3) Creates <base_path>/.reggata directory in repository root and
        empty sqlite database inside it.
            4) At last, this function opens just created repository and
        returns RepoMgr object, associated with it.
        '''
        if (not os.path.exists(base_path)):
            raise Exception("Directory {} doesn't exists.".format(base_path))

        if (os.path.exists(base_path + os.sep + consts.METADATA_DIR)):
            raise Exception("It looks like {} is already a repository base path."
                            .format(base_path))

        os.mkdir(base_path + os.sep + consts.METADATA_DIR)

        engine = sqa.create_engine("sqlite:///" + base_path + os.sep + \
                                   consts.METADATA_DIR + os.sep + consts.DB_FILE)
        Base.metadata.create_all(engine)

        return RepoMgr(base_path)


    def createUnitOfWork(self):
        return UnitOfWork(self.Session(), self.base_path)


class UnitOfWork(object):
    '''
        This class allows you to open a working session with database (unit of work),
    do some actions and close the session.
    '''

    #TODO Maybe argument repo_base_path should be moved to Command class ctor?..
    def __init__(self, session, repo_base_path):
        self._session = session
        self._repo_base_path = repo_base_path

    def __del__(self):
        if self._session is not None:
            self._session.close()

    def close(self):
        self._session.expunge_all()
        self._session.close()

    @property
    def session(self):
        return self._session

    def executeCommand(self, command):
        return command._execute(self)


    # This fun is obsolete and deprecated
    @staticmethod
    def _find_item_latest_history_rec(session, item_0):
        '''
            Returns the latest history record of item_0 Item object.
        Also, it returns None, if the record was not found.
        '''
        data_ref_hash = None
        data_ref_url = None
        if item_0.data_ref is not None:
            data_ref_hash = item_0.data_ref.hash
            data_ref_url = item_0.data_ref.url_raw
        parent_hr = session.query(HistoryRec).filter(HistoryRec.item_id==item_0.id)\
                .filter(HistoryRec.item_hash==item_0.hash())\
                .filter(HistoryRec.data_ref_hash==data_ref_hash)\
                .filter(HistoryRec.data_ref_url_raw==data_ref_url)\
                .order_by(HistoryRec.id.desc()).first()
        return parent_hr

    # This fun is obsolete and deprecated
    @staticmethod
    def _save_history_rec(session, item_0, user_login, operation, parent1_id=None, parent2_id=None):

        if operation is None:
            raise ValueError("Argument operation cannot be None.")

        if operation != HistoryRec.CREATE and parent1_id is None:
            raise ValueError("Argument parent1_id cannot be None in CREATE operation.")

        hr = HistoryRec(item_id = item_0.id, item_hash=item_0.hash(), \
                        operation=operation, \
                        user_login=user_login, \
                        parent1_id = parent1_id, parent2_id = parent2_id)
        if item_0.data_ref is not None:
            hr.data_ref_hash = item_0.data_ref.hash
            hr.data_ref_url = item_0.data_ref.url
        session.add(hr)
