/*
 * Copyright (c) 2020, Max Klein
 *
 * This file is part of the tree-finder library, distributed under the terms of
 * the BSD 3 Clause license. The full license can be found in the LICENSE file.
 */
const HtmlWebpackPlugin = require("html-webpack-plugin");
const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

// const TsconfigPathsPlugin = require("tsconfig-paths-webpack-plugin");
// To improve build times for large projects enable fork-ts-checker-webpack-plugin
// const ForkTsCheckerWebpackPlugin = require("fork-ts-checker-webpack-plugin");

const { dependencySrcMapRules, stylingRules, svgUrlRules, getContext, getOptimization, getResolve, tsRules } = require("./webpack.rules");

const isProd = process.env.NODE_ENV === "production";

const simpleExampleConfig = {
  devtool: "source-map",
  entry: "src/index.tsx",
  watch: false,
  ...getContext(__dirname),

  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "[name].js"
  },

  module: {
    rules: [
      ...dependencySrcMapRules,
      ...stylingRules,
      ...svgUrlRules,
      ...tsRules,
    ],
  },

  resolve: {
    ...getResolve(__dirname),
  },

  // devServer: {
  //   // contentBase: [path.join(__dirname, "examples"), path.join(__dirname, ".")],
  //   // inline: false,
  //   // publicPath: "/dist/",

  //   // dev-server writes to disk instead of keeping the bundle in memory
  //   writeToDisk: true,
  // },

  plugins: [
    new HtmlWebpackPlugin({
      title: "simple tree-finder example"
    }),
    new MiniCssExtractPlugin(),
  ],

  mode: isProd ? "production": "development",

  optimization: {
    minimize: isProd,
    ...isProd && getOptimization(),
  },
}

module.exports = [
  simpleExampleConfig,
];
