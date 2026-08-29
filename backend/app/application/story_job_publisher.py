from __future__ import annotations


class StoryJobPublisher:
    def __init__(self, outbox, transport) -> None:
        self._outbox = outbox
        self._transport = transport

    def run_once(self) -> str:
        dispatch = self._outbox.claim_one()
        if dispatch is None:
            return "idle"
        try:
            self._transport.publish(dispatch.job_id)
        except Exception:
            self._outbox.release(
                dispatch.job_id,
                dispatch.lease_token,
                "sqs_send_failed",
            )
            return "retry"
        self._outbox.mark_dispatched(dispatch.job_id, dispatch.lease_token)
        return "published"
