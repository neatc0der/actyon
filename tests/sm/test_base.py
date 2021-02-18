from unittest import TestCase
from typing import List

from actyon.sm import State, StateError, StateMachine, StateStore


class TestStateStore(TestCase):
    def test_initial(self) -> None:
        states: List[State] = [
            State("State1", initial=True),
            State("State2"),
        ]
        store: StateStore = StateStore.get_initial({
            state.id: state
            for state in states
        }, StateMachine)

        self.assertEqual(store.current, "state1")
        self.assertEqual(store.previous, None)

    def test_missing_initial_state(self) -> None:
        states: List[State] = [
            State("State1"),
            State("State2"),
        ]
        with self.assertRaises(StateError) as context:
            StateStore.get_initial({
                state.id: state
                for state in states
            }, StateMachine)

        self.assertTrue("no initial state defined for state machine: StateMachine" in str(context.exception))

    def test_too_many_initial_states(self) -> None:
        states: List[State] = [
            State("State1", initial=True),
            State("State2", initial=True),
        ]
        with self.assertRaises(StateError) as context:
            StateStore.get_initial({
                state.id: state
                for state in states
            }, StateMachine)

        self.assertTrue("too many initial states defined for state machine: StateMachine" in str(context.exception))

    def test_shift(self) -> None:
        states: List[State] = [
            State("State1", initial=True),
            State("State2"),
        ]
        store: StateStore = StateStore.get_initial({
            state.id: state
            for state in states
        }, StateMachine)

        store.shift("state2")

        self.assertEqual(store.current, "state2")
        self.assertEqual(store.previous, "state1")
