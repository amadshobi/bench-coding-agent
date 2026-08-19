class Calculator:
    def divide(self, a: float, b: float) -> float:
        # BUG: Crashes with raw ZeroDivisionError or wrong handling
        return a / b
