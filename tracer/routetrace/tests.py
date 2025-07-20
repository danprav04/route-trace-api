from tracer import find_route

import sys
from datetime import datetime


def main():
    test1_nihul_to_oneaman_with_mpls()
    test2_oneaman_to_nihul_with_mpls()
    test3_anannekaman_mpls()
    test4_sda_to_legacy()
    test5_sda_to_sda()


def run_test(source_ip, destination_ip, test_num):
    print(f"Executing test {test_num}...")
    try:
        sys.stdout = open('test_logs.txt', 'a')
        print(f"\n\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\ttest{test_num}\n")
        route = find_route(source_ip, destination_ip)
        print('\n\n')
        sys.stdout = sys.__stdout__

        if route:
            print(f"Test {test_num} passed.")
        else:
            print(f'Test {test_num} failed.')
    except Exception as e:
        sys.stdout = sys.__stdout__
        print(f"Test {test_num} failed because: {e}")


def test1_nihul_to_oneaman_with_mpls():
    source_ip = '{sensitive-ip}'
    destination_ip = '{sensitive-ip}'

    run_test(source_ip, destination_ip, 1)


def test2_oneaman_to_nihul_with_mpls():
    source_ip = '{sensitive-ip}'
    destination_ip = '{sensitive-ip}'

    run_test(source_ip, destination_ip, 2)


def test3_anannekaman_mpls():
    source_ip = '{sensitive-ip}'
    destination_ip = '{sensitive-ip}'

    run_test(source_ip, destination_ip, 3)


def test4_sda_to_legacy():
    source_ip = '{sensitive-ip}'
    destination_ip = '{sensitive-ip}'

    run_test(source_ip, destination_ip, 4)


def test5_sda_to_sda():
    source_ip = '{sensitive-ip}'
    destination_ip = '{sensitive-ip}'

    run_test(source_ip, destination_ip, 5)


if __name__ == '__main__':
    main()
