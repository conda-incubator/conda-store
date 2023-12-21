---
description: GitHub conventions for the conda-store issue and pull request trackers
---

# GitHub conventions

This page describes some common conventions and guidelines that we follow in all the conda-store GitHub repositories.

## GitHub labels for issues and pull requests

There are a few GitHub labels that we use to provide key metadata in our issues and pull requests.
These are added to all conda-store repositories, and share the same meaning across each of them.

Issues and pull requests are classified by having a [`type`](#issue-type) label and a number of optional labels such as [`area`](#area-tag) or [`impact`](#issue-impact).

:::note
Repositories may define their own labels in addition to the ones described here
to better reflect the areas and scope of the project.
:::

### Issue type

**REQUIRED :pushpin:**

**Issue type** determines the kind of issue and implies what sorts of actions must be taken to close it.
**All issues must be assigned a type label as soon as possible.**
Issue types are mutually-exclusive - **there may only be one issue type per issue**.

There are a few issue types that are defined for all repositories, for example:

- `type: enhancement 💅🏼`: an incremental improvement to something
- `type: bug 🐛`: a problem that needs to be fixed
- `type: maintenance 🛠`: regular maintenance and upkeep
- `type: discussion 💬`: discussion of general questions, ideas and so on

In addition, other repositories may use repository-specific types, with the caveat that **all issues must still only have one `type` label**.

### Issue impact

**OPTIONAL**

Issue impact is used to signal how much of an impact resolving an issue will have.
The meaning of this depends on the issue type (for example, enhancement, bug).

The impact should be proportional to a combination of:

- The number of users that will be impacted by an issue's resolution,
- The extent of the impact our users will feel (for example a major change in experience versus minor improvement)
- The importance of communities or stakeholders that are impacted by the issue.

These are the impact labels for our issues:

- `impact: high 🟥`
- `impact: medium 🟨`
- `impact: low 🟩`

#### Categorizing impact

Here are a few guidelines for how to categorize impact across a few major types of issues.

**Features / Enhancements**

- `impact: high`: Will be seen and commonly used by nearly all users. Has been requested by an abnormally large number of users.
  Is of particular importance to a key community.
- `impact: med`: Useful to many users but not an overwhelming amount. Will be a less-obvious improvement.
  Most issues should be in this category.
- `impact: low`: Useful but not a critical part of workflows. Is a niche use case that only a few users may need.

**Bugs**

- `impact: high`: Disruptive to nearly all users, or critically disruptive to many users or key communities
  (for example, instances won't work at all).
- `impact: med`: Disruptive to some users, but not in a critical way. Only noticeable under circumstances that aren't very common.
  Most issues should be in this category.
- `impact: low`: Minimally disruptive or cosmetic, or only affects a few users or niche use cases.
  Note that `accessibility` related issues should be `impact: high` as these are never purely cosmetic changes.

### Area tag

**OPTIONAL**

Tag labels provide hints about what topics that issue is relevant to.
They are highly repository-specific, optional, and non-exclusive (so issues may have many tags associated with them).

Here are some example tags:

- `area: documentation 📖`: related to documentation in a repository
- `area: CI 👷🏽‍♀️`: related to continuous integration/deployment
- `area: design 🎨`: related to design items including UX/UI and graphic design

### Needs labels

**OPTIONAL**

These labels are used to denote what sort of action is needed to resolve an issue or move a pull request forward.

- `needs: discussion 💬`: this issue needs to be discussed in a meeting or in a GitHub issue
- `needs: follow-up 📫`: someone in the team needs to follow up on this issue or with another stakeholder
- `needs: review 👀`: this issue needs to be reviewed by a team member
- `needs: triage 🚦`: this issue needs to be triaged by a team member
- `needs: investigation 🔍`: this issue needs to be investigated by a team member, often used when an issue was submitted without enough information or reproduction steps
- `needs: changes 🧱`: this pull request has been reviewed and changes have been requested
- `needs: tests ✅`: tests need to be added or updated to close this pull request
- `needs: documentation 📖`: documentation needs to be added or updated to close this pull request
- `needs: PR 📬`: this issue needs to be worked on, usually as a pull request

### Other labels

A few labels exist to denote particular situations:

- `Close?`: to denote an issue that might need closing, either because the discussion has dried out or there are no concrete follow-up actions
- `DO-NOT-MERGE`: to denote a PR that should not be merged yet
- `good first issue`: these issues represent self-contained work that would make a good introduction to project development for a new contributor
- `Roadmap 🚀`: this issue is part of the project roadmap

## Pull requests

Pull requests are usually associated with or linked to issues. The natural path is to start with an issue and move on to a pull request for resolution.
But sometimes a new pull request is created without an associated issue.
In such cases, a new issue should be created for that pull request to engage people in a general discussion, not the technical review which is performed in the pull request itself.

If the PR does not need a discussion (trivial fixes, tasks, and so on), the opening of an associated issue may be skipped, but the pull request must be labeled accordingly.

We use mutually exclusive GitHub labels with the prefix`status:` to classify PR's.

- `status: abandoned 🗑`: this pull request has not seen activity in a while (at least a month)
- `status: stale 🥖`: a "stale" pull request is no longer up to date with the main line of development, and it needs to be updated before it can be merged into the project.
- `status: in progress 🏗`: this PR is currently being worked on
- `status: in review 👀`: this PR is currently being reviewed by the team
- `status: declined 🙅🏻‍♀️`: this PR has been reviewed and declined for merged
- `status: approved 💪🏾`: this PR has been reviewed and approved for merge
- `status: blocked ⛔️`: this PR is blocked by another PR or issue

GitHub notifies team members when labels are changed, so it is useful to keep the status of each pull request as close as possible to reality.
For example, if you realize that your PR needs more work after a first pass review, then change the label to `status: in progress 🏗`.

**All PR's must be tagged with a status at all times**

## Issue and PR templates

We use Issue and PR Templates to provide helpful prompts for common issues across all of our repositories.
