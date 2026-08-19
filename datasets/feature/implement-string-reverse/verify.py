import sys
from utils import reverse_words

def test_reverse_words():
    assert reverse_words("hello world") == "world hello"
    assert reverse_words("coding agent benchmark") == "benchmark agent coding"
    assert reverse_words("single") == "single"
    assert reverse_words("") == ""

if __name__ == "__main__":
    try:
        test_reverse_words()
        print("ALL TESTS PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)
