# Token prefix scheme for agent type identification

Raw API tokens are prefixed with `ci_` for CI agents and `dev_` for Local agents before the random segment. This prefix is preserved in the token mask (`ci_abc...xyz`), which allows the verification function to filter candidate tokens by `token_mask__startswith=prefix` before running bcrypt comparisons. Without the prefix, verification would need to check every token in the database with bcrypt, which would be prohibitively slow. The prefix also gives users a visual cue about agent type when viewing tokens in the UI.
