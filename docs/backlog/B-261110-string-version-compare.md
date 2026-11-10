# Versions are compared as strings

`update_dependency.py:84,96`: `version_constraint.version != version_new` compares text, so `1.0` vs `1.0.0` counts as
a change and rewrites the constraint (the existing TODO "better version comparison"; `packaging.version` is a
candidate, a new dependency needs the repo's review). Write a characterization test of the current output first, then
decide.

Also: `src/uv_upx/cli/helpers/main.py:13` `collect_top_level_dependencies_from_project` has no caller (vulture); delete
it or use it.
