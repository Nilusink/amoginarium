import typing as tp

class Test:
    def test(self, arg: tp.Any) -> tp.Any:
        ...

# The first argument must explicitly be 'Test'
type c = tp.Callable[[tp.Any], tp.Any]

a: c = Test.test

to = Test()

a(to, "a")