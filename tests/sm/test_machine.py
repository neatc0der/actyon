from typing import Any, Dict
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, call, patch

from colorama import Style

from actyon.__meta__ import PACKAGE_NAME
from actyon.sm import State, StateHook, StateMachine, StateStore


class SampleMachine(StateMachine):
    state1: State = State("State1", initial=True)
    state2: State = State("State2")

    state1.to(state2, "trigger1")
    state2.to(state1, "trigger2")

    async def after_trigger1(self, state: StateStore, data: Dict[str, Any]) -> None:
        pass


class TestStateMachine(IsolatedAsyncioTestCase):
    def test_initialization(self) -> None:
        sample: SampleMachine = SampleMachine()

        self.assertEqual(sample.current, "state1")

    def test_initialization_of_hook(self) -> None:
        hook: StateHook = StateHook()
        sample: SampleMachine = SampleMachine(hook=hook)

        self.assertEqual(sample.current, "state1")
        self.assertEqual(hook.store_ref, sample._flux.state)

    @patch("actyon.flux.Flux.dispatch")
    async def test_direct_dispatch_on_known_trigger(self, dispatch_mock: AsyncMock) -> None:
        sample: SampleMachine = SampleMachine()

        await sample.trigger("trigger1")

        dispatch_mock.assert_awaited_once_with("trigger1")

    async def test_trigger_without_transition(self) -> None:
        sample: SampleMachine = SampleMachine()

        with self.assertLogs(PACKAGE_NAME, level='INFO') as cm:
            await sample.run()
            await sample.trigger("trigger2")
            await sample.done()
            self.assertEqual(cm.output, ['INFO:actyon:state "state1" has no transition for trigger: trigger2'])

        self.assertEqual(sample.current, "state1")

    @patch("actyon.flux.Flux.dispatch")
    async def test_no_dispatch_on_unknown_trigger(self, dispatch_mock: AsyncMock) -> None:
        sample: SampleMachine = SampleMachine()

        with self.assertLogs(PACKAGE_NAME, level='ERROR') as cm:
            await sample.trigger("unknown_trigger")
            self.assertEqual(cm.output, ["ERROR:actyon:no trigger found: unknown_trigger"])

        dispatch_mock.assert_not_awaited()

    @patch("actyon.flux.Flux.reducer")
    def test_after_function_is_registered(self, reducer_mock: Mock) -> None:
        sample: SampleMachine = SampleMachine()

        self.assertEqual(reducer_mock.mock_calls, [
            call("trigger1"),
            call()(sample._reducer),
            call("trigger2"),
            call()(sample._reducer),
        ])

    @patch(f"{SampleMachine.__module__}.SampleMachine.after_trigger1")
    async def test_transition_by_trigger(self, after_mock: AsyncMock) -> None:
        sample: SampleMachine = SampleMachine()

        await sample.run()
        await sample.trigger("trigger1", magic="black")
        await sample.done()

        self.assertEqual(sample.current, "state2")
        after_mock.assert_awaited_once_with(sample._flux._store, {"magic": "black"})


class TestStateHook(IsolatedAsyncioTestCase):
    def test_status_not_empty_after_running(self) -> None:
        hook: StateHook = StateHook()
        SampleMachine(hook=hook)

        status: str = hook.status
        self.assertNotEqual(status, "")
        self.assertIn(Style.RESET_ALL, status)

    def test_status_empty_while_running(self) -> None:
        hook: StateHook = StateHook()
        SampleMachine(hook=hook)
        hook._running = True

        self.assertEqual(hook.status, "")

    def test_status_without_color(self) -> None:
        hook: StateHook = StateHook(color=False)
        SampleMachine(hook=hook)
        hook._running = True

        status: str = hook.status
        self.assertEqual(status, "")
        self.assertNotIn(Style.RESET_ALL, status)
