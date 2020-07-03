export default {
  head: {
    link: [
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css?family=Montserrat+Alternates' },
      { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css?family=Lato'},
      { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/npm/@mdi/font@5.x/css/materialdesignicons.min.css'}
    ]
  },
  modules: [
    '@nuxt/http',
  ],
  buildModules: [
    '@nuxtjs/vuetify',
    '@nuxt/typescript-build',
  ],
  plugins: [
     { src: '~/plugins/vuetify', mode: 'client' }
  ],
  generate: {},
  vuetify: {
    customVariables: ['~/assets/variables.scss'],
    defaultAssets: false,
    treeShake: true
  },
};
