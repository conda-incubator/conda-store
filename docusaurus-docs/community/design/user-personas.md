---
description: Describes current and potential conda-store users`
---

# User groups and personas

The personas used for informing user research studies and future improvements to conda-store.

## User groups 🏘️

At a high-level, there are two key user groups:

- **General user:** Create, edit, use environments for their day-to-day work
- **Admin user:** In addition to the general use-case mentioned above, admin users also **setup** conda-store for their team, create various namespaces, add/update users and their permissions, set default packages/versions for their team, etc.

## User personas 🙋🏽‍♀️

### User: Alia

| Role | Reports to | User group|
|-------|-------|-------|
Staff Data Scientist | Head of Data Science | General |

#### User story

I want to quickly create a stable and reproducible environment for analyzing data and creating dashboards that I can share with my team to verify and build on my work.

#### Tools they need to do their job

- Libraries - data reader/writer (arrow), data processing (pandas), numerical computing (NumPy), ML (XGboost / PyTorch), Data Visualization and dashboarding (Matplotlib / Streamlit), job schedulers (Airflow)
- IDE - JupyterLab/Notebook (hence, extensions)
- Platform - Local computer, organization's JupyterHub on Cloud platform (potentially Nebari)
- Miscellaneous - Git, GitHub, conda

#### Journey with conda-store

- Discovery:
    - Team already uses it
    - Team leader sets it up for everyone
- Onboarding:
    - A team member gives them a walkthrough
    - Documented tutorials
    - Intuitiveness of the UI
- General Use:
    - Environment creation from GUI, YAML, Lockfile
    - Version control
    - Using the environment in Jupyter Notebook (local / cloud)
    - Ability to use any package/version out there
    - Access to special conda channels
    - Environments for GPU-powered data analysis and modelling
- Collaboration:
    - Share environment with colleagues with a URL (Part of 1-2 shared namespaces)
    - Fork/Copy environments between namespaces
    - Download artifacts like docker images for use in other (prod?) machines
- Troubleshooting:
    - Understand errors through the error message displayed
    - Look at conda-store’s documentation & GH issues/discussions, search for the error
    - Contact team-members or internal support
    - Open an issue/discussion on GitHub

#### Pain points or biggest challenges

- Environments need to be compliant with company standards, for example, approved conda channels and approved package versions
- Build environments with libraries from internal mirrors
- Ensure stable environments that are quickly reproducible by colleagues and can be used by Ops teams for deployment (often on similar machines and operating-systems)

#### Core needs

- Intuitive and fast environment creation & sharing
- Promise of stability, security, and compliance

### User: Dani

| Role | Reports to | User group|
|-------|-------|-------|
Research Scientist and Coordinator | PI | Admin |

#### User story

As a research coordinator, I manage the logistics and admin-tasks of multiple research projects, ensuring that the tools/dependencies used are accessible, reproducible and standardized across projects.

#### Tools they need to do their job

In addition to Alia’s tools, cloud or High Performance Computing (HPC) tools (for example, Google Cloud Platform's web interface and CLI tools.)

#### Journey with conda-store

- Discovery:
    - OSS Community, conferences, peer suggestions
    - Tries out conda-store locally and finds it useful
- Onboarding:
    - Documentation, self-exploration
- General Use:
    - Setup and deployment using the conda-store docs, within current Lab infra
    - Add team members, create default namespaces and environments, referring to the documentation
    - Onboard team members to the tool with demonstrations
    - Track and limit resource utilization
- Collaboration:
    - Uses environments created by colleagues to verify their work
- Troubleshooting:
    - Documentation, issue tracker (reach out to the conda-store dev team)

#### Pain points or biggest challenges

- Facilitating reproducible environment sharing within teams by setting up relevant infrastructure
- Managing and supporting team-members (like Alia)
- May not have DevOps expertise to setup and manage conda-store for the team
- Reliable environments with guardrails for people new to software development principles (example, not comfortable with YAML spec)
- Sharing environments widely, considering different operating systems and infrastructures.

#### Core needs

- Setting up & managing packaging infrastructure for the lab, potentially on an HPC system as as non-devops professional
- Visibility into groups’ package requirements and resources used
- Sharing environments widely, considering different operating systems and infrastructures

### User: Emma

| Role | Reports to | User group|
|-------|-------|-------|
Freelance data scientist | - | General |

#### User story

I want to manage my local conda environments, so that I can be more efficient in my day-to-day work.

#### Tools they need to do their job

Same as Alia, but primarily for individual work.

#### Journey with conda-store

- Discovery
    - Internet, community spaces, conferences
- Onboarding
    - Documentation
- General Use
    - Install and setup conda-store locally
    - Create environments in my personal namespace
    - Use the environments in Jupyter Notebooks
- Collaboration
    - Share relevant artifacts (e.g., Lockfiles) with clients
- Troubleshooting
    - Documentation, issue tracker

#### Pain points or biggest challenges

- Sometimes conda environments break while working, adding overhead
- Environments are not always reproducible when I share them
- Using the environment-creation artifacts  shared with the application should be as easy as possible (think installers/executables)

#### Core needs

- Reliable and quick environment creation that follow conda best practices
- Creating reproducible environments that I can share with clients later

### User: Ginny

| Role | Reports to | User group|
|-------|-------|-------|
Head of Data Science | CTO | Admin |

#### User story

I need to oversee the implementation, management, and adoption of tools like conda-store to ensure our teams’ workflows are efficient and our data science initiatives align with business goals.

#### Tools they need to do their job

The IDEs, platform, miscellaneous tools used by Alia, primarily for reviews and tracking work.

#### Journey with conda-store

- Discovery:
    - Team lead pitches it
    - Community spaces
- Onboarding:
    - Team lead/member who sets up conda-store helps them onboard
    - Documentation
- General Use:
    - Review resource utilization
    - Review package and channel requests

#### Pain points or biggest challenges

- Strategic alignment with organization goals
- Tool adoption across teams

#### Core needs

- Oversight on tool efficiency and team productivity
- Enablement of various teams
