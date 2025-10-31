"""
Base repository pattern for database operations.
"""

from typing import Type, TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from abc import ABC, abstractmethod

from db.models import Base

T = TypeVar('T')


class BaseRepository(Generic[T], ABC):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, session: Session, model: Type[T]):
        """Initialize repository with database session and model class."""
        self.session = session
        self.model = model
    
    def create(self, **kwargs) -> T:
        """Create a new instance."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()  # Get ID without committing
        return instance
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get instance by ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all instances with optional pagination."""
        query = self.session.query(self.model)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def get_by_filters(self, filters: Dict[str, Any], limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get instances by filters."""
        query = self.session.query(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    def get_one_by_filters(self, filters: Dict[str, Any]) -> Optional[T]:
        """Get single instance by filters."""
        query = self.session.query(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        return query.first()
    
    def update(self, instance: T, **kwargs) -> T:
        """Update instance with new values."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        self.session.flush()
        return instance
    
    def delete(self, instance: T) -> bool:
        """Delete instance."""
        try:
            self.session.delete(instance)
            self.session.flush()
            return True
        except Exception:
            return False
    
    def delete_by_id(self, id: Any) -> bool:
        """Delete instance by ID."""
        instance = self.get_by_id(id)
        if instance:
            return self.delete(instance)
        return False
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count instances with optional filters."""
        query = self.session.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if instance exists with given filters."""
        return self.get_one_by_filters(filters) is not None
    
    def bulk_create(self, instances_data: List[Dict[str, Any]]) -> List[T]:
        """Create multiple instances."""
        instances = []
        for data in instances_data:
            instance = self.model(**data)
            instances.append(instance)
            self.session.add(instance)
        
        self.session.flush()
        return instances
    
    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[T, bool]:
        """Get existing instance or create new one."""
        instance = self.get_one_by_filters(kwargs)
        
        if instance:
            return instance, False
        
        # Create new instance
        create_data = kwargs.copy()
        if defaults:
            create_data.update(defaults)
        
        instance = self.create(**create_data)
        return instance, True


class RepositoryManager:
    """Manager class for handling all repositories."""
    
    def __init__(self, session: Session):
        """Initialize repository manager with database session."""
        self.session = session
        self._repositories = {}
    
    def get_repository(self, model_class: Type[T]) -> BaseRepository[T]:
        """Get repository for specific model class."""
        model_name = model_class.__name__
        
        if model_name not in self._repositories:
            self._repositories[model_name] = BaseRepository(self.session, model_class)
        
        return self._repositories[model_name]
    
    def commit(self):
        """Commit all changes to database."""
        self.session.commit()
    
    def rollback(self):
        """Rollback all changes."""
        self.session.rollback()
    
    def close(self):
        """Close the session."""
        self.session.close()