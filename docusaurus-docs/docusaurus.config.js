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

  // Install plugings, then add here
  plugins: [
    require.resolve("docusaurus-lunr-search"),
  ],

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
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
      navbar: {
        title: 'conda-store',
        logo: {
          alt: 'conda-store logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            label: 'Docs',
            to: 'docs/intro',
            position: 'right',
          },
          {
            label: 'Community',
            to: 'docs/community',
            position: 'right',
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
