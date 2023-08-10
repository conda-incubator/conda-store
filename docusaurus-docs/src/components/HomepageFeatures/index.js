import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

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

export default function HomepageFeatures() {
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
