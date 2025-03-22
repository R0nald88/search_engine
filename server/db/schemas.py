from sqlalchemy import Boolean, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase, relationship, mapped_column, Mapped
from sqlalchemy.sql import func
from datetime import datetime
from typing import Any

# Create a base class for declarative models
class Base(DeclarativeBase):
    pass

class Relationship(Base):
    __tablename__ = 'relationship'

    relate_id: Mapped[str] = mapped_column(
        String(length=255), primary_key=True, unique=True, nullable=False)
    parent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('webpage.webpage_id'), index=True, nullable=False)
    child_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('webpage.webpage_id'), index=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    @staticmethod
    def to_basic_dict(obj: Any) -> dict[str, Any]:
        return {
            'parent_id': obj.parent_id,
            'child_id': obj.child_id,
            'relate_id': obj.relate_id,
            'is_active': obj.is_active,
        }
    
    @staticmethod
    def to_update_dict(obj: Any) -> dict[str, Any]:
        return {
            'is_active': obj.is_active,
        }
    
    def __eq__(self, value):
        if not isinstance(value, Relationship): return False
        return value.parent_id == self.parent_id and value.child_id == self.child_id
    
    def __hash__(self):
        return hash(f'{self.parent_id}-{self.child_id}')

class Index(Base):
    __tablename__ = "index"

    index_id: Mapped[str] = mapped_column(
        String(length=255), primary_key=True, unique=True, nullable=False)
    word_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('keyword.word_id'), index=True, nullable=False)
    webpage_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('webpage.webpage_id'), index=True, nullable=False)
    normalized_tf: Mapped[float] = mapped_column(Float, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    is_title: Mapped[bool] = mapped_column(Boolean, nullable=False)

    keyword: Mapped['Keyword'] = relationship('Keyword', back_populates='indexes')
    webpage: Mapped['Webpage'] = relationship('Webpage', back_populates='indexes')

    @staticmethod
    def to_basic_dict(obj: Any) -> dict[str, Any]:
        return {
            'word_id': obj.word_id,
            'webpage_id': obj.webpage_id,
            'frequency': obj.frequency,
            'is_title': obj.is_title,
            'index_id': obj.index_id,
            'normalized_tf': obj.normalized_tf
        }
    
    @staticmethod
    def to_update_dict(obj: Any) -> dict[str, Any]:
        return {
            'frequency': obj.frequency,
            'is_title': obj.is_title,
            'index_id': obj.index_id,
            'normalized_tf': obj.normalized_tf
        }
    
    def __eq__(self, value):
        if not isinstance(value, Index): return False
        return value.word_id == self.word_id and value.webpage_id == self.webpage_id
    
    def __hash__(self):
        return hash(f'{self.webpage_id}-{self.word_id}-{1 if self.is_title else 0}')

class Webpage(Base):
    __tablename__ = "webpage"

    webpage_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, unique=True, 
        autoincrement=True, nullable=False)
    url: Mapped[str] = mapped_column(String(length=255), index=True, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(length=255), nullable=True)
    last_modified_date: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=True)
    size: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_crawled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    children: Mapped[list['Webpage']] = relationship(
        'Webpage', secondary=Relationship.__table__,
        primaryjoin=webpage_id==Relationship.parent_id,
        secondaryjoin=webpage_id==Relationship.child_id, 
    )
    parent_relation: Mapped[list[Relationship]] = relationship(
        'Relationship', backref='parent',
        primaryjoin=webpage_id==Relationship.parent_id,
    )
    child_relation: Mapped[list[Relationship]] = relationship(
        'Relationship', backref='child',
        primaryjoin=webpage_id==Relationship.child_id,
    )
    indexes: Mapped[list['Index']] = relationship('Index', back_populates='webpage')
    keywords: Mapped[list['Keyword']] = relationship(
        'Keyword', secondary=Index.__table__, back_populates='webpages'
    )

    @staticmethod
    def to_basic_dict(obj: Any) -> dict[str, Any]:
        return {
            'url': obj.url,
            'title': obj.title,
            'last_modified_date': obj.last_modified_date,
            'size': obj.size,
            'is_active': obj.is_active,
            'is_crawled': obj.is_crawled,
        }
    
    @staticmethod
    def to_update_dict(obj: Any) -> dict[str, Any]:
        return Webpage.to_basic_dict(obj)
    
    def __eq__(self, value):
        if not isinstance(value, Webpage): return False
        return value.url == self.url
    
    def __hash__(self):
        return hash(self.url)

class Keyword(Base):
    __tablename__ = "keyword"

    word_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, unique=True, 
        autoincrement=True, nullable=False)
    word: Mapped[str] = mapped_column(String(length=255), index=True, unique=True, nullable=False)
    indexes: Mapped[list['Index']] = relationship('Index', back_populates='keyword')
    webpages: Mapped[list['Webpage']] = relationship(
        'Webpage', secondary=Index.__table__, back_populates='keywords'
    )

    @staticmethod
    def to_basic_dict(obj: Any) -> dict[str, Any]:
        return {
            'word': obj.word if not isinstance(obj, str) else obj.strip(),
        }
    
    @staticmethod
    def to_update_dict(obj: Any) -> dict[str, Any]:
        return Keyword.to_basic_dict(obj)
    
    def __eq__(self, value):
        if not isinstance(value, Keyword): return False
        return value.word == self.word
    
    def __hash__(self):
        return hash(self.word)
