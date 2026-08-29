# Facets

An OpenLineage-style extension registry: a small, stable core schema plus
namespaced, independently-versioned facets that can graduate into the
standard without forking `spec/schema/v1/`.

- Status: placeholder — see `BUILD-PLAN.md` §4 ("Facets") and feature #16
  in the feature inventory (targeted for v0.3).

Convention (draft, not yet normative): a facet lives at
`agent_audit.facet.<namespace>.*` and carries its own `_schemaURL`,
independent of the core schema's version. For example, a Salesforce
integration could add `agent_audit.facet.salesforce.object_type` without
requiring a change to `spec/schema/v1/agent-audit.schema.json`.

No facets are defined yet.
