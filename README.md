# dotslash-registry

Prepared [DotSlash](https://dotslash-cli.com) wrappers for public GitHub
release binaries. Requires `dotslash` on `$PATH`.

Check out this repo, then symlink or copy wrappers into a directory on
`$PATH` such as `/usr/local/bin`:

```bash
git clone https://github.com/stepancheg/dotslash-registry.git
cd dotslash-registry
ln -s "$(pwd)/packages/buildkite-cli/bin/bk" /usr/local/bin/bk
# or: cp packages/buildkite-cli/bin/bk /usr/local/bin/bk
```
