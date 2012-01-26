TEST_REPO_BASE_PATH = "./testrepo.rgt"
COPY_OF_TEST_REPO_BASE_PATH = "./copy_of_testrepo.rgt"

class ItemActualFacts(object):
    pass

#NOTE: This item MUST NOT have any tags/fields from other users
existingAliveItem = ItemActualFacts()
existingAliveItem.id = 2
existingAliveItem.title = "Don't Forget Me outro jam Montreal 2006"
existingAliveItem.ownerUserLogin = "user"
existingAliveItem.relFilePath = "./Dont_Forget_Me_Outro_Jam_Montreal 2006.txt"

nonExistingItem = ItemActualFacts()
nonExistingItem.id = 1000000000
