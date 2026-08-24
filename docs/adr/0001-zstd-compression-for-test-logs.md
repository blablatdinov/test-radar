# Zstd compression for test logs

Test record logs are stored as zstd-compressed binary data in a PostgreSQL `BinaryField`. We chose zstd over gzip because it offers a better compression ratio with comparable decompression speed, which matters because logs are stored per-test-record and decompressed on demand when a user views a single test. The compression library (`compression.zstd`) is used at the model level via a `decompressed_logs` property, keeping the storage concern inside the model rather than the view or serializer.
