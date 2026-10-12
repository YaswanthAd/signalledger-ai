# Showcase guide

## The story

An alert identifies a symptom. A useful AI copilot has to assemble an investigation with checkable evidence and the ability to abstain.

## A 60–90 second recording

1. Open `docs/assets/implementation.png` and point out the deterministic domain engine and optional model boundary.
2. Start the workbench in evidence-engine mode. Show the stale-dashboard fixture: the partner API ranks first while warehouse duration remains healthy.
3. Open Evidence ledger to inspect actual measurements and citation IDs.
4. Switch to the healthy scenario and show abstention.
5. Explain where local AI enters, what is validated, and how the app falls back when inference fails.
6. Close with one tradeoff: a heuristic root-cause ranking is useful, but it is not causal proof.

## Suggested post draft

A dashboard is late. The warehouse looks healthy. Where do you look next?

I’m building SignalLedger, an evidence-grounded incident copilot for data platforms.

The first local release includes lineage-aware hypothesis ranking, robust anomaly scoring, cited evidence, and explicit abstention. A local Ollama model can explain a supported hypothesis, while deterministic checks control which candidate and evidence references are accepted.

One synthetic scenario traces a stale dashboard back to upstream rate limiting while preserving the normal warehouse metric as a negative control.

The repo includes the running demo, an editable architecture diagram, the LLD, and tests. This is an early local release using synthetic data; production connectors and live model evaluation are next.

What evidence do you wish your incident alerts included?

https://github.com/YaswanthAd/signalledger-ai

#DataEngineering #AIEngineering #Python

## Share honestly

Lead with the failure you can demonstrate, not broad claims about autonomous agents. Attach `docs/assets/implementation.png` and a short screen recording. Use `docs/assets/architecture.png` when discussing the proposed AWS deployment, and label it as a blueprint. Do not claim production adoption, cost savings, model accuracy, stars, or traction without measured evidence. Pin the repo on your GitHub profile after publication.
