from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity


def ft(x):
    return Q_(x, "foot")


def lf(x):
    return Q_(x, "foot")


def sqft(x):
    return Q_(x, "foot**2")


def cy(x):
    return Q_(x, "yard**3")
