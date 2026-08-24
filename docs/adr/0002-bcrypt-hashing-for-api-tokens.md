# Bcrypt hashing for API tokens

API tokens are hashed with bcrypt before storage, rather than stored in plaintext or hashed with a fast hash like SHA-256. Bcrypt's slow hashing makes brute-force attacks on a compromised database infeasible. Token verification extracts the prefix from the raw token, filters candidate tokens by their masked preview's prefix, then checks each candidate with `bcrypt.checkpw` — this keeps the number of bcrypt comparisons small (only tokens with a matching prefix) while avoiding any need to store or index the raw token.
