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
        
        
    @staticmethod
    def removeFields(session, item, fieldNames):
        for ifield in item.item_fields:
            if ifield.field.name in fieldNames:
                session.delete(ifield)
        session.flush()
        
    @staticmethod
    def addOrUpdateFields(session, item, nameValuePairs, userLogin):
        for (name, value) in nameValuePairs:
            ifield = next((ifield for ifield in item.item_fields if ifield.field.name == name), None)
            if ifield:
                ifield.field_value = value
                continue

            field = session.query(db.Field).filter(db.Field.name==name).first()
            if field is None:
                field = db.Field(name)
                session.add(field)
                session.flush()
                
            itemField = db.Item_Field(field, value, userLogin)
            session.add(itemField)
            itemField.item = item
            item.item_fields.append(itemField)
            
        session.flush()
            
            
        
        
        