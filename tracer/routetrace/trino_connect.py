import time
from pprint import pprint
import psycopg2
from typing import Union
import trino
from trino.exceptions import HttpError
from trino.auth import BasicAuthentication
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TrinoDatalake:
    def __init__(self):
        self.cursor = self.connect_to_trino()

    class TrinoConnectionError(Exception):
        pass

    def execute_query(self, cursor: Union[psycopg2.extensions.cursor, trino.dbapi.Cursor], query: str, debug: bool = False):
        """
        function execute a sql script
        :param [cursor: cursor type, query: string of sql script]
        :return the output of the execute
        """
        cursor_type = "trino"
        if debug:
            start = time.time()
            print(query)
        result = None
        result_columns = None
        retry_counter = 0
        error = None
        connection = cursor.connection
        while retry_counter < 5 and result is None:
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                result_columns = [i[0] for i in cursor.description]
            except (psycopg2.OperationalError, psycopg2.InternalError, psycopg2.errors.InFailedSqlTransaction, Exception) as e:
                if debug:
                    print(f"Execute error: {e}, Retry: {retry_counter}")
                retry_counter = retry_counter + 1
                error = e
                cursor = connection.cursor()
        if error and result is None:
            raise error
        if debug:
            end = time.time()
            print(f"{cursor_type} query execute time: {end - start: .6f} seconds")
            print(result)
        return result, result_columns

    def connect_to_trino(self):
        print({'option': 'super_title', 'message': 'connecting to trino...'})
        try:
            auth = BasicAuthentication('{srv-sensitive}', '{password-sensitive}')
            connection = trino.dbapi.connect(
                host='{host-sensitive}',
                port=443,
                auth=auth,
                catalog='cockroachdb-devnet',
                schema='network',
                http_scheme='https',
                verify=False
            )
            cursor = connection.cursor()
            print({'option': 'title', 'message': 'successful connection'})
            return cursor
        except Exception as e:
            print(f"Can't Connect To Trino, {e}")

    def exec_query(self, query):
        cursor = self.cursor
        site_query = query
        result_from_query = self.execute_query(cursor, site_query)
        return result_from_query
