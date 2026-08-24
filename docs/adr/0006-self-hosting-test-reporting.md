# Self-hosting test reporting via pytest-test-radar

The project includes a custom pytest plugin (`pytest-test-radar`, published as a separate alpha package) that submits test results from CI runs back to a Test Radar instance. This means Test Radar tests itself: the CI pipeline for Test Radar reports its own test results to a running Test Radar deployment. This self-hosting validates the API contract from the client side and provides real-world usage data. The plugin connects using a `RADAR_TOKEN` secret configured in CI.
