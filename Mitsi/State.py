import json
from decimal import Decimal

import Mitsi.MitsiLookup as lookup


class State:
    """
    State holds the current state for the heatpump,
    for access in Mitsi QTT or TTP.
    This is an abstraction of both Lookup and validation
    of lookups
    """
    _state = {
        'power': lookup.POWER['OFF'],
        'temp': 18.5,
        'room_temp': 16.5,
        'vane': lookup.VANE['AUTO'],
        'mode': lookup.MODE['AUTO'],
        'fan': lookup.FAN['AUTO'],
        'dir': lookup.DIR['|']
    }

    def update(self, state):
        """
        Save the state to the State.state state :-D
        Validates inputted values against MitsiLookup
        :param state: string|dict
        :return: None
        """
        if not isinstance(dict, state):
            state = json.loads(state)
        for key, value in state:
            if self.validate(key, value):
                self._state[key.tolower()] = value

    def validate(self, key, value):
        """

        :param key: key of the state
        :param value: value to validate against
        :return: boolean
        """
        key = key.tolower()
        if key == 'temp':
            value = self.round_to_half(value)
        if (key == 'power' and value in lookup.POWER) or (
                key == 'mode' and value in lookup.MODE) or (
                key == 'vane' and value in lookup.VANE) or (
                key == 'dir' and value in lookup.DIR) or (
                key == 'fan' and value in lookup.FAN) or (
                key == 'temp' and Decimal(value) in lookup.TEMP):
            return True
        return False

    def json_state(self):
        return json.dumps(self.state())

    def state(self):
        return self.state

    @staticmethod
    def round_to_half(number):
        """Round a number to the closest half integer.
        >>> State.round_to_half(1.3)
        1.5
        >>> State.round_to_half(2.6)
        2.5
        >>> State.round_to_half(3.0)
        3.0
        >>> State.round_to_half(4.1)
        4.0
        >>> State.round_to_half(1.25)
        1.0
        WARNING, rounding double decimal numbers may
        yield unexpected results (e.g. 1.25 becomes 1.0, not 1.5)"""

        return round(number * 2) / 2
