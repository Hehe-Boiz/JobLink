from __future__ import annotations

import os
from collections.abc import Callable
from concurrent.futures import (
    FIRST_COMPLETED,
    Future,
    ThreadPoolExecutor,
    wait,
)
from dataclasses import dataclass
from typing import TypeVar, cast


T = TypeVar("T")


DEFAULT_MAX_IN_FLIGHT = int(
    os.environ.get(
        "CAREER_RAG_MAX_IN_FLIGHT",
        "10",
    )
)

DEFAULT_REFILL_SIZE = int(
    os.environ.get(
        "CAREER_RAG_REFILL_SIZE",
        "5",
    )
)


@dataclass(
    frozen=True,
    slots=True,
)
class RefillWindowConfig:
    max_in_flight: int = (
        DEFAULT_MAX_IN_FLIGHT
    )

    refill_size: int = (
        DEFAULT_REFILL_SIZE
    )

    def validate(self) -> None:
        if self.max_in_flight <= 0:
            raise ValueError(
                "max_in_flight must be > 0"
            )

        if self.refill_size <= 0:
            raise ValueError(
                "refill_size must be > 0"
            )

        if (
            self.refill_size
            > self.max_in_flight
        ):
            raise ValueError(
                "refill_size cannot exceed "
                "max_in_flight"
            )


def run_refill_window(
    tasks: list[Callable[[], T]],
    *,
    config: RefillWindowConfig | None = None,
    label: str = "requests",
) -> list[T]:
    """
    Execute I/O tasks using a bounded refill window.

    Example max=10, refill=5:

        submit 10
        wait until 5 logical tasks finish
        submit 5 more
        repeat

    Results are returned in original task order,
    not completion order.
    """

    if not tasks:
        return []

    config = (
        config
        or RefillWindowConfig()
    )

    config.validate()

    total = len(tasks)

    unset = object()

    results: list[object] = [
        unset
        for _ in tasks
    ]

    pending: dict[
        Future[T],
        int,
    ] = {}

    next_index = 0
    completed = 0
    completed_since_refill = 0

    with ThreadPoolExecutor(
        max_workers=config.max_in_flight,
        thread_name_prefix="career-rag",
    ) as executor:

        def submit(
            count: int,
        ) -> int:
            nonlocal next_index

            submitted = 0

            while (
                submitted < count
                and next_index < total
            ):
                index = next_index

                future = executor.submit(
                    tasks[index]
                )

                pending[
                    future
                ] = index

                next_index += 1
                submitted += 1

            return submitted

        initial = submit(
            min(
                config.max_in_flight,
                total,
            )
        )

        print(
            f"[concurrency] {label}: "
            f"tasks={total}; "
            f"max_in_flight="
            f"{config.max_in_flight}; "
            f"refill={config.refill_size}; "
            f"initial={initial}"
        )

        try:
            while pending:

                wait(
                    tuple(pending),
                    return_when=FIRST_COMPLETED,
                )

                # Several requests may have completed
                # between wake-up and this scan.
                done = [
                    future
                    for future
                    in tuple(pending)
                    if future.done()
                ]

                for future in done:
                    index = pending.pop(
                        future
                    )

                    results[index] = (
                        future.result()
                    )

                    completed += 1
                    completed_since_refill += 1

                submitted_now = 0

                while (
                    next_index < total
                    and completed_since_refill
                    >= config.refill_size
                ):
                    capacity = (
                        config.max_in_flight
                        - len(pending)
                    )

                    if capacity <= 0:
                        break

                    amount = min(
                        config.refill_size,
                        capacity,
                        total - next_index,
                    )

                    actual = submit(
                        amount
                    )

                    submitted_now += actual

                    completed_since_refill -= (
                        actual
                    )

                    if actual <= 0:
                        break

                # Defensive fallback.
                # Normally unreachable, but prevents
                # a scheduler deadlock if configuration
                # changes later.
                if (
                    not pending
                    and next_index < total
                ):
                    actual = submit(
                        min(
                            config.max_in_flight,
                            total - next_index,
                        )
                    )

                    submitted_now += actual
                    completed_since_refill = 0

                if submitted_now:
                    print(
                        f"[concurrency] {label}: "
                        f"completed="
                        f"{completed}/{total}; "
                        f"refilled="
                        f"{submitted_now}; "
                        f"in_flight="
                        f"{len(pending)}"
                    )

        except Exception:
            for future in pending:
                future.cancel()

            raise

    if any(
        value is unset
        for value in results
    ):
        raise RuntimeError(
            "Concurrency scheduler completed "
            "with missing results."
        )

    return cast(
        list[T],
        results,
    )
