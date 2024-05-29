---
title: UX research
description: conda-store usability study results (2024)
---

# conda-store Usability Study Results

## Introduction

[conda-store](https://conda.store/) is a suite of tools for managing conda environments, including creating, storing, and accessing environments across teams. conda-store is aimed at all team members, from individual data scientists to software engineers and IT administrators. This report details the findings from a comprehensive usability study focused on [conda-store-ui (a web interface)](https://github.com/conda-incubator/conda-store-ui) as integrated within the [Nebari](https://www.nebari.dev) platform.

## Objectives

* Pinpoint the specific areas within conda-store-ui where users encounter difficulties.
* Collect detailed feedback from real users about their experiences and expectations.
* Use the insights gathered to inform targeted enhancement efforts
* Ensure that conda-store continues to meet the evolving needs of the data science community.

## Methodology

The study utilized a mixed methods approach to capture detailed user feedback:

* **Participants:** Six developers with varying levels of familiarity with conda-store, participated in this study. They were selected through an open call, aiming to cover a range [of user personals previously identified as typical users of conda-store](https://conda.store/community/design/user-personas#user-personas-%EF%B8%8F).
* **Tasks:** Each participant was asked to complete predefined tasks that mirrored typical workflows within conda-store. These tasks explored key functionalities such as environment creation, configuration and collaboration capabilities.
* **Data collection:** We collected data through direct observation, one-on-one interviews, and screen recordings. Participants were encouraged to verbalize their thoughts and feedback while navigating conda-store, providing insights into their real-time user experience.
* **Analysis:** Data collected during the study was meticulously analyzed through thematic coding to identify recurring themes and insights. This involved reviewing transcriptions, observations, and screen recordings to categorize user feedback into distinct themes.

## Testing Environments Overview

1. **Operating systems:** MacOS, Linux Elementary OS
2. **Browsers:** Google Chrome, Firefox, Safari
3. **Interface:** Browser-based access to a Nebari instance (v2024.3.3) with conda-store (v2024.3.1).

## Team

Smera Goel, Pavithra Eswaramoorthy, Tania Allard, Kim Pevey

## Limitations

This study provides valuable insights into the usability of conda-store, yet it is important to acknowledge its limitations:

* **Sample Size:** The study was conducted with a small sample of six participants, which may not fully represent the broad range of experiences of all conda-store users.
* **Targeted Personas:** The study focused solely on conda-store user personas previously identified [and detailed in the conda-store design documentation](https://conda.store/community/design/user-personas).
It is important to acknowledge these limitations to correctly interpret the results, guide future enhancements and plan subsequent research.

## Actionable Insights

This section details the specific usability issues and participant feedback that necessitate changes to conda-store. Each insight is directly tied to observable challenges encountered by users during the study. Findings are organized by common patterns observed.

### Workflows

This section explores the critical workflows identified during our usability study, highlighting the experiences of users as they navigate through the different stages of environment management:

* **Logging in:** Users noted the need for multiple logins as a significant inconvenience and expected a more seamless integration between conda-store and Nebari. Additionally, some users indicated that they would use a password manager if credentials were not provided, highlighting the importance of ensuring that the login service is compatible with browser-saved passwords. Some users forgot that "Environment Management" refers to conda-store on the Nebari homepage; others clicked on it instinctively due to previous experience with conda-store. Thus, the link’s labeling on the Nebari homepage is not immediately clear to all users, leading to confusion for those less familiar with conda-store. Overall, users found the login mechanism smooth and seamless, except for a few hiccups.

* **Getting started:** Users generally reacted positively to the user interface. However, some found it confusing and were unsure of how to proceed after logging in. Introducing a welcome page that features quick navigation to core workflows would aid new users in getting started more effectively.

* **Creating an environment:** Users asked if there was a way to import `lockfiles` or artifacts to create a new environment because their usual workflows involve copying existing environments. Adding such a feature could streamline setting up new environments based on existing configurations, making it more efficient and user-friendly.

* **Using the environment:** Users were unsure how to effectively use the newly created environment and what the ideal next steps should be. Clear instructions on launching and using environments after creation should be provided, ensuring this primary user flow is well understood. Introducing a “Launch in JupyterLab” button directly within the conda-store UI would enable users to use the newly created environment without additional steps, enhancing efficiency and user satisfaction.

* **Sharing:** The sharing functionality in conda-store is still under development, but we extensively discussed it with the participants. These discussions revealed a strong user preference for features similar to those Google Docs offers, such as setting permissions (view, share, edit) and sharing via links. Users also suggested the platform should support secure and straightforward sharing mechanisms, like drag-and-drop functionality for moving environments between namespaces or external platforms. Sharing was identified as a critical feature and the primary use case for many users; thus, it is crucial to prioritize developing user-friendly and robust sharing features to enhance collaboration within conda-store.

* **Search:** Users found the search functionality confusing, as it didn’t clearly show which namespaces contained the search environments. This was further complicated by all namespaces showing in a collapsed state, leading to misconceptions about search results. Additionally, the search bar placeholder text could be improved for more clarity. Some users mentioned that they did not frequently use or notice the search bar because they don’t have a lot of environments, which reduced the necessity for searching.
![conda-store-search](https://github.com/conda-incubator/conda-store/assets/98317216/24baac01-7f75-42ab-95f4-bb909e4877b5)

### Environment Page

The Environment Page serves as a central hub for managing conda environments. It comprises two major functionalities: creating and viewing environments.

* **Creating the environment**
Overall, users found the process of creating environments to be intuitive and straightforward. During testing, one user inquired about the purpose of the environment description field, suggesting its potential utility in aiding Search capabilities. This indicates a user interest in more integrated features that enhance usability. Additionally, there were several UI-related suggestions for improvement:
  * **Consistency and Clarity:** Users recommended enhancing the UI text and making the call-to-action buttons more consistent regarding placement.
  * **Interaction:** Some users were confused by the CTA (Call to Action) button’s functionality during interactions with package and channel selection widgets. They expected it to ‘submit’ their entries, whereas it added a new line of input. This suggests that the UI cues might be misleading.

  ![conda-store-interaction](https://github.com/conda-incubator/conda-store/assets/98317216/7e0e2267-6883-4853-bad4-11264262d215)

  * **Default Channel Visibility:** If no specific channel is provided by the user, conda-store defaults to the ‘defaults’ channel. However, this default setting is not visible in the UI, which could lead to confusion. Users also want to be able to set custom default channels.
  * **Autocomplete Features:** Users appreciated the autocomplete suggestions for packages and expressed a desire for similar functionality for channel selections.
  * **YAML vs. GUI:** While most users preferred using the GUI for input, there were instances where YAML was deemed more practical, such as when copying environments. A suggestion was made to set YAML as the default option for those who frequently use it. Some missed the YAML/GUI toggle because its placement was far from other relevant UI elements.
  ![conda-store-yaml](https://github.com/conda-incubator/conda-store/assets/98317216/0d8d047b-ba01-4698-972d-2ff04e960041)

* **Viewing an environment**
The environment view page mirrors the layout of the creation page but includes additional information such as environment status, packages installed as dependencies and logs. When reviewing newly created environments, users look at the Build Status to see whether the requested packages have been added. These are the key points discussed:
  * **Status Clarity:** Users suggested improvements to the ‘Status’ indicators to make them clearer.
  ![conda-store-building](https://github.com/conda-incubator/conda-store/assets/98317216/5c320ec1-f7ad-4b36-a4ca-4c06885a7b37) ![conda-store-failedbuild](https://github.com/conda-incubator/conda-store/assets/98317216/ccc3ec21-1da7-4b99-8641-bc368ddd57c5)

  * **Progress Indication:** While a progress indicator is present when an environment is being created, users said it was not very noticeable, indicating a need for better design and visibility.
  * **Dependency Management:** A dependency tree was proposed to understand package relationships and dependencies better.
  * **Resource Monitoring:** Users expressed a need to see real-time data on storage and CPU usage during environment builds.
  * **Admin Settings Awareness:** There was confusion regarding automatically added packages, such as the `ipykernel` package, which users attempted to remove without success. This confusion stemmed from a lack of notification that some packages are installed automatically due to admin settings.

### Admin features

The current Admin panel in conda-store-ui isn’t directly accessible via the general user interface and remains outdated compared to the primary UI. This detachment not only affects the usability but also hinders administrative efficiency. Our discussions about admin workflows and features were primarily theoretical, although some experienced users navigated to the admin panel independently to discuss its functionalities. Key findings include:

* **Dedicated Admin Panel:** A dedicated admin panel similar to those found in other development tools like GitHub was proposed. This would make admin features more accessible and easier to use, directly integrating elements such as storage management, security settings, and metadata management into the user interface.
* **Admin Controls:** Admin or superuser controls are essential for managing environments more effectively, including deleting stuck or inactive environments, moving environments to different namespaces, etc.
* **Storage and Utilization:** Admins require clear visibility into storage availability and resource utilization.
* **Security Features:** Users identified the need for robust security measures, including the ability to notify all users about compromised packages, uninstall packages from all environments, and set policies to prohibit specific packages in environments due to security concerns.
* **Metadata Management:** Users expressed the desire for additional metadata about environments and builds, such as creation dates, usage statistics, number of times a build was run, etc.
* **Compliance and Configuration:** Participants suggested the ability to set configuration options that align with organizational policies and standards.
* **Backup and Restore:** There is a significant demand for robust backup and restore capabilities to ensure data integrity and operational continuity in conda-store.
* **Team and User Management:** Improved transparency of privileges and the ability to manage user permissions effectively were highlighted as critical needs. This includes managing users and groups, possibly through an integrated solution like Keycloak.

### Namespaces

Namespaces are organizational units within conda-store, intended to manage and facilitate environment sharing. Namespaces produced mixed reactions from participants due to unclear UI indications and a lack of intuitive understanding. Here are the main points discussed:

* **Understanding and Clarity:** Although some users were familiar with the concept of namespaces and understood their utility from previous experiences or tinkering with the REST API, for many, the purpose and function of namespaces were not clear from the UI alone. The lack of clarity impacts usability and could potentially deter effective usage of this important feature.

* **Visibility and Access:** Users expressed uncertainty about who has access to each namespace and who an environment is shared with. They highlighted the need for more transparency about namespace details such as ownership, members, description, purpose, and permissions. Enhancing the visibility of information related to namespaces within the UI will help. This can be accomplished by implementing tooltips, detailed sidebars, or a dedicated management page.

* **User-Friendly Management:** There was a strong desire for an easier way to manage namespaces, including the ability to add people directly from the UI. A suggestion was made to include a button next to the namespace title for this purpose, which indicates a need for more direct and interactive management tools.

* **Security Perception:** Namespaces are appreciated for their ability to enhance security by segregating environments based on team or project needs.

### Profile Information

Participants expressed the need to view their profile information directly within conda-store. This section would ideally include details about their permissions, such as access to specific namespaces and admin rights, which are currently not visible or accessible to the user. A dedicated profile section should be implemented to display this user-specific information. These profile management features can be modeled after other developer platforms like GitHub to enhance user familiarity.

### Navigation

Feedback from users highlighted challenges with conda-store’s navigation system, particularly regarding the tab layout:

* **Tab Clarity:** Users reported that the current tab system does not display sufficient information. Navigating multiple environments open, especially if they have similar names but belong to different namespaces, can be difficult. This issue is exacerbated by the lack of URL usage, which could otherwise help users navigate directly to specific environments or retain their state. (**Note**: Tabs have since been removed to simplify the UI and to enable URL sharing [https://github.com/conda-incubator/conda-store-ui/pull/389](https://github.com/conda-incubator/conda-store-ui/pull/389))

### User Interface (UI)

Conda-store’s UI plays a pivotal role in user adoption and satisfaction. Feedback from users has highlighted several areas where UI enhancements could significantly improve usability and aesthetic appeal:

* **Aesthetics:** Some users find the conda-store interface modern and straightforward to use, appreciating its simplicity over CLIs. However, some users suggested a fresher, more elegant look and better consistency of UI elements to avoid confusion.
* **Time Zone:** Clarify whether the environment build times are displayed in local time to aid users operating across different time zones.
* **Status Indicators:** Users suggested icons next to each environment in the sidebar to indicate building, ready or failed states. Redefining the green bullet to more accurately reflect the status, avoiding assumptions that it indicates readiness.
  ![conda-store-statusindicators](https://github.com/conda-incubator/conda-store/assets/98317216/d4f889eb-87be-49a7-bd25-05c9ff57e297)
* **Favicon:** Ensure the conda-store favicon is displayed for better brand consistency.
* **Custom controls:** Some users also expected a custom conda-store-based menu to open on right-click instead of the standard browser/system menu, so this could be a potential avenue for providing extra support to users to complete tasks.
* **New Button:** Some users pointed out that the ‘+ New’ button to create new namespaces cluttered the UI and was repetitive. The tooltip text for the button can also be simplified.
![conda-store-newbutton](https://github.com/conda-incubator/conda-store/assets/98317216/d59ea9e1-12b7-4829-a44c-cb328f095636)

* **Unclear loading states:** On initial interaction with conda-store, users found it surprising to see the status of an environment as “building”, even though they didn’t initiate the build, which might indicate unclear status indicators or initial loading states.

### Logs and Artifacts

Users found the environment logs and artifacts very useful. However, there were issues with their presentation:

* **Artifacts Functionality:** The copy of the artifacts link (‘Show Artifacts’) led to mismatched expectations, as users expected it to display the artifacts rather than downloading them. The links’ functionality (displaying vs downloading the environment) also varied between browsers, adding to the confusion. Sometimes saving the artifacts page resulted in downloading HTML instead of the artifact, leading users to copy-pasting the artifact text.

* **User Familiarity with Artifacts:** Some users were unfamiliar with the types of artifacts available, leading to confusion about their purpose and use. Introducing tooltips or a detailed help section within the artifact widget that explains each type of artifact, its use cases, and how to use it effectively will enhance usability.
![conda-store-artifacts](https://github.com/conda-incubator/conda-store/assets/98317216/d52bbcd9-37c9-4f4b-b1ab-c4d44b9cb334)

* **Visibility:** Users noted that logs and artifacts are not prominently displayed and can be difficult to access, complicating troubleshooting efforts. They can be made more prominent on the environment page and improve access by repositioning them near the build status or highlighting them through UI design changes.

* **Enhanced Presentation:** A suggestion was made for a richer presentation of logs, including syntax highlighting, which can help users parse and understand the logs more efficiently.

* **Platform-Specific Artifacts:** There was interest in having artifacts that cater to specific platforms, such as offering both platform-dependent and independent versions. The types of artifacts can include platform-specific versions where applicable and ensure they are clearly labeled and described to help users choose the appropriate options for their needs.

* **Sharing Artifacts:** Users shared concerns about the security of sharing artifact files directly, with a preference for sharing lockfiles or customized YAML specs without sensitive data.

### Errors, Debugging and Documentation
Errors are inevitable parts of managing software environments. The study highlighted several areas where conda-store could improve its handling and presentation of errors to support users better.

* **Log Parsing:** Users frequently check logs and backend processes to diagnose issues with failed or stuck environments. However, they noted that parsing JSON-formatted logs can be complex and error-prone. Enhancing log readability by implementing prettyprint (`pprint`) for JSON-encoded logs, centralizing error messages to make them more accessible, and adding intuitive error parsing tools directly within the UI will aid troubleshooting.

* **Stuck Environments:** Some users encountered issues with environments that remain stuck in the building state, leading to frustration. To improve this, a mechanism can be developed to diagnose and resolve stuck environments more easily. Additionally, users can be provided with tools to force-stop environment builds or delete environments without navigating complex backend processes. Users also prefer to recreate broken environments rather than troubleshoot. This preference indicates a need for streamlined processes to recreate environments quickly, ensuring minimal disruption to workflow.

* **Documentation Visibility and Clarity:** While documentation was deemed helpful, users often have trouble locating it in the conda-store-ui and rely on external search engines due to a broken link within conda-store UI (**Note**: This has been fixed since). Also, the documentation can be expanded to include more detailed descriptions of API endpoints, common errors, and step-by-step troubleshooting guides to support users in resolving issues independently.

* **UI Improvements:** Feedback highlighted that the dependencies column on the environment page attempts to retrieve dependencies even when a build has failed. The UI logic should be adjusted so that dependency retrieval attempts are halted or clearly marked as problematic when an environment build fails.

### Local Environment Management

Participants provided extensive feedback on their use of local development tools and the potential integration of conda-store into their local workflows. The feedback highlighted a variety of preferences and challenges that users face when managing local environments.

* **Integration with Local Editors:** Users expressed a desire for a more seamless integration of conda-store with common local editors like VSCode and PyCharm. A potential avenue would be developing plugins or extensions for popular IDEs that allow users to manage conda-store environments directly within their development environments. This integration should support common tasks such as environment creation, activation, and switching.

* **Enhanced CLI Capabilities:** While some users appreciate the potential for a robust CLI interface for conda-store, there is concern about its overlap with existing tools like conda or mamba. The conda-store CLI could be differentiated by integrating unique features that complement existing tools rather than competing with them, focusing on features that enhance collaboration, such as sharing environments directly via CLI or integrating VCSs like GitHub more closely.

* **Local Use and Cloud Integration:** There is a noted preference for using conda-store primarily in team settings or with cloud integration, rather than for individual local use. It would be worthwhile to explore and support features that support a hybrid model where local environments can sync or integrate smoothly with cloud-based conda-store environments. This could include syncing environment configurations or facilitating the easy deployment of local changes to cloud environments.

* **Support for Docker and Containerization:** Users frequently rely on Docker for local development, particularly ensuring consistency between local and production environments. Conda-store could generate Docker images from Conda-store environments or enhance support for using Conda-store managed environments within Docker containers. Offering utilities to export environments directly as Docker image configuration could also be considered.

### Miscellaneous

This section gathers various insights and feedback from participants that, while not directly aligning with the core themes of our study, offer valuable perspectives on the broader user experience within conda-store and its associated platforms. Here, we explore these assorted points to ensure no potential enhancement area is missed.

* **Storage Visibility:** Users expressed a desire to see MinIO storage capacities directly within conda-store, suggesting this would enhance their ability to manage resources effectively.
* **Log Accessibility:** Improvements in the visibility of MinIO logs, such as enhanced port forwarding, were suggested to simplify troubleshooting and monitoring tasks.
* **Potential for Custom Deployments:** The adaptability of conda-store for custom High-Performance Computing (HPC) setups was noted, highlighting its potential in specialized computing environments where tailored configuration and resource management are crucial.
* **Live Log Updates:** During the environment build process, users inquired whether the log updates were live. Confirmation of live updates was seen as a positive feature that aids real-time monitoring.
* **Persistent State:** Concerns were raised about losing the site's state upon reloading, which could disrupt user activities and tracking of environment setups.

## Informative Insights

This section compiles insights that might not be immediately actionable but provide valuable context about user behavior, preferences and the broader implications of how conda-store is used within various workflows. These insights contribute to a deeper understanding of our users’ needs, aiding in long-term strategic planning and feature development.

### User Behavior and Workflows

* Users favor using conda/mamba directly in the terminal to manage their environments, citing familiarity and ease of use. Some developers also use `venv` for project-specific setups. This highlights the diversity in tool preferences and the importance of supporting multiple workflows within conda-store.
* Homebrew emerged as a common tool, particularly when specific libraries are unavailable on PyPI. This suggests that conda-store could benefit from integration or improving support for non-Python dependencies to enhance its utility.

### Cloud and Local Environment Dynamics

* The use of Docker for both local and cloud environments illustrates the need for seamless transitions between these platforms. Users appreciated tools like VSCode's devcontainers extension for replicating cloud containers locally.
* A hybrid model that connects the CLI with cloud-based environments could enhance conda-store's appeal, suggesting potential areas for integration.

### Existing Mental Models

During the study, users frequently referenced other platforms, such as GitHub and Google Docs, when discussing conda-store features. This suggests the strong influence of existing mental models and design patterns formed by these widely-used platforms. We can leverage this cross-platform familiarity to simplify the learning curve and enhance user comfort.

### Namespace Naming Conventions

Namespace names significantly influence their assumptions about the scope of access to these namespaces. For example, a namespace named ‘global’ might be presumed to have more comprehensive access than it does, whereas a name like ‘admin’ might imply administrative privileges. As such, it is essential to carefully name the namespaces to ensure that the name aligns with the intent of the namespace.

## Conclusion

The findings in this report provide a comprehensive overview of conda-store’s current user experience and highlight strengths and areas for improvement that could significantly enhance functionality and user satisfaction.
We have documented key user behaviors, preferences, and challenges that impact user interaction with Conda Store. Moreover, the informative insights have provided us with a deeper understanding of our users' underlying needs and expectations, which is essential for guiding future enhancements.

As we move forward, it is vital to consider these insights in our ongoing development efforts to ensure that conda-store remains an intuitive and integral part of our users’ data science and development workflows. We thank all the participants and team members for their invaluable contributions and look forward to implementing improvements to make conda-store more user-friendly.

## Appendix: Research Board

To foster a deeper understanding of our research process, we have made our research board publicly available. This interactive board provides a visual representation of the user feedback, our analysis and the thematic organization of data that informed the insights presented in this report.

### Accessing the board

The dashboard can be accessed via the following link: [User Research Data](https://www.figma.com/file/SJqCXfRuwHMscGFGp0G3IU/User-Research-Data?type=whiteboard&node-id=0%3A1&t=d3cQMJOqVTjwPegu-1). No special permissions or software is required beyond access to the internet.

### Layout

The research data is organized into two main sections on the board:

* **User interview data:** This section contains a condensed version of notes from all participant interviews, organized by interview sections. Each participant is represented by a different color. It is populated with sticky notes containing direct quotes from participants, observational notes, and our analytical insights.
* **Affinity Diagram:** We have sorted all the notes and organized them into common themes and patterns to generate insights. This section visualizes how individual pieces of feedback interconnect and contribute to our broader understanding of user experiences.

Providing access to this visual collaboration board allows stakeholders and the broader community to see the raw data and the thought processes behind our conclusions.

## References

1. [UX Research & Design - pip documentation v24.1.dev1](https://pip.pypa.io/en/latest/ux-research-design/)
2. [JupyterLab User Testing](https://github.com/Quansight-Labs/JupyterLab-user-testing/blob/main/results/user-testing-results.md)
3. [UX Research at GitLab](https://handbook.gitlab.com/handbook/product/ux/ux-research/)
