---
description: Best practices for opening issues
---

# Create and improve issues

## Submit a bug report or feature request

The conda-store issue trackers are the preferred channel for bug reports, documentation requests, and submitting pull requests.

To resolve your issue, please select the appropriate category and follow the prompts to provide as much information as
possible:

- **Bug Report:** When something is not working as expected and documented
- **Feature request:** Request new enhancements to conda-store
- **Usage question:** Questions about how to use conda-store
- **General issue:** Anything that doesn't fit the above categories

## Best practices

When opening an issue, use a **descriptive title** and include all relevant details about your bug and environment (operating system, Python version, conda-store version, etc.). Our issue template helps you remember the most important details to include.

A few more tips:

- **Describing your issue**: Try to provide as many details as possible. What exactly goes wrong? How is it failing?
  Is there an error? "XY doesn't work" usually isn't that helpful for tracking down problems.
  Provide clear instructions for how to reproduce your issue.
  Always remember to include the code you ran and if possible,
  extract only the relevant parts and don't dump your entire script.
  You can also add screenshots and recordings of the issue.
  This is essential for the development team to triage, prioritize, and resolve your issue.

- **Getting info about your conda-store installation and environment**: You can use the command line interface to print details and even format them as Markdown to copy-paste into GitHub issues.

- **Sharing long blocks of code or logs**: If you need to include long code, logs or tracebacks, you can wrap them in `<details>` and `</details>`.
  This collapses the content, so it only becomes visible on click, making the issue easier to read and follow.

:::tip
See this page for an overview of the [system we use to tag our issues and pull requests][github-conventions].
:::

## Suggested workflow

If an issue is affecting you, start at the top of this list and complete as many tasks on the list as you can:

1. Check the issue tracker, if there is an open issue for this same problem, add a reaction or more details to the issue
   to indicate that it’s affecting you (tip: make sure to also check the open pull requests for ongoing work).
2. If there is an open issue, and you can add more detail, write a comment describing how the problem is affecting you (tip: learn to improve issues in the next section),
   OR if you can, write up a workaround or improvement for the issue.
3. If there is not an issue, write the most complete description of what’s happening including reproduction steps.
4. [Optional] - Offer to help fix the issue (and it is expected that you ask for help; open-source maintainers want to help contributors).
5. [Optional] - If you decide to help fix the issue, deliver a well-crafted, tested PR.

## Improve existing issues

Improving issues increases their chances of being successfully resolved. A third party can give useful feedback or even add comments on the issue.

The following actions are typically useful:

- Add missing elements that are blocking progress such as code samples to reproduce the problem.
- Suggest better use of code formatting.
- Suggest reformulating the title and description to make them more explicit about the problem to be solved.
- Link to related issues or discussions while briefly describing how they are related, for instance, “See also #xyz for a similar attempt at this” or “See also #xyz where the same thing happened in another cloud provider" provides context and helps the discussion.
- Summarize long discussions on issues to help new and existing contributors quickly understand the background, current status, and course of action for the issue.

You can further [contribute to triaging efforts with these guidelines][triage].

<!-- Internal links -->

[github-conventions]: /community/maintenance/github-conventions
[triage]: /community/maintenance/triage
