from unittest import TestCase

from actyon.sm import State, Transition
from actyon.__meta__ import PACKAGE_NAME


class TestState(TestCase):
    def test_state_id(self) -> None:
        state: State = State("State")

        self.assertEqual(state.id, "state")
        self.assertEqual(state.initial, False)
        self.assertEqual(len(state.transitions), 0)

    def test_state_unsupported_id(self) -> None:
        with self.assertLogs(PACKAGE_NAME, level="WARN") as cm:
            state: State = State("Stäit# 1")
            self.assertEqual(cm.output, ['WARNING:actyon:State ID was changed from ”stäit# 1” to ”st_it__1”'])

        self.assertEqual(state.id, "st_it__1")

    def test_state_transition(self) -> None:
        state1: State = State("State1")
        state2: State = State("State2")

        transition: Transition = state1.to(state2, "trigger1", "trigger2")

        self.assertEqual(transition.source, state1)
        self.assertEqual(transition.target, state2)
        self.assertEqual(transition.triggers, ("trigger1", "trigger2"))
        self.assertIn("trigger1", state1.transitions)
        self.assertIn("trigger2", state1.transitions)
        self.assertEqual(state1.transitions["trigger1"], transition)
        self.assertEqual(state1.transitions["trigger2"], transition)
        self.assertEqual(len(transition.after), 0)
