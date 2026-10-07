from __future__ import annotations

import unittest

from slean.worlds import ca


class BigPackedTables(unittest.TestCase):
    def test_large_tables_get_a_hexadecimal_literal(self):
        values = [(-1) ** i * (2**15 + i) for i in range(1024)]  # about 17 bits per entry: over 4300 digits
        term = ca.lean_fn(4, values)
        literal = term.rsplit(" ", 1)[1].rstrip(")")
        self.assertTrue(literal.startswith("0x"))
        off = -min(values)
        m = max(v + off for v in values).bit_length()
        self.assertEqual(int(literal, 16), ca.pack([v + off for v in values], m))
        self.assertFalse(ca.lean_fn(4, [1, 2, 3] * 30).split()[-1].startswith("0x"))


if __name__ == "__main__":
    unittest.main()
