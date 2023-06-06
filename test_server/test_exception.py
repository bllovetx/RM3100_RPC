class MyException(Exception):
    def __init__(self):
        super().__init__("my exception")

try:
    raise MyException
except Exception as e:
    print(e)