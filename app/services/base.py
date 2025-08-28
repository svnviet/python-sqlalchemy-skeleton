from typing import Type, TypeVar, Generic, List, Optional
from sqlalchemy.exc import NoResultFound
from config.db import session_scope, Base

T = TypeVar("T", bound=Base)


class BaseService(Generic[T]):
    model: Type[T]

    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, **kwargs) -> T:
        with session_scope() as session:
            obj = self.model(**kwargs)
            session.add(obj)
            session.flush()
            return obj

    def get(self, obj_id: int) -> Optional[T]:
        with session_scope() as session:
            return session.get(self.model, obj_id)

    def list(self, limit: int = 100) -> List[T]:
        with session_scope() as session:
            return session.query(self.model).limit(limit).all()

    def update(self, obj_id: int, **kwargs) -> Optional[T]:
        with session_scope() as session:
            obj = session.get(self.model, obj_id)
            if not obj:
                raise NoResultFound(f"{self.model.__name__} not found with id {obj_id}")
            for key, value in kwargs.items():
                setattr(obj, key, value)
            session.add(obj)
            session.flush()
            return obj

    def delete(self, obj_id: int) -> bool:
        with session_scope() as session:
            obj = session.get(self.model, obj_id)
            if obj:
                session.delete(obj)
                return True
            return False
