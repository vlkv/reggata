import os


TEST_REPO = "testrepo.rgt"
COPY_OF_TEST_REPO = "copy_of_testrepo.rgt"

__dirAbsPath = os.path.dirname(os.path.abspath(__file__))
TEST_REPO_BASE_PATH = os.path.join(__dirAbsPath, TEST_REPO)
COPY_OF_TEST_REPO_BASE_PATH = os.path.join(__dirAbsPath, COPY_OF_TEST_REPO)


class ItemReliableFacts(object):
    pass

nonExistingItem = ItemReliableFacts()
nonExistingItem.id = 1000000000

itemId_1 = ItemReliableFacts()
itemId_1.id = 1
itemId_1.title = "Dont Forget me Chorzow outro"
itemId_1.ownerUserLogin = "user"
itemId_1.relFilePath = "Dont Forget me Chorzow outro.txt"
itemId_1.tags = ["RHCP", "Tabs"]
itemId_1.fields = dict()

itemWithFile = ItemReliableFacts()
itemWithFile.id = 2
itemWithFile.title = "Don't Forget Me outro jam Montreal 2006"
itemWithFile.ownerUserLogin = "user"
itemWithFile.relFilePath = "Dont_Forget_Me_Outro_Jam_Montreal 2006.txt"


itemWithTagsAndFields = ItemReliableFacts()
itemWithTagsAndFields.id = 5
itemWithTagsAndFields.title = "I Could Have Lied.txt"
itemWithTagsAndFields.relFilePath = "lyrics/RHCP/I Could Have Lied.txt"
itemWithTagsAndFields.ownerUserLogin = "user"
itemWithTagsAndFields.tags = ["RHCP", "Lyrics"]
itemWithTagsAndFields.fields = {"Rating": 5, 
                                "Year": 1991, 
                                "Notes": "This item has both tags and fields",
                                "Albom": "Blood Sugar Sex Magik"}


itemWithoutFile = ItemReliableFacts()
itemWithoutFile.id = 6
itemWithoutFile.title = "Item without file"
itemWithoutFile.ownerUserLogin = "user"
itemWithoutFile.tags = ["Tag"]
itemWithoutFile.fields = {"Field": "test",
                          "Rating": 1,
                          "Notes": "This item has tags and fields, but it doesn't refereneces to any file"}

itemWithErrorFileNotFound = ItemReliableFacts()
itemWithErrorFileNotFound.id = 7
itemWithErrorFileNotFound.title = "Item with error: file not found"
itemWithErrorFileNotFound.ownerUserLogin = "user"
itemWithErrorFileNotFound.relFilePath = "consts.py"
itemWithErrorFileNotFound.tags = ["Tag", "Py"]
itemWithErrorFileNotFound.fields = dict()


itemWithErrorFileHashMismatch = ItemReliableFacts()
itemWithErrorFileHashMismatch.id = 8
itemWithErrorFileHashMismatch.title = "Item with error: file hash mismatch"
itemWithErrorFileHashMismatch.ownerUserLogin = "user"
itemWithErrorFileHashMismatch.relFilePath = "history/led_zeppelin_from_wikipedia.txt"
itemWithErrorFileHashMismatch.tags = ["Led_Zeppelin", "History"]
itemWithErrorFileHashMismatch.fields = {"Source": "http://en.wikipedia.org/wiki/Led_Zeppelin",
                                        "Rating": 2}


itemWithErrorFileNotFoundNo2 = ItemReliableFacts()
itemWithErrorFileNotFoundNo2.id = 9
itemWithErrorFileNotFoundNo2.title = "Item #2 with error: file not found"
itemWithErrorFileNotFoundNo2.ownerUserLogin = "user"
itemWithErrorFileNotFoundNo2.relFilePath = "this/is/lost/Dont_Forget_me_Chorzow_outro.tab"
itemWithErrorFileNotFoundNo2.tags = ["RHCP", "Tabs", "Error"]
itemWithErrorFileNotFoundNo2.fields = {"Notes": "This item references to a file which is lost. But in this repo there is a file with exactly the same contents (and the same hash)."}





