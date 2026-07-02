# geno-surf

Chromium orchestration for the geno agent — the **`surf`** CLI. The browser half of
[geno-tt](https://github.com/42euge/geno-tt): where `tt iterm` drives iTerm2, `surf`
drives a dedicated Chromium over the DevTools Protocol, addressed by the same
object-notation registry (`ngrt.main.tickets`, `hil.plans`, …).

**Safari stays human; Chromium is the agent's.** Safari can't script Tab Groups at
all, so geno-surf runs a separate Chromium under its own profile.

## Install

```bash
pipx install git+https://github.com/42euge/geno-surf.git
# or as a Claude Code plugin
/plugin marketplace add 42euge/geno-surf
/plugin install geno-surf@geno-surf
```

## Usage

```bash
surf launch                 # start the agent's Chromium (remote debugging)
surf ls                     # list open tabs
surf open https://…         # open a tab
surf focus <id> | close <id>
```

Core is dependency-free (CDP HTTP endpoints via stdlib). Deeper control and native
Tab Groups arrive in later phases — see [GENO.md](GENO.md).
