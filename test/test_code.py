import test_package

class Testingfunction(unittest.TestCase):

    def setUp(self):
        self.hello_message = "Hello test package!"

    def test_prints_hello_package(self):
        output = test_package.hello()
        assert(output == self.hello_message)