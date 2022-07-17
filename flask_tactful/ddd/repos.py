

from uuid import UUID
from abc import ABCMeta, abstractmethod

from sqlalchemy import and_
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from .entity import Entity
from .. import exceptions


class BaseRepo(metaclass=ABCMeta):
    """An interface for a generic repository with CRUD operations"""

    @abstractmethod
    def get_by_id(self, id: UUID) -> Entity:
        ...

    @abstractmethod
    def insert(self, entity: Entity):
        ...

    @abstractmethod
    def update(self, entity: Entity):
        ...

    @abstractmethod
    def delete(self, entity_id: UUID):
        ...

class GenericRepo:

    def __init__(self, session):
        self.session = session

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()


    def one_by_query(self, query_statement):
        try:
            return query_statement.one()
        except NoResultFound as no_result:
            raise exceptions.ItemNotExistsException() from no_result
        except MultipleResultsFound:  # FAAAAAAAAAAAAAALSE ERRROR MUST BE HANDLED WITH ANOTHER WAY
            return query_statement.first()


    def get_by_id(self, model, model_id: int, profile_id: int):
        query = self.session.query(model).filter(and_(model.id == model_id, model.profile_id == profile_id))
        return self.get_item(query)

    def delete(obj):
        self.session.delete(obj)
        self.session.commit()

