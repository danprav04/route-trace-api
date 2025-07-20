import json
from typing import List

from .models import engine, Route, User, RouteTypes
from sqlalchemy.orm import Session
from datetime import datetime


def one_session(func):
    """
    Decorator which opens database session if its not already provided, passes it to the database function, and closes
    it after the function is finished.
    :param func:
    :return session:
    """

    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, Session):
                return func(*args, **kwargs)

        session = create_session()
        result = func(session, *args, **kwargs)
        close_session(session)
        return result

    return wrapper


def create_session():
    """
    Creates session with the global engine, and returns it.
    """

    return Session(engine)


def close_session(session):
    """
    Closes the provided session.
    :param session:
    """

    session.close()


@one_session
def add_route(session: Session, source: str, destination: str, route: list, route_type: RouteTypes, username: str):
    """
    Adds a new route to the database.
    :param route_type:
    :param session:
    :param source:
    :param destination:
    :param route:
    :param username:
    """

    user = session.query(User).filter_by(username=username).first()
    if user is None:
        user = User(username=username)
        session.add(user)
        session.commit()
    new_route = Route(source=source, destination=destination, route=route, route_type=route_type, user_id=user.id, timestamp=datetime.now())
    session.add(new_route)
    session.commit()

    return dict(map(lambda attr: (attr[0], attr[1].value), new_route.__dict__['_sa_instance_state'].attrs.items()))


@one_session
def get_route(session: Session, route_id: int):
    """
    Retrieves a route from the database based on source and destination.
    :param route_id:
    :param session:
    :return:
    """
    result = session.query(Route).filter_by(id=route_id).first()
    return result


@one_session
def delete_route(session: Session, source: str, destination: str):
    """
    Deletes a route from the database.
    :param session:
    :param source:
    :param destination:
    """
    route = session.query(Route).filter_by(source=source, destination=destination).order_by(Route.timestamp.desc()).first()
    if route is not None:
        session.delete(route)
        session.commit()


@one_session
def add_user(session: Session, username: str):
    """
    Adds a new user to the database.
    :param session:
    :param username:
    """
    existing_user = session.query(User).filter_by(username=username).first()
    if existing_user is None:
        new_user = User(username=username)
        session.add(new_user)
        session.commit()
        return new_user
    else:
        return existing_user


@one_session
def get_all_routes(session: Session):
    """
    Retrieves all routes from the database, sorted by timestamp with the newest first.
    :param session:
    :return:
    """
    return session.query(Route).order_by(Route.timestamp.desc()).all()


@one_session
def get_user_routes(session: Session, username: str):
    """
    Retrieves all routes for a user from the database, sorted by timestamp with the newest first.
    :param session:
    :param username:
    :return:
    """
    user = session.query(User).filter_by(username=username).first()
    if user is not None:
        return session.query(Route).filter_by(user_id=user.id).order_by(Route.timestamp.desc()).all()
    else:
        return []


@one_session
def get_search_routes(session: Session,
                      search_string: str = None,
                      route_type: RouteTypes = None,
                      username: str = None,
                      limit: int = 10,
                      page: int = 1
                      ) -> List[dict]:
    """
    Retrieves all routes for a user from the database, sorted by timestamp with the newest first.
    :param page: The page number to retrieve
    :param limit: The number of items per page
    :param route_type:
    :param search_string:
    :param session:
    :param username:
    :return:
    """

    query = session.query(Route)

    if search_string:
        query = query.filter(Route.source.contains(search_string) | Route.destination.contains(search_string))

    if route_type:
        query = query.filter_by(type=route_type)

    if username:
        user = session.query(User).filter_by(username=username).first()
        if user is not None:
            # corrected filter_by to filter, as filter_by requires keyword arguments
            query = query.filter(Route.user_id == user.id)

    # Calculate the offset based on the page and limit
    offset = (page - 1) * limit

    # Apply the offset and limit to the query
    routes = query.order_by(Route.timestamp.desc()).offset(offset).limit(limit).all()

    if len(routes) < 1:
        return []

    # Execute the query and return the results
    return [include_user(route) for route in routes]


# Helper function to include user object in route
def include_user(route: Route) -> dict:
    """
    Helper function to include the user object in a route dictionary
    :param route: Route object
    :return: dict with user object
    """
    user = route.user
    return {
        'id': route.id,
        'source': route.source,
        'destination': route.destination,
        'route': route.route,
        'route_type': route.route_type.name,
        'user': {
            'id': user.id,
            'username': user.username
        },
        'timestamp': route.timestamp
    }

@one_session
def get_all_routes_with_user(session: Session) -> List[dict]:
    """
    Retrieves all routes with user from the database.
    :param session:
    :return:
    """
    routes = get_all_routes(session)
    return [include_user(route) for route in routes]

@one_session
def get_user_routes_with_user(session: Session, username: str) -> List[dict]:
    """
    Retrieves all routes for a user with user from the database.
    :param session:
    :param username:
    :return:
    """
    routes = get_user_routes(session, username)
    return [include_user(route) for route in routes]


@one_session
def get_route_by_id(session: Session, route_id: int):
    """
    Retrieves a route from the database based on its ID.
    :param session:
    :param route_id:
    :return:
    """
    return session.query(Route).filter_by(id=route_id).first()
