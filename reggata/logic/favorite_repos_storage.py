'''
Created on 01.09.2012
@author: vlkv
'''
import logging
import reggata.consts as consts
from reggata.user_config import UserConfig
import reggata.helpers as helpers

logger = logging.getLogger(consts.ROOT_LOGGER + "." + __name__)


class FavoriteReposStorage(object):
    '''
        Manages all favorite repositories lists in Reggata. Note that every user has it's own
    favorite repositories list.
    '''
    
    def __init__(self):
        pass
    
    def addRepoToFavorites(self, userLogin, repoBasePath, repoAlias):
        favoriteReposPropValue = UserConfig().get("favorite_repos." + userLogin)
        repos = self.__decodeFavoriteReposFromStr(favoriteReposPropValue)
        
        foundRepos = [x for x in repos if x[0] == repoBasePath]
        if len(foundRepos) > 0:
            assert len(foundRepos) == 1
            #TODO: Maybe replace assert with removing extra elements?..
            return
        
        repos.append((repoBasePath, repoAlias))
        
        favoriteReposPropValue = self.__encodeFavoriteReposToStr(repos)
        UserConfig().store("favorite_repos." + userLogin, favoriteReposPropValue)
    
    def removeRepoFromFavorites(self, userLogin, repoBasePath):
        favoriteReposPropValue = UserConfig().get("favorite_repos." + userLogin)
        repos = self.__decodeFavoriteReposFromStr(favoriteReposPropValue)
        
        foundRepos = [x for x in repos if x[0] == repoBasePath]
        if len(foundRepos) == 0:
            return
        
        for repo in foundRepos:
            repos.remove(repo)
        
        favoriteReposPropValue = self.__encodeFavoriteReposToStr(repos)
        UserConfig().store("favorite_repos." + userLogin, favoriteReposPropValue)
    
    def favoriteRepos(self, userLogin):
        '''
            Returns list of tuples (repoBasePath, repoAliasName). Every tuple represents a single
        favorite repository of a user with given userLogin.
        '''
        favoriteReposPropValue = UserConfig().get("favorite_repos." + userLogin)
        repos = self.__decodeFavoriteReposFromStr(favoriteReposPropValue)
        
        return repos
            

    def __decodeFavoriteReposFromStr(self, favoriteReposPropValue):
        if helpers.is_none_or_empty(favoriteReposPropValue):
            return []
        try:
            repos = eval(favoriteReposPropValue)
        except SyntaxError:
            repos = []
            logger.warn("Could not parse '" + favoriteReposPropValue + "' " +  
                        " Check the value of 'favorite_repos' property in your reggata.conf.")
        return repos
    
    def __encodeFavoriteReposToStr(self, repos):
        return repr(repos)
        

        