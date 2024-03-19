// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "conda-store",
  tagline: "Data science environments for collaboration",
  favicon: "img/favicon.ico",

  // Set production url
  url: "https://conda.store",
  // Set /<baseUrl>/ pathname under which your site is served
  baseUrl: "/",

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  // Add Plausible snippet as script
  scripts: [
    {
      src: "https://plausible.io/js/script.js",
      defer: true,
      "data-domain": "conda.store",
    }
  ],

  // Install plugins, then add here
  plugins: [
    require.resolve("docusaurus-lunr-search"),
    [
      "content-docs",
      /** @type {import('@docusaurus/plugin-content-docs').Options} */
      ({
        id: "community",
        path: "community",
        routeBasePath: "/community",
        breadcrumbs: true,
      }),
    ],
    [
      "content-docs",
      /** @type {import('@docusaurus/plugin-content-docs').Options} */
      ({
        id: "conda-store-ui",
        path: "conda-store-ui",
        routeBasePath: "/conda-store-ui",
        breadcrumbs: true,
      }),
    ],
    [
      "content-docs",
      /** @type {import('@docusaurus/plugin-content-docs').Options} */
      ({
        id: "jupyterlab-conda-store",
        path: "jupyterlab-conda-store",
        routeBasePath: "/jupyterlab-conda-store",
        breadcrumbs: true,
      }),
    ],
  ],

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          id: "conda-store",
          path: "conda-store",
          routeBasePath: "conda-store",
          editUrl:
            "https://github.com/conda-incubator/conda-store/tree/main/docusaurus-docs",
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: "Home",
        logo: {
          alt: "conda-store logo",
          src: "img/logo.svg",
        },
        items: [
          {
            label: "conda-store",
            to: "conda-store/introduction",
            position: "left",
          },
          {
            label: "conda-store UI",
            to: "conda-store-ui/introduction",
            position: "left",
          },
          {
            label: "JupyterLab extension",
            to: "jupyterlab-conda-store/introduction",
            position: "left",
          },
          {
            label: "Community",
            to: "community/introduction",
            position: "left",
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
            ],
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            items: [
              {
                label: "Code of Conduct",
                href: "https://github.com/conda-incubator/governance/blob/main/CODE_OF_CONDUCT.md",
              },
              {
                label: "Governance",
                href: "https://github.com/conda-incubator/governance/tree/main",
              },
              {
                label: "Support",
                to: "community/introduction#support",
              },
            ],
          },
          {
            items: [
              {
                label: "Brand guidelines",
                to: "community/design",
              },
              {
                label: "Contribute",
                to: "community/contribute/",
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
      announcementBar: {
        id: 'WIP',
        content:
          '⚠️ We are in the process of revamping our docs, some pages may be incomplete or inaccurate. ⚠️',
        isCloseable: false,
      },
      docs: {
        sidebar: {
          hideable: true,
        },
      },
    }),
};

module.exports = config;
