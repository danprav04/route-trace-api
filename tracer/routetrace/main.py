from pprint import pprint
from time import time

from tracer import find_route


def main():
    source_ip = '{sensitive-ip}'
    destination_ip = '{sensitive-ip}'

    route = find_route(source_ip, destination_ip)
    print('\n\n')
    pprint(route)


if __name__ == '__main__':
    start_time = time()
    main()
    delta = time() - start_time
    print(f'\n\nProgram finished in {round(delta, 4)}s')
