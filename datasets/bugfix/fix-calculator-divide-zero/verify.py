import sys
from calculator import Calculator

def test_divide_normal():
    c = Calculator()
    assert abs(c.divide(10, 2) - 5.0) < 1e-6
    assert abs(c.divide(7, 2) - 3.5) < 1e-6

def test_divide_by_zero():
    c = Calculator()
    try:
        c.divide(10, 0)
        print("FAIL: Did not raise ValueError on divide by zero")
        sys.exit(1)
    except ValueError as e:
        assert "Cannot divide by zero" in str(e)
    except Exception as e:
        print(f"FAIL: Raised {type(e).__name__} instead of ValueError")
        sys.exit(1)

if __name__ == "__main__":
    test_divide_normal()
    test_divide_by_zero()
    print("ALL TESTS PASSED")
    sys.exit(0)
