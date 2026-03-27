<template>
  <router-view />
</template>

<style>
:root {
  color-scheme: light;
  font-family: "IBM Plex Sans", "Noto Sans SC", "Segoe UI", sans-serif;
  color: #1f252b;
  background:
    radial-gradient(circle at top left, rgba(196, 152, 70, 0.18), transparent 24%),
    linear-gradient(180deg, #f4efe4 0%, #ecf0f3 100%);
}

html,
body,
#app {
  margin: 0;
  min-height: 100%;
}

body {
  min-width: 1280px;
}

* {
  box-sizing: border-box;
}

a {
  color: inherit;
  text-decoration: none;
}
</style>
