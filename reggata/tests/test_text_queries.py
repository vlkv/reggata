from reggata.tests.abstract_test_cases import AbstractTestCaseWithRepo
from reggata.data.commands import QueryItemsByParseTree
from reggata.parsers.query_parser import parser

class SimpleQueriesTest(AbstractTestCaseWithRepo):
    
    def test_Tag1AndTag2(self):
        try:
            uow = self.repo.createUnitOfWork()
            queryTree = parser.parse("Txt AND Lyrics")
            cmd = QueryItemsByParseTree(queryTree)
            items = uow.executeCommand(cmd)
            
            self.assertEqual(len(items), 2)
            expectedItemIds = [14, 15]
            self.assertTrue(items[0].id in expectedItemIds)
            self.assertTrue(items[1].id in expectedItemIds)
        finally:
            uow.close()
