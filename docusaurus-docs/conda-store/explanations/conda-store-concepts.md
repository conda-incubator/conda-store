---
sidebar_position: 2
description: Overview of some conda-store concepts
---

# conda-store concepts

conda-store was developed with two key goals in mind: reliable reproducibility of environments, and features for collaboratively using an environment.
This page describes how conda-store achieves these goals.

## Reproducibility

In the [conda-based environment creation process][conda-concepts-env-creation], there are two areas where runtime reproducibility is improved through conda-store:

* Auto-tracking when an `environment.yaml` (which is created and updated manually) file has changes. This can be easily tracked by taking a sha256 of the file, which is what conda-store does but sorts the dependencies to make sure it has a way of not triggering a rebuild if the order of two packages changes in the dependencies list.
* In step (2) `repodata.json` is updated regularly. When conda solves for a user's environment it tries to use the latest version of each package. Since `repodata.json` could be updated the very next minute, the same solve for the same
`environment.yaml` file can result in different solves. To enable reproducibility, conda-store auto-generates certain artifacts like lockfiles and tarballs that capture the actual versions of packages and can be used reliably re-create the same environment. Learn more about them in the [artifacts documentation][artifacts].

## Namespaces

Namespaces are how conda-store manages environment access for groups of users.

Every environment in conda-store is a part of a "namespace", and is displayed in the format: `<namespace>/<environment-name>`.

Users can have access to view/edit/manage certain "namespaces", which means they have that level of permission for all the environments in that namespace.
This allows a large team or organization to have isolated spaces for environment sharing between smaller groups.

Each individual user has a separate namespace, which has the same name as their username (used while logging in). All environments in this namespace are private to the individual.

A user can be a part of several other "shared" namespaces, and based on the level of access given to them, they can view and use the environment, edit the environment, or delete it all together. The permission are dictated by "role mappings".

## Role mappings

By default, the following roles are available in conda-store. All users are in one of these groups and have corresponding permissions.

- **Viewer:** Read-only permissions for environments in selected namespaces
- **Editor (previously called Developer):** Permission to read, create, and update environments in specific namespaces
- **Admin:** Permission to read, create, update, and delete environments in all existing namespaces

<details>
<summary> Specific role-mappings: </summary>

```yaml
    _viewer_permissions = {
        schema.Permissions.ENVIRONMENT_READ,
        schema.Permissions.NAMESPACE_READ,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_READ,
    }
    _editor_permissions = {
        schema.Permissions.BUILD_CANCEL,
        schema.Permissions.ENVIRONMENT_CREATE,
        schema.Permissions.ENVIRONMENT_READ,
        schema.Permissions.ENVIRONMENT_UPDATE,
        schema.Permissions.ENVIRONMENT_SOLVE,
        schema.Permissions.NAMESPACE_READ,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_READ,
        schema.Permissions.SETTING_READ,
    }
    _admin_permissions = {
        schema.Permissions.BUILD_DELETE,
        schema.Permissions.BUILD_CANCEL,
        schema.Permissions.ENVIRONMENT_CREATE,
        schema.Permissions.ENVIRONMENT_DELETE,
        schema.Permissions.ENVIRONMENT_READ,
        schema.Permissions.ENVIRONMENT_UPDATE,
        schema.Permissions.ENVIRONMENT_SOLVE,
        schema.Permissions.NAMESPACE_CREATE,
        schema.Permissions.NAMESPACE_DELETE,
        schema.Permissions.NAMESPACE_READ,
        schema.Permissions.NAMESPACE_UPDATE,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_CREATE,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_READ,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_UPDATE,
        schema.Permissions.NAMESPACE_ROLE_MAPPING_DELETE,
        schema.Permissions.SETTING_READ,
        schema.Permissions.SETTING_UPDATE,
    }
```

</details>

## Environment versions/builds

conda-store always re-builds an environment from scratch when edits are detected, which is required for ensuring truly reproducible environments.
Version control is very useful in any collaborative setting, and environments are no exception.
Hence, conda-store keeps older versions (also called "builds") of the environment for reference, and allows you to select and use different (previous or newer) versions when needed. conda-store-ui also provides a graphical way to [switch between versions][conda-store-ui-version-control].

:::tip
Internally, conda-store handles versions with ✨ symlinking magic ✨, where the environment name points to different environments corresponding to versions.
:::

<!-- Internal links -->
[conda-concepts-env-creation]: conda-concepts#environment-creation
[artifacts]: artifacts
[conda-store-ui-version-control]: ../../conda-store-ui/tutorials/version-control
