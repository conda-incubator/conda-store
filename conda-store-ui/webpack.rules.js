/*
 * Copyright (c) 2020, Max Klein
 *
 * This file is part of the tree-finder library, distributed under the terms of
 * the BSD 3 Clause license. The full license can be found in the LICENSE file.
 */
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const path = require("path");
const TerserPlugin = require("terser-webpack-plugin");

const cssLoader = () => {return {
  loader: "css-loader",
  options: {
    importLoaders: 1,
    import: true,
    modules: {
      localIdentName: "[local]", //"[path][name]__[local]--[hash:base64:5]",
      // compileType: "module",
      // mode: "local",
      // auto: true,
      // exportGlobals: true,
      // localIdentContext: path.resolve(__dirname, "src"),
      // localIdentHashPrefix: "my-custom-hash",
      // namedExport: true,
      // exportLocalsConvention: "camelCase",
      // exportOnlyLocals: false,
    },
  },
};}

// const postCssLoader = () => {return {
//   loader: "postcss-loader",
//   ...(process.env.NODE_ENV === "production") && {options: {
//     postcssOptions: {
//       minimize: true,
//       plugins: [
//         cssnano({
//           preset: "lite"
//         }),
//       ],
//     },
//   }},
// };}

// load bitmap image rules
const bitmapRules = [
  {
    test: /\.(jpg|png|gif)$/,
    use: "file-loader"
  },
];

// load dependency source maps
const dependencySrcMapRules = [
  {
    test: /\.js$/,
    use: "source-map-loader",
    enforce: "pre",
    exclude: /node_modules/,
  },
  {test: /\.js.map$/, use: "file-loader"},
];

// rules to cover all of pure/modules css/less
const stylingRules = [
  {
    test: /\.module\.css$/,
    use: [
      cssLoader(),
    ],
  },
  {
    test: /(?<!\.module)\.css$/,
    use: [
      // "style-loader",
      MiniCssExtractPlugin.loader,
      cssLoader(),
    ],
  },
  {
    test: /\.module\.less$/,
    use: [
      cssLoader(),
      // "postcss-loader",
      "less-loader",
    ],
  },
  {
    test: /(?<!\.module)\.less$/,
    use: [
      // "style-loader",
      MiniCssExtractPlugin.loader,
      cssLoader(),
      // "postcss-loader",
      "less-loader",
    ],
  },
];

// load svg via css url() rules
const svgUrlRules = [
  {
    test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
    use: {
      loader: "svg-url-loader",
      options: {encoding: "none", limit: 10000},
    },
  },
];

const tsRules = [
  {
    test: /\.tsx?$/,
    exclude: /node_modules/,
    use: {
      loader: "ts-loader",
      options: {
        transpileOnly: false, // Set to true if you are using fork-ts-checker-webpack-plugin
        projectReferences: true
      },
    },
  },
]

const getContext = (dir) => { return {
  // context: path.resolve(dir),
};}

const getOptimization = () => { return {
  minimizer: [
    // "...",
    new TerserPlugin({
      // turn off license gen
      terserOptions: {
        format: {
          comments: false,
        },
      },
      // turn off license gen
      extractComments: false,
    }),
    new CssMinimizerPlugin(),
  ],
};}

const getResolve = (dir) => { return {
  modules: [
    "node_modules",
    path.resolve(dir),
  ],
  extensions: [".tsx", ".ts", ".jsx", ".js", ".less", ".css"],
};}

module.exports = {
  bitmapRules,
  dependencySrcMapRules,
  stylingRules,
  svgUrlRules,
  tsRules,
  getContext,
  getOptimization,
  getResolve,
};
