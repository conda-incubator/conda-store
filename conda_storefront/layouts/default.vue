<template>
<v-app>
  <v-navigation-drawer v-model="drawer" app>
    <v-list dense>
      <v-list-item link>
        <v-list-item-action>
          <v-icon>mdi-home</v-icon>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>Environments</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-list-item link>
        <v-list-item-action>
          <v-icon>mdi-email</v-icon>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>Specifications</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-list-item link>
        <v-list-item-action>
          <v-icon>mdi-email</v-icon>
        </v-list-item-action>
        <v-list-item-content>
          <v-list-item-title>Builds</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-navigation-drawer>

  <v-app-bar app color="indigo" dark>
    <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
    <v-toolbar-title>Conda-Store</v-toolbar-title>
  </v-app-bar>

  <v-main>
    <nuxt/>
  </v-main>

  <v-btn bottom color="pink" dark fab fixed right @click="dialog = !dialog">
    <v-icon>mdi-plus</v-icon>
  </v-btn>

  <v-dialog v-model="dialog" width="800px">
    <v-card>
      <v-card-title class="grey darken-2">
        Create Environment
      </v-card-title>
      <v-container>
        <v-row class="mx-2">
          <v-text-field placeholder="Environment Name"></v-text-field>
        </v-row>

        <v-row class="mx-2">
          <v-combobox chips clearable label="Channels" multiple solo>
            <template v-slot:selection="{ attrs, item, select, selected }">
              <v-chip v-bind="attrs" :input-value="selected" close @click="select" @click:close="remove(item)">
                <strong>{{ item }}</strong>&nbsp;
              </v-chip>
            </template>
          </v-combobox>
        </v-row>

        <v-row class="mx-2">
          <v-combobox chips clearable label="Dependencies" multiple solo>
            <template v-slot:selection="{ attrs, item, select, selected }">
              <v-chip v-bind="attrs" :input-value="selected" close @click="select" @click:close="remove(item)">
                <strong>{{ item }}</strong>&nbsp;
              </v-chip>
            </template>
          </v-combobox>
        </v-row>
      </v-container>
      <v-card-actions>
        <v-btn text color="primary" @click="dialog = false">Cancel</v-btn>
        <v-btn text @click="dialog = false">Create</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</v-app>
</template>

<script>
export default {
  props: {
    source: String,
  },

  data() {
    return {
      dialog: false,
      drawer: null,
    };
  },

  components: {
  },

  methods: {
  }
};
</script>
