import unittest


def all_tests_suite():
    suite = unittest.TestLoader().loadTestsFromNames([
        'osxmetadata.tests.test_osxmetdata',
    ])
    return suite


def main():
    runner = unittest.TextTestRunner()
    suite = all_tests_suite()
    runner.run(suite)


if __name__ == '__main__':
    main()
