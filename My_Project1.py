class Node:
    """A single term in a polynomial: coeff * x^exp."""

    def __init__(self, coeff: float, exp: int, next_node=None):
        self.coeff = coeff
        self.exp = exp
        self.next = next_node


class Polynomial:
    """Linked-list polynomial with float coefficients and integer exponents.

    Zero-coefficient nodes are never stored; near-zero values are detected
    via an absolute tolerance rather than exact equality.
    """

    ZERO_TOL = 1e-10  # threshold below which |coeff| is treated as zero

    def __init__(self):
        self.head = None

    # ------------------------- helpers ------------------------
    @staticmethod
    def _is_zero(coeff: float) -> bool:
        """Return True if coeff is effectively zero (float-safe)."""
        return abs(coeff) < Polynomial.ZERO_TOL

    def _remove_zeros(self):
        """Eliminate all zero-coefficient nodes from the list."""
        # Remove leading zeros
        while self.head is not None and self._is_zero(self.head.coeff):
            self.head = self.head.next
        # Remove interior / trailing zeros
        current = self.head
        while current is not None and current.next is not None:
            if self._is_zero(current.next.coeff):
                current.next = current.next.next
            else:
                current = current.next

    # ------------------------ core operations ------------------------
    def add_term(self, coeff: float, exp: int):
        """Add coeff * x^exp into the polynomial, maintaining desc-exp order.

        If a node with the same exponent already exists, the coefficients
        are combined.  The resulting node is removed if the sum is ~zero.
        """
        if exp < 0 or not isinstance(exp, int):
            raise ValueError(f"Exponent must be a non-negative integer, got {exp}")

        new_coeff = coeff
        prev = None
        current = self.head

        # Traverse to find correct position (descending exponent order)
        while current is not None and current.exp > exp:
            prev = current
            current = current.next

        if current is not None and current.exp == exp:
            # Merge with existing node
            current.coeff += new_coeff
            if self._is_zero(current.coeff):
                # Remove the now-zero node
                if prev is None:
                    self.head = current.next
                else:
                    prev.next = current.next
        elif not self._is_zero(new_coeff):
            # Insert new node only if coefficient is not ~zero
            new_node = Node(new_coeff, exp, current)
            if prev is None:
                self.head = new_node
            else:
                prev.next = new_node

    def evaluate(self, x: float) -> float:
        """Evaluate the polynomial at the given value of x."""
        result = 0.0
        current = self.head
        while current is not None:
            result += current.coeff * (x ** current.exp)
            current = current.next
        return result

    def __repr__(self):
        if self.head is None:
            return "0"
        parts = []
        current = self.head
        while current is not None:
            coeff = current.coeff
            exp = current.exp
            abs_c = abs(coeff)

            # build term body without sign
            if exp == 0:
                body = f"{abs_c}"
            elif exp == 1:
                if abs(abs_c - 1.0) < Polynomial.ZERO_TOL:
                    body = "x"
                else:
                    body = f"{abs_c}x"
            else:
                if abs(abs_c - 1.0) < Polynomial.ZERO_TOL:
                    body = f"x^{exp}"
                else:
                    body = f"{abs_c}x^{exp}"

            if coeff < 0:
                parts.append(("-", body))
            else:
                parts.append(("+", body))
            current = current.next

        # assemble string: first term drop leading '+'
        output = []
        for idx, (sign, body) in enumerate(parts):
            if idx == 0:
                if sign == "-":
                    output.append(f"-{body}")
                else:
                    output.append(body)
            else:
                output.append(f" {sign} {body}")
        return "".join(output)

    def __add__(self, other):
        """Return a new Polynomial that is the sum of self and other.

        Supports:
            poly + poly   -> Polynomial
            poly + float  -> Polynomial  (float treated as constant term)
            float + poly  -> Polynomial  (via __radd__)
        """
        if isinstance(other, (int, float)):
            result = Polynomial()
            current = self.head
            while current is not None:
                result.add_term(current.coeff, current.exp)
                current = current.next
            result.add_term(float(other), 0)
            return result

        if not isinstance(other, Polynomial):
            return NotImplemented

        result = Polynomial()
        # Add your code here to combine self and other polynomials
        current = self.head
        while current is not None:
            result.add_term(current.coeff, current.exp)
            current = current.next
        current_other = other.head
        while current_other is not None:
            result.add_term(current_other.coeff, current_other.exp)
            current_other = current_other.next

        return result

    def __sub__(self, other):
        """Return a new Polynomial that is self - other."""
        if isinstance(other, (int, float)):
            return self + (-float(other))
        if not isinstance(other, Polynomial):
            return NotImplemented
        
        result = Polynomial()
        current = self.head
        while current is not None:
            result.add_term(current.coeff, current.exp)
            current = current.next
        current_other = other.head
        while current_other is not None:
            result.add_term(-current_other.coeff, current_other.exp)
            current_other = current_other.next
        return result

    def __mul__(self, other):
        """Return a new Polynomial that is self * other."""
        if isinstance(other, (int, float)):
            result = Polynomial()
            current = self.head
            while current is not None:
                result.add_term(current.coeff * other, current.exp)
                current = current.next
            return result
        if not isinstance(other, Polynomial):
            return NotImplemented
        
        result = Polynomial()
        curr_self = self.head
        while curr_self is not None:
            curr_other = other.head
            while curr_other is not None:
                # (c1 * x^e1) * (c2 * x^e2) = (c1 * c2) * x^(e1 + e2)
                new_coeff = curr_self.coeff * curr_other.coeff
                new_exp = curr_self.exp + curr_other.exp
                result.add_term(new_coeff, new_exp)
                curr_other = curr_other.next
            curr_self = curr_self.next
        return result

    def __radd__(self, other):
    # Support float + Polynomial by delegating to __add__
        return self + other


p1 = Polynomial()
p1.add_term(3, 2)  # 3x^2
p1.add_term(5, 0)  # 5
print(p1)
p2 = Polynomial()
p2.add_term(2, 3)  # 2x^3
p2.add_term(1, 1)  # x
print(p2)
print(p1+3.5)
print(p1+p2)
print(3.5+p1+p2)

# test negative coeff and -1 case
p3 = Polynomial()
p3.add_term(-1,2)
p3.add_term(-1,1)
p3.add_term(-2,0)
print(p3)

p4 = Polynomial()
p4.add_term(1,5)
p4.add_term(-1,3)
print(p4)

# 作业要求添加的测试语句
print((p1-3.5)*p2+(p1+p2)*p4)