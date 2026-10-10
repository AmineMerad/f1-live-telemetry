"""F1-relevant custom search attributes for workflow visibility.

Registered once per Temporal service (global with Elasticsearch):
  make temporal-setup

Used at workflow start and upserted as prediction cycles advance, so the
dashboard/operator can answer: which sessions are running, which driver pairs
are covered, which model/snapshot produced a prediction.
"""

from temporalio.common import SearchAttributeKey

SessionId = SearchAttributeKey.for_keyword("SessionId")
DriverPair = SearchAttributeKey.for_keyword("DriverPair")
ModelVersion = SearchAttributeKey.for_keyword("ModelVersion")
SnapshotVersion = SearchAttributeKey.for_keyword("SnapshotVersion")
