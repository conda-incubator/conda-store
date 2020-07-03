<template>
<v-container class="fill-height" fluid>
<p v-if="$fetchState.pending">Fetching posts...</p>
<p v-else-if="$fetchState.error">Error while fetching posts: {{ $fetchState.error.message }}</p>
<v-row v-else v-for="environment of environments" v-bind:key="environment.name">
  <v-card class="mx-auto" max-width="344" outlined>
    <v-list-item-content>
      <v-list-item-title class="headline mb-1">{{ environment.name }}</v-list-item-title>
      <v-list-item-subtitle>Greyhound divisely hello coldly fonwderfully</v-list-item-subtitle>
    </v-list-item-content>

    <v-card-actions>
      <v-btn v-bind:href="'/specification/' + environment.specification_id + '/'" text>View Spec</v-btn>
      <v-btn v-bind:href="'/build/' + environment.build_id + '/'" text>View Build</v-btn>
    </v-card-actions>
  </v-card>
</v-row>
</v-container>
</template>

<script>
export default {
  layout: 'default',

  props: {
    source: String,
  },

  data() {
    return {
      dialog: false,
      drawer: null,
      environments: []
    };
  },

  async fetch () {
    this.environments = await this.$http.$get('http://localhost:5000/api/v1/environment/')
  },

  components: {
  },

  methods: {
    refresh() {
      this.$fetch();
    }
  }
};
</script>
