// Copyright (c) conda-store development team. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

import Link from "@docusaurus/Link";
import useBaseUrl, { useBaseUrlUtils } from "@docusaurus/useBaseUrl";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import CondaStoreLogo from "@site/static/img/logo.svg";
import Layout from "@theme/Layout";
import clsx from "clsx";
import React from "react";

import styles from "./index.module.css";

function HomepageHeader() {
	const { siteConfig } = useDocusaurusContext();
	return (
		<header className={clsx("hero hero--secondary", styles.heroBanner)}>
			<div className="container">
				<CondaStoreLogo
					alt={siteConfig.title}
					className={clsx(styles.logo, "margin-vert--md")}
				/>
				<h1 className="hero__title">{siteConfig.title}</h1>
				<p className="hero__subtitle">{siteConfig.tagline}</p>
				<div className={styles.buttons}>
					<Link
						className="button button--primary button--lg"
						to="/community/introduction"
					>
						Learn more
					</Link>
				</div>
			</div>
		</header>
	);
}

const ProjectsList = [
	{
		title: "📦 conda-store",
		link: "/conda-store/introduction",
		description: (
			<>Core library that provides key features through a REST API</>
		),
	},
	{
		title: "💻 conda-store UI",
		link: "/conda-store-ui/introduction",
		description: (
			<>
				User-friendly frontend to access conda-store features in a React
				application
			</>
		),
	},
	{
		title: "🪐 JupyterLab extension",
		link: "/jupyterlab-conda-store/introduction",
		description: (
			<>JupyterLab interface that provides conda-store-ui frontend</>
		),
	},
];

const FeatureList = [
	{
		title: "🧶 Flexible & Intuitive UI",
		description: (
			<>
				Create, update, and manage environments using a user-friendly graphical
				UI or YAML editor, available from within JupyterLab or standalone.
			</>
		),
	},
	{
		title: "📋 Reproducible Artifacts",
		description: (
			<>
				Share fully-reproducible environments with auto-generated artifacts like
				lockfiles, YAML files, and tarballs.
			</>
		),
	},
	{
		title: "🌱 Free and Open Source",
		description: (
			<>
				A part of the conda (incubator) community, conda-store tools are built
				using OSS libraries and developed under a permissive license.
			</>
		),
	},
	{
		title: "🔀 Version Controlled",
		description: (
			<>
				Reference or use previous versions or artifacts of your environments
				with automatic version-control.
			</>
		),
	},
	{
		title: "⚖️ Role-based Access Control",
		description: (
			<>
				Admins can manage users or teams and approve packages and channels to
				maintain organizational standards.
			</>
		),
	},
	{
		title: "💻 System Agnostic",
		description: (
			<>
				Run conda-store on any major cloud provider, on-prem, or on local
				machines.
			</>
		),
	},
];

function Project({ Svg, title, description, link }) {
	return (
		<div className={clsx("col col--4")}>
			<div className="text--center padding--md">
				<h2>{title}</h2>
				<p>{description}</p>
				<a href={link}> Learn more →</a>
			</div>
		</div>
	);
}

function HomepageProjects() {
	const { siteConfig } = useDocusaurusContext();
	return (
		<section className={styles.features}>
			<div className="container">
				<div className="row">
					{ProjectsList.map((props, idx) => (
						<Project key={props.link} {...props} />
					))}
				</div>
			</div>
		</section>
	);
}

function Feature({ Svg, title, description }) {
	return (
		<div className={clsx("col col--4")}>
			<div className="text--center padding--md">
				<h3>{title}</h3>
				<p>{description}</p>
			</div>
		</div>
	);
}

function HomepageFeatures() {
	const { siteConfig } = useDocusaurusContext();
	return (
		<section className={clsx(styles.features, "hero hero--primary")}>
			<div className="container">
				<div className="row">
					{FeatureList.map((props, idx) => (
						<Feature key={props.title} {...props} />
					))}
				</div>
			</div>
		</section>
	);
}

function HomepageVideo() {
	const { siteConfig } = useDocusaurusContext();
	return (
		<header className={clsx(styles.heroBanner)}>
			<div className="container">
				<img
					src={useBaseUrl("/img/conda-store-ui.webp")}
					className={styles.video}
					alt="An animated webp showing the conda-store UI and some of its major features."
				/>
				<br />
			</div>
		</header>
	);
}

export default function Home() {
	const { siteConfig } = useDocusaurusContext();
	return (
		<Layout title="Homepage" description={`${siteConfig.tagline}`}>
			<HomepageHeader />
			<main>
				<HomepageProjects />
				<HomepageFeatures />
				<HomepageVideo />
			</main>
		</Layout>
	);
}
