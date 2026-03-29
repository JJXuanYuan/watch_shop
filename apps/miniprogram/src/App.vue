<script lang="ts">
import { ensureUserSession } from "./utils/session";

export default {
  onLaunch() {
    void ensureUserSession().catch((error) => {
      console.warn(
        "Watch Shop miniprogram login bootstrap failed.",
        error instanceof Error ? error.message : error,
      );
    });
  },
};
</script>

<template></template>

<style>
page {
  min-height: 100%;
  color: #f7f9ff;
  background:
    radial-gradient(circle at 16% -6%, rgba(161, 112, 255, 0.3), transparent 30%),
    radial-gradient(circle at 84% 0%, rgba(70, 211, 255, 0.16), transparent 24%),
    linear-gradient(180deg, #070813 0%, #0a1023 46%, #050711 100%);
  font-family: "Avenir Next", "PingFang SC", "Helvetica Neue", "Source Han Sans SC", sans-serif;
}
</style>
