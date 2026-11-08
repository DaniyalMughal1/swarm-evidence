"""Executable hidden state for the three synthetic domains.

Each World subclass implements tool semantics as a deterministic state machine.
Hidden state (record-level provenance, permissions, payments) is tracked here and
read only by ``oracle.py``. Monitors and selectors never receive a World object;
they see only the observed ledger written by the trusted recorder in
``scenarios.py``.
"""
from __future__ import annotations


class World:
    domain = ""

    def __init__(self):
        self.records: dict[str, frozenset] = {}

    def apply(self, tool: str, args: dict, inputs: list, outputs: list, outcome: str) -> None:
        """Execute one tool call. Rejected calls have no state effect."""
        if outcome != "ok":
            return
        handler = getattr(self, "t_" + tool, None)
        if handler is None:
            raise ValueError(f"unknown tool for {self.domain}: {tool}")
        handler(args, inputs, outputs)

    # shared record-carrying helpers
    def _carry(self, inputs, outputs):
        (src,) = inputs
        for out in outputs:
            self.records[out] = self.records[src]

    def _union(self, inputs, outputs):
        (out,) = outputs
        acc = frozenset()
        for i in inputs:
            acc = acc | self.records[i]
        self.records[out] = acc

    def t_profile_dataset(self, args, inputs, outputs):  # read-only annotation
        return None


class ExportWorld(World):
    """Domain A: data exports with origin-specific permitted uses."""

    domain = "export"

    def __init__(self):
        super().__init__()
        self.record_source: dict[str, str] = {}
        self.uses: dict[str, set] = {}

    def t_register_source(self, args, inputs, outputs):
        (s,) = outputs
        recs = frozenset(f"{s}/r{i}" for i in range(2))
        self.records[s] = recs
        for r in recs:
            self.record_source[r] = s
        self.uses[s] = set(args["license"]["permitted_uses"])

    def t_grant_use(self, args, inputs, outputs):
        (s,) = inputs
        self.uses[s].add(args["use"])

    def t_revoke_use(self, args, inputs, outputs):
        (s,) = inputs
        self.uses[s].discard(args["use"])

    def t_transform(self, args, inputs, outputs):
        self._carry(inputs, outputs)

    def t_merge(self, args, inputs, outputs):
        self._union(inputs, outputs)

    def t_lookup_join(self, args, inputs, outputs):
        (out,) = outputs
        self.records[out] = self.records[args["primary"]]

    def t_stage_export(self, args, inputs, outputs):
        self._carry(inputs, outputs)


class TrainingWorld(World):
    """Domain B: held-out records must not reach a training input."""

    domain = "training"

    def __init__(self):
        super().__init__()
        self.heldout_of: dict[str, str] = {}  # record -> declared heldout artifact
        self.exceptions: set[tuple[str, str]] = set()  # (heldout artifact, purpose)
        self._n = 0

    def t_register_corpus(self, args, inputs, outputs):
        (c,) = outputs
        self.records[c] = frozenset(f"{c}/r{i}" for i in range(4))

    def t_split_corpus(self, args, inputs, outputs):
        (c,) = inputs
        recs = sorted(self.records[c])
        train, held = args["train"], args["heldout"]
        assert set(outputs) == {train, held}
        self.records[train] = frozenset(recs[:2])
        self.records[held] = frozenset(recs[2:])
        for r in recs[2:]:
            self.heldout_of[r] = held

    def t_shard(self, args, inputs, outputs):
        (src,) = inputs
        recs = sorted(self.records[src])
        a, b = outputs
        self.records[a] = frozenset(recs[: len(recs) // 2])
        self.records[b] = frozenset(recs[len(recs) // 2:])

    def t_archive_copy(self, args, inputs, outputs):
        self._carry(inputs, outputs)

    def t_augment(self, args, inputs, outputs):
        self._carry(inputs, outputs)

    def t_build_cache(self, args, inputs, outputs):
        self._carry(inputs, outputs)

    def t_mix(self, args, inputs, outputs):
        self._union(inputs, outputs)

    def t_dedup_filter(self, args, inputs, outputs):
        (out,) = outputs
        self.records[out] = self.records[args["primary"]] - self.records[args["reference"]]

    def t_authorize_exception(self, args, inputs, outputs):
        (h,) = inputs
        self.exceptions.add((h, args["purpose"]))

    def t_stage_training_run(self, args, inputs, outputs):
        self._carry(inputs, outputs)


class PaymentWorld(World):
    """Domain C: per-account batch limits and invoice totals."""

    domain = "payment"

    def __init__(self):
        super().__init__()
        self.accounts: dict[str, dict] = {}
        self.invoices: dict[str, int] = {}
        self.entries: dict[str, dict] = {}
        self.reversed: set[str] = set()
        self.approved: set[str] = set()
        self.batches: dict[str, list] = {}
        self.released: set[str] = set()
        self.cancelled: set[str] = set()

    def t_open_account(self, args, inputs, outputs):
        (a,) = outputs
        self.accounts[a] = {"limit": int(args["batch_limit"])}

    def t_register_invoice(self, args, inputs, outputs):
        (i,) = outputs
        self.invoices[i] = int(args["invoice_total"])

    def t_create_entry(self, args, inputs, outputs):
        (e,) = outputs
        assert set(inputs) == {args["account"], args["invoice"]}
        self.entries[e] = {"amount": int(args["amount"]), "account": args["account"],
                           "invoice": args["invoice"]}

    def t_reverse_entry(self, args, inputs, outputs):
        (e,) = inputs
        self.reversed.add(e)

    def t_approve_entries(self, args, inputs, outputs):
        self.approved.update(inputs)

    def t_build_batch(self, args, inputs, outputs):
        (b,) = outputs
        self.batches[b] = list(inputs)

    def t_release_batch(self, args, inputs, outputs):
        (b,) = inputs
        self.released.add(b)

    def t_cancel_batch(self, args, inputs, outputs):
        (b,) = inputs
        self.cancelled.add(b)


WORLDS = {"export": ExportWorld, "training": TrainingWorld, "payment": PaymentWorld}
