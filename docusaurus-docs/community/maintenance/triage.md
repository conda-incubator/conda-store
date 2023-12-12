---
sidebar_position: 1
description: Guidelines for triaging the conda-store issue trackers
---

# Triage guidelines

Issue triage is a process by which conda-store maintainers and contributors understand and review new GitHub issues and pull requests, and organize them to be actioned.
Triaging involves categorizing issues and pull requests based on factors such as priority, area of ownership of the issue (tags), and the issue kind (bug, feature, and so on).

We aim to triage new issues or pull requests within a week.
Triage can happen asynchronously and continuously, or in regularly scheduled meetings.

## Why is triaging beneficial?

Projects that triage regularly say it offers several benefits, such as:

- Speeding up issue management
- Keeping contributors engaged by shortening response times
- Preventing work from lingering endlessly
- Replacing niche requests and one-offs with a neutral process that acts like a boundary
- Greater transparency, interesting discussions, and more collaborative, informed decision-making
- Building prioritization, negotiation and decision-making skills, which are critical to most tech roles
- Reinforcement of the project's community and culture

People who enjoy product management and iterating on processes tend to enjoy triaging because it empowers their project to maintain a steady,
continuous flow of work that is assessed and prioritized based on feedback, impact, and value.

## Triaging workflow

### Step 1: Review newly created issues

The first step in a triaging workflow is to review the newly created open issues in the repository.
An efficient way to do this is by using the `is:issue is:open sort:created-dec` query in the repository's issue search,
which will show the most recently created issues first (see an example of this in the [conda-store issue tracker](https://github.com/conda-incubator/conda-store/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-dec)).

Other useful queries include:

| Query                                           | Example search                                                                                                                              | What it sorts                                         |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `is:issue is:open sort:created-dec`             | [new-issues conda-store](https://github.com/conda-incubator/conda-store/issues?q=is%3Aopen+is%3Aissue)                                                     | Newest incoming issues                                |
| `is:issue is:open sort:comments-desc`           | [comments-descending conda-store](https://github.com/conda-incubator/conda-store/issues?q=is%3Aissue+is%3Aopen+sort%3Acomments-desc)                       | Busiest issues, sorted by # of comments               |
| `is:issue is:open sort:created-asc no:label`    | [created-ascending conda-store](https://github.com/conda-incubator/conda-store/issues?q=is%3Aissue+is%3Aopen+sort%3Acreated-asc+no%3Alabel)                | Untriaged issues by age                               |

You can also use the [conda-store project board](https://github.com/orgs/conda-incubator/projects/8) to keep track of issues that [need triage](https://github.com/orgs/conda-incubator/projects/8/views/4) and [follow-up](https://github.com/orgs/conda-incubator/projects/8/views/9).

### Step 2: Triage issues

1. **First things first: thank the reporter for opening an issue.**
   The issue tracker is many people’s first interaction with the conda-store project,
   beyond using the project itself. As such, we want it to be a welcoming, pleasant experience for everyone.

2. Assess the issue and label, assign, or close accordingly.
   1. Depending on your permissions, either close or comment on any issues that are identified as support requests, duplicates, or not-reproducible bugs, or that lack enough information from the reporter (see sections below).
   2. Make sure that the title accurately reflects the issue. If you have the necessary permissions edit it yourself if it's not clear.
   3. Add the relevant labels.
      Detailed rationale for our labelling system can be found in the [GitHub conventions section][github-conventions] of our documentation.

:::tip
Assign one and only one `type:` label to the issue and as many `area:` labels as are relevant.

Feel free to [use our saved replies][saved-replies] to help you with triaging.
:::

#### Abandoned or wrongly placed issues

If an issue is abandoned or in the wrong place, either close, move it, or comment on it.

#### Needs more information

The `needs: investigation  🔎` or `needs: more information 📝` label indicates an issue needs more information in order for work to continue; comment on or close it.
This can be steps to reproduce the bug, details on the environment, or any other information that would help the issue move forward.

#### Bugs

First, validate if the problem is a bug by trying to reproduce it.

If you can reproduce it:

- Define its impact and area (see our [GitHub conventions section][github-conventions] for more details).
- Search for duplicates to see if the issue has been reported already. If a duplicate is found, let the issue reporter know,
  reference the original issue, add the `duplicate 👯‍♀️` label, and close the duplicate.

If you can't reproduce it:

- Contact the issue reporter with your findings
- Close the issue if both the parties agree that it could not be reproduced

If you need more information to further work on the issue:

- Let the reporter know it by adding an issue comment, and label the issue with `needs: investigation  🔎`.

In all cases, if you do not get a response within 20 days, close the issue with an appropriate comment.
If you have permission to close someone else's issue, add an informative message, optionally `assign` the issue to yourself, then `close` it.
If you do not, please leave a comment describing your findings and ask for the issue to be closed.

#### Self-Assigning

If you think you can fix the issue, assign it to yourself. If you cannot self-assign for permissions-related reasons,
leave a comment that you'd like to claim it and begin working on a PR.

When an issue already has an assignee, **do not** assign it to yourself or create a PR without talking to the existing assignee first.
Creating a PR when someone else is already working on an issue is not a good practice and is discouraged.

## Further notes

Opening new issues and leaving comments on other people's issues is possible for all contributors.
However, permission to assign specific labels (such as `type: enhancement 💅🏼`), change milestones,
or close other contributors' issues is only granted to the author of an issue, assignees, and organization members.

We have multiple [saved replies][saved-replies] that can be used to help triage issues and while conducting contributions reviews.


<!-- Internal links -->

[saved-replies]: /community/maintenance/saved-replies
[github-conventions]: /community/maintenance/github-conventions.md
