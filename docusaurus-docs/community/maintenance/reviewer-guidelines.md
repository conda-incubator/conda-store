---
description: Guidelines and tips for reviewing contributions to Nebari
---

# Reviewer guidelines

## Who can be a reviewer?

Reviewing open pull requests (PRs) or other contributions helps move the project forward.
We encourage people outside the project to get involved as well; it’s a great way to get familiar with the project and
its development workflow.

## Communication guidelines

- Every PR, good or bad, is an act of generosity. Opening with a positive comment will help the author feel rewarded,
  and your subsequent remarks may be heard more openly. You may feel good also.
- Begin if possible with the large issues, so the author knows they’ve been understood.
  Resist the temptation to immediately go line by line, or to open with small pervasive issues.
- You are the face of the project, and the Nebari project aims to be: open, empathetic, welcoming, friendly and patient.
  [Be kind to contributors](https://youtu.be/tzFWz5fiVKU?t=49m30s).
- Do not let perfect be the enemy of the good, particularly for documentation. If you find yourself making many small suggestions,
  or being too nitpicky on style or grammar, consider merging the current PR when all important concerns are addressed.
  Then, either push a commit directly (if you are a maintainer) or open a follow-up PR yourself.
- Do not rush, take the time to make your comments clear and justify your suggestions.
- If you review a pull request from a "first-time contributor" (you will see a label on their pull request), be a little more patient with them and include additional context to your suggestions.

:::tip
If you need help writing replies in reviews, check out our [standard replies for reviewing][saved-replies].
:::

## Reviewer checklist

Here are a few important aspects that need to be covered in any review.
Note this is not an exhaustive, nor strictly list of items to cover on each review, use your best judgement.

- Do we want this in the project? Will the cost of maintaining it outweigh the benefits?
  Is this solving a niche use case or would it benefit the broader community? Should this contribution be made to an upstream project instead?
- Pull requests need triaging too - if you have the correct permissions,
  add the relevant labels as detailed in our [GitHub conventions docs][github-conventions].
- Should comments be added, or rather removed as unhelpful or extraneous?
- Do the documentation and code style adhere to our style guides?
- Does this contribution require changes or additions to the documentation? Have these changes been made? If not,
  add the `needs: docs 📖` label to the PR.
- Do the tests pass in the continuous integration build? If appropriate, help the contributor understand why tests failed.
  Add the `needs: changes 🧱` label if the PR needs to be updated.
- For code changes, at least one maintainer (someone with commit rights) should review and approve a pull request.
  If you are the first to review a PR and approve of the changes use the GitHub approve review tool to mark it as such.
  If a PR is straightforward, for example it’s a clearly correct bug fix, it can be merged straight away.
  If it’s more complex or introduces breaking changes, please leave it open for at least a couple of days, so other maintainers get a chance to review.
  You can also consider mentioning or requesting a review from specific maintainers who are familiar with relevant parts of the codebase.
- If you are a subsequent reviewer on an already approved PR, please use the same review method as for a new PR
  (focus on the larger issues, resist the temptation to add only a few nitpicks).
  If you have commit rights and think no more review is needed, merge the PR.
- If the PR is missing tests or the tests have not been updated let the contributor know and add the `needs: tests ✅` label.
- If the PR fixes an issue, the PR must mention that issue in the PR body for example `gh-xyz`.

### For maintainers

Only maintainers can merge pull requests. Please follow these guidelines:

- Make sure all automated CI tests pass before merging a PR, and that the documentation builds without any errors.
- In case of merge conflicts, ask the PR submitter to rebase on `main`.
- Squashing commits or cleaning up commit messages of a PR that you consider too messy is OK.
  Remember to retain the original author’s name when doing this.
- When you want to reject a PR: if it’s very straightforward, you can close it and explain why. If it’s not,
  then it’s a good idea to first explain why you think the PR is not suitable for inclusion in Nebari and then let a second committer comment or close.
- Maintainers are encouraged to finalize PRs when only small changes are necessary before merging
  (acceptable changes are fixing code style or grammatical errors). If a PR becomes inactive, maintainers may make larger changes.
  Remember, a PR is a collaboration between a contributor and a reviewer/s, sometimes a direct push is the best way to finish it.
- You should typically not self-merge your own pull requests. Exceptions include things like small changes to fix CI
  (for example pinning a package version).
- You should not merge pull requests that have an active discussion, or pull requests that has been proposed for rejection
  by another maintainer.

## GitHub workflow

When reviewing pull requests, please use workflow tracking features on GitHub as appropriate.

1. After you have finished reviewing, if you want to ask for the submitter to make changes,
   change your review status to “Changes requested.” This can be done on GitHub, PR page > Files changed tab, Review changes (button on the top right).
   Add the `needs: changes 🧱` label to the PR (or other relevant labels like `needs: tests` or `needs: docs`).
2. If you’re happy about the current status, mark the pull request as Approved (same way as Changes requested) and add the `status: approved 💪🏾` label.
3. **Alternatively (for maintainers):** merge the pull request, if you think it is ready to be merged.
   All the pull requests are **squashed merged** retaining the original author’s name.

## Asking questions

You are encouraged to ask questions and seek an understanding of what the PR is doing; however, your question might be answered further into the review.
You can stage your questions, and before you submit your review, revisit your own comments to see if they're still relevant or update them after gaining further context.

Often a question may turn into a request for further comments or changes to explain what is happening at that specific point.

In your questions, try and be empathetic when phrasing. Instead of: "Why did you do this?"

try: **"Am I understanding this correctly? Can you explain why...?"**

Remember a review is a discussion, often with multiple parties -- be reasonable.
Try to focus and summarize in ways which constructively move the conversation forward instead of retreading ground.

## Asking for changes

It's okay to ask for changes to be made on a PR.
In your comments, you should be clear on what is a 'nit' or small thing to be improved and a required change needed to accept the PR.

Be clear and state upfront architectural or larger changes. These should be resolved first before addressing any further nits.
Also, make sure to add the `needs: changes 🧱` label to the PR.

It's also okay to say "No" to a PR. As a community, we want to respect people's time and efforts,
but sometimes things don't make sense to accept.
As reviewers, you are the stewards of the code-base and sometimes that means pushing back on potential changes.


<!-- Internal links -->

[saved-replies]: /community/maintenance/saved-replies.md
[github-conventions]: /communitymaintenance/github-conventions.md
