from typing import List

from sqlalchemy import Column, Integer, String, Text, DATETIME, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import PickleType
from enum import Enum

Base = declarative_base()

class RouteTypes(Enum):
    Layer2 = 2
    Layer3 = 3

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(20), nullable=False, unique=True)

    routes = relationship("Route", back_populates="user")


class Route(Base):
    __tablename__ = 'routes'

    id = Column(Integer, primary_key=True)
    source = Column(String(20), nullable=False)
    destination = Column(String(20), nullable=False)
    route = Column(PickleType)
    type = Column(Integer, nullable=False)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="routes")

    timestamp = Column(DATETIME, nullable=False)

    def __init__(self, source: str, destination: str, route: List, route_type: RouteTypes, user_id: int, timestamp):
        self.source = source
        self.destination = destination
        self.route = route
        self.type = route_type.value
        self.user_id = user_id
        self.timestamp = timestamp

    @property
    def route_type(self):
        return RouteTypes(self.type)

    @route_type.setter
    def route_type(self, type):
        self.type = type.value


engine = create_engine("mysql+mysqlconnector://{connection-string-sensitive}",
                       pool_size=150, max_overflow=300)
# engine = create_engine('sqlite:///routetrace.db')

Base.metadata.create_all(engine)
