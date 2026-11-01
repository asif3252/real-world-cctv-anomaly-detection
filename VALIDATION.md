# Validation plan

## Current evidence

Two rule-engine unit tests pass. Inference dependencies could not be installed in the initial environment because of DNS/network access. No live-camera accuracy or performance measurements are available.

## One-camera experiment

1. Verify stream freshness with visible motion or a clock.
2. Draw and document the restricted area using a redacted or synthetic view.
3. Stage entries shorter and longer than two seconds, dwell above and below the threshold, exits, re-entries and simultaneous people.
4. Manually label event start/end times; define matching tolerance before calculating precision, recall and alert delay.
5. Record false alerts per camera-hour and missed events across lighting and occlusion conditions.
6. Check CSV timestamps, snapshot integrity, CPU/RAM use and disk growth.
7. Measure inference-loop throughput separately from end-to-end latency.
8. Disconnect the stream, verify the stop notification, and restart after recovery.

## Scaling

Increase camera count only after the single-camera test. Record resolution, bitrate, input FPS, detection rate, hardware and concurrent applications. Do not extrapolate supported camera count from single-camera inference FPS. The synchronous prototype may accumulate decoder latency.

Publish the protocol, labeled-event counts, aggregate metrics and failure cases. Keep unmeasured values pending and do not disclose site security details or identifiable footage.

