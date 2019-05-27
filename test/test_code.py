import gep_onsset

class Testingfunction(unittest.TestCase):

    def setUp(self):
        self.hello_message = "Hello GEP!"

    def test_prints_hello_package(self):
        output = gep_onsset.hello()
        assert(output == self.hello_message)