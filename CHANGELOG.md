
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
The project changed to `CalVer` in September 2023.

---
## [2024.11.2] - 2024-11-26

([full changelog](https://github.com/conda-incubator/conda-store/compare/2024.11.1...710d61c86b6b8591672c4819328ebd11f9c3a917))

### Merged PRs

FEATURES:

- Create catch-all/fallback route for UI app [#932](https://github.com/conda-incubator/conda-store/pull/932) ([@gabalafou]
(https://github.com/gabalafou))

IMPROVEMENTS:

- MAINT - Bump base Docker image version [#990](https://github.com/conda-incubator/conda-store/pull/990) ([@trallard](https://github.com/trallard))
- Bump cross-spawn from 7.0.3 to 7.0.5 in /docusaurus-docs [#989](https://github.com/conda-incubator/conda-store/pull/989) ([@dependabot](https://github.com/dependabot))
- MAINT - Update dependabot configuration [#988](https://github.com/conda-incubator/conda-store/pull/988) ([@trallard](https://github.com/trallard))
- [MAINT] Update pydantic to >=2.0 [#985](https://github.com/conda-incubator/conda-store/pull/985) ([@peytondmurray](https://github.com/peytondmurray))
- MAINT - Do not use `nodefaults` moving forward [#978](https://github.com/conda-incubator/conda-store/pull/978) ([@trallard](https://github.com/trallard))
- Bump sqlalchemy version [#970](https://github.com/conda-incubator/conda-store/pull/970) ([@soapy1](https://github.com/soapy1))

BUG FIXES:

- DEV - Set traitlets application version [#981](https://github.com/conda-incubator/conda-store/pull/981) ([@soapy1](https://github.com/soapy1))
- [BUG] Fix python version compatibility issues affecting tests [#973](https://github.com/conda-incubator/conda-store/pull/973) ([@peytondmurray](https://github.com/peytondmurray))
- Update conda-package-build causes an integrity error on conda_package_build table [#961](https://github.com/conda-incubator/conda-store/pull/961) ([@soapy1](https://github.com/soapy1))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/conda-incubator/conda-store/graphs/contributors?from=2024-11-08&to=2024-11-26&type=c))

[@dependabot](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adependabot+updated%3A2024-11-08..2024-11-26&type=Issues) | [@gabalafou](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Agabalafou+updated%3A2024-11-08..2024-11-26&type=Issues) | [@github-actions](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Agithub-actions+updated%3A2024-11-08..2024-11-26&type=Issues) | [@marcelovilla](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Amarcelovilla+updated%3A2024-11-08..2024-11-26&type=Issues) | [@netlify](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Anetlify+updated%3A2024-11-08..2024-11-26&type=Issues) | [@nkaretnikov](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ankaretnikov+updated%3A2024-11-08..2024-11-26&type=Issues) | [@peytondmurray](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apeytondmurray+updated%3A2024-11-08..2024-11-26&type=Issues) | [@rigzba21](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Arigzba21+updated%3A2024-11-08..2024-11-26&type=Issues) | [@soapy1](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Asoapy1+updated%3A2024-11-08..2024-11-26&type=Issues) | [@trallard](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Atrallard+updated%3A2024-11-08..2024-11-26&type=Issues)

## [2024.11.1] - 2024-11-08

([full changelog](https://github.com/conda-incubator/conda-store/compare/2104c4581489474a6f6c6c6b5744c5eeb62b3d14...92a199b52ee4a91d931afcdfb46aca4663c07ebe))

### Merged PRs

- Bump k8 example version [#960](https://github.com/conda-incubator/conda-store/pull/960) ([@soapy1](https://github.com/soapy1))
- [pre-commit.ci] pre-commit autoupdate [#959](https://github.com/conda-incubator/conda-store/pull/959) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- [DOC] Roadmap updates [#958](https://github.com/conda-incubator/conda-store/pull/958) ([@peytondmurray](https://github.com/peytondmurray))
- Move build to worker [#945](https://github.com/conda-incubator/conda-store/pull/945) ([@soapy1](https://github.com/soapy1))
- Fix link to GH issues for road map (operation) items [#943](https://github.com/conda-incubator/conda-store/pull/943) ([@soapy1](https://github.com/soapy1))
- Make conda-store server launch uvicorn with log level [#940](https://github.com/conda-incubator/conda-store/pull/940) ([@soapy1](https://github.com/soapy1))
- Add links to GH issues for roadmap items [#939](https://github.com/conda-incubator/conda-store/pull/939) ([@soapy1](https://github.com/soapy1))
- Move dependencies module into conda store server module [#935](https://github.com/conda-incubator/conda-store/pull/935) ([@soapy1](https://github.com/soapy1))
- [MAINT] Update lint tooling [#933](https://github.com/conda-incubator/conda-store/pull/933) ([@peytondmurray](https://github.com/peytondmurray))
- Remove unused _internal/client module [#928](https://github.com/conda-incubator/conda-store/pull/928) ([@soapy1](https://github.com/soapy1))
- [AUTO] Update openapi.json [#927](https://github.com/conda-incubator/conda-store/pull/927) ([@github-actions](https://github.com/github-actions))
- Add tests - storage + worker [#926](https://github.com/conda-incubator/conda-store/pull/926) ([@soapy1](https://github.com/soapy1))
- Move seeding tests functionality into test module [#925](https://github.com/conda-incubator/conda-store/pull/925) ([@soapy1](https://github.com/soapy1))
- Add coverage report to unit tests [#923](https://github.com/conda-incubator/conda-store/pull/923) ([@soapy1](https://github.com/soapy1))
- Update docs link [#922](https://github.com/conda-incubator/conda-store/pull/922) ([@pavithraes](https://github.com/pavithraes))
- Test improvements - part 1 [#919](https://github.com/conda-incubator/conda-store/pull/919) ([@soapy1](https://github.com/soapy1))
- Bump http-proxy-middleware from 2.0.6 to 2.0.7 in /docusaurus-docs [#917](https://github.com/conda-incubator/conda-store/pull/917) ([@dependabot](https://github.com/dependabot))
- [BUG] Pin pyyaml dependency due to cython>=3 incompatibility [#916](https://github.com/conda-incubator/conda-store/pull/916) ([@peytondmurray](https://github.com/peytondmurray))
- Wait for celery to return response to request to solve specification [#913](https://github.com/conda-incubator/conda-store/pull/913) ([@soapy1](https://github.com/soapy1))
- [DOCS] Describe new config vars for React router [#912](https://github.com/conda-incubator/conda-store/pull/912) ([@gabalafou](https://github.com/gabalafou))
- Bump version for dev [#910](https://github.com/conda-incubator/conda-store/pull/910) ([@soapy1](https://github.com/soapy1))
- REL - 2024.10.1 [#909](https://github.com/conda-incubator/conda-store/pull/909) ([@soapy1](https://github.com/soapy1))
- [DOCS] Update architecture diagram + fix docs links [#908](https://github.com/conda-incubator/conda-store/pull/908) ([@soapy1](https://github.com/soapy1))
- [ENH] Add hot reloading for development [#907](https://github.com/conda-incubator/conda-store/pull/907) ([@peytondmurray](https://github.com/peytondmurray))
- DEV - Extend compose to include target for local UI [#905](https://github.com/conda-incubator/conda-store/pull/905) ([@trallard](https://github.com/trallard))
- Respect worker log level config setting [#903](https://github.com/conda-incubator/conda-store/pull/903) ([@soapy1](https://github.com/soapy1))
- [DOC] Update contributing guidelines [#763](https://github.com/conda-incubator/conda-store/pull/763) ([@pavithraes](https://github.com/pavithraes))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/conda-incubator/conda-store/graphs/contributors?from=2024-10-22&to=2024-11-08&type=c))

[@Adam-D-Lewis](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3AAdam-D-Lewis+updated%3A2024-10-22..2024-11-08&type=Issues) | [@costrouc](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Acostrouc+updated%3A2024-10-22..2024-11-08&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adependabot+updated%3A2024-10-22..2024-11-08&type=Issues) | [@gabalafou](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Agabalafou+updated%3A2024-10-22..2024-11-08&type=Issues) | [@github-actions](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Agithub-actions+updated%3A2024-10-22..2024-11-08&type=Issues) | [@jaimergp](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ajaimergp+updated%3A2024-10-22..2024-11-08&type=Issues) | [@kcpevey](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Akcpevey+updated%3A2024-10-22..2024-11-08&type=Issues) | [@krassowski](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Akrassowski+updated%3A2024-10-22..2024-11-08&type=Issues) | [@netlify](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Anetlify+updated%3A2024-10-22..2024-11-08&type=Issues) | [@pavithraes](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apavithraes+updated%3A2024-10-22..2024-11-08&type=Issues) | [@peytondmurray](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apeytondmurray+updated%3A2024-10-22..2024-11-08&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apre-commit-ci+updated%3A2024-10-22..2024-11-08&type=Issues) | [@soapy1](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Asoapy1+updated%3A2024-10-22..2024-11-08&type=Issues) | [@trallard](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Atrallard+updated%3A2024-10-22..2024-11-08&type=Issues)


## [2024.10.1] - 2024-10-22

([full changelog](https://github.com/conda-incubator/conda-store/compare/87f8ffc98bd5e54436bfa5707a8d56b9c9d34c15...dc1134f88d02755e6371f655c20120e8402f0365))

### Merged PRs

- [AUTO] Update openapi.json [#904](https://github.com/conda-incubator/conda-store/pull/904) ([@github-actions](https://github.com/github-actions))
- Create local conda-store dir for celery beat data files [#902](https://github.com/conda-incubator/conda-store/pull/902) ([@soapy1](https://github.com/soapy1))
- REACT_APP_URL_BASENAME [#898](https://github.com/conda-incubator/conda-store/pull/898) ([@gabalafou](https://github.com/gabalafou))
- Bump cookie and express in /docusaurus-docs [#896](https://github.com/conda-incubator/conda-store/pull/896) ([@dependabot](https://github.com/dependabot))
- [BUG] Fix openapi.json generation workflow [#891](https://github.com/conda-incubator/conda-store/pull/891) ([@peytondmurray](https://github.com/peytondmurray))
- [MAINT] Add the 2024/2025 roadmap [#890](https://github.com/conda-incubator/conda-store/pull/890) ([@peytondmurray](https://github.com/peytondmurray))
- Revert "REL - 2024.9.1 (#880)" [#887](https://github.com/conda-incubator/conda-store/pull/887) ([@peytondmurray](https://github.com/peytondmurray))
- BUG - patch release workflow [#885](https://github.com/conda-incubator/conda-store/pull/885) ([@trallard](https://github.com/trallard))
- Set logout url properly when using the integrated ui [#884](https://github.com/conda-incubator/conda-store/pull/884) ([@dcmcand](https://github.com/dcmcand))
- update to latest miniforge image [#883](https://github.com/conda-incubator/conda-store/pull/883) ([@Adam-D-Lewis](https://github.com/Adam-D-Lewis))
- REL - 2024.9.1 [#880](https://github.com/conda-incubator/conda-store/pull/880) ([@peytondmurray](https://github.com/peytondmurray))
- [MAINT] Make github workflow format openapi.json [#879](https://github.com/conda-incubator/conda-store/pull/879) ([@peytondmurray](https://github.com/peytondmurray))
- BUG - Fix release workflows [#878](https://github.com/conda-incubator/conda-store/pull/878) ([@trallard](https://github.com/trallard))
- Bump body-parser and express in /docusaurus-docs [#873](https://github.com/conda-incubator/conda-store/pull/873) ([@dependabot](https://github.com/dependabot))
- DEV - Update conda-store build hook [#872](https://github.com/conda-incubator/conda-store/pull/872) ([@trallard](https://github.com/trallard))
- Bump actions/download-artifact from 3 to 4.1.7 in /.github/workflows [#869](https://github.com/conda-incubator/conda-store/pull/869) ([@dependabot](https://github.com/dependabot))
- [pre-commit.ci] pre-commit autoupdate [#868](https://github.com/conda-incubator/conda-store/pull/868) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Bump micromatch from 4.0.5 to 4.0.8 in /docusaurus-docs [#867](https://github.com/conda-incubator/conda-store/pull/867) ([@dependabot](https://github.com/dependabot))
- Bump webpack from 5.89.0 to 5.94.0 in /docusaurus-docs [#866](https://github.com/conda-incubator/conda-store/pull/866) ([@dependabot](https://github.com/dependabot))
- MAINT - Miscellaneous maintenance/governance tasks [#865](https://github.com/conda-incubator/conda-store/pull/865) ([@trallard](https://github.com/trallard))
- [ENH] Allow fetching of arbitrary user environments [#864](https://github.com/conda-incubator/conda-store/pull/864) ([@peytondmurray](https://github.com/peytondmurray))
- Update `openapi.json` file path in `generate_api_docs.yaml` [#863](https://github.com/conda-incubator/conda-store/pull/863) ([@pavithraes](https://github.com/pavithraes))
- [pre-commit.ci] pre-commit autoupdate [#860](https://github.com/conda-incubator/conda-store/pull/860) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- [MAINT] Prevent workers from trying to parse sys.argv upon intialization [#850](https://github.com/conda-incubator/conda-store/pull/850) ([@peytondmurray](https://github.com/peytondmurray))
- MAINT - Add dependabot config [#847](https://github.com/conda-incubator/conda-store/pull/847) ([@trallard](https://github.com/trallard))
- [MAINT] Remove deprecated docker-compose config option [#846](https://github.com/conda-incubator/conda-store/pull/846) ([@peytondmurray](https://github.com/peytondmurray))
- DEV -  Set a canonical default Python version (3.12) [#844](https://github.com/conda-incubator/conda-store/pull/844) ([@trallard](https://github.com/trallard))
- DEV - Simplify Docker images [#841](https://github.com/conda-incubator/conda-store/pull/841) ([@trallard](https://github.com/trallard))
- restart workers after executing 10 tasks to mitigate memory leaks [#840](https://github.com/conda-incubator/conda-store/pull/840) ([@Adam-D-Lewis](https://github.com/Adam-D-Lewis))
- [pre-commit.ci] pre-commit autoupdate [#839](https://github.com/conda-incubator/conda-store/pull/839) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- DEV - Update dev environments [#838](https://github.com/conda-incubator/conda-store/pull/838) ([@trallard](https://github.com/trallard))
- BUG - Fix triggers [#837](https://github.com/conda-incubator/conda-store/pull/837) ([@trallard](https://github.com/trallard))
- Bump braces from 3.0.2 to 3.0.3 in /docusaurus-docs [#835](https://github.com/conda-incubator/conda-store/pull/835) ([@dependabot](https://github.com/dependabot))
- MAINT - Mock out calls to `conda-lock` for `test_solve_lockfile` [#834](https://github.com/conda-incubator/conda-store/pull/834) ([@peytondmurray](https://github.com/peytondmurray))
- MAINT - Mock out call to env solve in `test_generate_constructor_installer` [#833](https://github.com/conda-incubator/conda-store/pull/833) ([@peytondmurray](https://github.com/peytondmurray))
- ENH - Update workflows triggers [#832](https://github.com/conda-incubator/conda-store/pull/832) ([@trallard](https://github.com/trallard))
- DOC - Update documentation [#831](https://github.com/conda-incubator/conda-store/pull/831) ([@trallard](https://github.com/trallard))
- REL - 2024.6.1 [#829](https://github.com/conda-incubator/conda-store/pull/829) ([@peytondmurray](https://github.com/peytondmurray))
- Add `conda config` warning docs/message; add duration log for actions [#823](https://github.com/conda-incubator/conda-store/pull/823) ([@peytondmurray](https://github.com/peytondmurray))
- Build docker images for arm (aarch64) [#822](https://github.com/conda-incubator/conda-store/pull/822) ([@aktech](https://github.com/aktech))
- Privatize internal conda-store API [#820](https://github.com/conda-incubator/conda-store/pull/820) ([@peytondmurray](https://github.com/peytondmurray))
- MAINT - Misc improvements to repo [#802](https://github.com/conda-incubator/conda-store/pull/802) ([@trallard](https://github.com/trallard))
- Bump express from 4.18.2 to 4.19.2 in /docusaurus-docs [#800](https://github.com/conda-incubator/conda-store/pull/800) ([@dependabot](https://github.com/dependabot))
- Bump follow-redirects from 1.15.4 to 1.15.6 in /docusaurus-docs [#785](https://github.com/conda-incubator/conda-store/pull/785) ([@dependabot](https://github.com/dependabot))
- [DOC] Auto-generate openapi.json [#782](https://github.com/conda-incubator/conda-store/pull/782) ([@pavithraes](https://github.com/pavithraes))
- Update metadata on landing page [#774](https://github.com/conda-incubator/conda-store/pull/774) ([@pavithraes](https://github.com/pavithraes))
- Update conda-store explanations [#726](https://github.com/conda-incubator/conda-store/pull/726) ([@pavithraes](https://github.com/pavithraes))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/conda-incubator/conda-store/graphs/contributors?from=2024-06-10&to=2024-10-22&type=c))

[@Adam-D-Lewis](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3AAdam-D-Lewis+updated%3A2024-06-10..2024-10-22&type=Issues) | [@aktech](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aaktech+updated%3A2024-06-10..2024-10-22&type=Issues) | [@asmeurer](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aasmeurer+updated%3A2024-06-10..2024-10-22&type=Issues) | [@costrouc](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Acostrouc+updated%3A2024-06-10..2024-10-22&type=Issues) | [@dcmcand](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adcmcand+updated%3A2024-06-10..2024-10-22&type=Issues) | [@dharhas](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adharhas+updated%3A2024-06-10..2024-10-22&type=Issues) | [@gabalafou](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Agabalafou+updated%3A2024-06-10..2024-10-22&type=Issues) | [@jaimergp](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ajaimergp+updated%3A2024-06-10..2024-10-22&type=Issues) | [@kcpevey](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Akcpevey+updated%3A2024-06-10..2024-10-22&type=Issues) | [@nkaretnikov](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ankaretnikov+updated%3A2024-06-10..2024-10-22&type=Issues) | [@pavithraes](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apavithraes+updated%3A2024-06-10..2024-10-22&type=Issues) | [@peytondmurray](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apeytondmurray+updated%3A2024-06-10..2024-10-22&type=Issues) | [@soapy1](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Asoapy1+updated%3A2024-06-10..2024-10-22&type=Issues) | [@trallard](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Atrallard+updated%3A2024-06-10..2024-10-22&type=Issues)

## [2024.6.1] - 2024-06-10

([full changelog](https://github.com/conda-incubator/conda-store/compare/2024.3.1...293d19fa7a7bce999b1069b147314a5966541a32))

## Merged PRs

- Update runtime dependencies [#827](https://github.com/conda-incubator/conda-store/pull/827) ([@peytondmurray](https://github.com/peytondmurray))
- Add conda-store Usability Study Report.md [#824](https://github.com/conda-incubator/conda-store/pull/824) ([@smeragoel](https://github.com/smeragoel))
- [pre-commit.ci] pre-commit autoupdate [#819](https://github.com/conda-incubator/conda-store/pull/819) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Run tests as separate jobs [#813](https://github.com/conda-incubator/conda-store/pull/813) ([@nkaretnikov](https://github.com/nkaretnikov))
- Add user journey test for canceling a build [#812](https://github.com/conda-incubator/conda-store/pull/812) ([@peytondmurray](https://github.com/peytondmurray))
- Implement log flushing [#808](https://github.com/conda-incubator/conda-store/pull/808) ([@nkaretnikov](https://gith
ub.com/nkaretnikov))
- Add user journey test to retrieve a lockfile for a build [#807](https://github.com/conda-incubator/conda-store/pull/807) ([@peytondmurray](https://github.com/peytondmurray))
- Add user journey test to mark build as active [#804](https://github.com/conda-incubator/conda-store/pull/804) ([@peytondmurray](https://github.com/peytondmurray))
- MAINT - Add conda-store dependencies to pyproject.toml [#798](https://github.com/conda-incubator/conda-store/pull/798) ([@trallard](https://github.com/trallard))
- Add user journey test to check that logs can be found for failed builds [#797](https://github.com/conda-incubator/conda-store/pull/797) ([@peytondmurray](https://github.com/peytondmurray))
- 🔧 Update .pre-commit-config [#796](https://github.com/conda-incubator/conda-store/pull/796) ([@trallard](https://github.com/trallard))
- MAINT -  Bump actions versions [#795](https://github.com/conda-incubator/conda-store/pull/795) ([@trallard](https://github.com/trallard))
- Bump webpack-dev-middleware from 5.3.3 to 5.3.4 in /docusaurus-docs [#794](https://github.com/conda-incubator/conda-store/pull/794) ([@dependabot](https://github.com/dependabot))
- Add conda recipe with verification workflow [#793](https://github.com/conda-incubator/conda-store/pull/793) ([@jaimergp](https://github.com/jaimergp))
- Make conda_flags configurable [#790](https://github.com/conda-incubator/conda-store/pull/790) ([@patrix58](https://github.com/patrix58))
- Added user journey test to delete old environment [#787](https://github.com/conda-incubator/conda-store/pull/787) ([@peytondmurray](https://github.com/peytondmurray))
- Set `CONDA_STORE_DIR` to `platformdirs.user_data_path` [#786](https://github.com/conda-incubator/conda-store/pull/786) ([@nkaretnikov](https://github.com/nkaretnikov))
- Update docs theme [#784](https://github.com/conda-incubator/conda-store/pull/784) ([@pavithraes](https://github.com/pavithraes))
- [pre-commit.ci] pre-commit autoupdate [#781](https://github.com/conda-incubator/conda-store/pull/781) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Add CHANGELOG entries for v2024.3.1 [#779](https://github.com/conda-incubator/conda-store/pull/779) ([@pavithraes](https://github.com/pavithraes))
- REL - 2024.3.1 [#778](https://github.com/conda-incubator/conda-store/pull/778) ([@pavithraes](https://github.com/pavithraes))
- Support hash-only build paths [#777](https://github.com/conda-incubator/conda-store/pull/777) ([@nkaretnikov](https://github.com/nkaretnikov))
- Add user journey for logging in and deleting shared environment [#776](https://github.com/conda-incubator/conda-store/pull/776) ([@peytondmurray](https://github.com/peytondmurray))
- Document user personas [#773](https://github.com/conda-incubator/conda-store/pull/773) ([@pavithraes](https://github.com/pavithraes))
- Add ability to create environment from lockfile [#772](https://github.com/conda-incubator/conda-store/pull/772) ([@nkaretnikov](https://github.com/nkaretnikov))
- Create temp REST API reference [#766](https://github.com/conda-incubator/conda-store/pull/766) ([@pavithraes](https://github.com/pavithraes))
- [DOC] Add JupyterLab Extension docs page [#752](https://github.com/conda-incubator/conda-store/pull/752) ([@pavithraes](https://github.com/pavithraes))
- Add standalone installation docs [#724](https://github.com/conda-incubator/conda-store/pull/724) ([@pavithraes](https://github.com/pavithraes))

## Contributors to this release

([GitHub contributors page for this release](https://github.com/conda-incubator/conda-store/graphs/contributors?from=2024-03-12&to=2024-06-10&type=c))

[@asmeurer](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aasmeurer+updated%3A2024-03-12..2024-06-10&type=Issues) | [@costrouc](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Acostrouc+updated%3A2024-03-12..2024-06-10&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adependabot+updated%3A2024-03-12..2024-06-10&type=Issues) | [@jaimergp](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ajaimergp+updated%3A2024-03-12..2024-06-10&type=Issues) | [@kcpevey](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Akcpevey+updated%3A2024-03-12..2024-06-10&type=Issues) | [@netlify](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Anetlify+updated%3A2024-03-12..2024-06-10&type=Issues) | [@nkaretnikov](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ankaretnikov+updated%3A2024-03-12..2024-06-10&type=Issues) | [@patrix58](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apatrix58+updated%3A2024-03-12..2024-06-10&type=Issues) | [@pavithraes](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apavithraes+updated%3A2024-03-12..2024-06-10&type=Issues) | [@peytondmurray](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apeytondmurray+updated%3A2024-03-12..2024-06-10&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apre-commit-ci+updated%3A2024-03-12..2024-06-10&type=Issues) | [@smeragoel](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Asmeragoel+updated%3A2024-03-12..2024-06-10&type=Issues) | [@trallard](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Atrallard+updated%3A2024-03-12..2024-06-10&type=Issues)

## [2024.3.1] - 2024-03-12

([full changelog](https://github.com/conda-incubator/conda-store/compare/2024.1.1...2024.3.1))

## Added

* Add upstream contribution policy by @pavithraes in https://github.com/conda-incubator/conda-store/pull/722
* Pass `CONDA_OVERRIDE_CUDA` to `with_cuda` of conda-lock by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/721
* Add backwards compatibility policy by @dcmcand in https://github.com/conda-incubator/conda-store/pull/687
* add how to test section to PR template by @dcmcand in https://github.com/conda-incubator/conda-store/pull/743
* Add extended-length prefix support by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/713
* Generate `constructor` artifacts by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/714
* Add support for the `editor` role by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/738
* Add a test for parallel builds, fix race conditions due to the shared conda cache by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/745
* Add user journey test by @dcmcand in https://github.com/conda-incubator/conda-store/pull/760
* Add status `CANCELED` by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/747
* [DOC] Document setting environment variable by @pavithraes in https://github.com/conda-incubator/conda-store/pull/765

## Fixed

* Log address and port, show exception trace from `uvicorn.run` by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/708
* Check if worker is initialized by @nkaretnikov in https://github.com/conda-incubator/conda-store/pull/705

## Contributors to this release

([GitHub contributors page for this release](https://github.com/conda-incubator/conda-store/graphs/contributors?from=2024-01-30&to=2024-03-12&type=c))

[@nkaretnikov](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ankaretnikov+updated%3A2024-01-30..2024-03-12&type=Issues) | [@dcmcand](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adcmcand+updated%3A2024-01-30..2024-03-12&type=Issues) | [@pavithraes](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apavithraes+updated%3A2024-01-30..2024-03-12&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adependabot+updated%3A2024-01-30..2024-03-12&type=Issues)| [@trallard](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Atrallard+updated%3A2024-01-30..2024-03-12&type=Issues)

## [2024.1.1] - 2024-01-30

([full changelog](https://github.com/conda-incubator/conda-store/compare/2023.10.1...ec606641f6d0bb7bde39b2e9f11cf515077feee8))

### Added

- MAINT - Add plausible tracking snippet [#716](https://github.com/conda-incubator/conda-store/pull/716) ([@pavithraes](https://github.com/pavithraes))
- ENH - Terminate worker tasks on SIGINT [#709](https://github.com/conda-incubator/conda-store/pull/709) ([@nkaretnikov](https://github.com/nkaretnikov))
- DOC -Add brand and design guidelines [#701](https://github.com/conda-incubator/conda-store/pull/701) ([@pavithraes](https://github.com/pavithraes))
- DOC - Misc clean-up docs structure [#700](https://github.com/conda-incubator/conda-store/pull/700) ([@pavithraes](https://github.com/pavithraes))
- MAINT - Remove Sphinx docs  [#695](https://github.com/conda-incubator/conda-store/pull/695) ([@pavithraes](https://github.com/pavithraes))
- DOC - Add basic conda-store-ui docs [#694](https://github.com/conda-incubator/conda-store/pull/694) ([@pavithraes](https://github.com/pavithraes))
- ENH - Set channel priority to strict, print config info [#693](https://github.com/conda-incubator/conda-store/pull/693) ([@nkaretnikov](https://github.com/nkaretnikov))
- DEV - Place a bound on docker-py [#689](https://github.com/conda-incubator/conda-store/pull/689) ([@nkaretnikov](https://github.com/nkaretnikov))
- ENH - Check the size of `build_path` [#653](https://github.com/conda-incubator/conda-store/pull/653) ([@nkaretnikov](https://github.com/nkaretnikov))
- ENH - Use shorter `build_key` [#652](https://github.com/conda-incubator/conda-store/pull/652) ([@nkaretnikov](https://github.com/nkaretnikov))
- ENH - Windows support [#640](https://github.com/conda-incubator/conda-store/pull/640) ([@nkaretnikov](https://github.com/nkaretnikov))
- ENH - Store the state and database files in ~/.conda-store by default [#639](https://github.com/conda-incubator/conda-store/pull/639) ([@nkaretnikov](https://github.com/nkaretnikov))
- ENH - Change API to be able to assign roles to namespaces [#607](https://github.com/conda-incubator/conda-store/pull/607) ([@nkaretnikov](https://github.com/nkaretnikov))
- ENH - Adding build canceling (only works with compatible celery brokers redis and rabbitmq) [#531](https://github.com/conda-incubator/conda-store/pull/531) ([@costrouc](https://github.com/costrouc))

### Changed

- ENH - Use string substitution in `normalized_channel_url` [#710](https://github.com/conda-incubator/conda-store/pull/710) ([@nkaretnikov](https://github.com/nkaretnikov))
- MAINT - Bump the npm_and_yarn group group in /docusaurus-docs with 1 update [#706](https://github.com/conda-incubator/conda-store/pull/706) ([@dependabot](https://github.com/dependabot))
- MAINT - Update npm dependencies for Docusaurus v3 [#704](https://github.com/conda-incubator/conda-store/pull/704) ([@pavithraes](https://github.com/pavithraes))
- DOC - Basic migration of conda-store (core) docs [#685](https://github.com/conda-incubator/conda-store/pull/685) ([@pavithraes](https://github.com/pavithraes))
- DEV - Disable code that depends on conda-docker [#667](https://github.com/conda-incubator/conda-store/pull/667) ([@nkaretnikov](https://github.com/nkaretnikov))

### Fixed

- BUG - Remove links to changelog [#698](https://github.com/conda-incubator/conda-store/pull/698) ([@trallard](https://github.com/trallard))
- ENH - replace port 5000 with port 8080 [#642](https://github.com/conda-incubator/conda-store/pull/642) ([@dcmcand](https://github.com/dcmcand))

## Contributors to this release

([GitHub contributors page for this release](https://github.com/conda-incubator/conda-store/graphs/contributors?from=2023-10-20&to=2024-01-05&type=c))

[@amjames](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aamjames+updated%3A2023-10-20..2024-01-05&type=Issues) | [@anirrudh](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aanirrudh+updated%3A2023-10-20..2024-01-05&type=Issues) | [@asmeurer](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aasmeurer+updated%3A2023-10-20..2024-01-05&type=Issues) | [@costrouc](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Acostrouc+updated%3A2023-10-20..2024-01-05&type=Issues) | [@dcmcand](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adcmcand+updated%3A2023-10-20..2024-01-05&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adependabot+updated%3A2023-10-20..2024-01-05&type=Issues) | [@dharhas](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adharhas+updated%3A2023-10-20..2024-01-05&type=Issues) | [@iameskild](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aiameskild+updated%3A2023-10-20..2024-01-05&type=Issues) | [@jaimergp](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ajaimergp+updated%3A2023-10-20..2024-01-05&type=Issues) | [@kcpevey](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Akcpevey+updated%3A2023-10-20..2024-01-05&type=Issues) | [@netlify](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Anetlify+updated%3A2023-10-20..2024-01-05&type=Issues) | [@nkaretnikov](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ankaretnikov+updated%3A2023-10-20..2024-01-05&type=Issues) | [@pavithraes](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apavithraes+updated%3A2023-10-20..2024-01-05&type=Issues) | [@pierrotsmnrd](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apierrotsmnrd+updated%3A2023-10-20..2024-01-05&type=Issues) | [@smeragoel](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Asmeragoel+updated%3A2023-10-20..2024-01-05&type=Issues) | [@trallard](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Atrallard+updated%3A2023-10-20..2024-01-05&type=Issues)



## [2023.10.1] - 2023-10-20

([full changelog](https://github.com/conda-incubator/conda-store/compare/2023.9.1...d2c7d23157e0e29cb4e61478a4f112a2eeee2c05))

## Merged PRs

- BUG - Add missing permissions for publishing [#637](https://github.com/conda-incubator/conda-store/pull/637) ([@trallard](https://github.com/trallard))
- DEV -  Add build check and test release workflow [#636](https://github.com/conda-incubator/conda-store/pull/636) ([@trallard](https://github.com/trallard))
- REL - 2023.10.1 [#635](https://github.com/conda-incubator/conda-store/pull/635) ([@trallard](https://github.com/trallard))
- ENH  -  Use miniforge throughout [#634](https://github.com/conda-incubator/conda-store/pull/634) ([@trallard](https://github.com/trallard))
- DEV -  Add python-docker [#633](https://github.com/conda-incubator/conda-store/pull/633) ([@trallard](https://github.com/trallard))
- DEV - optimize docker files [#625](https://github.com/conda-incubator/conda-store/pull/625) ([@dcmcand](https://github.com/dcmcand))
- DOC -  Tone and grammar improvements to templates [#624](https://github.com/conda-incubator/conda-store/pull/624) ([@trallard](https://github.com/trallard))
- Bump @babel/traverse from 7.22.10 to 7.23.2 in /docusaurus-docs [#623](https://github.com/conda-incubator/conda-store/pull/623) ([@dependabot](https://github.com/dependabot))
- Bug fix: use context manager for Sessions [#622](https://github.com/conda-incubator/conda-store/pull/622) ([@nkaretnikov](https://github.com/nkaretnikov))
- DEV - update conda store dockerfile to have prod target [#621](https://github.com/conda-incubator/conda-store/pull/621) ([@dcmcand](https://github.com/dcmcand))
- MAINT - remove extra redis and move to using built images for examples [#620](https://github.com/conda-incubator/conda-store/pull/620) ([@dcmcand](https://github.com/dcmcand))
- DOC - Add alembic example for postgres in docker [#610](https://github.com/conda-incubator/conda-store/pull/610) ([@nkaretnikov](https://github.com/nkaretnikov))
- Bump postcss from 8.4.27 to 8.4.31 in /docusaurus-docs [#609](https://github.com/conda-incubator/conda-store/pull/609) ([@dependabot](https://github.com/dependabot))
- MAINT - Update release docs and add issue template [#608](https://github.com/conda-incubator/conda-store/pull/608) ([@trallard](https://github.com/trallard))
- [DOC] Add Community documentation [#579](https://github.com/conda-incubator/conda-store/pull/579) ([@pavithraes](https://github.com/pavithraes))
- MAINT - Add a macOS worker to the CI [#550](https://github.com/conda-incubator/conda-store/pull/550) ([@asmeurer](https://github.com/asmeurer))
- DEV - Better handling of pydantic error msgs [#546](https://github.com/conda-incubator/conda-store/pull/546) ([@pierrotsmnrd](https://github.com/pierrotsmnrd))

## Contributors to this release

([GitHub contributors page for this release](https://github.com/conda-incubator/conda-store/graphs/contributors?from=2023-09-20&to=2023-10-20&type=c))

[@asmeurer](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aasmeurer+updated%3A2023-09-20..2023-10-20&type=Issues) | [@costrouc](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Acostrouc+updated%3A2023-09-20..2023-10-20&type=Issues) | [@dcmcand](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adcmcand+updated%3A2023-09-20..2023-10-20&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adependabot+updated%3A2023-09-20..2023-10-20&type=Issues) | [@dharhas](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Adharhas+updated%3A2023-09-20..2023-10-20&type=Issues) | [@iameskild](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Aiameskild+updated%3A2023-09-20..2023-10-20&type=Issues) | [@jaimergp](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ajaimergp+updated%3A2023-09-20..2023-10-20&type=Issues) | [@kcpevey](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Akcpevey+updated%3A2023-09-20..2023-10-20&type=Issues) | [@netlify](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Anetlify+updated%3A2023-09-20..2023-10-20&type=Issues) | [@nkaretnikov](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Ankaretnikov+updated%3A2023-09-20..2023-10-20&type=Issues) | [@pavithraes](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apavithraes+updated%3A2023-09-20..2023-10-20&type=Issues) | [@pierrotsmnrd](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Apierrotsmnrd+updated%3A2023-09-20..2023-10-20&type=Issues) | [@trallard](https://github.com/search?q=repo%3Aconda-incubator%2Fconda-store+involves%3Atrallard+updated%3A2023-09-20..2023-10-20&type=Issues)

## [2023.9.1] - 2023-09-21

### Added

- ENH - Make conda-store-server test port configurable (#571) [Kim
  Pevey]
- DOC - Update homepage to include project details (#565) [Kim Pevey, Pavithra Eswaramoorthy]
- [DOCS] Create multiple sidebars structure (#558) [Pavithra
  Eswaramoorthy]
- Make tests use a temporary directory for conda environments (#549)
  [Aaron Meurer]
- Set up Docusaurus (#534) [Pavithra Eswaramoorthy]
- Add a favicon to the docs and the conda-store server UI (#523) [Aaron
  Meurer, Chris Ostrouchov]
- Add trailing slash to avoid redirects (#500) [ClaytonAstrom, castrom]
- 🔧 Create new docs env (#533) [Pavithra Eswaramoorthy]
- Adding support for cleaning up builds stuck in BUILDING state (#530)
  [Christopher Ostrouchov]
- Adding additional routes for conda-lock lockfile (#526) [Christopher
  Ostrouchov]
- Allow setting a subdomain cookie for conda-store (#509) [Christopher
  Ostrouchov]
- MAINT - Add security policy. [Tania Allard]
- Add pre-commit (#479) [john lee]
- Adding incremental updates to the logs (#487) [Christopher Ostrouchov]
- Adding an api method for getting usage data for namespaces (#486)
  [Christopher Ostrouchov]
- Adding global/namespace/environment settings with api/ui and tests
  (#485) [Christopher Ostrouchov]
- Adding tests that test traitlets for conda-store-server (#484)
  [Christopher Ostrouchov]
- Adding tests for fastapi server without need for integration (#483)
  [Christopher Ostrouchov]

### Fixed

- MAINT - Update pre-commit hooks (#577) [Kim Pevey, Tania Allard]
- Handle argv in pytest fixture (#557) [Stephannie Jimenez]
- Fix some spelling errors in the PR template (#555) [Aaron Meurer]
- Allow all channels by default (#545) [Nikita Karetnikov]
- Don't run conda-docker on Mac (#539) [Aaron Meurer]
-  Make the disk_usage() function work on macOS (#537) [Aaron Meurer]
- Bugfix to allow backwards compatibility on metadata_ (#527)
  [Christopher Ostrouchov]
- Fixing vault role and paths (#525) [Christopher Ostrouchov]
- Fixing docker builds on main (#503) [Christopher Ostrouchov]
- Fixing docker builds temporarily by creating single image (#488)
  [Christopher Ostrouchov]
- Fix #476 : delete dangling build artifacts before migration (#477)
  [Pierre-Olivier Simonard]
- Pin SQLAlchemy <=1 .4.47 (#480) [Pierre-Olivier Simonard]
- Fixing username for pipeline. [Chris Ostrouchov]

### Changed

- Update build metadata on deletion, fix misc bugs (#572) [Nikita Karetnikov]
- Fix migration of artifact type for postgres (#574) [Pierre-Olivier Simonard]
- ENH - Return legacy lockfile if key is empty (#553) [Nikita
  Karetnikov]
- Update LICENSE attribution (#564) [Pavithra Eswaramoorthy]
- MAINT - Update release.yaml to use trusted publishing (#542) [Anirrudh
  Krishnan]
- Delete subdomain keys on logout (#541) [Anirrudh Krishnan]
- Update release docs to reflect pyproject.toml changes. [Chris
  Ostrouchov]
- MAINT - Update issue and PR templates. [Tania Allard]
- Update repository URL (#518) [Stephannie Jimenez Gacha]
- Add python-docker as an explicit dependency in environment.yml (#524)
  [Aaron Meurer]
  - Proper handling of sqlalchemy database sessions in fastapi and celery
  (#522) [Christopher Ostrouchov]
  - API : update a namespace's metadata and role mappings (#508) [Pierre-
  Olivier Simonard]
- Change the tests when using sqlite to not check threads  (#505)
  [Christopher Ostrouchov]
- Better error messages around pip packages (#504) [Christopher
  Ostrouchov]
- Removing use of old lockfile format using newer conda-lock.yml format
  (#501) [Christopher Ostrouchov, Pierre-Olivier Simonard]
- Role mapping (#496) [Chris Ostrouchov, Pierre-Olivier Simonard]
- Push images for main (#474) [john lee]
- Reworking on celery tasks into actions (#473) [Christopher Ostrouchov]
- Changing the vault url (#472) [Christopher Ostrouchov]

## [0.4.15] - 2023-04-21

### Added

- conda-store and conda-store-server images are now deployed to quay.io/Quansight, which has support for podman and rkt. (#455)
- Parallel builds of conda environments (#417)
- Switch to green theme by default for conda-store UI (#463)
- Fix for use environment stats (#466)

## [0.4.14] - 2023-04-07

### Fixed

- make conda-store-ui settings configurable (were previously hardcoded and broken) (#451)

## [0.4.13] - 2023-04-06

### Added

- Added new conda-store-ui (#444)
- Added new option `CondaStore.conda_indexed_channels` for indexed channels (#445)
- Allow passing environment variables in specification (#424)

### Changed

- Switched to hatch for conda-store and conda-store-server (#449, #450)
- Switch default UI to conda-store-ui and expose behind `/admin/` (#448)
- Significant database rework on package storage for performance (#300)

### Removed

- Remove unused helm chart (#450)
- Remove nix flakes from repository (#443)

## [0.4.12] - 2022-09-21

### Fixed

- environment description is optional

### Added

- Make symlink path configurable for builds on filesystem #388
- Redirect on login and cookie handling #381
- Visually split the namespace with bootstrap bit #374
- Make image name and tag configurable for uploads to registries #380

## [0.4.11] - 2022-08-17

### Fixed

- including package_data #379

## [0.4.10] - 2022-08-16

### Added

- `conda-store-server --standalone` now runs conda-store-server without any service dependencies (#378, #376)
- Initial helm chart skeleton still work to be done to have official helm chart

### Fixed

- Bug in LocalStorage implmentation #376
- Bug in docker builds when pushed to container registries #377
- CORS endpoint error on login when using POST #375

## [0.4.9] - 2022-08-09

### Added

- push/pull container images to/from additionall registries (#370)
- adding description associated with environments #363

## [0.4.8] - 2022-08-04

### Added

- Adding shebang support for conda-store (#362)

### Fixed

- Fixed example demo for docker
- Fixing docker registry implementation in conda-store (#368)

## Security

- Adding authentication behind docker registry (#369)

## [0.4.7] - 2022-07-28

### Added

- Adding additional query parameters environment_id, namespace, name in list api methods in build/environment #350
- Adding ability to sort based on start/schedule/ended for list builds #352
- Adding repo.anaconda.com to default channels #354
- Empty list for conda_allowed_channels now will allow any channel #358

### Fixed

- Changed docker images to no longer run as root by default #355

## [0.4.6] - 2022-07-08

### Added

- Added `c.CondaStoreServer.template_vars` for easy customization #347
- Consistent naming of `conda-store` throughout project #345
- Adding token endpoint #335
- Adding token UI create button #348

### Fixed

- Bug with user being able to modify `c.RBACAuthorizationBackend.authenticated_role_bindings` #346

## [0.4.5] - 2022-06-29

### Added

- Adding cli command `solve` to call remote conda solve api (#329)
- New filters for build and environment api calls status, artifact, package (#329)
- Adding Alembic migration integration (#314)

## [0.4.4] - 2022-06-25

### Added

- `wait` option in cli for waiting on artifacts and builds (#328)
- `list build` command (#328)
- tests for client conda-store (#328)

### Fixed

- issue with caching option in run command (#328)

### Changed

- api now exposes the build_artifacts field on `api/v1/build/<build-id>/`

## [0.4.2] - 2022-06-24

### Fixed

- fixed release process using build toolchain

## [0.4.1] - 2022-06-24

### Added

- Command line client for conda-store (#327)
- Adding searchbar for UI (#326)
- OpenAPI specification in documentation
- Added namespace query parameter to `/api/v1/environment/?namespace=` (#324)

## [0.4.0] - 2022-05-04

### Changed

- Transition to FastAPI for web server from Flask (#277) end user API should not have changed
- `conda_store_server.server.auth.Authentication.authenticate` is now an `async` method receiving a [Starlette request object](https://www.starlette.io/requests/)

### Added

- Adding PyPi validation for included, required, and default packages (#292)
- Creating a Conda solve API endpoint (#279)
- Fully tested API for `/api/v1/...` endpoints (#281)

### Fixed

- Support for valid `pip` options in `environment.yaml` (#295)

## [0.3.15] - 2022-03-25

### Added

- Debug mode now controlled by CondaStoreServer.log_level
- Make concurrency setting optional in configuration
- Sort namespaces in create environment UI button
- Allow cookies cross domain

### Fixed

- Correct default namespace for POST /api/v1/specification/

## [0.3.14] - 2022-03-24

### Added

- Account for None, "" values within namespace POST in `/api/v1/specification` #274

## [0.3.13] - 2022-03-23

### Added

- API endpoint `/api/v1/permission/` and UI user endpoint showing user permissions #271

## [0.3.12] - 2022-03-21

### Added

- better error messages when user not authenticated #261
- conda package builds independent from conda package download #258
- exact search route for conda-store api in packages #264
- adding lockfile to conda-store to provide a short term fix around conda/mamba concurrency issue #268

## [0.3.11] - 2022-03-08

### Added

- `CondaStore.conda_...` options for managing channels and packages in specification #256
- Ability to modify/validate specifications server side #252
- Concurrency option for conda-store celery worker #250
- Flask webserver has a `CondaStore.behind_proxy` option to properly handle X-Forward- headers #249
- Docker layer chaching to CI for docker image builds #234

### Changed

- `buildId` parameter in `/api/v1/environment/<namespace>/<name>/` changed to `build_id` #251

## [0.3.10] - 2022-02-24

### Added

- `build_id` response to `POST /api/v1/specification` route #244
- Added a validation for namespaces that is more flexible # 233
- Added ability to use via `nix run github:quansight/conda-store ...` #232
- API endpoints now return channel name instead of id #231

### Fixed

- Flask paths now support routes with and without a trailing slash #230

## [0.3.9] - 2022-01-23

### Added

- Adding support for templates for build and environment symlink directories
- Adding support for internal and external secure settings

### Fixed

- Error in build url with extra `/` in environment page

## [0.3.8] - 2022-01-13

### Fixed

- Ensure compatibility with keycloak authentication flow

## [0.3.7] - 2022-01-13

### Added

- Support for custom `GenericOAuthAuthentication.oauth_callback_url`
- Support for optional tls_verification on oauth2 flow `GenericOAuthAuthentication.tls_verify`

## [0.3.6] - 2022-01-12

### Added

- Testing to support mysql database

## [0.3.5] - 2022-01-11

### Fixed

- setting fixed sizes to Unicode columns

## [0.3.4] - 2022-01-11

### Added

- api endpoint for exporting yaml environment files #204

### Fixed

- using Unicode sqlalchemy column instead of String
- removed typer as a dependency
- removed hardcoded path for conda executable
- environment creation endpoint with namespaces
- removed psycopg2 as a dependency #206
- validate that config_file exists #223

## [0.3.3] - 2021-10-28

### Fixed

- missing dependency in `conda-store-server/setup.py` `yarl`

## [0.3.2] - 2021-10-28

### Added

- added ability to search within the `/api/v1/build/<build-id>/package/` path #193
- environments and namespaces no longer show up in API and UI when soft deleted #194

### Fixed

- `docker-compose.yaml` in `examples/docker` now compatible with 2.0 #195
- flask templates now included in the PyPi packages #196

## [0.3.1] - 2021-10-12

### Added

- support for credentials supplied for object storage including IAM credentials #176
- namespace UI to conda-store server #183
- create/read/delete methods for namespaces `/api/v1/namespace/` #181
- distinct_on query parameter to list REST API methods #164
- adding sorting query parameter to list REST API methods #162
- ability to filter Conda packages by build parameter #156
- delete environments and all related builds from REST API #154
- initial support for pagination for all list REST API methods #126
- support for filtering environments by name #125
- working Kubernetes deployment example #116
- significant documentation effort via multiple PRs

### Changed

- namespace parameter in JSON POST request to `/api/v1/specification/` #178
- API route for listing packages within build instead of including within build API response #157
- database relationship between build, environments, and namespaces improved #153

### Fixed

- adding conda-store gator extension to `example/docker` #165
- get query count before applying limits to query #159

## [0.3.0] - 2021-08-27

This is the beginning of the changelog. Here I will list the most
notable things done in the past 3-6 months.

### Added

- complete authentication and RBAC based authorization modeled after JupyterHub authentication model [#97](https://github.com/Quansight/conda-store/pull/97)
- support for a namespace associated with environments and builds [#96](https://github.com/Quansight/conda-store/pull/96)
- testing of conda-store UI via [cypress](https://www.cypress.io/) [#111](https://github.com/Quansight/conda-store/pull/111)
- delete and update buttons immediately update status [#107](https://github.com/Quansight/conda-store/pull/107)
- support for dummy authentication and OAuth2 (GitHub + JupyterHub) authentication [#103](https://github.com/Quansight/conda-store/pull/103)
- delete method for conda-store builds [#94](https://github.com/Quansight/conda-store/pull/94)
- support for url prefix [#109](https://github.com/Quansight/conda-store/pull/109)
- docker button says click to copy to clipboard [#110](https://github.com/Quansight/conda-store/pull/110)
- enabling rollbacks of environment builds [#93](https://github.com/Quansight/conda-store/pull/93)
- adding `conda env export` for pinned YAML file [#92](https://github.com/Quansight/conda-store/pull/92)
- celery integration for true task based builds [#90](https://github.com/Quansight/conda-store/pull/90)
- conda-store configuration is configured via Traitlets [#87](https://github.com/Quansight/conda-store/pull/87)
- Prometheus metrics endpoint [#84](https://github.com/Quansight/conda-store/pull/84)
- help button in top right hand corner [#83](https://github.com/Quansight/conda-store/pull/83)
- support for internal and external url for s3 bucket [#81](https://github.com/Quansight/conda-store/pull/81)

### Changed

- use Micromamba for environment builds by default [#66](https://github.com/Quansight/conda-store/pull/66)
- download repodata compressed [#76](https://github.com/Quansight/conda-store/pull/76)
- only show artifacts once it has been built [#113](https://github.com/Quansight/conda-store/pull/113)
- true parallel builds and retry if Conda channel update fails [#114](https://github.com/Quansight/conda-store/pull/114)

### Fixed

- SQLAlchemy connection leak to database [#105](https://github.com/Quansight/conda-store/pull/105)
