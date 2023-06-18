import re


def increment_letter(letter):
    if letter == "Z":
        return "A"
    else:
        return chr(ord(letter) + 1)


def increment_suffix(string):
    if string[1] == "Z":
        return increment_letter(string[0]) + "A"
    else:
        return string[0] + increment_letter(string[1])


def decrement_letter(letter):
    if letter == "A":
        return "Z"
    else:
        return chr(ord(letter) - 1)


def decrement_suffix(string):
    if string[1] == "A":
        return decrement_letter(string[0]) + "Z"
    else:
        return string[0] + decrement_letter(string[1])


class Nid:
    """
    Just used for comparison
    """

    def generate_nids(self, reverse=False):
        suffix = self.id[-2:]
        number = int(self.id[1:-2])

        if not reverse:
            while True:
                yield f'N{number:0>4}{suffix}'

                number += 1

                if number > 9999:
                    number = 0
                    suffix = increment_suffix(suffix)

        while True:
            yield f'N{number:0>4}{suffix}'

            number -= 1

            if number < 0:
                number = 9999
                suffix = decrement_suffix(suffix)

    def __init__(self, id):
        id = id.upper()

        # N0000A -> N0000AA
        if len(id) == 6:
            suffix = id[-1]
            id += suffix

        # verify
        pattern = r"N[0-9]{4}[A-Z]{2}"
        if not re.match(pattern, id):
            raise ValueError(f"Invalid Nid: {id}")

        self.id = id

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return (self.id[-2:] < other.id[-2:]) or (
                self.id[-2:] == other.id[-2:] and int(self.id[1:5]) < int(other.id[1:5]))
