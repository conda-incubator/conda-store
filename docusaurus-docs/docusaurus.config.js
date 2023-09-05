// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'conda-store',
  tagline: 'Data science environments, for collaboration',
  favicon: 'img/favicon.ico',

  // Set production url
  url: 'https://conda.store',
  // Set /<baseUrl>/ pathname under which your site is served
  baseUrl: '/',

  // GitHub pages deployment config - Remove after deployment mechanism is decided.
  // organizationName: 'conda-incubator',
  // projectName: 'conda-store',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  // Install plugins, then add here
  plugins: [
    require.resolve("docusaurus-lunr-search"),
    [
      "content-docs",
      /** @type {import('@docusaurus/plugin-content-docs').Options} */
      ({
        id: 'community',
        path: 'community',
        routeBasePath: '/community',
        breadcrumbs: true,
      }),
    ],
    [
      "content-docs",
      /** @type {import('@docusaurus/plugin-content-docs').Options} */
      ({
        id: 'conda-store-ui',
        path: 'conda-store-ui',
        routeBasePath: '/conda-store-ui',
        breadcrumbs: true,
      }),
    ],
  ],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          id: 'conda-store',
          path: 'conda-store',
          routeBasePath: 'conda-store',
          editUrl:
            'https://github.com/conda-incubator/conda-store/',
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
      navbar: {
        title: 'Home',
        logo: {
          alt: 'conda-store logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            label: 'conda-store',
            to: 'conda-store/intro',
            position: 'left',
          },
          {
            label: 'conda-store UI',
            to: 'conda-store-ui/intro',
            position: 'left',
          },
          {
            label: 'JupyterLab extension',
            to: 'conda-store-ui/intro',
            position: 'left',
          },
          {
            label: 'Community',
            to: 'community/intro',
            position: 'left',
          },
          {
            label: "GitHub",
            position: "right",
            items: [
              {
                label: "conda-store",
                href: "https://github.com/conda-incubator/conda-store",
              },
              {
                label: "conda-store-ui",
                href: "https://github.com/conda-incubator/conda-store-ui",
              },
              {
                label: "jupyterlab-conda-store",
                href: "https://github.com/conda-incubator/jupyterlab-conda-store",
              },
            ]
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            items: [
              {
                label: 'Code of Conduct',
                href: 'https://github.com/conda-incubator/governance/blob/main/CODE_OF_CONDUCT.md',
              },
              {
                label: 'Governance',
                to: 'docs/community/governance',
              },
              {
                label: 'Support',
                href: 'docs/community/support',
              },
            ],
          },
          {
            items: [
              {
                label: 'Brand guidelines',
                to: 'docs/community/design',
              },
              {
                label: 'Changelog',
                to: 'docs/community/design',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} | Made with 💚 by conda-store development team`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
