from contextlib import contextmanager
from typing import Generator

from app.database.session import SQLALCHEMY_DATABASE_URL, get_local_session
from app.log import get_logger

log = get_logger(__name__)


def get_db() -> Generator:
    """
    Returns a generator that yields a database session

    Yields:
        Session: A database session object.

    Raises:
        Exception: If an error occurs while getting the database session.
    """

    log.debug("getting database session")
    db = get_local_session(SQLALCHEMY_DATABASE_URL, False)()
    try:
        yield db
    finally: 
        log.debug("closing database session")
        db.close() 


@contextmanager
def get_ctx_db(database_url: str) -> Generator:
    """
    Context manager that creates a database session and yields
    it for use in a 'with' statement.

    Parameters:
        database_url (str): The URL of the database to connect to.

    Yields:
        Generator: A database session.

    Raises:
        Exception: If an error occurs while getting the database session.

    """
    log.debug("getting database session")
    db = get_local_session(database_url)()
    try:
        yield db
    except Exception as e:
        log.error("An error occurred while getting the database session. Error: %s", e)
        raise Exception from e
    finally:
        log.debug("closing database session")
        db.close()

