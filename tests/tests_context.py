TEST_REPO_BASE_PATH = "./testrepo.rgt"
COPY_OF_TEST_REPO_BASE_PATH = "./copy_of_testrepo.rgt"

class ItemReliableFacts(object):
    pass

#NOTE: This item MUST NOT have any tags/fields from other users
existingAliveItem = ItemReliableFacts()
existingAliveItem.id = 2
existingAliveItem.title = "Don't Forget Me outro jam Montreal 2006"
existingAliveItem.ownerUserLogin = "user"
existingAliveItem.relFilePath = "./Dont_Forget_Me_Outro_Jam_Montreal 2006.txt"

# This item id has no corresponding item in test repo
nonExistingItem = ItemReliableFacts()
nonExistingItem.id = 1000000000

#This is an existing correct item
itemWithTagsAndFields = ItemReliableFacts()
itemWithTagsAndFields.id = 5
itemWithTagsAndFields.title = "I Could Have Lied.txt"
itemWithTagsAndFields.relFilePath = "./lyrics/RHCP/I Could Have Lied.txt"
itemWithTagsAndFields.ownerUserLogin = "user"
itemWithTagsAndFields.tags = ["RHCP", "Lyrics"]
itemWithTagsAndFields.fields = {"Rating": 5, 
                                "Year": 1991, 
                                "Notes": "This item has both tags and fields",
                                "Albom": "Blood Sugar Sex Magik"}



