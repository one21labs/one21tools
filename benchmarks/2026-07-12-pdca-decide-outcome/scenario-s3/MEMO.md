# Decision memo: adopt an orchestration framework for the nightly warehouse sync?

Author: data engineer (team of two)
Date: 2026-07-01

## The job in question
Every night at 02:00 a small script (`nightly_sync.py`, attached — 41 lines) pulls
three tables from our Postgres application database, writes them to S3 as Parquet, and
refreshes two downstream views. It has run every night for 14 months. The run log
(`sync_runs.csv`) shows zero failed runs and a median runtime of about six minutes.

## The proposal
My teammate wants to adopt Conductor, a full workflow-orchestration framework, to run
this. The pitch is real and I do not want to strawman it: Conductor gives us a DAG UI,
retries with backoff, SLA alerting, backfills, a proper scheduler, lineage tracking,
and a plugin ecosystem. It is the industry-standard shape, and the argument is that we
would "grow into it."

## What adopting it actually costs
Conductor is not a library you import; it is a service you stand up and keep alive — a
scheduler process, a metadata database, worker pools, and a version-upgrade treadmill.
For a two-person team that is a standing operational commitment that never goes away.
Right now the sync has essentially no operational surface: cron fires it, and it either
writes the files or pages us. It has never paged us.

## The honest read
We have exactly one job. It has never failed. Most of Conductor's feature list solves
problems we do not have — fan-out DAGs, cross-task lineage, backfill orchestration.
The features are genuinely nice. The question is whether one reliable 41-line job
justifies standing up and maintaining a framework designed for hundreds of coupled ones.

## What would change the answer
If we grow to, say, a dozen interdependent jobs, or if this one starts failing in ways
a bare cron cannot retry sensibly, the maths flips and the framework earns its keep.

## Options
- A: keep the cron script; revisit if job count or failure rate crosses a stated line.
- B: adopt Conductor now and migrate the one job onto it.
- C: a middle path — add a tiny retry-and-alert wrapper around the script, no framework.

## Ask
Decide and record the decision with your rationale, including the specific trigger that
would make you revisit adoption later.
