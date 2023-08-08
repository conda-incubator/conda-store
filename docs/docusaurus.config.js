// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'conda-store',
  tagline: 'Data science environment for collaboration',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://conda.store',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // // GitHub pages deployment config.
  // // If you aren't using GitHub pages, you don't need these.
  // organizationName: 'facebook', // Usually your GitHub org/user name.
  // projectName: 'docusaurus', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/conda-incubator/conda-store/tree/main/docs',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'conda-store',
        logo: {
          alt: 'conda-store logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'right',
            label: 'Tutorial',
          },
          {
            href: 'https://github.com/conda-incubator/conda-store',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Documentation',
            items: [
              {
                label: 'TODO',
                to: '/',
              },
            ],
          },
          {
            title: 'Repositories',
            items: [
              {
                label: 'conda-store',
                href: 'https://github.com/conda-incubator/conda-store',
              },
              {
                label: 'conda-store-ui',
                href: 'https://github.com/conda-incubator/conda-store-ui',
              },
              {
                label: 'jupyterlab-conda-store',
                href: 'https://github.com/conda-incubator/jupyterlab-conda-store',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'TODO',
                to: '/',
              },
              {
                label: 'TODO',
                href: '/',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} | Quansight`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
