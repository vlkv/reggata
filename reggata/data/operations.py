'''
Created on 13.01.2013
@author: vlkv
'''
import reggata.data.db_schema as db

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