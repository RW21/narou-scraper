from unittest import TestCase

from nid import decrement_suffix, increment_suffix, generate_nids, Nid


class Test(TestCase):
    def test_decrement_letter(self):
        to_test = (
            ("AA", "ZZ"),
            ("AB", "AA"),
            ("CA", "BZ"), )
        for test in to_test:
            self.assertEqual(decrement_suffix(test[0]), test[1])

    def test_increment_suffix(self):
        to_test = (
            ("AA", "AB"),
            ("AB", "AC"),
            ("ZZ", "AA"),
        )
        for test in to_test:
            self.assertEqual(increment_suffix(test[0]), test[1])

    def test_generate_ids(self):
        to_test = (
            ("N0000AA", "N0001AA"),
            ("N9999AA", "N0000AB"),
            ("N9999CZ", "N0000DA"),
        )

        for test in to_test:
            gen = generate_nids(test[0])
            next(gen)
            a = next(gen)
            self.assertEqual(a, test[1])

    def test_generate_ids_reverse(self):
        to_test = (
            ("N0000AA", "N9999ZZ"),
            ("N0001AA", "N0000AA"),
            ("N0000AB", "N9999AA"),
            ("N0000DA", "N9999CZ"),
        )

        for test in to_test:
            gen = generate_nids(test[0], reverse=True)
            next(gen)
            a = next(gen)
            self.assertEqual(a, test[1])

    def test_nid_lt(self):
        self.assertTrue(Nid('N0000BB') < Nid('N0001BB'))
        self.assertTrue(Nid('N9999AA') < Nid('N0000AB'))
        self.assertFalse(Nid('N9999AA') > Nid('N0000AB'))

        # generated

        # Test case 1:
        id1 = Nid("N0000AA")
        id2 = Nid("N0000AB")
        assert id1 < id2

        # Test case 2:
        id1 = Nid("N0000AA")
        id2 = Nid("N0001AA")
        assert id1 < id2

        # Test case 3:
        id1 = Nid("N0000AZ")
        id2 = Nid("N0001AA")
        assert id1 > id2

        # Test case 4:
        id1 = Nid("N0000AA")
        id2 = Nid("N0000AA")
        assert not id1 < id2

        # Test case 5:
        id1 = Nid("N9999AA")
        id2 = Nid("N0000AB")
        assert id1 < id2
