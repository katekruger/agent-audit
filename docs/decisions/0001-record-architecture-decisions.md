# 0001. Record architecture decisions

- Status: accepted
- Date: 2026-08-29

## Context

This project makes several decisions early that are expensive to reverse
later — a wire-format choice, a distribution name, a positioning stance
against two competitors — and that will look arbitrary to a future
contributor without the reasoning that produced them.

## Decision

We record architecturally significant decisions as Markdown ADRs in
`docs/decisions/`, numbered sequentially, using the template in
[0000-template.md](0000-template.md).

## Consequences

Future contributors (human or agent) can see why a decision was made, not
just what it was. ADRs are never edited after acceptance; a changed decision
gets a new ADR that supersedes the old one.

## Assumption this relies on

That the cost of writing a short ADR is lower than the cost of a future
contributor re-litigating a settled question, or worse, silently reversing
it without knowing why it was made.

## Known limitation

ADRs document decisions, not the specification itself. They are not a
substitute for keeping `spec/SPECIFICATION.md` current.
