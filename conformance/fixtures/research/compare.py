from decimal import Decimal
def within_bound(expected, observed, bound):
    return abs(Decimal(observed) - Decimal(expected)) <= Decimal(bound)
