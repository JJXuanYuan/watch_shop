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
  background:
    radial-gradient(circle at top left, rgba(211, 169, 82, 0.26), transparent 28%),
    linear-gradient(180deg, #f5efe4 0%, #efe5d4 100%);
  font-family: "Source Han Sans SC", "Noto Sans SC", sans-serif;
}
</style>
