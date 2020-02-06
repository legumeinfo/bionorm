"""Check to see the code passes format"""
# third-party imports
import pytest
import sh


def test_formatting_with_black():
    print("Checking to see if black likes your formatting")
    try:
        output = sh.black(["--check", "."])
    except sh.ErrorReturnCode as e:
        print(e)
        pytest.fail(e)
    print(output)
