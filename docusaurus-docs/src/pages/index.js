import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import CondaStoreLogo from '@site/static/img/logo.svg';
import useBaseUrl, {useBaseUrlUtils} from '@docusaurus/useBaseUrl';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--secondary', styles.heroBanner)}>
      <div className="container">
        <CondaStoreLogo
          alt={siteConfig.title}
          className={clsx(styles.logo, 'margin-vert--md')}
        />
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--primary button--lg"
            to="/docs/get-started/">
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

function HomepageVideo() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <img
          src={useBaseUrl('/img/conda-store-ui.webp')}
          className={styles.video}
        />
        <br></br>
      </div>
    </header>
  );
}

const FeatureList = [
  {
    title: '🧶 Flexible',
    description: (
      <>
        Create and update environments quickly using a graphical UI or a YAML editor.
        All environments are automatically version-controlled, and available for use.
      </>
    ),
  },
  {
    title: '📋 Reproducible',
    description: (
      <>
        Share environments effortlessly through the auto-generated artifacts: lockfile, docker image, YAML file, or tarball.
        Exact versions of all packages and their dependencies are pinned in these artifacts.
      </>
    ),
  },
  {
    title: '⚖️ Governance',
    description: (
      <>
        Access admin-approved packages and channels, and request new ones when needed.
        Admins have role-based access management, to allow users to share environments across (and only with) their team.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center padding-horiz--md">
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
    </div>
  );
}

function HomepageFeatures() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title}`}
      description="Description will go into a meta tag in <head />">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <HomepageVideo />
      </main>
    </Layout>
  );
}
